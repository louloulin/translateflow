# Tools/WebServer/web_server.py
import os
import sys
import json
import threading
import subprocess
import time
import collections
import locale
from typing import List, Dict, Any, Optional

# --- Pre-emptive Import for FastAPI & Pydantic ---
try:
    from fastapi import FastAPI, HTTPException, Body
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
except ImportError:
    # This error will be caught and handled in ainiee_cli.py
    raise ImportError("Required packages are missing. Please run 'uv add fastapi uvicorn[standard] pydantic'.,Or run 'uv sync'")

# --- Add Project Root to Python Path ---
# This ensures that we can import modules from the main project (e.g., ainiee_cli)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Global State & Task Management ---

class TaskManager:
    """A singleton class to manage the CLI task execution state."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.process: Optional[subprocess.Popen] = None
            self.status: str = "idle"  # idle, running, stopping, completed, error
            self.logs = collections.deque(maxlen=500)
            self.chart_data = collections.deque(maxlen=60) # 1 min history at 1s intervals
            self.stats: Dict[str, Any] = self._get_initial_stats()
            self.initialized = True
            
            # Use a separate thread to monitor the process output
            self.monitor_thread: Optional[threading.Thread] = None

    def _get_initial_stats(self) -> Dict[str, Any]:
        return {
            "rpm": 0, "tpm": 0, "totalProgress": 0, "completedProgress": 0,
            "totalTokens": 0, "elapsedTime": 0, "status": "idle",
            "currentFile": "N/A"
        }

    def _log_and_parse(self, stream):
        """Read from a stream, log the output, and parse for stats."""
        # The stream provides correctly decoded strings because of the `encoding` setting in Popen
        for line in iter(stream.readline, ''):
            line = line.strip()
            if not line:
                continue

            # Check for our special stats line
            if line.startswith("[STATS]"):
                try:
                    # Example: [STATS] RPM: 0.00 | TPM: 0.00k | Progress: 0/1435 | Tokens: 0
                    parts = line.split('|')
                    rpm_part = parts[0].split(':')[1].strip()
                    tpm_part = parts[1].split(':')[1].strip().replace('k', '')
                    progress_part = parts[2].split(':')[1].strip()
                    tokens_part = parts[3].split(':')[1].strip()

                    completed, total = map(int, progress_part.split('/'))

                    self.stats["rpm"] = float(rpm_part)
                    self.stats["tpm"] = float(tpm_part) # This is already in k
                    self.stats["completedProgress"] = completed
                    self.stats["totalProgress"] = total
                    self.stats["totalTokens"] = int(tokens_part)
                except (IndexError, ValueError) as e:
                    # Log parsing error if the format is unexpected, but don't crash
                    self.logs.append({"timestamp": time.time(), "message": f"[PARSER_ERROR] Could not parse stats line: {line}. Error: {e}"})
            else:
                # It's a regular log line
                self.logs.append({"timestamp": time.time(), "message": line})



    def start_task(self, payload: Dict[str, Any]) -> bool:
        """Starts the ainiee_cli.py script as a subprocess with config overrides."""
        with self._lock:
            if self.status == "running":
                return False
            
            self.status = "running"
            self.logs.clear()
            self.stats = self._get_initial_stats()
            self.stats["status"] = "running"
            self.logs.append({"timestamp": time.time(), "message": "Task starting with parameters from web UI..."})

            # Base command using corrected keys and uv runner
            cli_args = [
                "uv",
                "run",
                os.path.join(PROJECT_ROOT, "ainiee_cli.py"),
                payload["task"], # Use 'task' key
                payload["input_path"],
                "-y",  # Crucial for non-interactive mode
                "--web-mode" # Activate parsable output
            ]
            
            # Add optional arguments based on the payload
            if payload.get("output_path"):
                cli_args.extend(["--output", payload["output_path"]])
            if payload.get("source_lang"):
                cli_args.extend(["--source", payload["source_lang"]])
            if payload.get("target_lang"):
                cli_args.extend(["--target", payload["target_lang"]])
            if payload.get("resume"):
                cli_args.append("--resume")
            
            # Additional Overrides from Payload
            if payload.get("threads") is not None:
                cli_args.extend(["--threads", str(payload["threads"])])
            if payload.get("retry") is not None:
                cli_args.extend(["--retry", str(payload["retry"])])
            if payload.get("timeout") is not None:
                cli_args.extend(["--timeout", str(payload["timeout"])])
            if payload.get("rounds") is not None:
                cli_args.extend(["--rounds", str(payload["rounds"])])
            if payload.get("pre_lines") is not None:
                cli_args.extend(["--pre-lines", str(payload["pre_lines"])])
            
            if payload.get("model"):
                cli_args.extend(["--model", payload["model"]])
            if payload.get("api_url"):
                cli_args.extend(["--api-url", payload["api_url"]])
            if payload.get("api_key"):
                cli_args.extend(["--api-key", payload["api_key"]])
            
            if payload.get("failover") is True:
                cli_args.extend(["--failover", "on"])
            elif payload.get("failover") is False:
                cli_args.extend(["--failover", "off"])

            if payload.get("lines") is not None:
                cli_args.extend(["--lines", str(payload["lines"])])
            if payload.get("tokens") is not None:
                cli_args.extend(["--tokens", str(payload["tokens"])])
            
            # Determine Profile: Payload > Active Config > Default
            profile_arg = payload.get("profile")
            if not profile_arg:
                try:
                    if os.path.exists(ROOT_CONFIG_FILE):
                        with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                            rc = json.load(f)
                            profile_arg = rc.get("active_profile", "default")
                    else:
                        profile_arg = "default"
                except:
                    profile_arg = "default"
            
            cli_args.extend(["--profile", profile_arg])
            
            # Note: other keys like 'threads' are in the payload but not used here
            # because ainiee_cli.py doesn't have CLI args for them. They are
            # expected to be part of the loaded profile config.

            try:
                # Get the system's preferred console encoding (e.g., 'gbk' on Chinese Windows)
                system_encoding = locale.getpreferredencoding(False)
                self.process = subprocess.Popen(
                    cli_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding=system_encoding,
                    errors='ignore', # Add extra safety
                    bufsize=1
                )
                
                self.monitor_thread = threading.Thread(target=self._process_monitor)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()

                return True
            except Exception as e:
                self.status = "error"
                self.logs.append({"timestamp": time.time(), "message": f"Failed to start process: {e}"})
                return False

    def _process_monitor(self):
        """Monitors the subprocess, which now provides correctly decoded strings."""
        if self.process and self.process.stdout:
            import re
            # Popen now handles the decoding, so we can iterate over strings directly.
            for line in iter(self.process.stdout.readline, ''):
                line = line.strip()
                if line:
                    self.logs.append({"timestamp": time.time(), "message": line})
                    
                    # 1. Parsing current file
                    if "File:" in line:
                        try: self.stats["currentFile"] = line.split("File:")[1].strip().split("|")[0].strip()
                        except: pass
                    
                    # 2. Parsing [STATS] line (Robust Regex)
                    if "[STATS]" in line:
                        try:
                            # RPM
                            rpm_match = re.search(r"RPM:\s*([\d\.]+)", line)
                            if rpm_match: self.stats["rpm"] = float(rpm_match.group(1))
                            
                            # TPM
                            tpm_match = re.search(r"TPM:\s*([\d\.]+k?)", line)
                            if tpm_match: 
                                tpm_val = tpm_match.group(1).replace('k', '')
                                self.stats["tpm"] = float(tpm_val)
                            
                            # Progress (Completed/Total)
                            prog_match = re.search(r"Progress:\s*(\d+)/(\d+)", line)
                            if prog_match:
                                self.stats["completedProgress"] = int(prog_match.group(1))
                                self.stats["totalProgress"] = int(prog_match.group(2))
                            
                            # Tokens
                            tokens_match = re.search(r"Tokens:\s*(\d+)", line)
                            if tokens_match: self.stats["totalTokens"] = int(tokens_match.group(1))
                            
                            # Append to Chart Data
                            self.chart_data.append({
                                "time": time.strftime('%H:%M:%S'),
                                "rpm": self.stats["rpm"],
                                "tpm": self.stats["tpm"]
                            })
                            
                        except Exception as e:
                            # Non-fatal parsing error
                            pass
        
        if self.process:
            self.process.wait()
        
        with self._lock:
            if self.status == "running":
                if self.process and self.process.returncode == 0:
                    self.status = "completed"
                    self.stats["status"] = "completed"
                else:
                    self.status = "error"
                    self.stats["status"] = "error"
            self.process = None

    def stop_task(self):
        """Stops the running task."""
        with self._lock:
            if self.status != "running" or not self.process:
                return
            
            self.status = "stopping"
            self.stats["status"] = "stopping"
            self.logs.append({"timestamp": time.time(), "message": "Sending stop signal..."})
            
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.logs.append({"timestamp": time.time(), "message": "Process did not respond, forcing kill."})
            
            self.status = "idle"
            self.stats["status"] = "idle"
            self.logs.append({"timestamp": time.time(), "message": "Task stopped."})


task_manager = TaskManager()

# --- Simple In-Memory Caches for API Endpoints ---
_version_cache: Dict[str, Any] = {}
_config_cache: Dict[str, Any] = {}
_profiles_cache: Optional[List[str]] = None

# --- Profile Handlers (Dependency Injection) ---
# Allows the host application (ainiee_cli.py) to override logic
profile_handlers: Dict[str, Any] = {
    "create": None,
    "rename": None,
    "delete": None
}

# --- Pydantic Models for API Requests ---

class AppConfig(BaseModel):
    # This needs to match the structure of the config JSON files
    # Define a few key fields for demonstration
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    actual_thread_counts: Optional[int] = None
    # Add other fields from your config...
    class Config:
        extra = 'allow' # Allow extra fields not defined here

class ProfileSwitchRequest(BaseModel):
    profile: str

class ProfileCreateRequest(BaseModel):
    name: str
    base: Optional[str] = None

class ProfileRenameRequest(BaseModel):
    old_name: str
    new_name: str

class ProfileDeleteRequest(BaseModel):
    profile: str

class TaskPayload(BaseModel):
    """Pydantic model that EXACTLY matches the frontend's TaskPayload interface in types.ts"""
    task: str
    input_path: str
    output_path: Optional[str] = None
    project_type: Optional[str] = None
    resume: Optional[bool] = False
    profile: Optional[str] = None # Added profile field
    
    # Overrides
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    threads: Optional[int] = None
    retry: Optional[int] = None
    timeout: Optional[int] = None
    rounds: Optional[int] = None
    pre_lines: Optional[int] = None
    
    # Platform Overrides
    platform: Optional[str] = None
    model: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    failover: Optional[bool] = None
    
    # Limits
    lines: Optional[int] = None
    tokens: Optional[int] = None

# --- FastAPI Application ---

app = FastAPI(title="AiNiee CLI Backend API")

# --- Paths to Resources ---
RESOURCE_PATH = os.path.join(PROJECT_ROOT, "Resource")
VERSION_FILE = os.path.join(RESOURCE_PATH, "Version", "version.json")
PROFILES_PATH = os.path.join(RESOURCE_PATH, "profiles")
ROOT_CONFIG_FILE = os.path.join(RESOURCE_PATH, "config.json")
WEB_SERVER_PATH = os.path.join(PROJECT_ROOT, "Tools", "WebServer")

# --- Helper Functions ---

def get_config_mode():
    """Checks if the config is in 'profile' mode or 'legacy' single-file mode."""
    if not os.path.exists(ROOT_CONFIG_FILE):
        return "legacy", {}
    try:
        with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        if "active_profile" in config:
            return "profile", config
        else:
            return "legacy", config
    except (IOError, json.JSONDecodeError):
        return "legacy", {}

def get_active_profile_path() -> str:
    """Gets the full path to the active profile JSON file."""
    mode, config = get_config_mode()
    if mode == "legacy":
        return ROOT_CONFIG_FILE
    
    profile_name = config.get("active_profile", "default")
    return os.path.join(PROFILES_PATH, f"{profile_name}.json")

# --- API Endpoints ---

@app.get("/api/version")
async def get_version():
    global _version_cache
    if "version" in _version_cache:
        return _version_cache["version"]

    if not os.path.exists(VERSION_FILE):
        raise HTTPException(status_code=404, detail="version.json not found")
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        version_data = json.load(f)
        _version_cache["version"] = version_data
        return version_data

@app.get("/api/config")
async def get_config():
    """
    Returns the content of the active configuration.
    Handles both legacy (single config.json) and profile-based configs.
    Ensures critical keys expected by the frontend are present, and caches results.
    """
    global _config_cache
    
    mode, config_data_from_root = get_config_mode()
    current_profile_name = config_data_from_root.get("active_profile", "legacy" if mode == "legacy" else "default")

    if current_profile_name in _config_cache:
        return _config_cache[current_profile_name]

    if mode == "legacy":
        loaded_config = config_data_from_root # In legacy mode, root config is the full config
    else: # profile mode
        profile_path = get_active_profile_path()
        if not os.path.exists(profile_path):
            loaded_config = {} # Return empty if profile file not found
        else:
            try:
                with open(profile_path, 'r', encoding='utf-8-sig') as f:
                    loaded_config = json.load(f)
            except (IOError, json.JSONDecodeError):
                loaded_config = {} # Return empty on read error

    # --- Frontend Compatibility Patch ---
    # The frontend expects 'response_check_switch' to exist. If it doesn't,
    # the settings page will crash on render. We add a default here.
    loaded_config["active_profile"] = current_profile_name
    
    if "response_check_switch" not in loaded_config:
        loaded_config["response_check_switch"] = {
            "newline_character_count_check": False,
            "return_to_original_text_check": False,
            "residual_original_text_check": False,
            "reply_format_check": False
        }
    
    _config_cache[current_profile_name] = loaded_config
    return loaded_config


@app.post("/api/config")
async def save_config(config: AppConfig):
    """
    Saves the provided JSON to the active configuration file.
    Handles both legacy and profile-based configs, and invalidates cache.
    """
    global _config_cache, _profiles_cache # Need to clear these caches
    
    target_path = get_active_profile_path()
    mode, config_data_from_root = get_config_mode()
    current_profile_name = config_data_from_root.get("active_profile", "legacy" if mode == "legacy" else "default")

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            config_dict = config.model_dump(exclude_unset=True) if hasattr(config, 'model_dump') else config.dict(exclude_unset=True)
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
        
        # Invalidate the cache for this specific profile or the legacy config
        if current_profile_name in _config_cache:
            del _config_cache[current_profile_name]
        # Also clear profiles cache as new profiles might have been created/renamed/deleted implicitly
        _profiles_cache = None

        return {"message": "Config saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to config file: {e}")

@app.get("/api/profiles", response_model=List[str])
async def get_profiles():
    """
    Returns a list of available profile filenames, utilizing cache.
    """
    global _profiles_cache

    if _profiles_cache is not None:
        return _profiles_cache

    if not os.path.isdir(PROFILES_PATH):
        _profiles_cache = ["default"]
        return _profiles_cache
    
    profiles = [f.replace(".json", "") for f in os.listdir(PROFILES_PATH) if f.endswith(".json")]
    _profiles_cache = profiles
    return profiles

@app.post("/api/profiles/switch")
async def switch_profile(request: ProfileSwitchRequest):
    """
    Switches the active profile, returns the new active config, and invalidates caches.
    """
    global _config_cache, _profiles_cache # Need to clear these caches
    
    profile_name = request.profile
    profile_path = os.path.join(PROFILES_PATH, f"{profile_name}.json")
    
    if not os.path.exists(profile_path):
        raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found.")
    
    try:
        # Update the root config to point to the new profile
        root_config = {}
        if os.path.exists(ROOT_CONFIG_FILE):
            with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                root_config = json.load(f)
        root_config["active_profile"] = profile_name
        with open(ROOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(root_config, f, indent=4, ensure_ascii=False)
        
        # Invalidate all config caches and profiles cache
        _config_cache.clear()
        _profiles_cache = None

        # Return the content of the new active profile (will be cached by get_config on next call)
        with open(profile_path, 'r', encoding='utf-8-sig') as f:
            new_active_config = json.load(f)
            new_active_config["active_profile"] = profile_name
            
            # Apply frontend compatibility patch for the returned config as well
            if "response_check_switch" not in new_active_config:
                new_active_config["response_check_switch"] = {
                    "newline_character_count_check": False,
                    "return_to_original_text_check": False,
                    "residual_original_text_check": False,
                    "reply_format_check": False
                }
            return new_active_config
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch profile: {e}")

@app.post("/api/profiles/create")
async def create_profile(request: ProfileCreateRequest):
    global _profiles_cache
    
    new_name = request.name
    if not new_name or not new_name.strip():
        raise HTTPException(status_code=400, detail="Profile name cannot be empty")

    # Use injected handler if available
    if profile_handlers["create"]:
        try:
            profile_handlers["create"](new_name, request.base)
            _profiles_cache = None
            return {"message": f"Profile '{new_name}' created successfully (via host)"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    new_path = os.path.join(PROFILES_PATH, f"{new_name}.json")
    if os.path.exists(new_path):
        raise HTTPException(status_code=409, detail="Profile already exists")

    # Determine base profile to copy from
    base_name = request.base
    if not base_name:
        # Use active profile as base
        mode, config = get_config_mode()
        base_name = config.get("active_profile", "default")
    
    base_path = os.path.join(PROFILES_PATH, f"{base_name}.json")
    preset_path = os.path.join(RESOURCE_PATH, "platforms", "preset.json")

    try:
        # Robust Creation Logic: Preset + Base -> New
        final_config = {}
        
        # 1. Load Preset
        if os.path.exists(preset_path):
            with open(preset_path, 'r', encoding='utf-8') as f:
                final_config = json.load(f)
        
        # 2. Load Base (Overlay)
        if os.path.exists(base_path):
            with open(base_path, 'r', encoding='utf-8') as f:
                base_config = json.load(f)
                # Deep merge could be complex, for now simple update is usually enough for flat configs
                # For nested configs like 'platforms', we might want deep merge, but standard dict update is standard fallback
                final_config.update(base_config)
        elif not final_config:
             # No preset and no base? Empty.
             final_config = {}

        # 3. Save
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(final_config, f, indent=4, ensure_ascii=False)

        _profiles_cache = None # Invalidate cache
        return {"message": f"Profile '{new_name}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {e}")

@app.post("/api/profiles/rename")
async def rename_profile(request: ProfileRenameRequest):
    global _profiles_cache, _config_cache
    
    # Use injected handler
    if profile_handlers["rename"]:
        try:
            profile_handlers["rename"](request.old_name, request.new_name)
            _profiles_cache = None
            _config_cache.clear()
            return {"message": f"Renamed '{request.old_name}' to '{request.new_name}' (via host)"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    old_path = os.path.join(PROFILES_PATH, f"{request.old_name}.json")
    new_path = os.path.join(PROFILES_PATH, f"{request.new_name}.json")
    
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Source profile not found")
    if os.path.exists(new_path):
        raise HTTPException(status_code=409, detail="Destination profile name already exists")
        
    try:
        os.rename(old_path, new_path)
        
        # Check if we renamed the active profile
        mode, config = get_config_mode()
        current_active = config.get("active_profile")
        
        if current_active == request.old_name:
            # Update root config to point to new name
            config["active_profile"] = request.new_name
            with open(ROOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Clear config cache as the key changed
            _config_cache.clear()
            
        _profiles_cache = None
        return {"message": f"Renamed '{request.old_name}' to '{request.new_name}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename profile: {e}")

@app.post("/api/profiles/delete")
async def delete_profile(request: ProfileDeleteRequest):
    global _profiles_cache
    
    # Use injected handler
    if profile_handlers["delete"]:
        try:
            profile_handlers["delete"](request.profile)
            _profiles_cache = None
            return {"message": f"Profile '{request.profile}' deleted (via host)"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    target_path = os.path.join(PROFILES_PATH, f"{request.profile}.json")
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Profile not found")

    # Check if active
    mode, config = get_config_mode()
    if config.get("active_profile") == request.profile:
        raise HTTPException(status_code=400, detail="Cannot delete the currently active profile. Please switch to another profile first.")

    # Check if it's the last one (optional safety, though frontend should handle)
    profiles = [f for f in os.listdir(PROFILES_PATH) if f.endswith(".json")]
    if len(profiles) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only remaining profile.")

    try:
        os.remove(target_path)
        _profiles_cache = None
        return {"message": f"Profile '{request.profile}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {e}")

# --- Task API Endpoints ---

@app.post("/api/task/run")
async def run_task(payload: TaskPayload):
    if task_manager.status == "running":
        raise HTTPException(status_code=409, detail="A task is already running.")
    
    if not task_manager.start_task(payload.dict()):
        raise HTTPException(status_code=500, detail="Failed to start task process.")
    
    return {"success": True, "message": "Task started successfully."}

@app.post("/api/task/stop")
async def stop_task():
    task_manager.stop_task()
    return {"message": "Stop signal sent."}

@app.get("/api/task/status")
async def get_task_status():
    return {
        "stats": task_manager.stats,
        "logs": list(task_manager.logs),
        "chart_data": list(task_manager.chart_data)
    }

# --- Static File Serving for the React Frontend ---

# This will serve the built React app (index.html, JS, CSS files)
# The React app should be built into a `dist` directory inside `Tools/WebServer`
dist_path = os.path.join(WEB_SERVER_PATH, 'dist')

if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

@app.get("/")
async def serve_index():
    """Serves the main index.html file of the React app."""
    index_path = os.path.join(dist_path, 'index.html')
    if not os.path.exists(index_path):
        # Fallback for development mode where `dist` might not exist
        return {"message": "AiNiee Backend is running. Frontend `dist` directory not found."}
    return FileResponse(index_path)

# --- Main Server Runner Function (to be called from ainiee_cli.py) ---

def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the FastAPI server in a separate thread."""
    try:
        import uvicorn

        def server_task():
            # Use reload=True for development, but it's better to disable it for production
            uvicorn.run(app, host=host, port=port, log_level="info")

        # Running in a daemon thread allows the main TUI to exit cleanly
        thread = threading.Thread(target=server_task, daemon=True)
        thread.start()
        return thread
    except ImportError:
        # This should ideally be handled before calling run_server
        print("Error: Uvicorn is required to run the web server.")
        return None

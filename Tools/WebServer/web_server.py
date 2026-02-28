# Tools/WebServer/web_server.py
import os
import sys
import json
import threading
import subprocess
import time
import collections
import locale
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Pre-emptive Import for FastAPI & Pydantic ---
try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Response, BackgroundTasks, Depends, Header, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
    from pydantic import BaseModel
    from typing import Optional
except ImportError:
    # This error will be caught and handled in ainiee_cli.py
    raise ImportError("Required packages are missing. Please run 'uv add fastapi uvicorn[standard] pydantic python-multipart'.,Or run 'uv sync'")

# --- Add Project Root to Python Path ---
# This ensures that we can import modules from the main project (e.g., ainiee_cli)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
UPDATETEMP_PATH = os.path.join(PROJECT_ROOT, "updatetemp") # Define upload directory
TEMP_EDIT_PATH = os.path.join(PROJECT_ROOT, "output", "temp_edit") # Define draft directory

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
            self.current_source = ""      # 当前批次原文
            self.current_translation = "" # 当前批次译文
            self.api_url = "http://127.0.0.1:8000" # 默认地址
            
            # Use a separate thread to monitor the process output
            self.monitor_thread: Optional[threading.Thread] = None

    def _get_initial_stats(self) -> Dict[str, Any]:
        return {
            "rpm": 0, "tpm": 0, "totalProgress": 0, "completedProgress": 0,
            "totalTokens": 0, "elapsedTime": 0, "status": "idle",
            "currentFile": "N/A", "successRate": 0, "errorRate": 0
        }

    def push_log(self, message: str, type: str = "info"):
        """Directly push a log message from the host process."""
        self.logs.append({"timestamp": time.time(), "message": message, "type": type})

    def push_comparison(self, source: str, translation: str):
        """Update the side-by-side comparison data from the host process."""
        self.current_source = source
        self.current_translation = translation

    def push_stats(self, stats: Dict[str, Any]):
        """Directly push stats from the host process."""
        self.stats.update(stats)
        # Also update chart data
        self.chart_data.append({
            "time": time.strftime('%H:%M:%S'),
            "rpm": self.stats.get("rpm", 0),
            "tpm": self.stats.get("tpm", 0)
        })

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
            self.chart_data.clear()
            self.current_source = ""
            self.current_translation = ""
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

            # Debug: Log the command being executed
            import shutil
            uv_path = shutil.which("uv")
            self.logs.append({"timestamp": time.time(), "message": f"[DEBUG] UV Path: {uv_path}"})
            self.logs.append({"timestamp": time.time(), "message": f"[DEBUG] Command: {' '.join(cli_args)}"})
            
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
            
            if payload.get("profile"):
                cli_args.extend(["--profile", payload["profile"]])
            if payload.get("rules_profile"):
                cli_args.extend(["--rules-profile", payload["rules_profile"]])
            
            # Note: other keys like 'threads' are in the payload but not used here
            # because ainiee_cli.py doesn't have CLI args for them. They are
            # expected to be part of the loaded profile config.

            try:
                # Get the system's preferred console encoding (e.g., 'gbk' on Chinese Windows)
                system_encoding = locale.getpreferredencoding(False)

                # 注入环境变量以便子进程知道 WebServer 的内部接口位置
                import os as system_os
                env = system_os.environ.copy()
                # 获取当前 WebServer 的运行地址
                env["AINIEE_INTERNAL_API_URL"] = task_manager.api_url
                # 强制子进程使用 UTF-8 编码输出，防止在 Windows 下产生编码冲突
                env["PYTHONIOENCODING"] = "utf-8"
                # 标记该进程为后端 Worker，与核心主进程（WebServer）区分
                env["AINIEE_BACKEND_WORKER"] = "1"

                self.process = subprocess.Popen(
                    cli_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace', # 增加解码容错，防止非法字符导致线程崩溃
                    bufsize=1,
                    cwd=PROJECT_ROOT,
                    env=env # 传递环境变量
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
                    print(f"[SUBPROCESS OUT] {line}") # DEBUG: Print to server console
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

                            # Success/Error Rate
                            s_rate_match = re.search(r"S-Rate:\s*([\d\.]+)%", line)
                            if s_rate_match: self.stats["successRate"] = float(s_rate_match.group(1))
                            
                            e_rate_match = re.search(r"E-Rate:\s*([\d\.]+)%", line)
                            if e_rate_match: self.stats["errorRate"] = float(e_rate_match.group(1))
                            
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
            self.logs.append({"timestamp": time.time(), "message": "Sending force stop signal..."})
            
            try:
                # Direct force kill as requested (Data safety guaranteed by cache)
                self.process.kill()
                self.process.wait(timeout=2)
            except Exception as e:
                self.logs.append({"timestamp": time.time(), "message": f"Force stop error: {e}"})
            
            self.status = "idle"
            self.stats["status"] = "idle"
            self.logs.append({"timestamp": time.time(), "message": "Task stopped."})


task_manager = TaskManager()

# --- Global System Mode ---
# monitor: Only monitoring is allowed
# full: Full control (default)
SYSTEM_MODE = "full"

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
    temp_file_limit: Optional[int] = 10
    cache_editor_page_size: Optional[int] = 15
    # Add other fields from your config...
    class Config:
        extra = 'allow' # Allow extra fields not defined here

class ProfileSwitchRequest(BaseModel):
    profile: str

class RulesProfileSwitchRequest(BaseModel):
    profile: str

class ProfileCreateRequest(BaseModel):
    name: str
    base: Optional[str] = None

class ProfileRenameRequest(BaseModel):
    old_name: str
    new_name: str

class ProfileDeleteRequest(BaseModel):
    profile: str

class GlossaryItem(BaseModel):
    src: str
    dst: str
    info: Optional[str] = None

class TermOption(BaseModel):
    dst: str
    info: str

class TermRetryRequest(BaseModel):
    src: str
    type: str
    avoid: List[str]
    temp_config: Optional[Dict[str, Any]] = None

class ExclusionItem(BaseModel):
    markers: str
    info: Optional[str] = None
    regex: Optional[str] = None

class CharacterizationItem(BaseModel):
    original_name: str
    translated_name: str
    gender: Optional[str] = ""
    age: Optional[str] = ""
    personality: Optional[str] = ""
    speech_style: Optional[str] = ""
    additional_info: Optional[str] = ""

class TranslationExampleItem(BaseModel):
    src: str
    dst: str

class StringContent(BaseModel):
    content: str

class PluginEnableRequest(BaseModel):
    name: str
    enabled: bool

class DeleteFileRequest(BaseModel):
    files: List[str]

class QueueTaskItem(BaseModel):
    task_type: int
    input_path: str
    output_path: Optional[str] = None
    profile: Optional[str] = None
    rules_profile: Optional[str] = None
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    project_type: Optional[str] = None
    platform: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    threads: Optional[int] = None
    retry: Optional[int] = None
    timeout: Optional[int] = None
    rounds: Optional[int] = None
    pre_lines: Optional[int] = None
    lines_limit: Optional[int] = None
    tokens_limit: Optional[int] = None
    think_depth: Optional[str] = None
    thinking_budget: Optional[int] = None
    status: Optional[str] = "waiting"

class QueueMoveRequest(BaseModel):
    to_index: int

class QueueReorderRequest(BaseModel):
    new_order: List[int]

class QueueRawRequest(BaseModel):
    content: str

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
RULES_PROFILES_PATH = os.path.join(RESOURCE_PATH, "rules_profiles")
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

def get_active_rules_profile_path() -> str:
    """Gets the full path to the active rules profile JSON file."""
    mode, root_config = get_config_mode()
    rules_profile = root_config.get("active_rules_profile", "default")
    os.makedirs(RULES_PROFILES_PATH, exist_ok=True)
    return os.path.join(RULES_PROFILES_PATH, f"{rules_profile}.json")

def save_rule_generic(key: str, value: Any):
    """Helper to save a specific rule key to the active RULES profile."""
    global _config_cache
    target_path = get_active_rules_profile_path()
    try:
        current_rules = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r', encoding='utf-8-sig') as f:
                    current_rules = json.load(f)
            except: pass
        current_rules[key] = value
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(current_rules, f, indent=4, ensure_ascii=False)
        _config_cache.clear()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save rule {key}: {e}")

def save_config_generic(key: str, value: Any):
    """Helper to save a specific key to the active SETTINGS profile."""
    global _config_cache
    target_path = get_active_profile_path()
    try:
        current_config = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r', encoding='utf-8-sig') as f:
                    current_config = json.load(f)
            except: pass
        current_config[key] = value
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=4, ensure_ascii=False)
        _config_cache.clear()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save setting {key}: {e}")

# --- API Endpoints ---

@app.get("/api/system/mode")
async def get_system_mode():
    return {"mode": SYSTEM_MODE}

@app.get("/api/system/status")
async def get_system_status():
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "boot_time": psutil.boot_time()
        }
    except ImportError:
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "boot_time": 0,
            "error": "psutil not installed"
        }

@app.post("/api/system/update")
async def update_system():
    try:
        # Run git pull
        result = subprocess.run(["git", "pull"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        return {"success": result.returncode == 0, "output": result.stdout + "\n" + result.stderr}
    except Exception as e:
        return {"success": False, "output": str(e)}

@app.post("/api/system/restart")
async def restart_system():
    """Restarts the server process."""
    def restart():
        time.sleep(1)
        # Re-execute the current script
        # Note: This might not work perfectly in all environments (e.g. docker, supervisor)
        # But for local dev it's usually fine.
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    threading.Thread(target=restart).start()
    return {"message": "Server is restarting..."}


# --- Auth Models ---

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str
    reset_url_base: Optional[str] = "https://translateflow.example.com/reset-password"


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class PasswordResetResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    user: Dict[str, Any]
    access_token: str
    refresh_token: str
    token_type: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    status: str


# --- User Management Request/Response Models ---

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UpdateEmailRequest(BaseModel):
    new_email: str
    password: str


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: Optional[str] = None


class UpdateUserRoleRequest(BaseModel):
    new_role: str


class UpdateUserStatusRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None


class UserListResponse(BaseModel):
    users: List[Dict[str, Any]]
    pagination: Dict[str, Any]


class LoginHistoryResponse(BaseModel):
    records: List[Dict[str, Any]]
    pagination: Dict[str, Any]


# --- Subscription Management Models ---

class CreateSubscriptionRequest(BaseModel):
    """创建订阅请求"""
    plan: str  # free, starter, pro, enterprise
    success_url: str = "http://localhost:8000/billing/success"
    cancel_url: str = "http://localhost:8000/billing/cancel"


class UpdateSubscriptionRequest(BaseModel):
    """更新订阅请求"""
    new_plan: str  # starter, pro, enterprise


class CancelSubscriptionRequest(BaseModel):
    """取消订阅请求"""
    at_period_end: bool = True  # True=周期结束时取消，False=立即取消


# --- Auth Dependencies ---

# Import JWT middleware from Auth module
from ModuleFolders.Service.Auth import jwt_middleware, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_client_ip(request):
    """Get client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --- Auth Routes ---

@app.post("/api/v1/auth/register", response_model=LoginResponse)
async def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    """Register a new user account."""
    try:
        # Import here to avoid circular imports
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        # Initialize database if needed
        try:
            init_database()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Database init error: {e}")
            pass  # Database might already be initialized

        auth_manager = get_auth_manager()

        # Get client info
        ip_address = "127.0.0.1"  # Will be updated with actual IP in production
        user_agent = "Web UI"

        result = auth_manager.register(
            email=request.email,
            username=request.username,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()

        # Get client info
        ip_address = "127.0.0.1"  # Will be updated with actual IP in production
        user_agent = "Web UI"

        result = auth_manager.login(
            email=form_data.username,  # OAuth2 uses username field for email
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/v1/auth/refresh", response_model=RefreshResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Refresh access token using refresh token."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()

        result = auth_manager.refresh_access_token(refresh_token)
        return result

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/v1/auth/logout")
async def logout(refresh_token: str = Body(..., embed=True)):
    """Logout user and revoke refresh token."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()
        auth_manager.logout(refresh_token)

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request a password reset email."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()
        result = auth_manager.forgot_password(
            email=request.email,
            reset_url_base=request.reset_url_base,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """Reset password using the reset token."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()
        result = auth_manager.reset_password(
            token=request.token,
            new_password=request.new_password,
        )
        return {"message": result.get("message", "Password reset successfully")}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/auth/verify-email")
async def verify_email(token: str = Query(..., description="Email verification token")):
    """Verify user's email using the verification token."""
    try:
        from ModuleFolders.Service.Auth import init_database, get_auth_manager

        try:
            init_database()
        except Exception:
            pass

        auth_manager = get_auth_manager()
        result = auth_manager.verify_email(token=token)
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """Get current user information."""
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "status": user.status,
    }


# --- Protected Route Examples ---

@app.get("/api/v1/auth/protected")
async def protected_route(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    Example of a protected route that requires authentication.
    Only authenticated users can access this endpoint.
    """
    return {
        "message": "This is a protected endpoint",
        "user_id": str(user.id),
        "username": user.username,
    }


@app.get("/api/v1/auth/optional")
async def optional_auth_route(
    user: Optional[User] = Depends(jwt_middleware.get_current_user_optional)
):
    """
    Example of a route with optional authentication.
    Returns user info if authenticated, otherwise returns anonymous response.
    """
    if user:
        return {
            "authenticated": True,
            "user_id": str(user.id),
            "username": user.username,
        }
    return {
        "authenticated": False,
        "message": "Anonymous user"
    }


@app.get("/api/v1/auth/admin")
async def admin_only_route(
    user: User = Depends(jwt_middleware.require_admin())
):
    """
    Example of an admin-only route.
    Only users with 'admin' or 'superuser' role can access.
    """
    return {
        "message": "Welcome, admin!",
        "user_id": str(user.id),
        "username": user.username,
    }


@app.get("/api/version")
async def get_version():
    global _version_cache
    if "version" in _version_cache:
        return _version_cache["version"]

    if not os.path.exists(VERSION_FILE):
        # Fallback to a default if file is missing
        return {"version": "V0.0.0 (Version file not found)"}
        
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            _version_cache["version"] = version_data
            return version_data
    except:
        return {"version": "V0.0.0 (Read Error)"}

@app.post("/api/config")
async def save_config(config: AppConfig):
    """
    Saves the provided JSON to the active configuration file (settings only).
    """
    global _config_cache
    target_path = get_active_profile_path()

    # Identify keys that belong to rules (to exclude them from settings save)
    rule_keys = [
        "prompt_dictionary_data", "exclusion_list_data", "characterization_data",
        "world_building_content", "writing_style_content", "translation_example_data"
    ]

    try:
        config_dict = config.model_dump(exclude_unset=True) if hasattr(config, 'model_dump') else config.dict(exclude_unset=True)

        # Filter out rule data to prevent corruption/desync
        settings_only = {k: v for k, v in config_dict.items() if k not in rule_keys}

        # Read existing config first to preserve fields not sent by frontend
        current_config = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r', encoding='utf-8-sig') as f:
                    current_config = json.load(f)
            except:
                pass

        # Merge new settings into existing config
        current_config.update(settings_only)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=4, ensure_ascii=False)

        _config_cache.clear()
        return {"message": "Settings saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to config file: {e}")

@app.get("/api/config")
async def get_config():
    """
    Returns the content of the active configuration merged with active rules.
    """
    global _config_cache
    
    mode, root_config = get_config_mode()
    current_profile_name = root_config.get("active_profile", "default")
    current_rules_name = root_config.get("active_rules_profile", "default")

    cache_key = f"{current_profile_name}_{current_rules_name}"
    if cache_key in _config_cache:
        return _config_cache[cache_key]

    # 1. Load Base Config
    profile_path = get_active_profile_path()
    loaded_config = {}
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r', encoding='utf-8-sig') as f:
                loaded_config = json.load(f)
        except: pass

    # 2. Load Rules Config
    rules_config = {}
    if current_rules_name and current_rules_name != "None":
        rules_path = get_active_rules_profile_path()
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r', encoding='utf-8-sig') as f:
                    rules_config = json.load(f)
            except: pass

    # 3. Merge (Rules override Profile if keys overlap)
    rule_keys = [
        "prompt_dictionary_data", "exclusion_list_data", "characterization_data",
        "world_building_content", "writing_style_content", "translation_example_data"
    ]
    
    for k in rule_keys:
        if k in rules_config:
            loaded_config[k] = rules_config[k]

    # Meta
    loaded_config["active_profile"] = current_profile_name
    loaded_config["active_rules_profile"] = current_rules_name

    # 防护：确保 response_check_switch 是正确的 dict 类型
    default_check_switch = {
        "newline_character_count_check": False, "return_to_original_text_check": False,
        "residual_original_text_check": False, "reply_format_check": False
    }
    if "response_check_switch" not in loaded_config or not isinstance(loaded_config.get("response_check_switch"), dict):
        loaded_config["response_check_switch"] = default_check_switch

    _config_cache[cache_key] = loaded_config
    return loaded_config

def save_config_generic(key: str, value: Any):
    """Helper to save a specific key to the active profile."""
    global _config_cache
    target_path = get_active_profile_path()
    try:
        # Load existing config to preserve other fields
        current_config = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, 'r', encoding='utf-8-sig') as f:
                    current_config = json.load(f)
            except:
                pass # If file is corrupt, we might overwrite, or maybe backup first? For now, we proceed.
        
        current_config[key] = value
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, indent=4, ensure_ascii=False)
            
        _config_cache.clear()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save {key}: {e}")

@app.get("/api/glossary", response_model=List[GlossaryItem])
async def get_glossary():
    config = await get_config()
    return config.get("prompt_dictionary_data", [])

@app.post("/api/glossary")
async def save_glossary(items: List[GlossaryItem]):
    save_rule_generic("prompt_dictionary_data", [item.dict() for item in items])
    return {"message": "Glossary saved successfully."}

@app.post("/api/glossary/add")
async def add_glossary_item(item: GlossaryItem):
    current = await get_glossary()
    # Check if exists - current items may be dicts
    found = False
    for i, existing in enumerate(current):
        existing_src = existing.src if hasattr(existing, 'src') else existing.get('src', '')
        if existing_src == item.src:
            current[i] = item
            found = True
            break

    if not found:
        current.append(item)

    save_rule_generic("prompt_dictionary_data", [i.dict() if hasattr(i, 'dict') else i for i in current])
    return {"message": "Term added to glossary."}

@app.post("/api/glossary/batch-add")
async def batch_add_glossary_items(request: Dict[str, List[GlossaryItem]]):
    items = request.get("terms", [])
    current = await get_glossary()

    # Build map from current glossary (handle both dict and GlossaryItem)
    current_map = {}
    for it in current:
        if isinstance(it, dict):
            current_map[it.get('src', '')] = it
        else:
            current_map[it.src] = it

    # Add/update items (items from request are dicts)
    for item in items:
        if isinstance(item, dict):
            src = item.get('src', '')
            current_map[src] = item
        else:
            current_map[item.src] = item.dict() if hasattr(item, 'dict') else item

    # Save all as dicts
    save_rule_generic("prompt_dictionary_data", list(current_map.values()))
    return {"message": f"Successfully added {len(items)} terms."}

@app.post("/api/term/retry")
async def retry_term_translation(request: TermRetryRequest):
    try:
        from ModuleFolders.Infrastructure.LLMRequester.LLMRequester import LLMRequester
        from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig
        from ModuleFolders.Infrastructure.TaskConfig.TaskType import TaskType

        # 1. Load configuration
        config = await get_config()
        task_config = TaskConfig()
        task_config.load_config_from_dict(config)
        
        # 2. Handle temporary overrides if provided
        if request.temp_config:
            platform_name = request.temp_config.get("platform")
            if platform_name:
                # Ensure the platform exists in config
                if platform_name not in task_config.platforms:
                    # Create a default structure if it's a new platform tag
                    task_config.platforms[platform_name] = {
                        "tag": platform_name,
                        "name": platform_name,
                        "group": "custom",
                        "api_format": "OpenAI"
                    }
                
                # Update specific fields
                plat_ref = task_config.platforms[platform_name]
                if request.temp_config.get("api_key"): plat_ref["api_key"] = request.temp_config["api_key"]
                if request.temp_config.get("api_url"): plat_ref["api_url"] = request.temp_config["api_url"]
                if request.temp_config.get("model"): plat_ref["model"] = request.temp_config["model"]
                
                # Set as active platform for this request
                task_config.api_settings["translate"] = platform_name

        # 3. Prepare task config (this handles model normalization, URL completion, API key rotation)
        task_config.prepare_for_translation(TaskType.TRANSLATION)
        platform_config = task_config.get_platform_configuration("translationReq")
        target_language = task_config.target_language
        
        # 4. Construct Prompt (Match ainiee_cli.py logic)
        term_type = request.type or "专有名词"
        avoid_hint = ""
        if request.avoid:
            avoid_list = ", ".join(request.avoid[:5])
            avoid_hint = f"\nPlease provide a different translation from: {avoid_list}"

        system_prompt = f"""You are a terminology translator. Translate the term into "{target_language}".
Term type: {term_type}
{avoid_hint}

Output format (use | as separator):
Translation|Note"""

        messages = [{"role": "user", "content": request.src}]

        # 5. Execute Request
        requester = LLMRequester()
        skip, _, response, _, _ = requester.sent_request(messages, system_prompt, platform_config)
        
        if skip or not response:
            raise HTTPException(status_code=500, detail="LLM request failed or was skipped")
            
        # 6. Parse Response (Match ainiee_cli.py logic)
        response_text = response.strip()
        if '|' in response_text:
            parts = response_text.split('|', 1)
            dst = parts[0].strip()
            info = parts[1].strip() if len(parts) > 1 else ""
        else:
            dst = response_text
            info = ""
            
        # Post-process dst
        if dst.startswith(("Translation:", "译文:", "译文：")):
            dst = dst.split(":", 1)[-1].split("：", 1)[-1].strip()
        dst = dst.strip('"').strip("'")
            
        return {"dst": dst, "info": info}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exclusion", response_model=List[ExclusionItem])
async def get_exclusion():
    config = await get_config()
    return config.get("exclusion_list_data", [])

@app.post("/api/exclusion")
async def save_exclusion(items: List[ExclusionItem]):
    save_rule_generic("exclusion_list_data", [item.dict() for item in items])
    return {"message": "Exclusion list saved successfully."}

# --- New Features Endpoints ---

@app.get("/api/characterization", response_model=List[CharacterizationItem])
async def get_characterization():
    config = await get_config()
    return config.get("characterization_data", [])

@app.post("/api/characterization")
async def save_characterization(items: List[CharacterizationItem]):
    save_rule_generic("characterization_data", [item.dict() for item in items])
    return {"message": "Characterization saved."}

@app.get("/api/world_building", response_model=StringContent)
async def get_world_building():
    config = await get_config()
    return {"content": config.get("world_building_content", "")}

@app.post("/api/world_building")
async def save_world_building(data: StringContent):
    save_rule_generic("world_building_content", data.content)
    return {"message": "World building saved."}

@app.get("/api/writing_style", response_model=StringContent)
async def get_writing_style():
    config = await get_config()
    return {"content": config.get("writing_style_content", "")}

@app.post("/api/writing_style")
async def save_writing_style(data: StringContent):
    save_rule_generic("writing_style_content", data.content)
    return {"message": "Writing style saved."}

@app.get("/api/translation_example", response_model=List[TranslationExampleItem])
async def get_translation_example():
    config = await get_config()
    return config.get("translation_example_data", [])

@app.post("/api/translation_example")
async def save_translation_example(items: List[TranslationExampleItem]):
    save_rule_generic("translation_example_data", [item.dict() for item in items])
    return {"message": "Translation examples saved."}

# --- AI Glossary Analysis Endpoints ---

class GlossaryAnalysisRequest(BaseModel):
    input_path: str
    analysis_percent: int = 100
    analysis_lines: Optional[int] = None
    use_temp_config: bool = False
    temp_platform: Optional[str] = None
    temp_api_key: Optional[str] = None
    temp_api_url: Optional[str] = None
    temp_model: Optional[str] = None
    temp_threads: Optional[int] = None

class GlossaryAnalysisStatus(BaseModel):
    status: str  # 'idle', 'running', 'completed', 'error'
    progress: int = 0
    total: int = 0
    message: str = ""
    results: List[dict] = []

# Global state for analysis task
_analysis_state = {
    "status": "idle",
    "progress": 0,
    "total": 0,
    "message": "",
    "results": [],
    "logs": []
}

@app.get("/api/glossary/analysis/status")
async def get_analysis_status():
    return _analysis_state

@app.post("/api/glossary/analysis/start")
async def start_glossary_analysis(request: GlossaryAnalysisRequest):
    global _analysis_state

    if _analysis_state["status"] == "running":
        raise HTTPException(status_code=400, detail="Analysis already running")

    # Reset state
    _analysis_state = {
        "status": "running",
        "progress": 0,
        "total": 0,
        "message": "初始化中...",
        "results": [],
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] 开始分析: {request.input_path}"]
    }

    # Start analysis in background thread
    import threading
    thread = threading.Thread(
        target=_run_glossary_analysis,
        args=(request.input_path, request.analysis_percent, request.analysis_lines,
              request.use_temp_config, request.temp_platform, request.temp_api_key,
              request.temp_api_url, request.temp_model, request.temp_threads)
    )
    thread.daemon = True
    thread.start()

    return {"message": "Analysis started"}

def _add_analysis_log(message: str):
    """添加分析日志"""
    global _analysis_state
    timestamp = datetime.now().strftime('%H:%M:%S')
    _analysis_state["logs"].append(f"[{timestamp}] {message}")

def _run_glossary_analysis(input_path: str, analysis_percent: int, analysis_lines: Optional[int],
                           use_temp: bool = False, temp_platform: str = None, temp_key: str = None,
                           temp_url: str = None, temp_model: str = None, temp_threads: int = None):
    global _analysis_state

    try:
        from ModuleFolders.Domain.FileReader.FileReader import FileReader
        from ModuleFolders.Infrastructure.LLMRequester.LLMRequester import LLMRequester
        from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig
        from ModuleFolders.Infrastructure.TaskConfig.TaskType import TaskType
        import concurrent.futures
        import threading
        import re

        # Load config
        config = {}
        config_file = get_active_profile_path()
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Read file
        _analysis_state["message"] = "正在读取文件..."
        _add_analysis_log("正在读取文件...")
        file_reader = FileReader()
        project_type = config.get("translation_project", "auto")
        cache_data = file_reader.read_files(project_type, input_path, "")

        if not cache_data:
            _analysis_state["status"] = "error"
            _analysis_state["message"] = "无法读取文件内容"
            _add_analysis_log("错误: 无法读取文件内容")
            return

        all_items = list(cache_data.items_iter())
        total_lines = len(all_items)

        if total_lines == 0:
            _analysis_state["status"] = "error"
            _analysis_state["message"] = "未找到可分析的文本"
            _add_analysis_log("错误: 未找到可分析的文本")
            return

        # Calculate lines to analyze
        if analysis_lines:
            lines_to_analyze = min(analysis_lines, total_lines)
        else:
            lines_to_analyze = int(total_lines * analysis_percent / 100)
        lines_to_analyze = max(1, lines_to_analyze)

        _add_analysis_log(f"总行数: {total_lines}, 将分析: {lines_to_analyze} 行")

        items_to_analyze = all_items[:lines_to_analyze]
        batch_size = config.get("lines_limit", 20)
        batches = [items_to_analyze[i:i+batch_size] for i in range(0, len(items_to_analyze), batch_size)]

        _analysis_state["total"] = len(batches)
        _analysis_state["message"] = f"准备分析 {lines_to_analyze} 行文本，共 {len(batches)} 批次"
        _add_analysis_log(f"共 {len(batches)} 批次，每批 {batch_size} 行")

        # Load prompt
        prompt_file = os.path.join(PROJECT_ROOT, "Resource", "Prompt", "System", "glossary_extract_zh.txt")
        if not os.path.exists(prompt_file):
            prompt_file = os.path.join(PROJECT_ROOT, "Resource", "Prompt", "System", "glossary_extract_en.txt")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        # Configure request
        task_config = TaskConfig()
        task_config.load_config_from_dict(config)
        task_config.prepare_for_translation(TaskType.TRANSLATION)

        # Use temp config or current config
        if use_temp and temp_platform:
            platform_config = {
                "target_platform": temp_platform,
                "api_key": temp_key or "",
                "api_url": temp_url or "",
                "model": temp_model or ""
            }
            _analysis_state["message"] = f"使用临时配置: {temp_platform}"
            _add_analysis_log(f"使用临时配置: {temp_platform}, 模型: {temp_model or 'default'}")
        else:
            platform_config = task_config.get_platform_configuration("translationReq")
            _add_analysis_log(f"使用当前配置: {platform_config.get('target_platform', 'unknown')}")

        # Collect results
        all_terms = []
        terms_lock = threading.Lock()
        # 只有在使用临时配置时才使用 temp_threads，否则使用当前配置的线程数
        if use_temp and temp_threads and temp_threads > 0:
            thread_count = temp_threads
        else:
            thread_count = task_config.actual_thread_counts
        _add_analysis_log(f"并发线程数: {thread_count}")

        def analyze_batch(batch_info):
            batch_idx, batch = batch_info
            text_content = "\n".join([item.source_text for item in batch])
            messages = [{"role": "user", "content": text_content}]

            try:
                requester = LLMRequester()
                skip, _, response, _, _ = requester.sent_request(messages, system_prompt, platform_config)

                if not skip and response:
                    terms = _parse_glossary_response(response)
                    with terms_lock:
                        all_terms.extend(terms)
                        _analysis_state["progress"] += 1
                        _analysis_state["message"] = f"已完成 {_analysis_state['progress']}/{_analysis_state['total']} 批次"
            except Exception as e:
                with terms_lock:
                    _analysis_state["progress"] += 1

        # Run analysis
        _analysis_state["message"] = "开始并发分析..."
        _add_analysis_log("开始并发分析...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            batch_infos = list(enumerate(batches))
            list(executor.map(analyze_batch, batch_infos))

        # Calculate frequency
        term_freq = _calculate_term_frequency(all_terms)

        # Convert to list format
        results = []
        for term, data in term_freq.items():
            results.append({
                "src": term,
                "type": data["type"],
                "count": data["count"]
            })

        _analysis_state["status"] = "completed"
        _analysis_state["message"] = f"分析完成，发现 {len(results)} 个专有名词"
        _analysis_state["results"] = results
        _add_analysis_log(f"分析完成! 发现 {len(results)} 个专有名词")

    except Exception as e:
        _analysis_state["status"] = "error"
        _analysis_state["message"] = f"分析出错: {str(e)}"
        _add_analysis_log(f"错误: {str(e)}")

def _parse_glossary_response(response: str) -> list:
    import re
    terms = []
    try:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            json_str = json_match.group()
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and 'src' in item:
                        terms.append({
                            'src': item.get('src', ''),
                            'type': item.get('type', '专有名词')
                        })
    except:
        pass
    return terms

def _calculate_term_frequency(terms: list) -> dict:
    freq = {}
    for term in terms:
        src = term.get('src', '').strip()
        if not src:
            continue
        if src in freq:
            freq[src]['count'] += 1
        else:
            freq[src] = {'count': 1, 'type': term.get('type', '专有名词')}
    return dict(sorted(freq.items(), key=lambda x: x[1]['count'], reverse=True))

@app.post("/api/glossary/analysis/stop")
async def stop_glossary_analysis():
    global _analysis_state
    from ModuleFolders.Base.Base import Base
    Base.work_status = Base.STATUS.STOPING
    _analysis_state["status"] = "idle"
    _analysis_state["message"] = "已停止"
    return {"message": "Analysis stopped"}

class SaveAnalysisRequest(BaseModel):
    min_frequency: int = 1
    filename: str = "auto_glossary"

@app.post("/api/glossary/analysis/save")
async def save_analysis_results(request: SaveAnalysisRequest):
    """保存分析结果为新的rules_profile并自动切换"""
    global _analysis_state, _config_cache

    if _analysis_state["status"] != "completed":
        raise HTTPException(status_code=400, detail="No completed analysis to save")

    # Filter by frequency
    filtered = [r for r in _analysis_state["results"] if r["count"] >= request.min_frequency]

    if not filtered:
        raise HTTPException(status_code=400, detail="No terms after filtering")

    # Convert to glossary format
    glossary_data = [{"src": r["src"], "dst": "", "info": r["type"]} for r in filtered]

    # 新建一个 rules profile 文件
    new_profile_name = request.filename
    new_profile_path = os.path.join(RULES_PROFILES_PATH, f"{new_profile_name}.json")

    # 确保目录存在
    os.makedirs(RULES_PROFILES_PATH, exist_ok=True)

    # 创建新的 rules profile，只包含术语表数据
    new_rules_config = {
        "prompt_dictionary_data": glossary_data
    }

    with open(new_profile_path, 'w', encoding='utf-8') as f:
        json.dump(new_rules_config, f, indent=4, ensure_ascii=False)

    # 自动切换到新创建的 rules profile
    root_config = {}
    if os.path.exists(ROOT_CONFIG_FILE):
        with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            root_config = json.load(f)

    root_config["active_rules_profile"] = new_profile_name
    with open(ROOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(root_config, f, indent=4, ensure_ascii=False)

    # 清除缓存以便前端获取最新数据
    _config_cache.clear()

    return {
        "message": f"已保存 {len(glossary_data)} 条术语到新配置 '{new_profile_name}'，并已自动切换",
        "file": new_profile_path,
        "profile": new_profile_name,
        "count": len(glossary_data)
    }

# --- Stev Extraction Endpoints ---

stev_status = "idle"
stev_logs = []
stev_lock = threading.Lock()

class StevLogCapture:
    def __init__(self):
        self.logs = []
    def write(self, message):
        if message.strip():
            self.logs.append(message.rstrip())
    def flush(self):
        pass

def run_stev_task(task_type: str, config: dict):
    global stev_status, stev_logs
    
    with stev_lock:
        stev_status = "running"
        stev_logs = [f"[{datetime.now().strftime('%H:%M:%S')}] Task '{task_type}' started."]
    
    # Capture stdout
    import sys
    from io import StringIO
    
    capture = StevLogCapture()
    original_stdout = sys.stdout
    sys.stdout = capture
    
    try:
        from source.AiNiee.StevExtraction.jtpp import Jr_Tpp
        
        # Jr_Tpp expects a config dict with some defaults if not present
        # We pass the payload directly as config
        tpp = Jr_Tpp(config) 
        
        if task_type == 'extract':
            tpp.FromGame(config.get('game_dir'), config.get('save_path'), config.get('data_path'))
        elif task_type == 'inject':
            tpp.ToGame(config.get('game_dir'), config.get('path'), config.get('output_path'), "")
        elif task_type == 'update':
            tpp.Update(config.get('game_dir'), config.get('path'), config.get('save_path'), config.get('data_path'))
            
        with stev_lock:
            stev_status = "completed"
            stev_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Task completed successfully.")
    except Exception as e:
        with stev_lock:
            stev_status = "error"
            stev_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = original_stdout
        # Copy captured logs
        with stev_lock:
            stev_logs.extend(capture.logs)

@app.post("/api/stev/{task_type}")
def start_stev_task(task_type: str, payload: dict, background_tasks: BackgroundTasks):
    global stev_status
    if stev_status == "running":
        raise HTTPException(status_code=400, detail="A Stev task is already running")
    
    background_tasks.add_task(run_stev_task, task_type, payload)
    return {"status": "started"}

@app.get("/api/stev/status")
def get_stev_status():
    global stev_status, stev_logs
    with stev_lock:
        return {"status": stev_status, "logs": list(stev_logs)}

# --- Plugin Management Endpoints ---

@app.get("/api/plugins")
async def get_plugins():
    """
    Returns a list of all loaded plugins and their enable status.
    """
    try:
        # We need an instance of PluginManager to get the loaded plugins
        from ModuleFolders.Base.PluginManager import PluginManager
        pm = PluginManager()
        pm.load_plugins_from_directory(os.path.join(PROJECT_ROOT, "PluginScripts"))
        
        plugins = pm.get_plugins()
        
        # Load enable status from root config
        root_config = {}
        if os.path.exists(ROOT_CONFIG_FILE):
            with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                root_config = json.load(f)
        
        plugin_enables = root_config.get("plugin_enables", {})
        
        result = []
        for name, plugin in plugins.items():
            result.append({
                "name": name,
                "description": plugin.description,
                "enabled": plugin_enables.get(name, plugin.default_enable),
                "default_enable": plugin.default_enable
            })
            
        return sorted(result, key=lambda x: x["name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugins: {e}")

@app.post("/api/plugins/toggle")
async def toggle_plugin(request: PluginEnableRequest):
    """
    Toggles a plugin's enable status and saves it to root config.
    """
    try:
        root_config = {}
        if os.path.exists(ROOT_CONFIG_FILE):
            with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                root_config = json.load(f)
        
        plugin_enables = root_config.get("plugin_enables", {})
        plugin_enables[request.name] = request.enabled
        root_config["plugin_enables"] = plugin_enables
        
        with open(ROOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(root_config, f, indent=4, ensure_ascii=False)
            
        return {"message": f"Plugin '{request.name}' {'enabled' if request.enabled else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle plugin: {e}")

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

@app.get("/api/rules_profiles", response_model=List[str])
async def get_rules_profiles():
    if not os.path.isdir(RULES_PROFILES_PATH):
        os.makedirs(RULES_PROFILES_PATH, exist_ok=True)
        return ["None", "default"]
    profiles = [f.replace(".json", "") for f in os.listdir(RULES_PROFILES_PATH) if f.endswith(".json")]
    return ["None"] + (profiles or ["default"])

# --- Prompt Management Endpoints ---

@app.get("/api/prompts")
async def list_prompt_categories():
    base_dir = os.path.join(PROJECT_ROOT, "Resource", "Prompt")
    if not os.path.exists(base_dir): return []
    return sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

@app.get("/api/prompts/{category}")
async def list_prompts(category: str):
    # category: "Translate", "Polishing", "Local", "Sakura", "System"
    prompt_dir = os.path.join(PROJECT_ROOT, "Resource", "Prompt", category)
    if not os.path.exists(prompt_dir):
        return []
    # Support both .txt and .json (for error_analysis.json)
    files = [f for f in os.listdir(prompt_dir) if f.endswith((".txt", ".json"))]
    return sorted(files)

@app.get("/api/prompts/{category}/{filename}")
async def get_prompt_content(category: str, filename: str):
    # Try literal match first, then fallback to .txt
    file_path = os.path.join(PROJECT_ROOT, "Resource", "Prompt", category, filename)
    if not os.path.exists(file_path):
        if not filename.endswith(".txt"):
            file_path += ".txt"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Prompt file not found")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read prompt: {e}")

@app.post("/api/prompts/{category}/{filename}")
async def save_prompt_content(category: str, filename: str, data: Dict[str, str] = Body(...)):
    file_path = os.path.join(PROJECT_ROOT, "Resource", "Prompt", category, filename)
    # Check if we should append .txt (only if it doesn't exist and doesn't have an extension)
    if not os.path.exists(file_path) and "." not in filename:
        file_path += ".txt"
        
    content = data.get("content", "")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"message": "Prompt saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {e}")

@app.post("/api/rules_profiles/switch")
async def switch_rules_profile(request: RulesProfileSwitchRequest):
    global _config_cache
    profile_name = request.profile
    
    if profile_name != "None":
        profile_path = os.path.join(RULES_PROFILES_PATH, f"{profile_name}.json")
        if not os.path.exists(profile_path):
            raise HTTPException(status_code=404, detail="Rules profile not found")
    
    try:
        root_config = {}
        if os.path.exists(ROOT_CONFIG_FILE):
            with open(ROOT_CONFIG_FILE, 'r', encoding='utf-8') as f: root_config = json.load(f)
        root_config["active_rules_profile"] = profile_name
        with open(ROOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(root_config, f, indent=4, ensure_ascii=False)
        
        _config_cache.clear()
        return await get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

            # 防护：确保 response_check_switch 是正确的 dict 类型
            default_check_switch = {
                "newline_character_count_check": False,
                "return_to_original_text_check": False,
                "residual_original_text_check": False,
                "reply_format_check": False
            }
            if "response_check_switch" not in new_active_config or not isinstance(new_active_config.get("response_check_switch"), dict):
                new_active_config["response_check_switch"] = default_check_switch
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

class PlatformCreateRequest(BaseModel):
    name: str
    base_config: Optional[Dict[str, Any]] = None

@app.post("/api/platforms/create")
async def create_platform(request: PlatformCreateRequest):
    global _config_cache
    new_name = request.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Platform name cannot be empty")
    
    # Load current platforms from active profile
    profile_path = get_active_profile_path()
    try:
        with open(profile_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        if "platforms" not in config: config["platforms"] = {}
        if new_name in config["platforms"]:
            raise HTTPException(status_code=409, detail="Platform already exists")
        
        # Use template from custom or a default
        template = config["platforms"].get("custom", {
            "tag": "custom", "group": "custom", "name": "Custom API",
            "api_url": "", "api_key": "", "api_format": "OpenAI",
            "model": "gpt-4o", "key_in_settings": ["api_url", "api_key", "model"]
        }).copy()
        
        template["tag"] = new_name
        template["name"] = new_name
        
        if request.base_config:
            template.update(request.base_config)
            
        config["platforms"][new_name] = template
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        _config_cache.clear()
        return {"message": f"Platform '{new_name}' created", "config": template}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/task/run")
async def run_task(payload: TaskPayload):
    if task_manager.status == "running":
        raise HTTPException(status_code=409, detail="A task is already running.")
    
    # 强制同步 Web 端缓存到磁盘，确保子进程能读取到编辑器中最新的修改
    try:
        cm = get_cache_manager()
        if hasattr(cm, 'project') and cm.project and getattr(cm, 'save_to_file_require_flag', False):
            # 获取输出路径（优先使用 payload 里的，如果没有则从当前配置读）
            output_path = payload.output_path or (await get_config()).get("label_output_path")
            if output_path:
                cm.save_to_file_require_path = output_path
                cm.save_to_file()
                cm.save_to_file_require_flag = False
    except Exception as e:
        print(f"Warning: Failed to flush web cache before task start: {e}")

    if not task_manager.start_task(payload.dict()):
        raise HTTPException(status_code=500, detail="Failed to start task process.")
    
    return {"success": True, "message": "Task started successfully."}

@app.post("/api/task/stop")
async def stop_task():
    task_manager.stop_task()
    return {"message": "Stop signal sent."}

@app.get("/api/task/status")
async def get_task_status(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {
        "stats": task_manager.stats,
        "logs": list(task_manager.logs),
        "chart_data": list(task_manager.chart_data),
        "comparison": {
            "source": task_manager.current_source,
            "translation": task_manager.current_translation
        }
    }

class InternalComparisonPayload(BaseModel):
    source: str
    translation: str

@app.post("/api/internal/update_comparison")
async def internal_update_comparison(payload: InternalComparisonPayload):
    """Internal endpoint for subprocesses to push comparison data."""
    task_manager.current_source = payload.source
    task_manager.current_translation = payload.translation
    return {"status": "ok"}

@app.get("/api/task/breakpoint-status")
async def get_breakpoint_status(input_path: str = ""):
    """
    Check if there's an incomplete translation task that can be resumed.
    Reads ProjectStatistics.json from the cache folder to detect breakpoint.
    """
    try:
        config = await get_config()
        output_path = config.get("label_output_path", os.path.join(PROJECT_ROOT, "output"))
        cache_folder_path = os.path.join(output_path, "cache")

        # Check if cache folder exists
        if not os.path.isdir(cache_folder_path):
            return {
                "can_resume": False,
                "has_incomplete": False,
                "message": "No cache folder found"
            }

        json_file_path = os.path.join(cache_folder_path, "ProjectStatistics.json")
        if not os.path.isfile(json_file_path):
            return {
                "can_resume": False,
                "has_incomplete": False,
                "message": "No project statistics found"
            }

        # Try to read the statistics file
        try:
            # Check file size to avoid reading empty files
            if os.path.getsize(json_file_path) == 0:
                return {
                    "can_resume": False,
                    "has_incomplete": False,
                    "message": "Project statistics file is empty"
                }

            with open(json_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {
                        "can_resume": False,
                        "has_incomplete": False,
                        "message": "Project statistics content is empty"
                    }

                data = json.loads(content)

            # Get statistics
            project_name = data.get("project_name", "Unknown")
            total_line = data.get("total_line", 0)
            line = data.get("line", 0)
            total_requests = data.get("total_requests", 0)
            success_requests = data.get("success_requests", 0)
            token = data.get("token", 0)
            time_elapsed = data.get("time", 0)

            # Check if there's incomplete work
            has_incomplete = total_line > 0 and line < total_line
            can_resume = total_line > 0

            # Format progress percentage
            progress = 0
            if total_line > 0:
                progress = (line / total_line) * 100

            return {
                "can_resume": can_resume,
                "has_incomplete": has_incomplete,
                "project_name": project_name,
                "progress": round(progress, 2),
                "total_line": total_line,
                "completed_line": line,
                "total_requests": total_requests,
                "success_requests": success_requests,
                "token": token,
                "time_elapsed": round(time_elapsed, 2),
                "message": f"Found incomplete project: {project_name} ({line}/{total_line} lines, {progress:.1f}%)" if has_incomplete else f"Project complete: {project_name}"
            }

        except (json.JSONDecodeError, OSError, IOError) as e:
            return {
                "can_resume": False,
                "has_incomplete": False,
                "message": f"Failed to read project statistics: {str(e)}"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- File Management Endpoints ---

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...), policy: str = "default"):
    """
    Uploads a file to the project's 'updatetemp' directory with limit enforcement.
    policy: 'default' | 'buffer' | 'overwrite'
    """
    try:
        os.makedirs(UPDATETEMP_PATH, exist_ok=True)
        
        # 1. Get current sorted files
        files = []
        for f in os.listdir(UPDATETEMP_PATH):
            fp = os.path.join(UPDATETEMP_PATH, f)
            if os.path.isfile(fp):
                files.append((fp, os.path.getmtime(fp)))
        files.sort(key=lambda x: x[1]) # Oldest first
        
        # 2. Get Limit
        config = await get_config()
        limit = config.get("temp_file_limit", 10)
        count = len(files)
        
        # 3. Logic
        if count < limit:
            pass # Safe to upload
        
        elif count == limit:
            if policy == "default":
                return {
                    "status": "limit_reached", 
                    "limit": limit,
                    "oldest": os.path.basename(files[0][0])
                }
            elif policy == "overwrite":
                try: os.remove(files[0][0])
                except: pass
            elif policy == "buffer":
                pass # Allow +1
        
        elif count >= limit + 1:
            # Force delete oldest to bring back to limit (or limit+1 if we allow swap?)
            # Requirement: "Only to the 12th file... prompt user 'Earliest has been deleted'"
            # If current is 11 (limit+1), adding 12th means we MUST delete 1st.
            # So we delete oldest, and return a warning flag.
            try: os.remove(files[0][0])
            except: pass
            
            # Now count is back to limit (10). Wait, if we had 11, deleting 1 makes 10.
            # Then we save new file -> 11.
            # So we are effectively rotating at limit+1.
            return {
                "status": "forced_delete",
                "limit": limit,
                "deleted": os.path.basename(files[0][0]),
                "path": "" # Will be filled after save
            }

        # 4. Save File
        file_location = os.path.join(UPDATETEMP_PATH, file.filename)
        # Security check
        if not os.path.abspath(file_location).startswith(os.path.abspath(UPDATETEMP_PATH)):
             raise HTTPException(status_code=400, detail="Invalid file path")

        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
            
        return {"info": f"file '{file.filename}' saved", "path": file_location}

    except Exception as e:
        # If it was our custom return, don't wrap it in 500
        if isinstance(e, HTTPException): raise e
        # If the return was a dict (status logic above), fastapi handles it? 
        # No, async def returns JSON directly. 
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")

@app.get("/api/files/temp")
async def list_temp_files():
    """
    Lists files in the 'updatetemp' directory.
    """
    if not os.path.exists(UPDATETEMP_PATH):
        return []
    
    files = []
    for f in os.listdir(UPDATETEMP_PATH):
        full_path = os.path.join(UPDATETEMP_PATH, f)
        if os.path.isfile(full_path):
            files.append({
                "name": f,
                "path": full_path,
                "size": os.path.getsize(full_path)
            })
    return files

@app.delete("/api/files/temp")
async def delete_temp_files(request: DeleteFileRequest):
    """
    Deletes specified files from the 'updatetemp' directory.
    """
    if not os.path.exists(UPDATETEMP_PATH):
        return {"deleted": [], "failed": []}
    
    deleted = []
    failed = []
    
    for filename in request.files:
        # Security: Prevent path traversal
        safe_path = os.path.join(UPDATETEMP_PATH, os.path.basename(filename))
        if os.path.exists(safe_path):
            try:
                os.remove(safe_path)
                deleted.append(filename)
            except Exception as e:
                failed.append({"file": filename, "error": str(e)})
        else:
            failed.append({"file": filename, "error": "File not found"})
            
    return {"deleted": deleted, "failed": failed}

# --- Draft Management Endpoints ---

def save_draft_generic(filename: str, data: Any):
    try:
        os.makedirs(TEMP_EDIT_PATH, exist_ok=True)
        draft_path = os.path.join(TEMP_EDIT_PATH, filename)
        with open(draft_path, 'w', encoding='utf-8') as f:
            # If data is list of models, convert to list of dicts
            if isinstance(data, list) and len(data) > 0 and hasattr(data[0], 'dict'):
                json.dump([item.dict() for item in data], f, indent=4, ensure_ascii=False)
            # If data is simple dict/list/str
            elif hasattr(data, 'dict'):
                json.dump(data.dict(), f, indent=4, ensure_ascii=False)
            else:
                json.dump(data, f, indent=4, ensure_ascii=False)
        return {"message": "Draft saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {e}")

def get_draft_generic(filename: str):
    draft_path = os.path.join(TEMP_EDIT_PATH, filename)
    if not os.path.exists(draft_path):
        return None # Return None to indicate no draft
    try:
        with open(draft_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

@app.post("/api/draft/glossary")
async def save_glossary_draft(items: List[GlossaryItem]):
    return save_draft_generic("glossary_draft.json", items)

@app.get("/api/draft/glossary")
async def get_glossary_draft():
    return get_draft_generic("glossary_draft.json") or []

@app.post("/api/draft/exclusion")
async def save_exclusion_draft(items: List[ExclusionItem]):
    return save_draft_generic("exclusion_draft.json", items)

@app.get("/api/draft/exclusion")
async def get_exclusion_draft():
    return get_draft_generic("exclusion_draft.json") or []

@app.post("/api/draft/characterization")
async def save_characterization_draft(items: List[CharacterizationItem]):
    return save_draft_generic("characterization_draft.json", items)

@app.get("/api/draft/characterization")
async def get_characterization_draft():
    return get_draft_generic("characterization_draft.json") or []

@app.post("/api/draft/translation_example")
async def save_translation_example_draft(items: List[TranslationExampleItem]):
    return save_draft_generic("translation_example_draft.json", items)

@app.get("/api/draft/translation_example")
async def get_translation_example_draft():
    return get_draft_generic("translation_example_draft.json") or []

@app.post("/api/draft/world_building")
async def save_world_building_draft(data: StringContent):
    return save_draft_generic("world_building_draft.json", data.content)

@app.get("/api/draft/world_building")
async def get_world_building_draft():
    res = get_draft_generic("world_building_draft.json")
    if res is None: return {"content": ""}
    return {"content": res}

@app.post("/api/draft/writing_style")
async def save_writing_style_draft(data: StringContent):
    return save_draft_generic("writing_style_draft.json", data.content)

@app.get("/api/draft/writing_style")
async def get_writing_style_draft():
    res = get_draft_generic("writing_style_draft.json")
    if res is None: return {"content": ""}
    return {"content": res}

# --- Cache Management API ---

class CacheItem(BaseModel):
    id: int
    file_path: str
    text_index: int
    source: str
    translation: str
    original_translation: str
    translation_status: int
    modified: bool = False

class CacheUpdateRequest(BaseModel):
    item_id: int
    translation: str

class CacheLoadRequest(BaseModel):
    project_path: str

class ProofreadStartRequest(BaseModel):
    project_path: str

# Global cache manager instance
_cache_manager_instance = None

def get_cache_manager():
    """Get CacheManager singleton instance"""
    global _cache_manager_instance
    try:
        if _cache_manager_instance is None:
            from ModuleFolders.Infrastructure.Cache.CacheManager import CacheManager
            _cache_manager_instance = CacheManager()
        return _cache_manager_instance
    except ImportError:
        raise HTTPException(status_code=500, detail="CacheManager not available")

@app.get("/api/cache/status")
async def get_cache_status():
    """Get cache loading status and basic info"""
    try:
        cache_manager = get_cache_manager()
        has_project = hasattr(cache_manager, 'project') and cache_manager.project and cache_manager.project.files

        if has_project:
            file_count = len(cache_manager.project.files)
            total_items = cache_manager.get_item_count()
            return {
                "loaded": True,
                "file_count": file_count,
                "total_items": total_items,
                "project_name": getattr(cache_manager.project, 'project_name', 'Unknown Project')
            }
        else:
            return {
                "loaded": False,
                "file_count": 0,
                "total_items": 0,
                "project_name": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {e}")

@app.post("/api/cache/load")
async def load_cache(request: CacheLoadRequest):
    """Load cache data from project path"""
    try:
        cache_manager = get_cache_manager()

        # Smart path handling - detect if path already points to cache file or directory
        input_path = request.project_path.strip()

        # Normalize path separators for Windows
        input_path = os.path.normpath(input_path)

        # Determine the correct output_path for CacheManager
        if input_path.endswith("AinieeCacheData.json"):
            # Path points directly to cache file
            output_path = os.path.dirname(os.path.dirname(input_path))  # Remove /cache/AinieeCacheData.json
        elif input_path.endswith("cache"):
            # Path points to cache directory
            output_path = os.path.dirname(input_path)  # Remove /cache
        elif "AinieeCacheData.json" in input_path:
            # Handle case where path contains the filename but endswith failed due to encoding issues
            cache_filename_pos = input_path.find("AinieeCacheData.json")
            if cache_filename_pos != -1:
                cache_dir = input_path[:cache_filename_pos].rstrip(os.path.sep)
                output_path = os.path.dirname(cache_dir)
                input_path = os.path.join(cache_dir, "AinieeCacheData.json")
        else:
            # Path points to project directory (output directory)
            output_path = input_path

        # Validate that cache file exists before attempting to load
        if input_path.endswith("AinieeCacheData.json"):
            # User provided path to cache file directly - use it
            cache_file_to_check = input_path
        elif "AinieeCacheData.json" in input_path:
            # Path contains cache filename somewhere - extract it properly
            cache_filename_pos = input_path.find("AinieeCacheData.json")
            cache_file_to_check = input_path[:cache_filename_pos + len("AinieeCacheData.json")]
        else:
            # User provided project directory - construct cache file path
            cache_file_to_check = os.path.join(output_path, "cache", "AinieeCacheData.json")

        cache_file_to_check = os.path.normpath(cache_file_to_check)

        if not os.path.exists(cache_file_to_check):
            # Try to provide more helpful error information
            cache_dir = os.path.dirname(cache_file_to_check)
            if not os.path.exists(cache_dir):
                raise HTTPException(
                    status_code=404,
                    detail=f"Cache directory not found: {cache_dir}. Please check if the project path is correct."
                )
            else:
                # List files in cache directory to help debug
                try:
                    files_in_cache = os.listdir(cache_dir)
                    raise HTTPException(
                        status_code=404,
                        detail=f"Cache file 'AinieeCacheData.json' not found in {cache_dir}. Found files: {files_in_cache}"
                    )
                except PermissionError:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Cache file not found: {cache_file_to_check}. Permission denied accessing cache directory."
                    )

        # Load cache data - CacheManager expects output_path, not the full cache file path
        cache_manager.load_from_file(output_path)

        if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
            raise HTTPException(status_code=500, detail="Failed to load cache data")

        file_count = len(cache_manager.project.files)
        total_items = cache_manager.get_item_count()

        return {
            "success": True,
            "message": f"Cache loaded successfully. Found {file_count} files with {total_items} items.",
            "file_count": file_count,
            "total_items": total_items
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load cache: {e}")

@app.get("/api/cache/items")
async def get_cache_items(page: int = 1, page_size: Optional[int] = None, search: str = None, file_path: str = None):
    """Get paginated cache items"""
    try:
        cache_manager = get_cache_manager()

        if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
            raise HTTPException(status_code=400, detail="No cache data loaded")

        # Get page size from config if not provided
        if page_size is None:
            try:
                config = get_config_data()
                page_size = config.get('cache_editor_page_size', 15)
            except:
                page_size = 15

        # Extract items (similar to TUI's _extract_cache_items)
        items = []
        with cache_manager.file_lock:
            for f_path, cache_file in cache_manager.project.files.items():
                # Filter by file_path if provided
                if file_path and f_path != file_path:
                    continue
                    
                for idx, item in enumerate(cache_file.items):
                    if item.source_text and item.source_text.strip():
                        translation = ""
                        if item.translated_text:
                            translation = item.translated_text
                        elif item.polished_text:
                            translation = item.polished_text

                        # Include all items with source text (translated or not)
                        items.append({
                            'id': len(items),
                            'file_path': f_path,
                            'text_index': item.text_index,
                            'source': item.source_text,
                            'translation': translation,
                            'original_translation': translation,
                            'translation_status': item.translation_status,
                            'modified': False
                        })

        # Apply search filter
        if search and search.strip():
            search_lower = search.lower()
            items = [
                item for item in items
                if search_lower in item['source'].lower() or search_lower in item['translation'].lower()
            ]

        # Apply pagination
        total_items = len(items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]

        total_pages = (total_items + page_size - 1) // page_size

        return {
            "items": paginated_items,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache items: {e}")

class CacheUpdateRequestWithPath(BaseModel):
    item_id: int
    translation: str
    project_path: str

@app.put("/api/cache/items/{item_id}")
async def update_cache_item(item_id: int, request: CacheUpdateRequestWithPath):
    """Update a cache item's translation"""
    try:
        cache_manager = get_cache_manager()

        if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
            raise HTTPException(status_code=400, detail="No cache data loaded")

        # Parse project path same way as load_cache
        input_path = request.project_path.strip()
        input_path = os.path.normpath(input_path)

        # Determine the correct output_path for CacheManager (same logic as load_cache)
        if input_path.endswith("AinieeCacheData.json"):
            output_path = os.path.dirname(os.path.dirname(input_path))
        elif input_path.endswith("cache"):
            output_path = os.path.dirname(input_path)
        elif "AinieeCacheData.json" in input_path:
            # Handle case where path contains the filename but endswith failed
            cache_filename_pos = input_path.find("AinieeCacheData.json")
            if cache_filename_pos != -1:
                cache_dir = input_path[:cache_filename_pos].rstrip(os.path.sep)
                output_path = os.path.dirname(cache_dir)
        else:
            output_path = input_path

        # Find the item to update
        item_found = False
        current_idx = 0

        with cache_manager.file_lock:
            for file_path, cache_file in cache_manager.project.files.items():
                for item in cache_file.items:
                    if item.source_text and item.source_text.strip():
                        if current_idx == item_id:
                            # Update the translation
                            new_translation = request.translation

                            if item.translation_status == 2:  # POLISHED
                                item.polished_text = new_translation
                            else:
                                item.translated_text = new_translation
                                if item.translation_status == 0:
                                    item.translation_status = 1

                            # Save to file
                            cache_manager.require_save_to_file(output_path)
                            item_found = True
                            break

                        current_idx += 1

                if item_found:
                    break

        if not item_found:
            raise HTTPException(status_code=404, detail="Cache item not found")

        return {"success": True, "message": "Cache item updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cache item: {e}")

@app.post("/api/cache/search")
async def search_cache_items(query: str, scope: str = "all", is_regex: bool = False):
    """Search cache items with advanced options"""
    try:
        cache_manager = get_cache_manager()

        if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
            raise HTTPException(status_code=400, detail="No cache data loaded")

        # Use cache manager's search functionality
        results = cache_manager.search_items(query, scope, is_regex, False)

        # Convert results to web format
        search_results = []
        for file_path, line_num, cache_item in results:
            translation = cache_item.translated_text or cache_item.polished_text or ""
            search_results.append({
                "file_path": file_path,
                "line_number": line_num,
                "source": cache_item.source_text,
                "translation": translation,
                "text_index": cache_item.text_index,
                "translation_status": cache_item.translation_status
            })

        return {
            "results": search_results,
            "total_found": len(search_results),
            "query": query,
            "scope": scope
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search cache: {e}")

# --- AI Proofread API ---

# Global state for proofread task
_proofread_state = {
    "running": False,
    "progress": 0,
    "total": 0,
    "issues": [],
    "tokens_used": 0,
    "error": None,
    "completed": False
}

@app.get("/api/proofread/status")
async def get_proofread_status():
    """Get AI proofread task status"""
    return _proofread_state

@app.post("/api/proofread/start")
async def start_proofread(request: ProofreadStartRequest, background_tasks: BackgroundTasks):
    """Start AI proofread task"""
    global _proofread_state

    if _proofread_state["running"]:
        raise HTTPException(status_code=400, detail="Proofread task already running")

    cache_manager = get_cache_manager()

    # Smart path handling - same as cache/load
    input_path = request.project_path.strip()
    input_path = os.path.normpath(input_path)

    # Determine the correct output_path
    if input_path.endswith("AinieeCacheData.json"):
        output_path = os.path.dirname(os.path.dirname(input_path))
    elif input_path.endswith("cache"):
        output_path = os.path.dirname(input_path)
    elif "AinieeCacheData.json" in input_path:
        cache_filename_pos = input_path.find("AinieeCacheData.json")
        if cache_filename_pos != -1:
            cache_dir = input_path[:cache_filename_pos].rstrip(os.path.sep)
            output_path = os.path.dirname(cache_dir)
    else:
        output_path = input_path

    # Validate cache file exists
    cache_file_path = os.path.join(output_path, "cache", "AinieeCacheData.json")
    if not os.path.exists(cache_file_path):
        raise HTTPException(status_code=404, detail=f"Cache file not found: {cache_file_path}")

    # Load cache if not already loaded or different path
    try:
        cache_manager.load_from_file(output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load cache: {e}")

    if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
        raise HTTPException(status_code=400, detail="No cache data loaded")
        raise HTTPException(status_code=400, detail="No cache data loaded")

    # Reset state
    _proofread_state = {
        "running": True,
        "progress": 0,
        "total": 0,
        "issues": [],
        "tokens_used": 0,
        "error": None,
        "completed": False
    }

    # Start background task
    background_tasks.add_task(run_proofread_task)

    return {"status": "started"}

@app.post("/api/proofread/stop")
async def stop_proofread():
    """Stop AI proofread task"""
    global _proofread_state
    _proofread_state["running"] = False
    return {"status": "stopped"}

@app.post("/api/proofread/accept")
async def accept_proofread_issue(issue_id: int):
    """Accept a proofread issue and apply the correction"""
    global _proofread_state

    cache_manager = get_cache_manager()
    if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
        raise HTTPException(status_code=400, detail="No cache data loaded")

    # Find the issue
    issue = None
    for i, iss in enumerate(_proofread_state["issues"]):
        if iss.get("id") == issue_id:
            issue = iss
            break

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if not issue.get("corrected_translation"):
        raise HTTPException(status_code=400, detail="No correction available")

    # Apply correction to cache
    try:
        text_index = issue.get("text_index")
        file_path = issue.get("file_path")
        corrected_text = issue.get("corrected_translation")

        cache_file = cache_manager.project.get_file(file_path)
        if cache_file:
            item = cache_file.get_item(text_index)
            if item:
                item.translated_text = corrected_text
                item.translation_status = 4  # AI_PROOFREAD

                # Mark issue as accepted
                issue["accepted"] = True

                return {"status": "accepted", "text_index": text_index}

        raise HTTPException(status_code=404, detail="Cache item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply correction: {e}")

class ProofreadSingleRequest(BaseModel):
    project_path: str
    file_path: str
    text_index: int
    translation: Optional[str] = None

@app.post("/api/proofread/single_check")
async def check_single_line(request: ProofreadSingleRequest):
    """
    On-demand check for a single line with context.
    Used when user clicks 'AI Analyze' on a specific line in editor.
    """
    try:
        from ModuleFolders.Service.Proofreader.AIProofreader import AIProofreader
        from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig

        cache_manager = get_cache_manager()
        
        # Ensure project is loaded
        if not hasattr(cache_manager, 'project') or not cache_manager.project.files:
             # Try to load if project is not in memory
             try:
                 load_cache_sync(request.project_path)
             except:
                 raise HTTPException(status_code=400, detail="Project cache not loaded")

        cache_file = cache_manager.project.get_file(request.file_path)
        if not cache_file:
            raise HTTPException(status_code=404, detail="File not found in cache")
        
        item = cache_file.get_item(request.text_index)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Determine target translation: prefer the one sent from web UI (editing state)
        target_translation = request.translation
        if target_translation is None:
            target_translation = item.translated_text or item.polished_text

        # Get context (5 lines before and after)
        list_idx = -1
        for idx, it in enumerate(cache_file.items):
            if it.text_index == request.text_index:
                list_idx = idx
                break
        
        if list_idx == -1:
             raise HTTPException(status_code=404, detail="Item index error")

        context_lines = 5
        start = max(0, list_idx - context_lines)
        end = min(len(cache_file.items), list_idx + context_lines + 1)
        
        context_parts = []
        for i in range(start, end):
            if i != list_idx:
                ctx_item = cache_file.items[i]
                if ctx_item.source_text:
                    # Provide original translation as context if available
                    ctx_trans = ctx_item.translated_text or ctx_item.polished_text or ""
                    context_parts.append(f"[{i}] {ctx_item.source_text[:60]} -> {ctx_trans[:40]}")
        
        context_str = "\n".join(context_parts)
        
        # Load Config
        config = load_config_sync()
        ai_proofreader = AIProofreader(config)
        
        # Run Check
        result = ai_proofreader.proofread_single(
            source=item.source_text,
            translation=target_translation,
            glossary=config.get("prompt_dictionary_data", []),
            context=context_str,
            world_building=config.get("world_building_content", ""),
            writing_style=config.get("writing_style_content", ""),
            characterization=config.get("characterization_data", [])
        )
        
        if not result.has_issues:
            return {"has_issues": False, "message": "AI分析后发现此行并无问题"}
        
        return {
            "has_issues": True,
            "issues": [
                {
                    "type": iss.type,
                    "severity": iss.severity,
                    "description": iss.description,
                    "suggestion": iss.suggestion,
                    "corrected_translation": result.corrected_translation
                } for iss in result.issues
            ],
            "corrected_translation": result.corrected_translation
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

def load_cache_sync(project_path: str):
    """Helper to load cache synchronously if needed"""
    cm = get_cache_manager()
    input_path = os.path.normpath(project_path.strip())
    if input_path.endswith("AinieeCacheData.json"):
        output_path = os.path.dirname(os.path.dirname(input_path))
    elif input_path.endswith("cache"):
        output_path = os.path.dirname(input_path)
    else:
        output_path = input_path
    cm.load_from_file(output_path)


@app.post("/api/proofread/clear")
async def clear_proofread_issues():
    """Clear all proofread issues"""
    global _proofread_state
    _proofread_state["issues"] = []
    _proofread_state["completed"] = False
    return {"status": "cleared"}

def load_config_sync() -> Dict[str, Any]:
    """Synchronously load the merged configuration."""
    mode, root_config = get_config_mode()
    current_profile_name = root_config.get("active_profile", "default")
    current_rules_name = root_config.get("active_rules_profile", "default")

    # Load Base Config
    profile_path = os.path.join(PROFILES_PATH, f"{current_profile_name}.json")
    loaded_config = {}
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r', encoding='utf-8-sig') as f:
                loaded_config = json.load(f)
        except: pass

    # Load Rules Config
    rules_config = {}
    if current_rules_name and current_rules_name != "None":
        rules_path = os.path.join(RULES_PROFILES_PATH, f"{current_rules_name}.json")
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r', encoding='utf-8-sig') as f:
                    rules_config = json.load(f)
            except: pass

    # Merge
    rule_keys = [
        "prompt_dictionary_data", "exclusion_list_data", "characterization_data",
        "world_building_content", "writing_style_content", "translation_example_data"
    ]
    for k in rule_keys:
        if k in rules_config:
            loaded_config[k] = rules_config[k]

    return loaded_config

def run_proofread_task():
    """Background task to run AI proofread"""
    global _proofread_state

    try:
        from ModuleFolders.Service.Proofreader.AIProofreader import AIProofreader
        from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig

        cache_manager = get_cache_manager()
        config = load_config_sync()

        # Collect items to check
        to_check = []
        with cache_manager.file_lock:
            for file_path, cache_file in cache_manager.project.files.items():
                for item in cache_file.items:
                    if item.translation_status in [1, 2]:  # TRANSLATED or POLISHED
                        source = item.source_text
                        target = item.translated_text or item.polished_text
                        if source and target:
                            to_check.append({
                                "index": len(to_check),
                                "text_index": item.text_index,
                                "file_path": file_path,
                                "source": source,
                                "translation": target
                            })

        _proofread_state["total"] = len(to_check)

        if not to_check:
            _proofread_state["running"] = False
            _proofread_state["completed"] = True
            return

        # Initialize proofreader
        ai_proofreader = AIProofreader(config)

        def progress_callback(current, total, prompt_tokens, completion_tokens):
            _proofread_state["progress"] = current
            _proofread_state["tokens_used"] = prompt_tokens + completion_tokens

        # Process using batching and threading to match CLI logic
        # 1. Determine batch size and threads from config
        # Default lines_limit is usually 20, threads 5
        batch_size = config.get("lines_limit", 20)
        thread_count = config.get("actual_thread_counts", 5) 
        if thread_count <= 0: thread_count = 5

        # 2. Split items into blocks
        blocks = [to_check[i:i + batch_size] for i in range(0, len(to_check), batch_size)]
        
        # 3. Define worker function
        import concurrent.futures
        
        results_lock = threading.Lock()
        
        def process_block(block):
            if not _proofread_state["running"]: return
            
            try:
                # Call the new batch method with full rules
                block_results = ai_proofreader.proofread_lines_block(
                    block,
                    glossary=config.get("prompt_dictionary_data", []),
                    world_building=config.get("world_building_content", ""),
                    writing_style=config.get("writing_style_content", ""),
                    characterization=config.get("characterization_data", [])
                )
                
                with results_lock:
                    # Update state with results
                    for idx, result in block_results.items():
                        original_item = next((item for item in block if item.get("index") == idx), None)
                        
                        if result.has_issues and original_item:
                            for issue in result.issues:
                                _proofread_state["issues"].append({
                                    "id": len(_proofread_state["issues"]) + 1,
                                    "text_index": original_item["text_index"],
                                    "file_path": original_item["file_path"],
                                    "source": original_item["source"],
                                    "original_translation": original_item["translation"],
                                    "corrected_translation": result.corrected_translation,
                                    "issue_type": issue.type,
                                    "severity": issue.severity,
                                    "description": issue.description,
                                    "accepted": False
                                })
                    
                    _proofread_state["progress"] += len(block)
                    p_tok = sum(r.prompt_tokens for r in block_results.values())
                    c_tok = sum(r.completion_tokens for r in block_results.values())
                    _proofread_state["tokens_used"] += (p_tok + c_tok)
                    
            except Exception as e:
                print(f"Error processing block: {e}")

        # 4. Execute with ThreadPool
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            # We must monitor running state
            futures = []
            for block in blocks:
                if not _proofread_state["running"]: break
                futures.append(executor.submit(process_block, block))
            
            # Wait for completion
            concurrent.futures.wait(futures)

        _proofread_state["running"] = False
        _proofread_state["completed"] = True

    except Exception as e:
        _proofread_state["running"] = False
        _proofread_state["error"] = str(e)
        import traceback
        traceback.print_exc()

# --- Queue Management API ---

def get_queue_manager():
    """Get QueueManager instance"""
    try:
        from ModuleFolders.Service.TaskQueue.QueueManager import QueueManager
        return QueueManager()
    except ImportError:
        raise HTTPException(status_code=500, detail="QueueManager not available")

@app.get("/api/queue")
async def get_queue():
    """Get all tasks in the queue with accurate processing status"""
    try:
        qm = get_queue_manager()

        # 清理过期的锁定状态
        if hasattr(qm, 'cleanup_stale_locks'):
            qm.cleanup_stale_locks()

        tasks = []

        for idx, task in enumerate(qm.tasks):
            # Ensure all tasks have the locked attribute and default status
            if not hasattr(task, 'locked'):
                task.locked = False
            if not hasattr(task, 'status'):
                task.status = "waiting"

            # 获取准确的处理状态
            is_actually_processing = False
            processing_info = None
            if hasattr(qm, 'is_task_actually_processing'):
                is_actually_processing = qm.is_task_actually_processing(idx)

            if hasattr(qm, 'get_task_processing_status'):
                processing_info = qm.get_task_processing_status(idx)

            # 如果任务被标记为locked但实际上没有在处理，则解锁
            if task.locked and not is_actually_processing:
                if hasattr(qm, 'stop_task_processing'):
                    qm.stop_task_processing(idx)
                    task.locked = False

            task_dict = {
                "task_type": task.task_type,
                "input_path": task.input_path,
                "output_path": getattr(task, "output_path", ""),
                "profile": getattr(task, "profile", ""),
                "rules_profile": getattr(task, "rules_profile", ""),
                "source_lang": getattr(task, "source_lang", ""),
                "target_lang": getattr(task, "target_lang", ""),
                "project_type": getattr(task, "project_type", ""),
                "platform": getattr(task, "platform", ""),
                "api_url": getattr(task, "api_url", ""),
                "api_key": getattr(task, "api_key", ""),
                "model": getattr(task, "model", ""),
                "threads": getattr(task, "threads", None),
                "retry": getattr(task, "retry", None),
                "timeout": getattr(task, "timeout", None),
                "rounds": getattr(task, "rounds", None),
                "pre_lines": getattr(task, "pre_lines", None),
                "lines_limit": getattr(task, "lines_limit", None),
                "tokens_limit": getattr(task, "tokens_limit", None),
                "think_depth": getattr(task, "think_depth", ""),
                "thinking_budget": getattr(task, "thinking_budget", None),
                "status": getattr(task, "status", "waiting"),
                "locked": getattr(task, "locked", False),

                # 新增：准确的处理状态信息
                "is_actually_processing": is_actually_processing,
                "is_processing": getattr(task, "is_processing", False),
                "process_start_time": getattr(task, "process_start_time", None),
                "last_activity_time": getattr(task, "last_activity_time", None)
            }
            tasks.append(task_dict)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/queue")
async def add_to_queue(item: QueueTaskItem):
    """Add a new task to the queue"""
    try:
        qm = get_queue_manager()
        from ModuleFolders.Service.TaskQueue.QueueManager import QueueTaskItem as QueueTaskItemImpl

        # Create task with proper constructor parameters
        task = QueueTaskItemImpl(
            task_type=item.task_type,
            input_path=item.input_path,
            output_path=item.output_path,
            profile=item.profile,
            rules_profile=item.rules_profile,
            source_lang=item.source_lang,
            target_lang=item.target_lang,
            project_type=item.project_type,
            platform=item.platform,
            api_url=item.api_url,
            api_key=item.api_key,
            model=item.model,
            threads=item.threads,
            retry=item.retry,
            timeout=item.timeout,
            rounds=item.rounds,
            pre_lines=item.pre_lines,
            lines_limit=item.lines_limit,
            tokens_limit=item.tokens_limit,
            think_depth=item.think_depth,
            thinking_budget=item.thinking_budget
        )

        # Ensure the task has proper defaults
        task.status = "waiting"
        task.locked = False

        qm.add_task(task)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/queue/{index}")
async def remove_from_queue(index: int):
    """Remove a task from the queue"""
    try:
        qm = get_queue_manager()
        if qm.remove_task(index):
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/queue/{index}")
async def update_queue_item(index: int, item: QueueTaskItem):
    """Update a task in the queue"""
    try:
        qm = get_queue_manager()
        if index < 0 or index >= len(qm.tasks):
            raise HTTPException(status_code=400, detail="Invalid task index")

        task = qm.tasks[index]
        task.task_type = item.task_type
        task.input_path = item.input_path
        if item.output_path:
            task.output_path = item.output_path
        if item.profile:
            task.profile = item.profile
        if item.rules_profile:
            task.rules_profile = item.rules_profile
        if item.source_lang:
            task.source_lang = item.source_lang
        if item.target_lang:
            task.target_lang = item.target_lang
        if item.project_type:
            task.project_type = item.project_type
        if item.platform:
            task.platform = item.platform
        if item.api_url:
            task.api_url = item.api_url
        if item.api_key:
            task.api_key = item.api_key
        if item.model:
            task.model = item.model
        if item.threads is not None:
            task.threads = item.threads
        if item.retry is not None:
            task.retry = item.retry
        if item.timeout is not None:
            task.timeout = item.timeout
        if item.rounds is not None:
            task.rounds = item.rounds
        if item.pre_lines is not None:
            task.pre_lines = item.pre_lines
        if item.lines_limit is not None:
            task.lines_limit = item.lines_limit
        if item.tokens_limit is not None:
            task.tokens_limit = item.tokens_limit
        if item.think_depth:
            task.think_depth = item.think_depth
        if item.thinking_budget is not None:
            task.thinking_budget = item.thinking_budget

        if qm.update_task(index, task):
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to update task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/queue/clear")
async def clear_queue():
    """Clear all tasks from the queue"""
    try:
        qm = get_queue_manager()
        if qm.clear_tasks():
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to clear queue")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/queue/run")
async def run_queue():
    """Start queue execution"""
    try:
        qm = get_queue_manager()
        # Check if QueueManager has run_queue method, if not use alternative
        if hasattr(qm, 'run_queue'):
            qm.run_queue()
        else:
            # Alternative: set is_running flag or call CLI task execution
            qm.is_running = True
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queue/edit_file")
async def edit_queue_file():
    """Open queue file in external editor"""
    try:
        qm = get_queue_manager()
        # Check if method exists, if not provide fallback
        if hasattr(qm, 'open_queue_editor'):
            qm.open_queue_editor()
        else:
            # Fallback: could open file with system editor
            import subprocess
            import sys
            if sys.platform.startswith('win'):
                subprocess.run(['notepad', qm.queue_file])
            else:
                subprocess.run(['xdg-open', qm.queue_file])
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/queue/raw")
async def get_queue_raw():
    """Get raw queue JSON content"""
    try:
        qm = get_queue_manager()
        # Read the file directly if method doesn't exist
        if hasattr(qm, 'get_queue_json'):
            content = qm.get_queue_json()
        else:
            # Fallback: read file content directly
            try:
                with open(qm.queue_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                content = "[]"
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/queue/raw")
async def save_queue_raw(request: QueueRawRequest):
    """Save raw queue JSON content"""
    try:
        qm = get_queue_manager()
        if hasattr(qm, 'load_from_json'):
            qm.load_from_json(request.content)
        else:
            # Fallback: save to file directly and reload
            try:
                import rapidjson as json
                # Validate JSON first
                json.loads(request.content)
                # Save to file
                with open(qm.queue_file, 'w', encoding='utf-8') as f:
                    f.write(request.content)
                # Reload tasks
                qm.load_tasks()
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/queue/{from_index}/move")
async def move_queue_item(from_index: int, request: QueueMoveRequest):
    """Move a task to a different position"""
    try:
        qm = get_queue_manager()

        if from_index < 0 or from_index >= len(qm.tasks) or request.to_index < 0 or request.to_index >= len(qm.tasks):
            raise HTTPException(status_code=400, detail="Invalid task index")

        # Check if tasks can be modified
        if not qm.can_modify_task(from_index):
            raise HTTPException(status_code=400, detail="Source task is locked")

        # Check range between from and to for locked tasks
        start, end = min(from_index, request.to_index), max(from_index, request.to_index)
        for i in range(start, end + 1):
            if i != from_index and not qm.can_modify_task(i):
                raise HTTPException(status_code=400, detail="Cannot move task due to locked tasks in path")

        # Use QueueManager's move_task method
        if qm.move_task(from_index, request.to_index):
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to move task")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/queue/reorder")
async def reorder_queue(request: QueueReorderRequest):
    """Reorder tasks according to new order"""
    try:
        qm = get_queue_manager()
        if len(request.new_order) != len(qm.tasks):
            raise HTTPException(status_code=400, detail="New order length doesn't match queue length")

        # Use QueueManager's reorder_tasks method if available
        if hasattr(qm, 'reorder_tasks'):
            if qm.reorder_tasks(request.new_order):
                return {"success": True}
            else:
                raise HTTPException(status_code=400, detail="Failed to reorder tasks")
        else:
            # Fallback: manual reorder
            # Validate indices first
            for i in request.new_order:
                if i < 0 or i >= len(qm.tasks):
                    raise HTTPException(status_code=400, detail="Invalid task index in new order")

            # Reorder tasks according to new order
            new_tasks = [qm.tasks[i] for i in request.new_order]
            qm.tasks = new_tasks
            qm.save_tasks()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Scheduler API Endpoints ---

# Global scheduler manager instance
_scheduler_manager = None

def get_scheduler_manager():
    """Get or create the scheduler manager instance."""
    global _scheduler_manager
    if _scheduler_manager is None:
        from ModuleFolders.Infrastructure.Automation.SchedulerManager import SchedulerManager
        _scheduler_manager = SchedulerManager()
        # Load from config
        _scheduler_manager.load_from_config(load_config_sync())
    return _scheduler_manager


class ScheduledTaskItem(BaseModel):
    task_id: str
    name: str
    schedule: str
    input_path: str
    profile: str
    task_type: str
    enabled: bool = True


@app.get("/api/scheduler/status", response_model=dict)
async def get_scheduler_status():
    """Get scheduler status."""
    try:
        sm = get_scheduler_manager()
        return sm.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/tasks", response_model=List[dict])
async def get_scheduler_tasks():
    """Get all scheduled tasks."""
    try:
        sm = get_scheduler_manager()
        tasks = sm.get_all_tasks()
        return [task.to_dict() for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/tasks")
async def add_scheduler_task(task: ScheduledTaskItem):
    """Add a new scheduled task."""
    try:
        sm = get_scheduler_manager()
        from ModuleFolders.Infrastructure.Automation.SchedulerManager import ScheduledTask

        new_task = ScheduledTask(
            task_id=task.task_id,
            name=task.name,
            schedule=task.schedule,
            input_path=task.input_path,
            profile=task.profile,
            task_type=task.task_type,
            enabled=task.enabled
        )

        if sm.add_task(new_task):
            temp_config = {}
            sm.save_to_config(temp_config)
            save_config_generic("scheduler", temp_config["scheduler"])
            return {"success": True, "message": "Task added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Task ID already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/scheduler/tasks/{task_id}")
async def update_scheduler_task(task_id: str, enabled: bool = None, schedule: str = None, input_path: str = None, profile: str = None):
    """Update a scheduled task."""
    try:
        sm = get_scheduler_manager()
        update_data = {}
        if enabled is not None:
            update_data["enabled"] = enabled
        if schedule is not None:
            update_data["schedule"] = schedule
        if input_path is not None:
            update_data["input_path"] = input_path
        if profile is not None:
            update_data["profile"] = profile

        if sm.update_task(task_id, **update_data):
            temp_config = {}
            sm.save_to_config(temp_config)
            save_config_generic("scheduler", temp_config["scheduler"])
            return {"success": True, "message": "Task updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/scheduler/tasks/{task_id}")
async def delete_scheduler_task(task_id: str):
    """Delete a scheduled task."""
    try:
        sm = get_scheduler_manager()
        if sm.remove_task(task_id):
            temp_config = {}
            sm.save_to_config(temp_config)
            save_config_generic("scheduler", temp_config["scheduler"])
            return {"success": True, "message": "Task deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/start")
async def start_scheduler():
    """Start the scheduler."""
    try:
        sm = get_scheduler_manager()
        sm.start()
        temp_config = {}
        sm.save_to_config(temp_config)
        save_config_generic("scheduler", temp_config["scheduler"])
        return {"success": True, "message": "Scheduler started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    try:
        sm = get_scheduler_manager()
        sm.stop()
        temp_config = {}
        sm.save_to_config(temp_config)
        save_config_generic("scheduler", temp_config["scheduler"])
        return {"success": True, "message": "Scheduler stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/logs", response_model=List[dict])
async def get_scheduler_logs():
    """Get scheduler execution logs."""
    try:
        sm = get_scheduler_manager()
        return sm.get_logs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- User Management API Routes ---

@app.get("/api/v1/users/me", response_model=Dict[str, Any])
async def get_my_profile(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取当前用户资料

    返回完整的用户资料信息，包括：
    - 基本信息（邮箱、用户名、角色、状态）
    - 资料数据（全名、简介、头像）
    - 账户状态（邮箱验证、最后登录时间）
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()
        profile = user_manager.get_profile(str(user.id))

        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/me", response_model=Dict[str, Any])
async def update_my_profile(
    request: UpdateProfileRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新当前用户资料

    允许更新：
    - username（必须唯一）
    - full_name
    - bio（最多500字符）
    - avatar_url（必须是有效URL）
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        # Build update dict with only provided fields
        update_data = {}
        if request.username is not None:
            update_data['username'] = request.username
        if request.full_name is not None:
            update_data['full_name'] = request.full_name
        if request.bio is not None:
            update_data['bio'] = request.bio
        if request.avatar_url is not None:
            update_data['avatar_url'] = request.avatar_url

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        profile = user_manager.update_profile(str(user.id), **update_data)

        return profile

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/me/email", response_model=Dict[str, Any])
async def update_my_email(
    request: UpdateEmailRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新当前用户邮箱

    需要密码验证以确保安全
    新邮箱必须唯一且需要验证
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        profile = user_manager.update_email(
            user_id=str(user.id),
            new_email=request.new_email,
            password=request.password,
        )

        return profile

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/me/password", response_model=Dict[str, Any])
async def update_my_password(
    request: UpdatePasswordRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新当前用户密码

    需要当前密码验证
    密码更改后将撤销所有刷新令牌
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.update_password(
            user_id=str(user.id),
            current_password=request.current_password,
            new_password=request.new_password,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/users/me")
async def delete_my_account(
    request: DeleteAccountRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    删除当前用户账户

    如果用户有密码，需要密码确认
    此操作不可撤销
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.delete_account(
            user_id=str(user.id),
            password=request.password,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/me/login-history", response_model=LoginHistoryResponse)
async def get_my_login_history(
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取当前用户登录历史

    返回登录尝试的分页列表，包括：
    - IP地址
    - User Agent
    - 成功/失败状态
    - 时间戳
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.get_login_history(
            user_id=str(user.id),
            page=page,
            per_page=per_page,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/me/preferences", response_model=Dict[str, Any])
async def get_my_preferences(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取当前用户偏好设置

    返回用户的自定义偏好/设置
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        preferences = user_manager.get_preferences(str(user.id))

        return preferences

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/me/preferences", response_model=Dict[str, Any])
async def update_my_preferences(
    preferences: Dict[str, Any] = Body(...),
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新当前用户偏好设置

    允许存储自定义用户设置
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.update_preferences(
            user_id=str(user.id),
            preferences=preferences,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 管理员用户管理路由 ---

@app.get("/api/v1/users", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(jwt_middleware.require_admin())
):
    """
    获取所有用户列表，支持过滤和分页（仅管理员）

    支持过滤：
    - search: 在用户名和邮箱中搜索
    - role: 按用户角色过滤
    - status: 按账户状态过滤
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.list_users(
            page=page,
            per_page=per_page,
            search=search,
            role=role,
            status=status,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: str,
    user: User = Depends(jwt_middleware.require_admin())
):
    """
    根据ID获取用户详情（仅管理员）

    返回完整的用户资料信息
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()
        profile = user_manager.get_profile(user_id)

        return profile

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/{user_id}/role", response_model=Dict[str, Any])
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    user: User = Depends(jwt_middleware.require_admin())
):
    """
    更新用户角色（仅管理员）

    可用角色：
    - super_admin: 完整平台访问权限
    - tenant_admin: 租户级管理
    - team_admin: 团队管理
    - translation_admin: 翻译任务管理
    - developer: API访问
    - user: 基础翻译功能
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.update_user_role(
            admin_id=str(user.id),
            user_id=user_id,
            new_role=request.new_role,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/users/{user_id}/status", response_model=Dict[str, Any])
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    user: User = Depends(jwt_middleware.require_admin())
):
    """
    更新用户状态（仅管理员）

    可用状态：
    - active: 正常激活账户
    - inactive: 暂时禁用
    - suspended: 永久暂停

    可选原因字段用于审计跟踪
    """
    try:
        from ModuleFolders.Service.User import get_user_manager

        user_manager = get_user_manager()

        result = user_manager.update_user_status(
            admin_id=str(user.id),
            user_id=user_id,
            new_status=request.new_status,
            reason=request.reason,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Subscription Management API Routes ---

@app.get("/api/v1/subscriptions/plans", response_model=List[Dict[str, Any]])
async def get_subscription_plans():
    """
    获取所有可用的订阅计划

    返回所有订阅计划的详细信息，包括：
    - plan: 计划名称
    - daily_characters: 每日字符数限制
    - monthly_price: 月费价格（CNY）
    - features: 功能列表
    """
    try:
        from ModuleFolders.Service.Billing import SubscriptionManager

        manager = SubscriptionManager()
        plans = manager.get_all_plans()

        return plans

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/subscriptions", response_model=Dict[str, Any])
async def create_subscription(
    request: CreateSubscriptionRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    创建新的订阅

    创建一个新的订阅，返回 Stripe Checkout Session URL。
    用户需要访问返回的 URL 完成支付。

    参数：
    - plan: 订阅计划（starter, pro, enterprise）
    - success_url: 支付成功后的跳转 URL
    - cancel_url: 取消支付后的跳转 URL

    返回：
    - session_id: Stripe Checkout Session ID
    - url: Stripe Checkout URL（用户访问此 URL 完成支付）
    """
    try:
        from ModuleFolders.Service.Billing import PaymentProcessor
        from ModuleFolders.Service.Auth.models import SubscriptionPlan

        # 验证计划
        try:
            plan_enum = SubscriptionPlan(request.plan)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的订阅计划: {request.plan}。可选值: free, starter, pro, enterprise"
            )

        # Free 计划不需要 Stripe
        if plan_enum == SubscriptionPlan.FREE:
            return {
                "message": "Free 计划无需订阅",
                "plan": "free",
                "url": None
            }

        processor = PaymentProcessor()

        # 获取或创建 Stripe 客户 ID
        from ModuleFolders.Service.Auth.models import Tenant
        customer_id = None

        if user.tenant_id:
            try:
                tenant = Tenant.get_by_id(user.tenant_id)
                customer_id = tenant.stripe_customer_id
            except Tenant.DoesNotExist:
                pass

        # 如果没有客户 ID，创建一个
        if not customer_id:
            customer_id = processor.create_customer(
                user_id=str(user.id),
                email=user.email
            )

        # 创建结账会话
        result = processor.create_checkout_session(
            user_id=str(user.id),
            plan=plan_enum,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/subscriptions/current", response_model=Dict[str, Any])
async def get_current_subscription(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取当前用户的订阅信息

    返回当前用户的订阅详情，包括：
    - plan: 当前计划
    - status: 订阅状态
    - expires_at: 过期时间
    - stripe_subscription_id: Stripe 订阅 ID（如果有）
    """
    try:
        from ModuleFolders.Service.Auth.models import Tenant, SubscriptionPlan

        # 获取用户的租户信息
        if not user.tenant_id:
            return {
                "plan": "free",
                "status": "active",
                "expires_at": None,
                "stripe_subscription_id": None
            }

        try:
            tenant = Tenant.get_by_id(user.tenant_id)
        except Tenant.DoesNotExist:
            return {
                "plan": "free",
                "status": "active",
                "expires_at": None,
                "stripe_subscription_id": None
            }

        result = {
            "plan": tenant.plan,
            "status": "active",
            "expires_at": tenant.subscription_expires_at.isoformat() if tenant.subscription_expires_at else None,
            "stripe_subscription_id": tenant.stripe_subscription_id,
            "stripe_customer_id": tenant.stripe_customer_id,
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/subscriptions/current", response_model=Dict[str, Any])
async def update_subscription(
    request: UpdateSubscriptionRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新当前订阅（升降级）

    更新用户的订阅计划，支持：
    - 从 starter 升级到 pro
    - 从 pro 降级到 starter
    - 切换到 enterprise

    参数：
    - new_plan: 新的计划（starter, pro, enterprise）

    返回：
    - subscription_id: Stripe 订阅 ID
    - status: 订阅状态
    - current_period_start: 当前计费周期开始时间
    - current_period_end: 当前计费周期结束时间
    """
    try:
        from ModuleFolders.Service.Billing import PaymentProcessor
        from ModuleFolders.Service.Auth.models import Tenant, SubscriptionPlan
        import os

        # 验证新计划
        try:
            new_plan = SubscriptionPlan(request.new_plan)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的订阅计划: {request.new_plan}。可选值: starter, pro, enterprise"
            )

        if new_plan == SubscriptionPlan.FREE:
            raise HTTPException(
                status_code=400,
                detail="无法降级到 Free 计划，请使用取消订阅功能"
            )

        # 获取用户的租户和订阅信息
        if not user.tenant_id:
            raise HTTPException(
                status_code=400,
                detail="用户没有租户信息，无法更新订阅"
            )

        try:
            tenant = Tenant.get_by_id(user.tenant_id)
        except Tenant.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="租户不存在"
            )

        if not tenant.stripe_subscription_id:
            raise HTTPException(
                status_code=400,
                detail="用户没有活跃的订阅，请先创建订阅"
            )

        # 获取新计划的 Price ID
        price_ids = {
            SubscriptionPlan.STARTER: os.getenv("STRIPE_PRICE_STARTER"),
            SubscriptionPlan.PRO: os.getenv("STRIPE_PRICE_PRO"),
            SubscriptionPlan.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE"),
        }

        new_price_id = price_ids.get(new_plan)
        if not new_price_id:
            raise HTTPException(
                status_code=500,
                detail=f"未配置 {new_plan.value} 计划的 Price ID"
            )

        # 更新订阅
        processor = PaymentProcessor()
        result = processor.update_subscription(
            subscription_id=tenant.stripe_subscription_id,
            new_price_id=new_price_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/subscriptions/current", response_model=Dict[str, Any])
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    取消当前订阅

    取消用户的订阅，可以选择：
    - at_period_end=true: 在当前计费周期结束时取消（默认）
    - at_period_end=false: 立即取消

    取消后，订阅将降级到 Free 计划。
    """
    try:
        from ModuleFolders.Service.Billing import PaymentProcessor
        from ModuleFolders.Service.Auth.models import Tenant

        # 获取用户的租户和订阅信息
        if not user.tenant_id:
            raise HTTPException(
                status_code=400,
                detail="用户没有租户信息，无法取消订阅"
            )

        try:
            tenant = Tenant.get_by_id(user.tenant_id)
        except Tenant.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="租户不存在"
            )

        if not tenant.stripe_subscription_id:
            raise HTTPException(
                status_code=400,
                detail="用户没有活跃的订阅"
            )

        # 取消订阅
        processor = PaymentProcessor()
        result = processor.cancel_subscription(
            subscription_id=tenant.stripe_subscription_id,
            at_period_end=request.at_period_end,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/subscriptions/invoices", response_model=List[Dict[str, Any]])
async def get_subscription_invoices(
    limit: int = 12,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取订阅发票列表

    返回当前用户的发票列表，包括：
    - id: 发票 ID
    - number: 发票编号
    - status: 发票状态（paid, open, void, uncollectible）
    - amount_due: 应付金额
    - currency: 货币
    - created: 创建时间
    - due_date: 到期日期
    """
    try:
        from ModuleFolders.Service.Billing import PaymentProcessor
        from ModuleFolders.Service.Auth.models import Tenant

        # 获取用户的 Stripe 客户 ID
        if not user.tenant_id:
            return []

        try:
            tenant = Tenant.get_by_id(user.tenant_id)
        except Tenant.DoesNotExist:
            return []

        if not tenant.stripe_customer_id:
            return []

        # 获取发票列表
        processor = PaymentProcessor()
        invoices = processor.list_invoices(
            customer_id=tenant.stripe_customer_id,
            limit=limit,
        )

        return invoices

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/subscriptions/invoices/{invoice_id}")
async def get_invoice_pdf(
    invoice_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取发票 PDF 下载链接

    返回指定发票的详细信息，包括 PDF 下载链接。

    参数：
    - invoice_id: Stripe 发票 ID（通常以 in_ 开头）

    返回：
    - id: 发票 ID
    - number: 发票编号
    - status: 发票状态
    - amount_due: 应付金额
    - amount_paid: 已付金额
    - currency: 货币
    - invoice_pdf: PDF 下载链接
    - hosted_invoice_url: 发票托管页面 URL
    - created: 创建时间
    """
    try:
        from ModuleFolders.Service.Billing import PaymentProcessor
        from ModuleFolders.Service.Auth.models import Tenant

        # 获取用户的 Stripe 客户 ID
        if not user.tenant_id:
            raise HTTPException(
                status_code=400,
                detail="用户没有租户信息"
            )

        try:
            tenant = Tenant.get_by_id(user.tenant_id)
        except Tenant.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="租户不存在"
            )

        # 获取发票详情
        processor = PaymentProcessor()
        invoice = processor.get_invoice(invoice_id)

        # 验证发票是否属于该用户
        if not invoice.get("hosted_invoice_url"):
            raise HTTPException(
                status_code=404,
                detail="发票不存在或无法访问"
            )

        return invoice

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/subscriptions/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    下载发票 PDF 文件

    生成并下载指定发票的自定义 PDF 文件。

    参数：
    - invoice_id: 发票 ID（本地数据库 ID 或 Stripe 发票 ID）

    返回：
    - PDF 文件流（Content-Type: application/pdf）
    """
    try:
        from ModuleFolders.Service.Billing import InvoiceGenerator
        from fastapi.responses import Response

        # 生成 PDF
        invoice_generator = InvoiceGenerator()

        # 尝试生成为字节数据
        try:
            pdf_data = invoice_generator.generate_pdf_bytes(invoice_id)
        except ValueError:
            # 如果本地数据库没有此发票，尝试通过 Stripe 发票 ID 查找
            # 这里可以添加逻辑从 Stripe 获取发票信息并生成本地发票
            raise HTTPException(
                status_code=404,
                detail="发票不存在"
            )

        # 返回 PDF 文件
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="invoice_{invoice_id}.pdf"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {str(e)}")


# --- Usage Management API Routes ---

@app.get("/api/v1/usage/current", response_model=Dict[str, Any])
async def get_current_usage(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取当前用户的用量汇总

    返回用户今日、本月和总计的使用量，包括：
    - characters: 翻译字符数
    - api_calls: API调用次数
    - storage_mb: 存储使用(MB)
    - concurrent_tasks: 并发任务数
    - team_members: 团队成员数
    """
    try:
        from ModuleFolders.Service.Billing.UsageTracker import UsageTracker

        tracker = UsageTracker()
        summary = tracker.get_usage_summary(user.id)

        return {
            "user_id": user.id,
            "today": summary["today"],
            "month": summary["month"],
            "total": summary["total"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/usage/history", response_model=Dict[str, Any])
async def get_usage_history(
    metric_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取用户使用历史记录（分页）

    参数：
    - metric_type: 指标类型过滤（可选: characters, api_calls, storage_mb, concurrent_tasks, team_members）
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - page: 页码（从1开始，默认1）
    - per_page: 每页记录数（默认50，最大100）

    返回：
    - records: 使用记录列表
    - pagination: 分页信息
    """
    try:
        from ModuleFolders.Service.Billing.UsageTracker import UsageTracker

        # 验证指标类型
        if metric_type and metric_type not in UsageTracker.METRIC_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的指标类型: {metric_type}. 支持的类型: {list(UsageTracker.METRIC_TYPES.keys())}"
            )

        # 限制每页数量
        per_page = min(per_page, 100)

        tracker = UsageTracker()
        history = tracker.get_usage_history(
            user_id=user.id,
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

        return history

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/usage/daily", response_model=List[Dict[str, Any]])
async def get_daily_usage(
    metric_type: str = "characters",
    days: int = 30,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取每日使用量统计（用于趋势图）

    参数：
    - metric_type: 指标类型（默认: characters）
      可选: characters, api_calls, storage_mb, concurrent_tasks, team_members
    - days: 统计天数（默认30天，最大90天）

    返回：
    每日使用量列表，包含：
    - date: 日期 (YYYY-MM-DD)
    - quantity: 使用量
    """
    try:
        from ModuleFolders.Service.Billing.UsageTracker import UsageTracker

        # 验证指标类型
        if metric_type not in UsageTracker.METRIC_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的指标类型: {metric_type}. 支持的类型: {list(UsageTracker.METRIC_TYPES.keys())}"
            )

        # 限制天数
        days = min(days, 90)

        tracker = UsageTracker()
        stats = tracker.get_daily_usage_stats(
            user_id=user.id,
            metric_type=metric_type,
            days=days,
        )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- OAuth API Routes ---


class OAuthUrlResponse(BaseModel):
    """OAuth 授权 URL 响应"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调请求"""
    code: str
    state: str


class OAuthLinkAccountRequest(BaseModel):
    """OAuth 关联账户请求"""
    provider: str
    oauth_id: str
    access_token: str
    account_email: Optional[str] = None
    account_username: Optional[str] = None
    account_data: Optional[Dict[str, Any]] = None


@app.get("/api/v1/auth/oauth/{provider}/authorize", response_model=OAuthUrlResponse)
async def get_oauth_authorization_url(provider: str):
    """
    获取 OAuth 授权 URL

    参数：
    - provider: OAuth 提供商（github, google）

    返回：
    - authorization_url: OAuth 授权 URL（用户访问此 URL 进行授权）
    - state: CSRF 防护状态码（需在回调时验证）

    说明：
    1. 前端使用返回的 authorization_url 重定向用户到 OAuth 提供商
    2. 用户授权后，OAuth 提供商会重定向回回调 URL 并带上 code 和 state
    3. 将 code 和 state 传递给 /api/v1/auth/oauth/callback 完成登录
    """
    try:
        from ModuleFolders.Service.Auth import get_oauth_manager

        # 验证提供商
        if provider not in ["github", "google"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 OAuth 提供商: {provider}。可选值: github, google"
            )

        oauth_manager = get_oauth_manager()

        # 生成授权 URL
        auth_url, state = oauth_manager.get_authorization_url(provider)

        return {
            "authorization_url": auth_url,
            "state": state
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/auth/oauth/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request
):
    """
    OAuth 回调处理

    参数：
    - provider: OAuth 提供商（github, google）
    - code: OAuth 授权码
    - state: CSRF 防护状态码

    返回：
    - user: 用户信息
    - access_token: JWT 访问令牌
    - refresh_token: JWT 刷新令牌
    - provider: OAuth 提供商

    说明：
    1. 验证 state 参数（前端应在 session 中存储 state 并验证）
    2. 使用 code 交换 OAuth 访问令牌
    3. 获取用户信息并创建或登录账户
    4. 返回 JWT 令牌

    注意：
    - state 参数验证应由前端实现（建议在 session 中存储并验证）
    - 新用户的邮箱自动标记为已验证
    - OAuth 用户可以设置密码以支持密码登录
    """
    try:
        from ModuleFolders.Service.Auth import get_oauth_manager

        # 验证提供商
        if provider not in ["github", "google"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 OAuth 提供商: {provider}"
            )

        oauth_manager = get_oauth_manager()

        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 完成 OAuth 登录流程
        result = await oauth_manager.oauth_login(
            provider=provider,
            code=code,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/auth/oauth/accounts", response_model=List[Dict[str, Any]])
async def get_linked_oauth_accounts(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取已关联的 OAuth 账户列表

    返回：
    已关联的 OAuth 账户列表，每个账户包含：
    - provider: OAuth 提供商（github, google）
    - account_email: OAuth 账户邮箱
    - account_username: OAuth 账户用户名
    - linked_at: 关联时间
    - last_login_at: 最后登录时间

    说明：
    - 用户可以关联多个 OAuth 提供商（如 GitHub 和 Google）
    - 每个提供商只能关联一个账户
    """
    try:
        from ModuleFolders.Service.Auth import get_oauth_manager

        oauth_manager = get_oauth_manager()

        accounts = oauth_manager.get_linked_accounts(user_id=str(user.id))

        return accounts

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/auth/oauth/accounts/{provider}")
async def unlink_oauth_account(
    provider: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    解除 OAuth 账户关联

    参数：
    - provider: OAuth 提供商（github, google）

    返回：
    - message: 成功消息

    说明：
    - 解除关联后，用户将无法使用该 OAuth 提供商登录
    - 如果这是最后一个 OAuth 账户且用户未设置密码，需要先设置密码
    - 解除关联不会删除用户账户

    错误：
    - 400: 尝试解除最后一个 OAuth 账户（未设置密码）
    - 404: 未找到关联的 OAuth 账户
    """
    try:
        from ModuleFolders.Service.Auth import get_oauth_manager

        # 验证提供商
        if provider not in ["github", "google"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 OAuth 提供商: {provider}"
            )

        oauth_manager = get_oauth_manager()

        result = oauth_manager.unlink_oauth_account(
            user_id=str(user.id),
            provider=provider,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 团队管理 API ---

# 请求/响应模型
class CreateTeamRequest(BaseModel):
    """创建团队请求"""
    name: str
    slug: str
    description: Optional[str] = None

class UpdateTeamRequest(BaseModel):
    """更新团队请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class InviteMemberRequest(BaseModel):
    """邀请成员请求"""
    email: str
    role: str = "member"  # owner, admin, member

class UpdateMemberRoleRequest(BaseModel):
    """更新成员角色请求"""
    new_role: str  # owner, admin, member

class AcceptInvitationRequest(BaseModel):
    """接受邀请请求"""
    token: str

class DeclineInvitationRequest(BaseModel):
    """拒绝邀请请求"""
    token: str


@app.post("/api/v1/teams", response_model=Dict[str, Any])
async def create_team(
    request: CreateTeamRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    创建团队

    请求体：
    - name: 团队名称（必填）
    - slug: 团队URL标识（必填，3-50字符，小写字母数字连字符）
    - description: 团队描述（可选）

    返回：
    创建的团队信息，包含：
    - id: 团队ID
    - name: 团队名称
    - slug: 团队URL标识
    - description: 团队描述
    - owner_id: 所有者ID
    - max_members: 最大成员数
    - created_at: 创建时间

    说明：
    - 创建者自动成为团队所有者（Owner）
    - 最大成员数根据订阅计划自动设置
    - Free: 5人, Starter: 10人, Pro: 50人, Enterprise: 无限制

    错误：
    - 400: slug格式无效或已被使用
    - 404: 用户不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager
        from ModuleFolders.Service.Auth.models import Tenant

        # 获取用户的租户ID（如果有）
        tenant_id = None
        try:
            tenant = Tenant.get(Tenant.owner == user.id)
            tenant_id = str(tenant.id)
        except:
            pass

        team_manager = TeamManager()

        # 创建团队
        team = team_manager.create_team(
            owner_id=str(user.id),
            name=request.name,
            slug=request.slug,
            tenant_id=tenant_id,
            description=request.description,
        )

        return {
            "id": str(team.id),
            "name": team.name,
            "slug": team.slug,
            "description": team.description,
            "owner_id": str(team.owner.id),
            "max_members": team.max_members,
            "is_active": team.is_active,
            "created_at": team.created_at.isoformat() if team.created_at else None,
        }

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/teams", response_model=List[Dict[str, Any]])
async def list_teams(
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取我的团队列表

    返回：
    用户参与的所有团队，每个团队包含：
    - id: 团队ID
    - name: 团队名称
    - slug: 团队URL标识
    - description: 团队描述
    - owner_id: 所有者ID
    - is_active: 是否激活
    - member_count: 成员数量
    - my_role: 用户在团队中的角色

    说明：
    - 包括用户拥有的团队（Owner）
    - 包括用户参与的团队（Admin/Member）
    """
    try:
        from ModuleFolders.Service.Team import TeamManager, TeamRepository

        team_manager = TeamManager()
        team_repository = TeamRepository()

        # 获取用户所有团队
        teams = team_manager.list_user_teams(user_id=str(user.id))

        result = []
        for team in teams:
            # 获取成员数量
            member_count = team_repository.count_members(team.id, include_pending=False)

            # 获取用户在团队中的角色
            member = team_repository.find_member(team.id, str(user.id))
            my_role = member.role if member else None

            result.append({
                "id": str(team.id),
                "name": team.name,
                "slug": team.slug,
                "description": team.description,
                "owner_id": str(team.owner.id),
                "is_active": team.is_active,
                "max_members": team.max_members,
                "member_count": member_count,
                "my_role": my_role,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/teams/{team_id}", response_model=Dict[str, Any])
async def get_team(
    team_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取团队详情

    路径参数：
    - team_id: 团队ID

    返回：
    团队的完整信息，包含：
    - id: 团队ID
    - name: 团队名称
    - slug: 团队URL标识
    - description: 团队描述
    - owner_id: 所有者ID
    - max_members: 最大成员数
    - is_active: 是否激活
    - member_count: 当前成员数
    - my_role: 当前用户在团队中的角色
    - created_at: 创建时间

    错误：
    - 403: 无权限访问该团队
    - 404: 团队不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager, TeamRepository

        team_manager = TeamManager()
        team_repository = TeamRepository()

        # 获取团队（包含权限验证）
        team = team_manager.get_team(team_id=team_id, user_id=str(user.id))

        # 获取成员数量
        member_count = team_repository.count_members(team.id, include_pending=False)

        # 获取用户在团队中的角色
        member = team_repository.find_member(team.id, str(user.id))
        my_role = member.role if member else None

        return {
            "id": str(team.id),
            "name": team.name,
            "slug": team.slug,
            "description": team.description,
            "owner_id": str(team.owner.id),
            "max_members": team.max_members,
            "is_active": team.is_active,
            "member_count": member_count,
            "my_role": my_role,
            "settings": team.settings,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
        }

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/teams/{team_id}", response_model=Dict[str, Any])
async def update_team(
    team_id: str,
    request: UpdateTeamRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新团队信息

    路径参数：
    - team_id: 团队ID

    请求体：
    - name: 团队名称（可选）
    - description: 团队描述（可选）
    - settings: 团队设置（可选，JSON对象）

    返回：
    更新后的团队信息

    说明：
    - 只有团队所有者（Owner）可以更新团队信息
    - 支持部分字段更新

    错误：
    - 403: 无权限（非Owner）
    - 404: 团队不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 构建更新参数（只包含提供的字段）
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.settings is not None:
            update_data["settings"] = request.settings

        # 更新团队
        team = team_manager.update_team(
            team_id=team_id,
            user_id=str(user.id),
            **update_data
        )

        return {
            "id": str(team.id),
            "name": team.name,
            "slug": team.slug,
            "description": team.description,
            "owner_id": str(team.owner.id),
            "max_members": team.max_members,
            "is_active": team.is_active,
            "settings": team.settings,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
        }

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/teams/{team_id}")
async def delete_team(
    team_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    删除团队

    路径参数：
    - team_id: 团队ID

    返回：
    - message: 成功消息

    说明：
    - 只有团队所有者（Owner）可以删除团队
    - 删除团队将级联删除所有成员记录
    - 此操作不可撤销

    错误：
    - 403: 无权限（非Owner）
    - 404: 团队不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 删除团队
        team_manager.delete_team(team_id=team_id, user_id=str(user.id))

        return {"message": "团队删除成功"}

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/teams/{team_id}/members", response_model=Dict[str, Any])
async def invite_team_member(
    team_id: str,
    request: InviteMemberRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    邀请成员加入团队

    路径参数：
    - team_id: 团队ID

    请求体：
    - email: 被邀请用户邮箱
    - role: 成员角色（member/admin，默认member）

    返回：
    邀请信息，包含：
    - invitation_id: 邀请ID
    - invitation_token: 邀请令牌（用于接受邀请）
    - email: 被邀请邮箱
    - role: 分配的角色
    - team_id: 团队ID
    - team_name: 团队名称

    说明：
    - 只有Owner和Admin可以邀请成员
    - 被邀请用户必须已存在
    - 邀请令牌有效期为7天
    - 需要使用邀请令牌调用接受邀请API

    错误：
    - 400: 角色无效、团队成员已满、用户已在团队中
    - 403: 无权限
    - 404: 团队或用户不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager
        from ModuleFolders.Service.Auth.models import User

        team_manager = TeamManager()

        # 根据邮箱查找被邀请用户
        try:
            invited_user = User.get(User.email == request.email)
        except:
            raise HTTPException(
                status_code=404,
                detail=f"用户不存在: {request.email}"
            )

        # 验证角色
        if request.role not in ["admin", "member"]:
            raise HTTPException(
                status_code=400,
                detail=f"无效的角色: {request.role}，应为 admin 或 member"
            )

        # 发送邀请
        member = team_manager.invite_member(
            team_id=team_id,
            inviter_id=str(user.id),
            user_id=str(invited_user.id),
            role=request.role,
        )

        return {
            "invitation_id": str(member.id),
            "invitation_token": member.invitation_token,
            "email": request.email,
            "role": member.role,
            "team_id": team_id,
            "team_name": member.team.name,
            "invited_at": member.invited_at.isoformat() if member.invited_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            if e.code in ["team_full", "already_member"]:
                raise HTTPException(status_code=400, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/teams/{team_id}/members", response_model=List[Dict[str, Any]])
async def list_team_members(
    team_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取团队成员列表

    路径参数：
    - team_id: 团队ID

    返回：
    团队成员列表，每个成员包含：
    - id: 成员记录ID
    - user_id: 用户ID
    - username: 用户名
    - email: 用户邮箱
    - full_name: 用户全名
    - avatar_url: 用户头像
    - role: 成员角色（owner/admin/member）
    - invitation_status: 邀请状态（pending/accepted/declined）
    - invited_at: 邀请时间
    - joined_at: 加入时间

    说明：
    - 只有团队成员可以查看成员列表
    - 包含待接受邀请的成员

    错误：
    - 403: 无权限访问
    - 404: 团队不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 获取成员列表（包含权限验证）
        members = team_manager.list_members(team_id=team_id, user_id=str(user.id))

        result = []
        for member in members:
            user_data = member.user
            result.append({
                "id": str(member.id),
                "user_id": str(user_data.id),
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "avatar_url": user_data.avatar_url,
                "role": member.role,
                "invitation_status": member.invitation_status,
                "invited_at": member.invited_at.isoformat() if member.invited_at else None,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            })

        return result

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/teams/{team_id}/members/{member_user_id}", response_model=Dict[str, Any])
async def update_team_member_role(
    team_id: str,
    member_user_id: str,
    request: UpdateMemberRoleRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    更新团队成员角色

    路径参数：
    - team_id: 团队ID
    - member_user_id: 成员用户ID

    请求体：
    - new_role: 新角色（owner/admin/member）

    返回：
    更新后的成员信息，包含：
    - id: 成员记录ID
    - user_id: 用户ID
    - username: 用户名
    - email: 用户邮箱
    - role: 新角色
    - updated_at: 更新时间

    说明：
    - 只有Owner可以更新成员角色
    - 不能修改Owner的角色
    - 可以将Admin降级为Member
    - 可以将Member升级为Admin

    错误：
    - 400: 角色无效、不能修改Owner角色
    - 403: 无权限
    - 404: 团队或成员不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 验证角色
        if request.new_role not in ["owner", "admin", "member"]:
            raise HTTPException(
                status_code=400,
                detail=f"无效的角色: {request.new_role}"
            )

        # 更新成员角色
        member = team_manager.update_member_role(
            team_id=team_id,
            operator_id=str(user.id),
            member_user_id=member_user_id,
            new_role=request.new_role,
        )

        user_data = member.user
        return {
            "id": str(member.id),
            "user_id": str(user_data.id),
            "username": user_data.username,
            "email": user_data.email,
            "role": member.role,
            "invitation_status": member.invitation_status,
            "updated_at": member.team.updated_at.isoformat() if member.team.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code in ["team_not_found", "member_not_found"]:
                raise HTTPException(status_code=404, detail=e.message)
            if e.code in ["permission_denied", "cannot_change_owner"]:
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/teams/{team_id}/members/{member_user_id}")
async def remove_team_member(
    team_id: str,
    member_user_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    移除团队成员

    路径参数：
    - team_id: 团队ID
    - member_user_id: 成员用户ID

    返回：
    - message: 成功消息

    说明：
    - Owner可以移除任何人
    - Admin可以移除Member，但不能移除Owner和其他Admin
    - 不能移除团队所有者
    - 移除后用户将无法访问团队资源

    错误：
    - 403: 无权限或不能移除Owner
    - 404: 团队或成员不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 移除成员
        team_manager.remove_member(
            team_id=team_id,
            operator_id=str(user.id),
            member_user_id=member_user_id,
        )

        return {"message": "成员移除成功"}

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code in ["team_not_found", "member_not_found"]:
                raise HTTPException(status_code=404, detail=e.message)
            if e.code in ["permission_denied", "cannot_remove_owner"]:
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/teams/accept", response_model=Dict[str, Any])
async def accept_team_invitation(
    request: AcceptInvitationRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    接受团队邀请

    请求体：
    - token: 邀请令牌

    返回：
    团队信息，包含：
    - id: 团队ID
    - name: 团队名称
    - slug: 团队URL标识
    - role: 用户在团队中的角色
    - joined_at: 加入时间

    说明：
    - 用户必须已登录
    - 邀请令牌有效期为7天
    - 接受后用户成为团队成员
    - 邀请令牌只能使用一次

    错误：
    - 400: 邀请已被接受或拒绝
    - 404: 邀请不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 接受邀请
        member = team_manager.accept_invitation(
            token=request.token,
            user_id=str(user.id),
        )

        team = member.team
        return {
            "id": str(team.id),
            "name": team.name,
            "slug": team.slug,
            "description": team.description,
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        }

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code in ["invitation_not_found", "already_accepted", "already_declined"]:
                raise HTTPException(status_code=400, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/teams/decline")
async def decline_team_invitation(
    request: DeclineInvitationRequest,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    拒绝团队邀请

    请求体：
    - token: 邀请令牌

    返回：
    - message: 成功消息
    - team_name: 团队名称

    说明：
    - 用户必须已登录
    - 拒绝后邀请令牌失效
    - 无法重新使用同一令牌接受邀请

    错误：
    - 400: 邀请已被接受或拒绝
    - 404: 邀请不存在
    """
    try:
        from ModuleFolders.Service.Team import TeamManager

        team_manager = TeamManager()

        # 拒绝邀请
        member = team_manager.decline_invitation(
            token=request.token,
            user_id=str(user.id),
        )

        return {
            "message": "邀请已拒绝",
            "team_name": member.team.name,
        }

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code in ["invitation_not_found", "already_accepted", "already_declined"]:
                raise HTTPException(status_code=400, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/teams/{team_id}/quota", response_model=Dict[str, Any])
async def get_team_quota_status(
    team_id: str,
    user: User = Depends(jwt_middleware.get_current_user)
):
    """
    获取团队配额状态

    路径参数：
    - team_id: 团队ID

    返回：
    团队配额信息，包含：
    - current_members: 当前成员数（已加入）
    - pending_invites: 待接受邀请数
    - total_reserved: 总占用名额（已加入 + 待接受）
    - max_members: 最大成员数（基于订阅计划）
    - remaining_slots: 剩余可用名额
    - usage_percentage: 使用百分比
    - plan: 订阅计划名称
    - is_unlimited: 是否无限制

    说明：
    - 配额基于团队所有者的订阅计划
    - Free: 5人, Starter: 10人, Pro: 50人, Enterprise: 无限制
    - 待接受的邀请也计入配额

    错误：
    - 403: 无权限访问团队
    - 404: 团队不存在
    """
    try:
        from ModuleFolders.Service.Team.team_quota_middleware import TeamQuotaMiddleware
        from ModuleFolders.Service.Team.team_manager import TeamManager, TeamError

        # 验证访问权限
        team_manager = TeamManager()
        team = team_manager.get_team(team_id, str(user.id))

        # 获取配额状态
        quota_middleware = TeamQuotaMiddleware()
        quota_status = quota_middleware.get_quota_status(team_id, str(user.id))

        return quota_status

    except Exception as e:
        from ModuleFolders.Service.Team.team_manager import TeamError
        if isinstance(e, TeamError):
            if e.code == "team_not_found":
                raise HTTPException(status_code=404, detail=e.message)
            if e.code == "permission_denied":
                raise HTTPException(status_code=403, detail=e.message)
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=500, detail=str(e))


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

class StoppableServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @property
    def is_running(self):
        return self.started and not self.should_exit

_current_server: Optional[StoppableServer] = None

def stop_server():
    """Stops the running uvicorn server and any active tasks."""
    global _current_server
    if _current_server:
        # 1. Stop any running subprocess task
        task_manager.stop_task()
        # 2. Tell uvicorn to exit
        _current_server.should_exit = True
        _current_server = None

def run_server(host: str = "127.0.0.1", port: int = 8000, monitor_mode: bool = False):
    """Starts the FastAPI server in a separate thread."""
    global SYSTEM_MODE, _current_server
    SYSTEM_MODE = "monitor" if monitor_mode else "full"
    
    # 动态记录 WebServer 的地址，以便子进程上报数据
    task_manager.api_url = f"http://{host}:{port}"
    
    try:
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        _current_server = StoppableServer(config)

        def server_task():
            _current_server.run()

        # Running in a daemon thread allows the main TUI to exit cleanly
        thread = threading.Thread(target=server_task, daemon=True)
        thread.start()
        return thread
    except ImportError:
        # This should ideally be handled before calling run_server
        print("Error: Uvicorn is required to run the web server.")
        return None

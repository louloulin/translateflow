import os
import sys

# Silence TF and other C++ logs that break TUI
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'

import re
import time
import signal
import threading
import warnings
import locale
import collections
import rapidjson as json

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn, SpinnerColumn
from rich import print

warnings.filterwarnings('ignore')

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from ModuleFolders.Infrastructure.Tokener.TiktokenLoader import initialize_tiktoken
import ModuleFolders.Infrastructure.Tokener.TiktokenLoader as TiktokenLoaderModule
import ModuleFolders.Domain.FileReader.ReaderUtil as ReaderUtilModule
TiktokenLoaderModule._SUPPRESS_OUTPUT = True
ReaderUtilModule._SUPPRESS_OUTPUT = True
try: initialize_tiktoken()
except Exception: pass

from ModuleFolders.Base.Base import Base
from ModuleFolders.Base.PluginManager import PluginManager
from ModuleFolders.Infrastructure.Cache.CacheManager import CacheManager
from ModuleFolders.Domain.FileReader.FileReader import FileReader
from ModuleFolders.Domain.FileOutputer.FileOutputer import FileOutputer
from ModuleFolders.Service.SimpleExecutor.SimpleExecutor import SimpleExecutor
from ModuleFolders.Service.TaskExecutor.TaskExecutor import TaskExecutor
from ModuleFolders.Infrastructure.TaskConfig.TaskType import TaskType
from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig
from ModuleFolders.Service.HttpService.HttpService import HttpService
from ModuleFolders.UserInterface.FileSelector import FileSelector

console = Console()

class I18NLoader:
    def __init__(self, lang="en"):
        self.lang, self.data = lang, {}
        self.load_language(lang)
    def load_language(self, lang):
        path = os.path.join(PROJECT_ROOT, "I18N", f"{lang}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: self.data = json.load(f)
        elif lang != "en": self.load_language("en")
    def get(self, key): return self.data.get(key, key)

config_path = os.path.join(PROJECT_ROOT, "Resource", "config.json")
config = {}
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f: config = json.load(f)

saved_lang = config.get("interface_language")
current_lang = saved_lang or (lambda: "zh_CN" if (l := locale.getdefaultlocale()[0]) and l.startswith("zh") else "ja" if l and l.startswith("ja") else "en")()
i18n = I18NLoader(current_lang)

def mask_key(key):
    if not key: return ""
    if len(key) < 8: return "*" * len(key)
    return key[:4] + "****" + key[-4:]

class TaskUI:
    def __init__(self):
        self.logs = collections.deque(maxlen=20)
        self.progress = Progress(SpinnerColumn(), 
            TextColumn("[bold blue]{task.fields[action]}", justify="right"), 
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%", "•", 
            TextColumn("[bold green]{task.completed}/{task.total} L"), "•", 
            TextColumn("[bold yellow]{task.fields[rpm]} R"), "•",
            TextColumn("[bold magenta]{task.fields[tpm]} K"), "•",
            TimeRemainingColumn(), "•", TimeElapsedColumn(), expand=True)
        self.task_id = self.progress.add_task("", total=100, action="Initializing", rpm="0", tpm="0")
        self.layout = Layout()
        # Use ratio for upper to allow "shaking" it later
        self.layout.split(
            Layout(name="upper", ratio=4, minimum_size=10),
            Layout(Panel(self.progress, title="Progress", border_style="green"), name="lower", size=4)
        )
    def log(self, msg):
        if not isinstance(msg, str):
            from rich.console import Console
            from io import StringIO
            with StringIO() as buf:
                # Use a higher width to prevent excessive wrapping for tables
                temp_console = Console(file=buf, force_terminal=True, width=120)
                temp_console.print(msg)
                msg = buf.getvalue().strip()
        
        # Strip ANSI if the msg is too long or looks like TUI artifacts to prevent breaking the log panel
        # But for Tables we usually want to keep the formatting if possible.
        # Rich Panel usually handles ANSI correctly.
        
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.layout["upper"].update(Panel("\n".join(self.logs), title="Logs", border_style="blue", padding=(0, 1)))
    def update_progress(self, event, data):
        completed = data.get("line", 0)
        total = data.get("total_line", 0)
        
        # Log success message in action bar with stats if available
        if completed > 0:
             # Calculate session stats if possible
             elapsed = data.get("time", 0)
             tokens = data.get("token", 0)
             if elapsed > 0 and tokens > 0:
                 stats_str = f"Done! ({completed}/{total}) | {elapsed:.1f}s | {tokens}T"
                 self.progress.update(self.task_id, action=stats_str)
             else:
                 self.progress.update(self.task_id, action=f"Done! ({completed}/{total})")

        # Only update total if it's a valid positive number
        if total > 0:
            self.progress.update(self.task_id, total=total, completed=completed)
        
        rpm, tpm_k = 0, 0
        elapsed = data.get("time", 0)
        if elapsed > 0:
            # rpm = total requests / (seconds / 60)
            rpm = data.get("total_requests", 0) / (elapsed / 60)
            # tpm = total tokens / (seconds / 60)
            tpm_k = (data.get("token", 0) / (elapsed / 60)) / 1000
            
        # Add Current File hint if available
        current_file_info = ""
        if "file_name" in data:
            f_idx = data.get("file_index", 0)
            f_total = data.get("total_files", 0)
            f_name = data.get("file_name", "")
            current_file_info = f" | [{f_idx}/{f_total}] {f_name}"
            
        self.progress.update(self.task_id, completed=completed, rpm=f"{rpm:.1f}", tpm=f"{tpm_k:.1f}")
        
        if current_file_info:
            # Update action with file info periodically if it's still "Translating" or similar
            current_action = self.progress.tasks[self.task_id].fields.get("action", "")
            if "Translating" in current_action or "Done" in current_action:
                # We prefix it
                new_action = f"{current_action.split('|')[0].strip()}{current_file_info}"
                self.progress.update(self.task_id, action=new_action)

class CLIMenu:
    def __init__(self):
        self.root_config_path = os.path.join(PROJECT_ROOT, "Resource", "config.json")
        self.profiles_dir = os.path.join(PROJECT_ROOT, "Resource", "profiles")
        self.config = {}
        self.root_config = {}
        self.active_profile_name = "default"
        self.load_config()

        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins_from_directory(os.path.join(PROJECT_ROOT, "PluginScripts"))
        self.file_reader, self.file_outputer, self.cache_manager = FileReader(), FileOutputer(), CacheManager()
        self.simple_executor = SimpleExecutor()
        self.task_executor = TaskExecutor(self.plugin_manager, self.cache_manager, self.file_reader, self.file_outputer)
        self.file_selector = FileSelector(i18n)
        signal.signal(signal.SIGINT, self.signal_handler)
        self.task_running, self.original_print = False, Base.print

    def _migrate_and_load_profiles(self):
        os.makedirs(self.profiles_dir, exist_ok=True)
        active_profile_path = os.path.join(self.profiles_dir, f"{self.active_profile_name}.json")

        # One-time migration from old config to default profile
        if not os.path.exists(self.profiles_dir) or not os.listdir(self.profiles_dir):
            if os.path.exists(self.root_config_path):
                try:
                    shutil.move(self.root_config_path, active_profile_path)
                    self.root_config = {"active_profile": "default", "recent_projects": []}
                    with open(self.root_config_path, 'w', encoding='utf-8') as f:
                        json.dump(self.root_config, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    console.print(f"[red]Failed to migrate config: {e}[/red]")
                    # Create a blank default profile if migration fails
                    if not os.path.exists(active_profile_path):
                        with open(active_profile_path, 'w', encoding='utf-8') as f: json.dump({}, f)

        # Load the active profile
        if os.path.exists(active_profile_path):
            with open(active_profile_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else: # If active profile is missing, create a blank one
            self.config = {}
            self.save_config()

    def load_config(self):
        # Load root config
        if os.path.exists(self.root_config_path) and os.path.getsize(self.root_config_path) > 0:
            try:
                with open(self.root_config_path, 'r', encoding='utf-8') as f:
                    self.root_config = json.load(f)
                self.active_profile_name = self.root_config.get("active_profile", "default")
            except (json.JSONDecodeError, UnicodeDecodeError):
                 # This can happen if the root config is the old, large settings file. Trigger migration path.
                 self.active_profile_name = "default"
                 self._migrate_and_load_profiles()
                 return
        else:
            self.active_profile_name = "default"
        
        self._migrate_and_load_profiles()

    def save_config(self, save_root=False):
        # Save the main settings to the active profile file
        active_profile_path = os.path.join(self.profiles_dir, f"{self.active_profile_name}.json")
        os.makedirs(os.path.dirname(active_profile_path), exist_ok=True)
        with open(active_profile_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

        # Optionally save the root config (e.g., when changing active profile or recent projects)
        if save_root:
            with open(self.root_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.root_config, f, indent=4, ensure_ascii=False)
    def _update_recent_projects(self, project_path):
        recent = self.root_config.get("recent_projects", [])
        if project_path in recent:
            recent.remove(project_path)
        recent.insert(0, project_path)
        self.root_config["recent_projects"] = recent[:5] # Keep last 5
        self.save_config(save_root=True)
    def signal_handler(self, sig, frame):
        if self.task_running:
            if getattr(self, "stop_requested", False):
                console.print("\n[bold red]Force quitting immediately...[/bold red]")
                os._exit(1)
            
            console.print("\n[yellow]Stopping task... (Press Ctrl+C again to force quit)[/yellow]")
            self.stop_requested = True
            
            # Immediately set status to stop threads faster
            Base.work_status = Base.STATUS.STOPING
            
            from ModuleFolders.Base.EventManager import EventManager
            EventManager.get_singleton().emit(Base.EVENT.TASK_STOP, {})
        else:
            sys.exit(0)
    def display_banner(self):
        profile_display = f"[bold yellow]({self.active_profile_name})[/bold yellow]"
        console.clear()
        console.print(Panel.fit(f"[bold cyan]AiNiee CLI[/bold cyan] {profile_display}\nGUI Original: By NEKOparapa\nCLI Version: By ShadowLoveElysia\nLang: {current_lang}", title="Welcome"))

    def main_menu(self):
        if "interface_language" not in self.config: self.first_time_lang_setup()
        while True:
            self.display_banner()
            table = Table(show_header=False, box=None)
            menus, colors = ["start_translation", "start_polishing", "export_only", "settings", "api_settings", "glossary", "profiles"], ["green", "green", "magenta", "blue", "blue", "yellow", "cyan"]
            for i, (m, c) in enumerate(zip(menus, colors)): table.add_row(f"[{c}]{i+1}.[/]", i18n.get(f"menu_{m}"))
            table.add_row("[red]0.[/]", i18n.get("menu_exit")); console.print(table)
            choice = IntPrompt.ask(f"\n{i18n.get('prompt_select')}", choices=[str(i) for i in range(len(menus) + 1)], show_choices=False)
            console.print("\n")
            [sys.exit, lambda: self.run_task(TaskType.TRANSLATION), lambda: self.run_task(TaskType.POLISH), self.run_export_only, self.settings_menu, self.api_settings_menu, self.prompt_menu, self.profiles_menu][choice]()

    def profiles_menu(self):
        while True:
            self.display_banner()
            console.print(Panel(f"[bold]{i18n.get('menu_profiles')}[/bold]"))
            
            profiles = [f.replace(".json", "") for f in os.listdir(self.profiles_dir) if f.endswith(".json")]
            
            table = Table(show_header=False, box=None)
            table.add_row("[cyan]1.[/]", "Switch Profile")
            table.add_row("[cyan]2.[/]", "Create New Profile")
            table.add_row("[cyan]3.[/]", "Rename Current Profile")
            table.add_row("[red]4.[/]", "Delete a Profile")
            console.print(table)
            console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")

            choice = IntPrompt.ask(f"\n{i18n.get('prompt_select')}", choices=["0", "1", "2", "3", "4"], show_choices=False)
            
            if choice == 0:
                break
            elif choice == 1: # Switch Profile
                sel = Prompt.ask("Select profile to activate", choices=profiles, default=self.active_profile_name)
                self.root_config["active_profile"] = sel
                self.save_config(save_root=True)
                self.load_config() # Reload everything
                console.print(f"[green]Profile '{sel}' activated.[/green]"); time.sleep(1)
                break # Exit to main menu to reflect change
            elif choice == 2: # Create New Profile
                new_name = Prompt.ask("Enter name for new profile").strip()
                if new_name and not os.path.exists(os.path.join(self.profiles_dir, f"{new_name}.json")):
                    shutil.copyfile(
                        os.path.join(self.profiles_dir, f"{self.active_profile_name}.json"),
                        os.path.join(self.profiles_dir, f"{new_name}.json")
                    )
                    console.print(f"[green]Profile '{new_name}' created.[/green]")
                else:
                    console.print("[red]Invalid or existing profile name.[/red]")
                time.sleep(1)
            elif choice == 3: # Rename Current Profile
                new_name = Prompt.ask("Enter new name for current profile").strip()
                if new_name and not os.path.exists(os.path.join(self.profiles_dir, f"{new_name}.json")):
                    os.rename(
                        os.path.join(self.profiles_dir, f"{self.active_profile_name}.json"),
                        os.path.join(self.profiles_dir, f"{new_name}.json")
                    )
                    self.active_profile_name = new_name
                    self.root_config["active_profile"] = new_name
                    self.save_config(save_root=True)
                    console.print(f"[green]Profile renamed to '{new_name}'.[/green]")
                else:
                    console.print("[red]Invalid or existing profile name.[/red]")
                time.sleep(1)

            elif choice == 4: # Delete Profile
                if len(profiles) <= 1:
                    console.print("[red]Cannot delete the last profile.[/red]"); time.sleep(1); continue

                sel = Prompt.ask("Select profile to DELETE", choices=[p for p in profiles if p != self.active_profile_name])
                if Confirm.ask(f"[bold red]Are you sure you want to PERMANENTLY delete '{sel}'?[/bold red]"):
                    os.remove(os.path.join(self.profiles_dir, f"{sel}.json"))
                    console.print(f"[green]Profile '{sel}' deleted.[/green]")
                else:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                time.sleep(1)

    def first_time_lang_setup(self):
        global current_lang, i18n; console.print(f"[cyan]Detected: {current_lang}[/cyan]")
        if Confirm.ask(f"Use {current_lang}?", default=True): self.config["interface_language"] = current_lang
        else:
            console.print("\n1. 中文\n2. 日本語\n3. English"); c = IntPrompt.ask("Select", choices=["1", "2", "3"], default=1)
            current_lang = {"1": "zh_CN", "2": "ja", "3": "en"}[str(c)]; self.config["interface_language"] = current_lang
        self.save_config(); i18n = I18NLoader(current_lang)
    def settings_menu(self):
        while True:
            self.display_banner(); console.print(Panel(f"[bold]{i18n.get('menu_settings')}[/bold]"))
            table = Table(show_header=True); table.add_column("ID", style="dim"); table.add_column("Setting"); table.add_column("Value", style="cyan")
            limit_switch = self.config.get("tokens_limit_switch", False)
            limit_mode_str = "Token" if limit_switch else "Line"; limit_val_key = "tokens_limit" if limit_switch else "lines_limit"
            table.add_row("1", i18n.get("setting_input_path"), self.config.get("label_input_path", ""))
            table.add_row("2", i18n.get("setting_output_path"), self.config.get("label_output_path", ""))
            table.add_row("3", i18n.get("setting_src_lang"), self.config.get("source_language", ""))
            table.add_row("4", i18n.get("setting_tgt_lang"), self.config.get("target_language", ""))
            table.add_row("5", i18n.get("setting_thread_count"), str(self.config.get("actual_thread_counts", 5)))
            table.add_row("6", i18n.get("setting_project_type"), self.config.get("translation_project", "AutoType"))
            table.add_row("7", i18n.get("setting_trans_mode"), f"{limit_mode_str} ({self.config.get(limit_val_key, 20)})")
            table.add_row("8", i18n.get("setting_detailed_logs"), "[green]ON[/]" if self.config.get("show_detailed_logs", False) else "[red]OFF[/]")
            table.add_row("9", i18n.get("setting_cache_backup"), "[green]ON[/]" if self.config.get("enable_cache_backup", False) else "[red]OFF[/]")
            table.add_row("10", i18n.get("setting_cache_backup_limit"), str(self.config.get("cache_backup_limit", 10)))
            table.add_row("11", i18n.get("setting_auto_restore_ebook"), "[green]ON[/]" if self.config.get("enable_auto_restore_ebook", False) else "[red]OFF[/]")
            table.add_row("12", i18n.get("setting_dry_run"), "[green]ON[/]" if self.config.get("enable_dry_run", True) else "[red]OFF[/]")
            table.add_row("13", i18n.get("setting_auto_heal"), "[green]ON[/]" if self.config.get("enable_auto_heal", True) else "[red]OFF[/]")
            table.add_row("14", i18n.get("setting_retry_backoff"), "[green]ON[/]" if self.config.get("enable_retry_backoff", True) else "[red]OFF[/]")
            table.add_row("15", i18n.get("setting_task_notification"), "[green]ON[/]" if self.config.get("enable_task_notification", True) else "[red]OFF[/]")
            table.add_row("16", i18n.get("setting_session_logging"), "[green]ON[/]" if self.config.get("enable_session_logging", True) else "[red]OFF[/]")
            
            table.add_section()
            table.add_row("17", i18n.get("setting_enable_api_failover"), "[green]ON[/]" if self.config.get("enable_api_failover", False) else "[red]OFF[/]")
            table.add_row("18", i18n.get("setting_api_failover_threshold"), str(self.config.get("api_failover_threshold", 3)))
            table.add_row("19", i18n.get("setting_backup_apis"), ", ".join(self.config.get("backup_apis", [])))

            console.print(table); console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")
            choice = IntPrompt.ask(f"\n{i18n.get('prompt_select')}", choices=[str(i) for i in range(20)], show_choices=False)
            console.print("\n")
            if choice == 0: break
            elif choice == 1 or choice == 2:
                console.print(f"\n[yellow]{i18n.get('warn_path_change')}[/yellow]")
                key = "label_input_path" if choice == 1 else "label_output_path"
                prompt_key = "prompt_input_path" if choice == 1 else "prompt_output_path"
                new_val = Prompt.ask(f"\n{i18n.get(prompt_key)}", default=self.config.get(key, ""))
                if new_val == "0": continue
                self.config[key] = new_val
            elif choice == 3: 
                new_val = Prompt.ask(f"\n{i18n.get('prompt_source_lang')}", default=self.config.get('source_language'))
                if new_val == "0": continue
                self.config["source_language"] = new_val
            elif choice == 4: 
                new_val = Prompt.ask(f"\n{i18n.get('prompt_target_lang')}", default=self.config.get('target_language'))
                if new_val == "0": continue
                self.config["target_language"] = new_val
            elif choice == 5:
                console.print(f"\n[cyan]{i18n.get('tip_thread_count')}[/cyan]")
                val = IntPrompt.ask(f"\n{i18n.get('setting_thread_count')}", default=self.config.get("actual_thread_counts"))
                if val == 0: continue
                self.config["actual_thread_counts"] = val
                self.config["user_thread_counts"] = val
            elif choice == 6:
                console.print(f"\n[yellow]{i18n.get('warn_project_type')}[/yellow]")
                self.project_type_menu()
            elif choice == 7:
                self.trans_mode_menu()
            elif choice == 8:
                self.config["show_detailed_logs"] = not self.config.get("show_detailed_logs", False)
            elif choice == 9:
                self.config["enable_cache_backup"] = not self.config.get("enable_cache_backup", False)
            elif choice == 10:
                val = IntPrompt.ask(f"\n{i18n.get('setting_cache_backup_limit')}", default=self.config.get("cache_backup_limit", 10))
                if val >= 0:
                    self.config["cache_backup_limit"] = val
            elif choice == 11:
                self.config["enable_auto_restore_ebook"] = not self.config.get("enable_auto_restore_ebook", False)
            elif choice == 12:
                self.config["enable_dry_run"] = not self.config.get("enable_dry_run", True)
            elif choice == 13:
                self.config["enable_auto_heal"] = not self.config.get("enable_auto_heal", True)
            elif choice == 14:
                self.config["enable_retry_backoff"] = not self.config.get("enable_retry_backoff", True)
            elif choice == 15:
                self.config["enable_task_notification"] = not self.config.get("enable_task_notification", True)
            elif choice == 16:
                self.config["enable_session_logging"] = not self.config.get("enable_session_logging", True)
            elif choice == 17:
                self.config["enable_api_failover"] = not self.config.get("enable_api_failover", False)
            elif choice == 18:
                val = IntPrompt.ask(f"\n{i18n.get('setting_api_failover_threshold')}", default=self.config.get("api_failover_threshold", 3))
                if val > 0:
                    self.config["api_failover_threshold"] = val
            elif choice == 19:
                val = Prompt.ask(f"\n{i18n.get('setting_backup_apis')}", default=", ".join(self.config.get("backup_apis", [])))
                self.config["backup_apis"] = [api.strip() for api in val.split(",") if api.strip()]
            self.save_config()

    def trans_mode_menu(self):
        console.clear(); console.print(Panel(f"[bold]{i18n.get('menu_trans_mode_select')}[/bold]"))
        console.print(f"1. {i18n.get('mode_line')}")
        console.print(f"2. {i18n.get('mode_token')}")
        console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")
        
        c = IntPrompt.ask(i18n.get('prompt_select'), choices=["0", "1", "2"], show_choices=False)
        console.print()
        if c == 0: return
        elif c == 1: # Line Mode
            console.print(f"[cyan]{i18n.get('tip_line_mode')}[/cyan]")
            val = IntPrompt.ask(i18n.get('prompt_new_value'), default=20)
            self.config["tokens_limit_switch"] = False
            self.config["lines_limit"] = val
        elif c == 2: # Token Mode
            console.print(f"[bold red]{i18n.get('warn_token_mode_severe')}[/bold red]")
            confirm_phrase = i18n.get('phrase_confirm_risk')
            
            user_input = Prompt.ask(i18n.get('prompt_confirm_risk').format(confirm_phrase))

            # Final Validation
            if user_input != confirm_phrase:
                console.print(f"[red]{i18n.get('msg_risk_abort')}[/red]"); time.sleep(2); return
            
            val = IntPrompt.ask(i18n.get('prompt_new_value'), default=1500)
            self.config["tokens_limit_switch"] = True
            self.config["tokens_limit"] = val
            self.config["tokens_limit_switch"] = True
            self.config["tokens_limit"] = val
    def project_type_menu(self):
        while True:
            self.display_banner(); console.print(Panel(f"[bold]{i18n.get('menu_project_type')}[/bold]"))
            table = Table(show_header=False, box=None)
            cats = ["auto", "game", "doc", "sub", "dev"]
            for i, cat in enumerate(cats): table.add_row(f"[cyan]{i+1}.[/]", i18n.get(f"cat_{cat}"))
            console.print(table); console.print(f"\n[dim]0. Back[/dim]")
            choice = IntPrompt.ask(i18n.get('prompt_select'), choices=[str(i) for i in range(len(cats)+1)], show_choices=False)
            console.print()
            if choice == 0: return
            elif choice == 1: self.config["translation_project"] = "AutoType"
            else:
                types = [["MTool", "RenPy", "TPP"], ["Txt", "Epub", "Docx"], ["Srt", "Ass"], ["Po", "I18next"]][choice-2]
                self.config["translation_project"] = Prompt.ask("Select Type", choices=types, default=types[0])
            self.save_config(); return
    def api_settings_menu(self):
        while True:
            self.display_banner(); current_p, current_m = self.config.get("target_platform", "None"), self.config.get("model", "None")
            console.print(Panel(f"[bold]{i18n.get('menu_api_settings')}[/bold] [dim](Current: {current_p} - {current_m})[/dim]"))
            menus=["online", "local", "validate", "manual"]
            for i, m in enumerate(menus): table.add_row(f"[{'cyan' if i<2 else 'green' if i<3 else 'yellow'}]{i+1}.[/]", i18n.get(f"menu_api_{m}"))
            console.print(table); console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")
            choice = IntPrompt.ask(i18n.get('prompt_select'), choices=list("01234"), show_choices=False)
            console.print()
            if choice == 0: break
            elif choice in [1, 2]: self.select_api_menu(online=choice==1)
            elif choice == 3: self.validate_api()
            elif choice == 4: self.manual_edit_api_menu()
    def select_api_menu(self, online: bool):
        local_keys = ["localllm", "sakura"]; platforms = self.config.get("platforms", {})
        options = {k: v for k, v in platforms.items() if (k.lower() not in local_keys) == online}
        if not options: return
        sel = Prompt.ask(i18n.get("msg_api_select_" + ("online" if online else "local")), choices=list(options.keys()))
        plat_conf = options[sel]
        self.config.update({
            "target_platform": sel, 
            "base_url": plat_conf.get("url"), 
            "model": plat_conf.get("models", [""])[0],
            "api_settings": {"translate": sel, "polish": sel}
        })
        if online:
            key = Prompt.ask(i18n.get("msg_api_key_for").format(sel), password=True)
            self.config["platforms"][sel]["api_key"] = key; self.config["api_key"] = key
        self.save_config(); console.print(f"[green]{i18n.get('msg_active_platform').format(sel)}[/green]"); time.sleep(1)
    def validate_api(self):
        task_config = TaskConfig(); task_config.initialize(); task_config.prepare_for_translation(TaskType.TRANSLATION)
        target_platform = task_config.target_platform
        
        with console.status(f"[cyan]{i18n.get('msg_api_validating')}[/cyan]"):
            try:
                if target_platform.lower() in ["localllm", "sakura"]:
                    # Use direct httpx for local APIs to bypass model param issues
                    import httpx
                    api_url = task_config.base_url.rstrip('/') + "/chat/completions"
                    api_key = task_config.get_next_apikey()
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"messages": [{"role": "user", "content": i18n.get("msg_test_msg")}], "max_tokens": 50}
                    
                    with httpx.Client(timeout=20) as client:
                        response = client.post(api_url, json=payload, headers=headers)
                        response.raise_for_status()
                        content = response.json()["choices"][0]["message"]["content"]
                else:
                    # Use standard LLMRequester for online APIs
                    from ModuleFolders.Infrastructure.LLMRequester.LLMRequester import LLMRequester
                    platform_config = task_config.get_platform_configuration("translationReq")
                    requester = LLMRequester()
                    messages = [{"role": "user", "content": i18n.get("msg_test_msg")}]
                    skip, think, content, p_tokens, c_tokens = requester.sent_request(
                        messages=messages, system_prompt=i18n.get("msg_test_sys"), platform_config=platform_config
                    )
                    if skip:
                        raise Exception("Request failed or was skipped by requester.")
                
                console.print(f"[green]✓ {i18n.get('msg_api_ok')}[/green]")
                console.print(f"[dim]Response: {content[:100]}...[/dim]")

            except Exception as e:
                console.print(f"[red]✗ {i18n.get('msg_api_fail')}:[/red] {e}")

        Prompt.ask("\nPress Enter...")
    def manual_edit_api_menu(self):
        while True:
            self.display_banner(); console.print(Panel(f"[bold]{i18n.get('menu_api_manual')}[/bold]"))
            table = Table(show_header=True); table.add_column("ID", style="dim"); table.add_column("Setting"); table.add_column("Value", style="cyan")
            table.add_row("1", i18n.get("label_platform"), self.config.get("target_platform", ""))
            table.add_row("2", i18n.get("label_url"), self.config.get("base_url", ""))
            table.add_row("3", i18n.get("label_key"), "****")
            table.add_row("4", i18n.get("label_model"), self.config.get("model", ""))
            console.print(table); console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")
            choice = IntPrompt.ask(i18n.get('prompt_select'), choices=list("01234"), show_choices=False)
            console.print()
            if choice == 0: break
            elif choice == 1: self.config["target_platform"] = Prompt.ask(i18n.get("label_platform"), default=self.config.get("target_platform"))
            elif choice == 2: self.config["base_url"] = Prompt.ask(i18n.get("label_url"), default=self.config.get("base_url"))
            elif choice == 3: self.config["api_key"] = Prompt.ask(i18n.get("label_key"), password=True)
            elif choice == 4: self.config["model"] = Prompt.ask(i18n.get("label_model"), default=self.config.get("model"))
            self.save_config()
    def prompt_menu(self):
        while True:
            self.display_banner(); console.print(Panel(f"[bold]{i18n.get('menu_glossary')}[/bold]"))
            trans_sel = self.config.get("translation_prompt_selection", {}).get("last_selected_id", "common")
            polish_sel = self.config.get("polishing_prompt_selection", {}).get("last_selected_id", "common")
            table = Table(show_header=False, box=None)
            table.add_row("[cyan]1.[/]", f"{i18n.get('menu_select_trans_prompt')} ({i18n.get('prompt_current_selection')}[green]{trans_sel}[/green])")
            table.add_row("[cyan]2.[/]", f"{i18n.get('menu_select_polish_prompt')} ({i18n.get('prompt_current_selection')}[green]{polish_sel}[/green])")
            console.print(table); console.print(f"\n[dim]0. {i18n.get('menu_exit')}[/dim]")
            choice = IntPrompt.ask(i18n.get('prompt_select'), choices=["0", "1", "2"], show_choices=False)
            console.print()
            if choice == 0: break
            elif choice == 1: self.select_prompt_template("Translate", "translation_prompt_selection")
            elif choice == 2: self.select_prompt_template("Polishing", "polishing_prompt_selection")
    def select_prompt_template(self, folder, key):
        prompt_dir = os.path.join(PROJECT_ROOT, "Resource", "Prompt", folder)
        if not os.path.exists(prompt_dir): return
        files = [f for f in os.listdir(prompt_dir) if f.endswith(".txt")]
        if not files: return
        for i, f in enumerate(files): console.print(f"{i+1}. {f}")
        
        choice_str = Prompt.ask(f"\n{i18n.get('prompt_template_select')}", choices=[str(i+1) for i in range(len(files))] + ["0"], show_choices=False)
        if choice_str == "0": return
        
        f_name = files[int(choice_str)-1]
        try:
            with open(os.path.join(prompt_dir, f_name), 'r', encoding='utf-8') as f: content = f.read()
            
            # Preview
            console.print(Panel(content, title=f"Preview: {f_name}", border_style="blue", height=15))
            
            if Confirm.ask(f"Apply '{f_name}'?", default=True):
                self.config[key] = {"last_selected_id": f_name.replace(".txt", ""), "prompt_content": content}
                self.save_config()
                console.print(f"[green]{i18n.get('msg_prompt_updated')}[/green]")
            else:
                console.print("[yellow]Cancelled.[/yellow]")
            time.sleep(1)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]"); time.sleep(2)
    def run_task(self, task_mode):
        # Check if we can resume the last task
        last_path = self.config.get("label_input_path")
        can_resume = False
        
        if last_path and os.path.exists(last_path):
            abs_last = os.path.abspath(last_path)
            last_parent = os.path.dirname(abs_last)
            last_base = os.path.basename(abs_last)
            if os.path.isfile(last_path):
                last_base = os.path.splitext(last_base)[0]
            last_opath = os.path.join(last_parent, f"{last_base}_AiNiee_Output")
            if os.path.exists(os.path.join(last_opath, "cache", "AinieeCacheData.json")):
                can_resume = True

        # Input Mode Selection
        console.clear()
        
        menu_text = f"1. {i18n.get('mode_single_file')}\n2. {i18n.get('mode_batch_folder')}"
        choices = ["0", "1", "2"]
        next_option_idx = 3
        
        if can_resume:
            short_path = last_path if len(last_path) < 60 else "..." + last_path[-57:]
            menu_text += f"\n{next_option_idx}. {i18n.get('mode_resume').format(short_path)}"
            choices.append(str(next_option_idx))
            next_option_idx += 1

        recent_projects = self.config.get("recent_projects", [])
        recent_projects_start_idx = next_option_idx
        
        if recent_projects:
            menu_text += f"\n\n[bold cyan]--- {i18n.get('menu_recent_projects')} ---[/bold cyan]"
            for i, path in enumerate(recent_projects):
                short_path = path if len(path) < 60 else "..." + path[-57:]
                menu_text += f"\n{recent_projects_start_idx + i}. {short_path}"
                choices.append(str(recent_projects_start_idx + i))

        menu_text += f"\n\n[dim]0. {i18n.get('menu_exit')}[/dim]"
        console.print(Panel(menu_text, title=f"[bold]{i18n.get('menu_input_mode')}[/bold]", expand=False))
        
        prompt_text = i18n.get('prompt_select').strip().rstrip(':').rstrip('：')
        choice = IntPrompt.ask(f"\n{prompt_text}", choices=choices, show_choices=False)
        console.print("\n")
        if choice == 0: return
        
        target_path = ""
        continue_status = False
        
        if can_resume and choice == 3:
            target_path = last_path
            continue_status = True
        elif choice >= recent_projects_start_idx:
            recent_idx = choice - recent_projects_start_idx
            if 0 <= recent_idx < len(recent_projects):
                target_path = recent_projects[recent_idx]
        elif choice == 1: # Single File
            start_path = self.config.get("label_input_path", ".")
            if os.path.isfile(start_path):
                start_path = os.path.dirname(start_path)
            target_path = self.file_selector.select_path(start_path=start_path, select_file=True, select_dir=False)
            if not target_path: return
        
        elif choice == 2: # Batch Folder
            start_path = self.config.get("label_input_path", ".")
            target_path = self.file_selector.select_path(start_path=start_path, select_file=False, select_dir=True)
            if not target_path: return

        # Update Config & Auto-set Output
        if not target_path:
            return

        self._update_recent_projects(target_path)
        self.config["label_input_path"] = target_path
        
        abs_input = os.path.abspath(target_path)
        parent_dir = os.path.dirname(abs_input)
        base_name = os.path.basename(abs_input)
        
        is_file_input = os.path.isfile(target_path)
        if is_file_input:
            base_name = os.path.splitext(base_name)[0]
            
        opath = os.path.join(parent_dir, f"{base_name}_AiNiee_Output")
        self.config["label_output_path"] = opath
        self.save_config()
        
        # Final check: If user manually entered a path that has a cache, ask to resume
        if choice != 3 and os.path.exists(os.path.join(opath, "cache", "AinieeCacheData.json")):
             if Confirm.ask(f"\n[yellow]Detected existing cache for this file. Resume?[/yellow]", default=True):
                 continue_status = True

        console.print(f"[dim]{i18n.get('label_input')}: {target_path}[/dim]")
        console.print(f"[dim]{i18n.get('label_output')}: {opath}[/dim]")

        # Start Logic
        self.ui = TaskUI(); Base.print = self.ui.log
        self.stop_requested = False
        
        # --- Middleware Conversion Logic ---
        original_ext = os.path.splitext(target_path)[1].lower()
        is_middleware_converted = False
        
        # Supported middleware formats that aren't natively handled well by AiNiee
        middleware_exts = [
            '.mobi', '.azw3', '.kepub', '.fb2', '.lit', '.lrf', 
            '.pdb', '.pmlz', '.rb', '.rtf', '.tcr', '.txtz', '.htmlz'
        ]
        
        if original_ext in middleware_exts:
            is_middleware_converted = True
            self.ui.log(f"[cyan]Detected {original_ext} format, calling conversion middleware...[/cyan]")
            temp_conv_dir = os.path.join(os.path.dirname(target_path), "temp_conv")
            os.makedirs(temp_conv_dir, exist_ok=True)
            
            # Construct the command for the conversion tool
            # -f for file mode, -m 1 for EPUB output
            conv_script = os.path.join(PROJECT_ROOT, "Tools", "批量电子书整合.py")
            cmd = f'uv run python "{conv_script}" -f "{target_path}" -m 1 -o "{temp_conv_dir}"'
            
            try:
                import subprocess
                # Run conversion silently
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    # Find the generated epub in the temp_conv_dir
                    epubs = [f for f in os.listdir(temp_conv_dir) if f.endswith(".epub")]
                    if epubs:
                        new_path = os.path.join(temp_conv_dir, epubs[0])
                        self.ui.log(f"[green]Conversion successful: {os.path.basename(new_path)}[/green]")
                        target_path = new_path # Swap path to the new epub
                    else:
                        raise Exception("Conversion script finished but no EPUB found.")
                else:
                    self.ui.log(f"[red]Conversion failed (Code {result.returncode}): {result.stderr}[/red]")
                    raise Exception("Conversion failed")
            except Exception as e:
                self.ui.log(f"[red]Middleware Error: {e}[/red]")
                Prompt.ask("Press Enter to abort..."); return
        # --- End Middleware ---


        # Patch tqdm to avoid conflict with Rich Live
        import ModuleFolders.Service.TaskExecutor.TaskExecutor as TaskExecutorModule
        TaskExecutorModule.tqdm = lambda x, **kwargs: x
        
        # Initialize suppression flags early
        import ModuleFolders.Infrastructure.Tokener.TiktokenLoader as TiktokenLoaderModule
        import ModuleFolders.Domain.FileReader.ReaderUtil as ReaderUtilModule
        TiktokenLoaderModule._SUPPRESS_OUTPUT = True
        ReaderUtilModule._SUPPRESS_OUTPUT = True

        original_stdout, original_stderr = sys.stdout, sys.stderr
        
        # Ensure our UI console uses the REAL stdout to avoid recursion
        self.ui_console = Console(file=original_stdout)
        
        # --- NEW: Session Logger ---
        log_file = None
        if self.config.get("enable_session_logging", True):
            try:
                log_dir = os.path.join(opath, "logs")
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, f"session_{time.strftime('%Y%m%d_%H%M%S')}.log")
                log_file = open(log_path, "w", encoding="utf-8")
            except: pass

        # Redirect stdout/stderr to capture errors in UI
        class LogStream:
            def __init__(self, ui, f=None): 
                self.ui = ui
                self.f = f
            def write(self, msg): 
                if not msg: return
                
                # Strip ANSI codes for logic and file
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                clean_msg = ansi_escape.sub('', msg).strip()
                
                if self.f:
                    try:
                        self.f.write(f"[{time.strftime('%H:%M:%S')}] {clean_msg}\n")
                        self.f.flush()
                    except: pass

                if not clean_msg or msg.startswith('\r'): return 
                
                # Aggressive filtering of UI artifacts or huge text blocks
                if " --> " in clean_msg and len(clean_msg) > 100:
                    return
                
                if any(c in clean_msg for c in "╭╮╯╰─│") and len(clean_msg) > 500:
                    return

                # Handle Status Updates specially
                if clean_msg.startswith("[STATUS]"):
                    status_text = clean_msg.replace("[STATUS]", "").strip()
                    if " --> " in status_text:
                        status_text = status_text.split(" --> ")[0]
                    if len(status_text) > 80: status_text = status_text[:77] + "..."
                    self.ui.progress.update(self.ui.task_id, action=status_text)
                    return

                if clean_msg: self.ui.log(msg) # Pass original msg with ANSI to log
            def flush(self): pass
        
        sys.stdout = sys.stderr = LogStream(self.ui, log_file)

        try:
            self.ui.log(f"{i18n.get('msg_task_started')}")
            # Ensure FileReader knows how to handle single file if needed
            # FileReader.read_files usually takes a path and DirectoryReader handles dir/file differentiation
            cache_project = self.file_reader.read_files(self.config.get("translation_project", "AutoType"), target_path, self.config.get("exclude_rule_str", ""))
            
            if not cache_project:
                self.ui.log("[red]No files loaded.[/red]"); raise Exception("Load failed")
                
            self.cache_manager.load_from_project(cache_project)
            total_items = self.cache_manager.get_item_count()
            untranslated = self.cache_manager.get_item_count_by_status(TranslationStatus.UNTRANSLATED)
            translated = self.cache_manager.get_item_count_by_status(TranslationStatus.TRANSLATED)
            
            self.ui.log(f"Loaded {total_items} items. ({translated} translated, {untranslated} remaining)")
            
            # Check if everything is already done
            already_done = False
            if task_mode == TaskType.TRANSLATION and untranslated == 0:
                already_done = True
            elif task_mode == TaskType.POLISH and translated == 0: # Actually check polished status
                # Simple check for now
                if self.cache_manager.get_item_count_by_status(TranslationStatus.POLISHED) == total_items:
                    already_done = True

            if already_done:
                self.ui.log("[bold green]All items already processed. Triggering export...[/bold green]")
                # Manually trigger export and finish
                try:
                    # Initialize config for outputer
                    self.task_executor.config.initialize()
                    cfg = self.task_executor.config
                    output_config = {
                        "translated_suffix": cfg.output_filename_suffix,
                        "bilingual_suffix": "_bilingual",
                        "bilingual_order": cfg.bilingual_text_order 
                    }
                    self.file_outputer.output_translated_content(
                        self.cache_manager.project, opath, target_path, output_config
                    )
                    self.ui.log(f"[green]Export completed successfully.[/green]")
                    # Force success/finished events for finally block
                    # We define success/finished later, so we need to be careful.
                    # Better: let the loop below handle it if we set a flag
                except Exception as ex:
                    self.ui.log(f"[red]Export failed: {ex}[/red]")
        except Exception as e:
            if log_file: log_file.close()
            sys.stdout, sys.stderr = original_stdout, original_stderr
            Base.print = self.original_print; console.print(f"[red]Error: {e}[/red]"); Prompt.ask("Press Enter..."); return
        
        self.task_running = True; finished = threading.Event(); success = threading.Event()
        
        # If already done, set events immediately
        if 'already_done' in locals() and already_done:
            success.set()
            finished.set()
        
        def on_complete(e, d): 
            self.ui.log(f"[bold green]{i18n.get('msg_task_completed')}[/bold green]")
            success.set(); finished.set()
        def on_stop(e, d): self.ui.log(f"[bold yellow]{i18n.get('msg_task_stopped')}[/bold yellow]"); finished.set()
        
        from ModuleFolders.Base.EventManager import EventManager
        EventManager.get_singleton().subscribe(Base.EVENT.TASK_COMPLETED, on_complete)
        EventManager.get_singleton().subscribe(Base.EVENT.TASK_STOP_DONE, on_stop)
        EventManager.get_singleton().subscribe(Base.EVENT.TASK_UPDATE, self.ui.update_progress)
        
        # Track last data for report
        last_task_data = {"line": translated if 'translated' in locals() else 0, "token": 0, "time": 0}
        def track_last_data(e, d):
            nonlocal last_task_data
            last_task_data = d
        EventManager.get_singleton().subscribe(Base.EVENT.TASK_UPDATE, track_last_data)

        try:
            if not finished.is_set(): # Only enter Live if not already done
                with Live(self.ui.layout, console=self.ui_console, refresh_per_second=10, screen=True, transient=False) as live:
                    # Thorough stabilization using Layout Shake instead of physical resizing
                    # This forces Rich to recalculate sizes internally multiple times
                    for _ in range(10):
                        # Toggle ratio slightly to force layout recalculation
                        self.ui.layout["upper"].ratio = 3 if _ % 2 == 0 else 4
                        live.refresh()
                        time.sleep(0.4)
                    
                    # Final restoration and refresh
                    self.ui.layout["upper"].ratio = 4
                    live.refresh()
                    
                    # Start the task AFTER Live is initialized and thoroughly refreshed
                    EventManager.get_singleton().emit(
                        Base.EVENT.TASK_START, 
                        {
                            "continue_status": continue_status, 
                            "current_mode": task_mode,
                            "session_input_path": target_path,
                            "session_output_path": opath
                        }
                    )
                    
                    while not finished.is_set(): 
                        time.sleep(0.5)
        except KeyboardInterrupt: self.signal_handler(None, None)
        except Exception as e:
            self.ui.log(f"[red]Critical Error in loop: {e}[/red]")
        finally:
            if log_file: log_file.close()
            sys.stdout, sys.stderr = original_stdout, original_stderr
            self.task_running = False; Base.print = self.original_print
            EventManager.get_singleton().unsubscribe(Base.EVENT.TASK_COMPLETED, on_complete)
            EventManager.get_singleton().unsubscribe(Base.EVENT.TASK_STOP_DONE, on_stop)
            EventManager.get_singleton().unsubscribe(Base.EVENT.TASK_UPDATE, self.ui.update_progress)
            EventManager.get_singleton().unsubscribe(Base.EVENT.TASK_UPDATE, track_last_data)
            
            # --- NEW: Summary Report and Notification ---
            if success.is_set():
                # Notification
                if self.config.get("enable_task_notification", True):
                    try:
                        title = i18n.get("msg_notification_title")
                        body = i18n.get("msg_notification_body").format(base_name)
                        if sys.platform == "win32":
                            import winsound
                            winsound.MessageBeep()
                            # Use PowerShell for native toast without dependencies
                            ps_cmd = f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $notify = New-Object System.Windows.Forms.NotifyIcon; $notify.Icon = [System.Drawing.SystemIcons]::Information; $notify.Visible = $true; $notify.ShowBalloonTip(5000, \\"{title}\\", \\"{body}\\", [System.Windows.Forms.ToolTipIcon]::Info);"'
                            import subprocess
                            subprocess.run(ps_cmd, shell=True)
                        else:
                            print("\a") # ASCII Bell
                    except: pass
                
                # Report Panel
                lines = last_task_data.get("line", 0)
                tokens = last_task_data.get("token", 0)
                duration = last_task_data.get("time", 1)
                reqs = last_task_data.get("total_requests", 0)
                errs = last_task_data.get("error_requests", 0)
                
                report_table = Table(show_header=False, box=None, padding=(0, 2))
                report_table.add_row(f"[cyan]{i18n.get('label_report_total_lines')}:[/]", f"[bold]{lines}[/]")
                report_table.add_row(f"[cyan]{i18n.get('label_report_total_tokens')}:[/]", f"[bold]{tokens}[/]")
                report_table.add_row(f"[cyan]{i18n.get('label_report_total_time')}:[/]", f"[bold]{duration:.1f}s[/]")
                report_table.add_row(f"[cyan]{i18n.get('label_report_efficiency')}:[/]", f"[bold]{lines/(duration/60):.1f} L/m | {tokens/(duration/60):.1f} T/m[/]")
                success_rate = ((reqs - errs) / reqs * 100) if reqs > 0 else 100
                report_table.add_row(f"[cyan]{i18n.get('label_report_success_rate')}:[/]", f"[bold]{success_rate:.1f}%[/]")
                
                console.print("\n")
                console.print(Panel(report_table, title=f"[bold green]✓ {i18n.get('msg_task_report_title')}[/bold green]", expand=False))
            # --- End Report ---
            
            # --- Post-Translation Reverse Conversion ---
            if success.is_set() and is_middleware_converted and self.config.get("enable_auto_restore_ebook", False):
                console.print(f"\n[cyan]Auto-restoring to {original_ext}...[/cyan]")
                # 1. Find the translated EPUB in the output directory
                output_dir = self.config.get("label_output_path")
                if output_dir and os.path.isdir(output_dir):
                    translated_epubs = [f for f in os.listdir(output_dir) if f.endswith(".epub")]
                    if translated_epubs:
                        translated_epub_path = os.path.join(output_dir, translated_epubs[0])
                        
                        # 2. Get format index from map (1:epub, 4:mobi, 5:azw3, etc)
                        format_map_inv = {
                            'epub': '1', 'mobi': '4', 'azw3': '5',
                            'kepub': '8', 'fb2': '9', 'lit': '10', 'lrf': '11',
                            'pdb': '12', 'pmlz': '13', 'rb': '14', 'rtf': '15',
                            'tcr': '16', 'txtz': '17', 'htmlz': '18'
                        }
                        fmt_idx = format_map_inv.get(original_ext.lstrip('.'))
                        
                        if fmt_idx:
                            conv_script = os.path.join(PROJECT_ROOT, "Tools", "批量电子书整合.py")
                            cmd = f'uv run python "{conv_script}" -f "{translated_epub_path}" -m {fmt_idx} -o "{output_dir}"'
                            
                            try:
                                import subprocess
                                console.print(f"[dim]Running: {cmd}[/dim]")
                                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                if res.returncode == 0:
                                    console.print(f"[green]Successfully restored to {original_ext}[/green]")
                                else:
                                    console.print(f"[red]Restore failed: {res.stderr}[/red]")
                            except Exception as e:
                                console.print(f"[red]Restore error: {e}[/red]")
                
                # 3. Clean up the temp_conv directory if middleware was used
                if is_middleware_converted:
                    try:
                        import shutil
                        temp_dir = os.path.join(os.path.dirname(abs_input), "temp_conv")
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                            console.print(f"[dim]Cleaned up temporary conversion files.[/dim]")
                    except Exception as e:
                        console.print(f"[dim]Note: Could not clean up temp files: {e}[/dim]")
            # --- End Post-Translation ---

            if len(unique_logs) > 5:
                console.print("...")
                for log in unique_logs[-5:]:
                    if "ERROR" not in log: # Don't print twice
                        console.print(log)
        Prompt.ask("\nTask ended. Press Enter...")

    def run_export_only(self):
        # 1. Select Target (similar to run_task but for export)
        last_path = self.config.get("label_input_path")
        can_resume = last_path and os.path.exists(last_path)
        
        console.clear()
        menu_text = f"1. {i18n.get('mode_single_file')}\n2. {i18n.get('mode_batch_folder')}"
        if can_resume:
            short_path = last_path if len(last_path) < 40 else "..." + last_path[-37:]
            menu_text += f"\n3. {i18n.get('mode_resume').format(short_path)}"
        
        console.print(Panel(menu_text, title=f"[bold]{i18n.get('menu_export_only')}[/bold]", expand=False))
        
        choices = ["0", "1", "2"]
        if can_resume: choices.append("3")
        choice = IntPrompt.ask(f"\n{i18n.get('prompt_select').strip().rstrip(':').rstrip('：')}", choices=choices, show_choices=False)
        
        if choice == 0: return
        
        target_path = last_path if choice == 3 else ""
        if not target_path:
            is_file_mode = choice == 1
            start_path = self.config.get("label_input_path", ".")
            if is_file_mode and os.path.isfile(start_path):
                start_path = os.path.dirname(start_path)

            target_path = self.file_selector.select_path(
                start_path=start_path,
                select_file=is_file_mode,
                select_dir=not is_file_mode
            )
            if not target_path: 
                return

        # 2. Setup paths
        abs_input = os.path.abspath(target_path)
        parent_dir = os.path.dirname(abs_input)
        base_name = os.path.basename(abs_input)
        if os.path.isfile(target_path):
            base_name = os.path.splitext(base_name)[0]
        opath = os.path.join(parent_dir, f"{base_name}_AiNiee_Output")
        
        # 3. Load cache
        cache_path = os.path.join(opath, "cache", "AinieeCacheData.json")
        while not os.path.exists(cache_path):
            console.print(f"\n[yellow]Cache not found at default path: {cache_path}[/yellow]")
            opath = Prompt.ask(f"Please enter the correct path to the output directory (or 'q' to quit)").strip('"').strip("'")
            if opath.lower() == 'q':
                return
            cache_path = os.path.join(opath, "cache", "AinieeCacheData.json")

        try:
            with console.status(f"[cyan]{i18n.get('msg_export_started')}[/cyan]"):
                project = CacheManager.read_from_file(cache_path)
                
                # Setup output config
                self.task_executor.config.initialize()
                cfg = self.task_executor.config
                output_config = {
                    "translated_suffix": cfg.output_filename_suffix,
                    "bilingual_suffix": "_bilingual",
                    "bilingual_order": cfg.bilingual_text_order 
                }
                
                self.file_outputer.output_translated_content(
                    project, opath, target_path, output_config
                )
            console.print(f"\n[green]✓ {i18n.get('msg_export_completed')}[/green]")
            console.print(f"[dim]Output: {opath}[/dim]")
        except Exception as e:
            console.print(f"[red]Export Error: {e}[/red]")
            
        Prompt.ask("\nPress Enter...")

def main():
    cli = CLIMenu(); cli.main_menu()
if __name__ == "__main__":
    main()

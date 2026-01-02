import os
import sys
import shutil
import zipfile
import requests
import time
import subprocess
import rapidjson as json
from ModuleFolders.Base.Base import Base

class UpdateManager(Base):
    GITHUB_REPO = "ShadowLoveElysia/AiNiee-CLI"
    UPDATE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    DOWNLOAD_URL = f"https://github.com/ShadowLoveElysia/AiNiee-CLI/archive/refs/heads/main.zip"

    def __init__(self, i18n_loader):
        super().__init__()
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.i18n = i18n_loader
        self._msgs = {
            "zh_CN": {
                "checking": "正在检查更新...",
                "no_update": "当前已是最新版本。",
                "downloading": "正在下载最新代码包",
                "extracting": "正在解压更新内容",
                "applying": "正在覆盖安装更新",
                "complete": "更新已完成，正在重启脚本..."
            },
            "ja": {
                "checking": "アップデートを確認中...",
                "no_update": "現在は最新バージョンです。",
                "downloading": "最新のパッケージをダウンロード中",
                "extracting": "アップデート内容を展開中",
                "applying": "アップデートを適用中",
                "complete": "アップデートが完了しました。スクリプトを再起動しています..."
            },
            "en": {
                "checking": "Checking for updates...",
                "no_update": "You are already on the latest version.",
                "downloading": "Downloading latest update package",
                "extracting": "Extracting update content",
                "applying": "Applying update",
                "complete": "Update complete, restarting script..."
            }
        }

    def get_msg(self, key):
        lang = getattr(self.i18n, 'lang', 'en')
        lang_data = self._msgs.get(lang, self._msgs["en"])
        return lang_data.get(key, self._msgs["en"][key])

    def get_local_version(self):
        """从 version.json 读取本地版本号"""
        try:
            v_path = os.path.join(self.project_root, "Resource", "Version", "version.json")
            if os.path.exists(v_path):
                with open(v_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    v_str = data.get("version", "0.0.0")
                    if 'V' in v_str:
                        return v_str.split('V')[-1].strip()
                    return v_str
        except: pass
        return "0.0.0"

    def check_update(self, silent=False):
        """检查更新，返回 (是否有更新, 最新版本号)"""
        try:
            if not silent:
                self.print(f"[cyan]{self.get_msg('checking')}[/cyan]")
            
            headers = {"User-Agent": "AiNiee-CLI-Updater"}
            response = requests.get(self.UPDATE_URL, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_v = data.get("tag_name", "0.0.0").replace('v', '').replace('V', '').strip()
                local_v = self.get_local_version()
                
                if latest_v != local_v:
                    return True, latest_v
            
            return False, self.get_local_version()
        except Exception as e:
            if not silent:
                self.error(f"Check update failed: {e}")
            return False, None

    def start_update(self, force=False):
        """开始下载并更新"""
        has_update, latest_v = self.check_update(silent=False)
        
        if not has_update and not force:
            self.print(f"[green]{self.get_msg('no_update')}[/green]")
            time.sleep(1.5)
            return

        temp_zip = os.path.join(self.project_root, "update_temp.zip")
        temp_dir = os.path.join(self.project_root, "update_temp_extract")

        try:
            self.print(f"[cyan]{self.get_msg('downloading')}...[/cyan]")
            response = requests.get(self.DOWNLOAD_URL, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(temp_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            
            self.print(f"[cyan]{self.get_msg('extracting')}...[/cyan]")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if not extracted_subdirs: raise Exception("Failed to find extracted content.")
            
            src_dir = os.path.join(temp_dir, extracted_subdirs[0])
            self.print(f"[cyan]{self.get_msg('applying')}...[/cyan]")
            
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(self.project_root, item)
                if item in [".env", "output", "Resource/profiles", ".git", "__pycache__", ".venv"]:
                    continue
                if os.path.isdir(s):
                    if os.path.exists(d):
                        if item in ["ModuleFolders", "PluginScripts", "I18N", "Resource"]:
                            if item == "Resource": self._merge_resource_dir(s, d)
                            else:
                                shutil.rmtree(d)
                                shutil.copytree(s, d)
                        else: self._merge_dirs(s, d)
                    else: shutil.copytree(s, d)
                else: shutil.copy2(s, d)

            self.print(f"[bold green]{self.get_msg('complete')}[/bold green]")
            time.sleep(2)
            if os.path.exists(temp_zip): os.remove(temp_zip)
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            self._restart_script()
        except Exception as e:
            self.error(f"Update failed: {e}")
            return False

    def _merge_dirs(self, src, dst):
        for item in os.listdir(src):
            s, d = os.path.join(src, item), os.path.join(dst, item)
            if os.path.isdir(s):
                if not os.path.exists(d): os.makedirs(d)
                self._merge_dirs(s, d)
            else: shutil.copy2(s, d)

    def _merge_resource_dir(self, src, dst):
        for item in os.listdir(src):
            s, d = os.path.join(src, item), os.path.join(dst, item)
            if item in ["config.json", "profiles"]: continue
            if os.path.isdir(s):
                if not os.path.exists(d): os.makedirs(d)
                self._merge_dirs(s, d)
            else: shutil.copy2(s, d)

    def _restart_script(self):
        executable, script_path = sys.executable, os.path.join(self.project_root, "ainiee_cli.py")
        if sys.platform == "win32":
            launch_bat = os.path.join(self.project_root, "Launch.bat")
            if os.path.exists(launch_bat): subprocess.Popen(["cmd.exe", "/c", launch_bat], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else: subprocess.Popen([executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            launch_sh = os.path.join(self.project_root, "Launch.sh")
            if os.path.exists(launch_sh): subprocess.Popen(["bash", launch_sh])
            else: subprocess.Popen([executable, script_path])
        sys.exit(0)

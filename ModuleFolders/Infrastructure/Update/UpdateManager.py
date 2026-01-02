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
    RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/Resource/Version/version.json"
    
    # GitHub 代理列表，首位为空表示直接连接
    GITHUB_PROXIES = [
        "", 
        "https://ghproxy.net/",
        "https://mirror.ghproxy.com/",
        "https://github.moeyy.xyz/",
        "https://gh-proxy.com/"
    ]

    def __init__(self, i18n_loader):
        super().__init__()
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.i18n = i18n_loader
        self._msgs = {
            "zh_CN": {
                "checking": "正在检查更新...",
                "no_update": "当前已是最新版本。",
                "downloading": "正在下载最新代码包",
                "downloading_proxy": "正在通过代理下载",
                "extracting": "正在解压更新内容",
                "applying": "正在覆盖安装更新",
                "complete": "更新已完成，正在重启脚本...",
                "fail_all": "所有下载尝试均已失败。",
                "retry_query": "是否继续重试自动下载？(有的时候多试几次就好了) [y/n]: ",
                "manual_guide": "\n[bold yellow]已进入手动更新模式：[/bold yellow]\n1. 请手动下载源码压缩包 (ZIP 格式)\n2. 在项目根目录下创建 [cyan]Update[/cyan] 文件夹\n3. 将下载好的 ZIP 文件放入该文件夹中\n4. 完成后在此处按 [green]Enter (回车键)[/green] 继续...",
                "no_zip_found": "未在 Update 文件夹中找到任何 ZIP 压缩包，请检查后重试。",
                "version_check": "正在检查压缩包版本...",
                "manual_already_latest": "压缩包内的版本与当前一致，无需更新。"
            },
            "ja": {
                "checking": "アップデートを確認中...",
                "no_update": "現在は最新バージョンです。",
                "downloading": "最新のパッケージをダウンロード中",
                "downloading_proxy": "プロキシ経由でダウンロード中",
                "extracting": "アップデート内容を展開中",
                "applying": "アップデートを適用中",
                "complete": "アップデートが完了しました。スクリプトを再起動しています...",
                "fail_all": "すべてのダウンロード試行が失敗しました。",
                "retry_query": "自動ダウンロードを再試行しますか？ [y/n]: ",
                "manual_guide": "\n[bold yellow]手動アップデートモード：[/bold yellow]\n1. ソースコードのZIPファイルをダウンロードしてください\n2. プロジェクト直下に [cyan]Update[/cyan] フォルダを作成してください\n3. ZIPファイルをそのフォルダに配置してください\n4. 配置後、[green]Enter[/green] キーを押してください...",
                "no_zip_found": "Update フォルダに ZIP ファイルが見つかりません。",
                "version_check": "ZIP内のバージョンを確認中...",
                "manual_already_latest": "ZIP内のバージョンは現在と同じです。"
            },
            "en": {
                "checking": "Checking for updates...",
                "no_update": "You are already on the latest version.",
                "downloading": "Downloading latest update package",
                "downloading_proxy": "Downloading via proxy",
                "extracting": "Extracting update content",
                "applying": "Applying update",
                "complete": "Update complete, restarting script...",
                "fail_all": "All download attempts failed.",
                "retry_query": "Would you like to retry automatic download? [y/n]: ",
                "manual_guide": "\n[bold yellow]Manual Update Mode:[/bold yellow]\n1. Download the source ZIP file manually\n2. Create an [cyan]Update[/cyan] folder in the project root\n3. Put the ZIP file into that folder\n4. Press [green]Enter[/green] here to continue...",
                "no_zip_found": "No ZIP file found in the Update folder.",
                "version_check": "Checking version in ZIP...",
                "manual_already_latest": "The version in the ZIP is the same as the current one."
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
        if not silent:
            self.print(f"[cyan]{self.get_msg('checking')}[/cyan]")
            
        headers = {"User-Agent": "AiNiee-CLI-Updater"}
        local_v = self.get_local_version()
        
        # 1. 尝试直接通过 GitHub API 获取
        try:
            response = requests.get(self.UPDATE_URL, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_v = data.get("tag_name", "0.0.0").replace('v', '').replace('V', '').strip()
                if latest_v != local_v:
                    return True, latest_v
                return False, local_v
        except:
            pass

        # 2. 如果 API 失败，尝试通过代理读取远程 version.json
        for proxy in self.GITHUB_PROXIES:
            if not proxy: continue
            try:
                v_url = f"{proxy.replace('github.com', 'raw.githubusercontent.com')}{self.GITHUB_REPO}/main/Resource/Version/version.json" if 'ghproxy' in proxy else f"{proxy}{self.RAW_VERSION_URL}"
                response = requests.get(v_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    v_str = data.get("version", "0.0.0")
                    latest_v = v_str.split('V')[-1].strip() if 'V' in v_str else v_str
                    if latest_v != local_v:
                        return True, latest_v
                    return False, local_v
            except:
                continue
        
        return False, local_v

    def start_update(self, force=False):
        """开始下载并更新"""
        has_update, latest_v = self.check_update(silent=False)
        
        if not has_update and not force:
            self.print(f"[green]{self.get_msg('no_update')}[/green]")
            time.sleep(1.5)
            return

        temp_zip = os.path.join(self.project_root, "update_temp.zip")
        
        while True:
            success = False
            for proxy in self.GITHUB_PROXIES:
                try:
                    download_url = f"{proxy}{self.DOWNLOAD_URL}" if proxy else self.DOWNLOAD_URL
                    msg_key = 'downloading_proxy' if proxy else 'downloading'
                    proxy_name = proxy.split('/')[2] if proxy else "Direct"
                    self.print(f"[cyan]{self.get_msg(msg_key)} ({proxy_name})...[/cyan]")
                    
                    response = requests.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(temp_zip, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk: f.write(chunk)
                    
                    success = True
                    break
                except Exception:
                    continue

            if success:
                self._apply_update_from_zip(temp_zip)
                return True
            else:
                self.print(f"[red]{self.get_msg('fail_all')}[/red]")
                try:
                    choice = input(self.get_msg('retry_query')).strip().lower()
                except (EOFError, KeyboardInterrupt):
                    choice = 'n'
                if choice != 'y':
                    break
        
        self.start_manual_update()

    def start_manual_update(self):
        """手动更新逻辑"""
        update_dir = os.path.join(self.project_root, "Update")
        if not os.path.exists(update_dir):
            os.makedirs(update_dir)
            
        self.print(self.get_msg('manual_guide'))
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            return False
        
        zips = [f for f in os.listdir(update_dir) if f.lower().endswith('.zip')]
        if not zips:
            self.error(self.get_msg('no_zip_found'))
            return False
            
        zips.sort(key=lambda x: os.path.getmtime(os.path.join(update_dir, x)), reverse=True)
        target_zip = os.path.join(update_dir, zips[0])
        
        self.print(f"[cyan]{self.get_msg('version_check')}[/cyan]")
        try:
            with zipfile.ZipFile(target_zip, 'r') as z:
                v_content = None
                for name in z.namelist():
                    if name.endswith("Resource/Version/version.json"):
                        v_content = z.read(name)
                        break
                
                if v_content:
                    data = json.loads(v_content)
                    v_str = data.get("version", "0.0.0")
                    zip_v = v_str.split('V')[-1].strip() if 'V' in v_str else v_str
                    local_v = self.get_local_version()
                    
                    if zip_v == local_v:
                        self.print(f"[yellow]{self.get_msg('manual_already_latest')}[/yellow]")
                        time.sleep(2)
                        return False
        except Exception:
            pass # 即使检查失败也尝试更新
            
        return self._apply_update_from_zip(target_zip)

    def _apply_update_from_zip(self, zip_path):
        """通用的解压并应用更新逻辑"""
        temp_dir = os.path.join(self.project_root, "update_temp_extract")
        try:
            self.print(f"[cyan]{self.get_msg('extracting')}...[/cyan]")
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if not extracted_subdirs: raise Exception("Failed to find extracted content.")
            
            src_dir = os.path.join(temp_dir, extracted_subdirs[0])
            self.print(f"[cyan]{self.get_msg('applying')}...[/cyan]")
            
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(self.project_root, item)
                if item in [".env", "output", "Resource/profiles", ".git", "__pycache__", ".venv", "Update"]:
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
            if "update_temp.zip" in zip_path and os.path.exists(zip_path): 
                os.remove(zip_path)
            if os.path.exists(temp_dir): 
                shutil.rmtree(temp_dir)
            self._restart_script()
            return True
        except Exception as e:
            self.error(f"Update application failed: {e}")
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

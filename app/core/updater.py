"""
Update Manager for VaultKeeper.
Checks GitHub Releases for new versions.
"""

import json
import urllib.request
import threading
from PySide6.QtCore import QObject, Signal
from app import __version__
from app.core.config import GITHUB_REPO

class UpdateManager(QObject):
    """
    Manages update checks against GitHub Releases.
    """
    update_available = Signal(str, str) # version, download_url
    no_update = Signal()
    check_failed = Signal(str) # error message
    download_progress = Signal(int) # percentage
    download_complete = Signal(str) # file_path
    download_error = Signal(str)
    install_complete = Signal()

    def __init__(self):
        super().__init__()
        self.current_version = __version__

    def check_for_updates(self):
        """Starts the update check in a separate thread."""
        thread = threading.Thread(target=self._check_worker)
        thread.daemon = True
        thread.start()

    def _check_worker(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "VaultKeeper-App")
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    self.check_failed.emit(f"GitHub API Error: {response.status}")
                    return
                    
                data = json.loads(response.read().decode())
                
                latest_tag = data.get("tag_name", "").lstrip("v")
                
                # Determine download URL (prefer Setup .exe, fallback to zip)
                download_url = data.get("zipball_url", "")
                assets = data.get("assets", [])
                
                setup_exe = None
                app_image = None
                portable_zip = None
                
                for asset in assets:
                    name = asset["name"].lower()
                    url = asset["browser_download_url"]
                    if name.endswith(".exe") and "setup" in name:
                        setup_exe = url
                    elif name.endswith(".appimage"):
                        app_image = url
                    elif name.endswith(".zip") and "windows" in name:
                        portable_zip = url
                
                # Platform specific preference
                import sys
                if sys.platform == "win32":
                    download_url = setup_exe or portable_zip or download_url
                elif sys.platform == "linux":
                    download_url = app_image or download_url
                
                if not latest_tag:
                    self.check_failed.emit("Could not parse version tag.")
                    return

                if self._is_newer(latest_tag):
                    self.update_available.emit(latest_tag, download_url)
                else:
                    self.no_update.emit()
                    
        except Exception as e:
            self.check_failed.emit(str(e))

    def download_update(self, url):
        """Downloads the update to a temporary file."""
        thread = threading.Thread(target=self._download_worker, args=(url,))
        thread.daemon = True
        thread.start()

    def _download_worker(self, url):
        try:
            import tempfile
            import os
            from urllib.parse import urlparse
            
            # Determine extension from URL
            path = urlparse(url).path
            ext = os.path.splitext(path)[1]
            if not ext:
                if "appimage" in url.lower():
                    ext = ".AppImage"
                else:
                    ext = ".zip"
            
            # Create temp file with correct extension
            fd, path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            
            def report(block_num, block_size, total_size):
                if total_size > 0:
                    percent = int((block_num * block_size * 100) / total_size)
                    self.download_progress.emit(percent)

            urllib.request.urlretrieve(url, path, report)
            self.download_complete.emit(path)
            
        except Exception as e:
            self.download_error.emit(str(e))

    def install_update(self, file_path: str, target_dir: str):
        """Installs the update (runs EXE/AppImage or extracts ZIP)."""
        thread = threading.Thread(target=self._install_worker, args=(file_path, target_dir))
        thread.daemon = True
        thread.start()

    def _install_worker(self, file_path, target_dir):
        try:
            import os
            import subprocess
            import sys
            
            if file_path.lower().endswith(".exe"):
                # Run the installer and exit
                try:
                    # Run detached
                    subprocess.Popen([file_path], shell=True)
                    self.install_complete.emit()
                except Exception as e:
                    self.download_error.emit(f"Failed to launch installer: {e}")
            
            elif file_path.lower().endswith(".appimage"):
                # Linux AppImage
                try:
                    # Make executable
                    os.chmod(file_path, 0o755)
                    # Run detached
                    subprocess.Popen([file_path])
                    self.install_complete.emit()
                except Exception as e:
                    self.download_error.emit(f"Failed to launch AppImage: {e}")
            
            else:
                # Fallback to ZIP extraction (legacy behavior)
                import zipfile
                import shutil
                from pathlib import Path
                
                extract_dir = os.path.join(os.path.dirname(file_path), "update_extracted")
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find the root folder inside the zip
                source_dir = extract_dir
                subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
                if len(subdirs) == 1:
                    source_dir = os.path.join(extract_dir, subdirs[0])
                    
                # Copy files using copytree
                shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                
                # Cleanup
                try:
                    os.remove(file_path)
                    shutil.rmtree(extract_dir)
                except:
                    pass
                    
                self.install_complete.emit()
        except Exception as e:
            self.download_error.emit(f"Install Error: {e}")

    def _is_newer(self, latest_ver: str) -> bool:
        """
        Compare semver strings.
        Returns True if latest_ver > current_version.
        """
        try:
            v1_parts = [int(x) for x in latest_ver.split(".")]
            v2_parts = [int(x) for x in self.current_version.split(".")]
            
            # Pad with zeros if lengths differ
            while len(v1_parts) < len(v2_parts): v1_parts.append(0)
            while len(v2_parts) < len(v1_parts): v2_parts.append(0)
            
            return v1_parts > v2_parts
        except ValueError:
            # Fallback for non-semver tags
            return latest_tag != self.current_version

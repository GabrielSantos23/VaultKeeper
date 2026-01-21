
import json

import urllib.request

import threading

from PySide6.QtCore import QObject, Signal

from app import __version__

from app.core.config import GITHUB_REPO

class UpdateManager(QObject):

    update_available = Signal(str, str)

    no_update = Signal()

    check_failed = Signal(str)

    download_progress = Signal(int)

    download_complete = Signal(str)

    download_error = Signal(str)

    install_complete = Signal()

    def __init__(self):

        super().__init__()

        self.current_version = __version__

    def check_for_updates(self):

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

        thread = threading.Thread(target=self._download_worker, args=(url,))

        thread.daemon = True

        thread.start()

    def _download_worker(self, url):

        try:

            import tempfile

            import os

            from urllib.parse import urlparse

            path = urlparse(url).path
            
            # Try to get the filename from the URL
            filename = os.path.basename(path)
            
            # If no filename or generic, fallback
            if not filename or filename.strip() == "":
                if "appimage" in url.lower():
                    filename = "update.AppImage"
                else:
                    filename = "update.zip"
            
            # Use mkdtemp to create a directory, so we can keep the original filename
            temp_dir = tempfile.mkdtemp()
            save_path = os.path.join(temp_dir, filename)

            def report(block_num, block_size, total_size):

                if total_size > 0:

                    percent = int((block_num * block_size * 100) / total_size)

                    self.download_progress.emit(percent)

            urllib.request.urlretrieve(url, save_path, report)

            self.download_complete.emit(save_path)

        except Exception as e:

            self.download_error.emit(str(e))

    def install_update(self, file_path: str, target_dir: str):

        thread = threading.Thread(target=self._install_worker, args=(file_path, target_dir))

        thread.daemon = True

        thread.start()

    def _install_worker(self, file_path, target_dir):

        try:

            import os

            import subprocess

            import sys

            if file_path.lower().endswith(".exe"):

                try:

                    subprocess.Popen([file_path], shell=True)

                    self.install_complete.emit()

                except Exception as e:

                    self.download_error.emit(f"Failed to launch installer: {e}")

            elif file_path.lower().endswith(".appimage"):
                try:
                    import shutil
                    os.chmod(file_path, 0o755)

                    # Check if running as AppImage
                    current_appimage = os.environ.get("APPIMAGE")
                    if current_appimage and os.path.exists(current_appimage):
                        # Determine installation location
                        install_dir = os.path.dirname(current_appimage)
                        new_filename = os.path.basename(file_path)
                        target_path = os.path.join(install_dir, new_filename)
                        
                        # Move new version to the installation directory
                        # If target exists (e.g. reinstalling same version?), remove it first
                        if os.path.exists(target_path):
                            try:
                                os.remove(target_path)
                            except:
                                pass
                        
                        shutil.move(file_path, target_path)
                        os.chmod(target_path, 0o755)
                        
                        # Remove old version if filename is different and it's not the same file
                        if current_appimage != target_path:
                            try:
                                os.remove(current_appimage)
                            except:
                                # If remove fails/locked, rename to .old to hide it 
                                # (AppImageLauncher might handle this transition)
                                try:
                                    os.rename(current_appimage, current_appimage + ".old")
                                except:
                                    pass

                        # Launch the new AppImage
                        subprocess.Popen([target_path])
                    else:
                        subprocess.Popen([file_path])

                    self.install_complete.emit()

                except Exception as e:
                    self.download_error.emit(f"Failed to install AppImage: {e}")

            else:

                import zipfile

                import shutil

                from pathlib import Path

                extract_dir = os.path.join(os.path.dirname(file_path), "update_extracted")

                with zipfile.ZipFile(file_path, 'r') as zip_ref:

                    zip_ref.extractall(extract_dir)

                source_dir = extract_dir

                subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]

                if len(subdirs) == 1:

                    source_dir = os.path.join(extract_dir, subdirs[0])

                shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

                try:

                    os.remove(file_path)

                    shutil.rmtree(extract_dir)

                except:

                    pass

                self.install_complete.emit()

        except Exception as e:

            self.download_error.emit(f"Install Error: {e}")

    def _is_newer(self, latest_ver: str) -> bool:

        try:

            v1_parts = [int(x) for x in latest_ver.split(".")]

            v2_parts = [int(x) for x in self.current_version.split(".")]

            while len(v1_parts) < len(v2_parts): v1_parts.append(0)

            while len(v2_parts) < len(v1_parts): v2_parts.append(0)

            return v1_parts > v2_parts

        except ValueError:

            return latest_tag != self.current_version

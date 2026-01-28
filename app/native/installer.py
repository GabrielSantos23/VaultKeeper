
import sys

import os

import json

import platform

import subprocess

import shutil

from pathlib import Path

from typing import Optional, List, Tuple

FIREFOX_EXTENSION_ID = "vaultkeeper@example.com"

CHROME_EXTENSION_ID = "bklgfpmbbpfboanbdjakcgmlldhmlkco"

HOST_NAME = "com.vaultkeeper.host"

HOST_DESCRIPTION = "VaultKeeper Native Messaging Host"

def get_chrome_extension_id() -> Optional[str]:

    if CHROME_EXTENSION_ID:

        return CHROME_EXTENSION_ID

    project_root = Path(__file__).parent.parent.parent

    id_file = project_root / ".chrome_extension_id"

    if id_file.exists():

        ext_id = id_file.read_text().strip()

        if ext_id and len(ext_id) == 32:

            return ext_id

    env_id = os.environ.get("VAULTKEEPER_CHROME_EXTENSION_ID")

    if env_id and len(env_id) == 32:

        return env_id

    return None

class NativeHostInstaller:

    def __init__(self):

        self.system = platform.system().lower()

        self.project_root = Path(__file__).parent.parent.parent

        self.host_script = self.project_root / "app" / "native" / "host.py"

        self.wrapper_script = self.project_root / "app" / "native" / "vaultkeeper_host.sh"

    def get_browser_paths(self) -> dict:
        home = Path.home()
        paths = {}

        if self.system == "linux":
            # Firefox & Derivatives
            firefox_paths = [
                home / ".mozilla" / "native-messaging-hosts",
                home / ".librewolf" / "native-messaging-hosts",
                home / ".waterfox" / "native-messaging-hosts",
                # Snap
                home / "snap" / "firefox" / "common" / ".mozilla" / "native-messaging-hosts",
                # Flatpak
                home / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "native-messaging-hosts",
                home / ".var" / "app" / "io.gitlab.librewolf-community" / ".librewolf" / "native-messaging-hosts",
            ]
            paths["firefox"] = firefox_paths

            # Chromium Based
            chrome_paths = [
                home / ".config" / "google-chrome" / "NativeMessagingHosts",
                home / ".var" / "app" / "com.google.Chrome" / "config" / "google-chrome" / "NativeMessagingHosts",
            ]
            paths["chrome"] = chrome_paths

            chromium_paths = [
                home / ".config" / "chromium" / "NativeMessagingHosts",
                home / "snap" / "chromium" / "common" / ".chromium" / "NativeMessagingHosts",
                home / ".var" / "app" / "org.chromium.Chromium" / "config" / "chromium" / "NativeMessagingHosts",
            ]
            paths["chromium"] = chromium_paths

            brave_paths = [
                home / ".config" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
                home / ".var" / "app" / "com.brave.Browser" / "config" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
            ]
            paths["brave"] = brave_paths

            edge_paths = [
                home / ".config" / "microsoft-edge" / "NativeMessagingHosts",
                home / ".var" / "app" / "com.microsoft.Edge" / "config" / "microsoft-edge" / "NativeMessagingHosts",
            ]
            paths["edge"] = edge_paths

            # Zen Browser (AppImage / Portable / Flatpak?)
            zen_paths = [
                home / ".zen" / "native-messaging-hosts",
                home / ".config" / "zen" / "native-messaging-hosts",
                home / ".var" / "app" / "io.github.zen_browser.zen" / ".zen" / "native-messaging-hosts"
            ]
            paths["zen"] = zen_paths

        elif self.system == "darwin":
            # MacOS paths usually standard, but prepared for list structure
            paths["firefox"] = [home / "Library" / "Application Support" / "Mozilla" / "NativeMessagingHosts"]
            paths["chrome"] = [home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"]
            # ... others can be added similarly
            paths["chromium"] = [home / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts"]
            paths["brave"] = [home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts"]
            paths["edge"] = [home / "Library" / "Application Support" / "Microsoft Edge" / "NativeMessagingHosts"]

        elif self.system == "windows":
            appdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            # Windows usually uses Registry for Chrome-based, but Filesystem for Firefox
            paths["firefox"] = [appdata / "Mozilla" / "NativeMessagingHosts"]
            paths["chrome"] = [appdata / "Google" / "Chrome" / "User Data" / "NativeMessagingHosts"]
            # ... others

        return paths

    def create_manifest(self, browser: str, chrome_extension_id: Optional[str] = None) -> dict:

        if getattr(sys, 'frozen', False):

            base_path = Path(sys.executable).parent

            if self.system == "windows":

                host_path = str(base_path / "vk_host.exe")

            else:

                host_path = str(base_path / "vk_host")

        else:

            if self.system == "windows":

                self.wrapper_bat = self.project_root / "app" / "native" / "vaultkeeper_host.bat"

                host_path = str(self.wrapper_bat)

            else:

                host_path = str(self.wrapper_script)

        manifest = {

            "name": HOST_NAME,

            "description": HOST_DESCRIPTION,

            "path": host_path,

            "type": "stdio"

        }

        firefox_based = {"firefox", "librewolf", "waterfox", "floorp", "zen", "zen_xdg"}

        if browser in firefox_based:

            manifest["allowed_extensions"] = [FIREFOX_EXTENSION_ID]

        else:

            ext_id = chrome_extension_id or get_chrome_extension_id() or CHROME_EXTENSION_ID

            manifest["allowed_origins"] = [f"chrome-extension://{ext_id}/"]

        return manifest

    def create_wrapper_script(self):

        if getattr(sys, 'frozen', False):

            return None

        if self.system == "windows":

            wrapper_path = self.project_root / "app" / "native" / "vaultkeeper_host.bat"

            content = r'''@echo off
setlocal

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Go up two directories to project root (app/native -> app -> project_root)
set "PROJECT_DIR=%SCRIPT_DIR%..\.."

REM Try venv first, then fallback to system Python
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    "%PROJECT_DIR%\.venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    "%PROJECT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%host.py"
) else (
    REM Fallback to system Python
    python "%SCRIPT_DIR%host.py"
)
'''

        else:

            wrapper_path = self.wrapper_script

            content = '''#!/bin/bash
# VaultKeeper Native Host Wrapper
# Activates virtual environment and runs the host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Try different venv locations
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    exec "$PROJECT_DIR/.venv/bin/python" "$SCRIPT_DIR/host.py"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    exec "$PROJECT_DIR/venv/bin/python" "$SCRIPT_DIR/host.py"
else
    # Fallback: system Python
    exec python3 "$SCRIPT_DIR/host.py"
fi
'''

        wrapper_path.write_text(content)

        if self.system != "windows":

            os.chmod(wrapper_path, 0o755)

        return wrapper_path

    def install_for_browser(self, browser: str, chrome_extension_id: Optional[str] = None) -> Tuple[bool, str]:
        paths_map = self.get_browser_paths()
        
        if browser not in paths_map:
            return False, f"Unknown browser: {browser}"
            
        target_paths = paths_map[browser]
        installed_paths = []
        errors = []
        
        for target_dir in target_paths:
            # Check if browser config exists (parent directory)
            # For standard ~/.config/google-chrome/NativeMessagingHosts, parent is google-chrome
            # For ~/.mozilla/native-messaging-hosts, parent is .mozilla
            
            # Snap/Flatpak paths logic remains the same: we look if the config root exists.
            
            if not target_dir.parent.exists():
                continue
                
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                manifest = self.create_manifest(browser, chrome_extension_id)
                manifest_path = target_dir / f"{HOST_NAME}.json"
                
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                    
                if self.system == "windows":
                    self._register_windows(browser, manifest_path)
                    
                installed_paths.append(str(manifest_path))
                
            except Exception as e:
                errors.append(f"{target_dir}: {e}")

        if installed_paths:
            return True, f"Installed to {len(installed_paths)} locations"
        elif errors:
             return False, f"Failed: {', '.join(errors)}"
        else:
             return False, f"{browser.title()} config not found"

    def _register_windows(self, browser: str, manifest_path: Path):

        import winreg

        firefox_based = {"firefox", "librewolf", "waterfox", "floorp", "zen"}

        if browser in firefox_based:

            key_path = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"

        else:

            key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"

        try:

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))

            winreg.CloseKey(key)

        except Exception as e:

            raise Exception(f"Failed to register in Windows registry: {e}")

    def install_all(self, chrome_extension_id: Optional[str] = None) -> List[Tuple[str, bool, str]]:

        results = []

        results = []

        if not getattr(sys, 'frozen', False):

            self.create_wrapper_script()

        if self.system != "windows":

            if self.host_script.exists():
                os.chmod(self.host_script, 0o755)

        for browser in self.get_browser_paths().keys():

            success, message = self.install_for_browser(browser, chrome_extension_id)

            results.append((browser, success, message))

        return results

    def uninstall_for_browser(self, browser: str) -> Tuple[bool, str]:
        paths_map = self.get_browser_paths()
        
        if browser not in paths_map:
            return False, f"Unknown browser: {browser}"
            
        target_paths = paths_map[browser]
        removed_count = 0
        
        for path in target_paths:
            manifest_path = path / f"{HOST_NAME}.json"
            try:
                if manifest_path.exists():
                    manifest_path.unlink()
                    removed_count += 1
            except:
                pass

        if self.system == "windows":
            self._unregister_windows(browser)

        if removed_count > 0:
            return True, f"Removed from {removed_count} locations"
        else:
            return False, "Not found"

    def _unregister_windows(self, browser: str):

        import winreg

        if browser == "firefox":

            key_path = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"

        else:

            key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"

        try:

            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)

        except WindowsError:

            pass

    def check_installation(self) -> List[Tuple[str, bool, str]]:
        results = []
        paths_map = self.get_browser_paths()

        for browser, paths in paths_map.items():
            browser_installed = False
            details = []
            
            for path in paths:
                manifest_path = path / f"{HOST_NAME}.json"
                if manifest_path.exists():
                    browser_installed = True
                    details.append(f"✓ {path}")
                # else:
                #     details.append(f"✗ {path}")
            
            if browser_installed:
                results.append((browser, True, ", ".join(details)))
            else:
                results.append((browser, False, "Not Configured"))

        return results

def main():

    import argparse

    parser = argparse.ArgumentParser(description="VaultKeeper Native Host Installer")

    parser.add_argument("action", choices=["install", "uninstall", "check"],

                       help="Action to perform")

    parser.add_argument("--browser", "-b",

                       help="Specific browser (firefox, chrome, chromium, brave)")

    parser.add_argument("--chrome-id",

                       help="Chrome extension ID for allowed_origins")

    args = parser.parse_args()

    installer = NativeHostInstaller()

    if args.action == "install":

        if args.browser:

            success, msg = installer.install_for_browser(args.browser, args.chrome_id)

            status = "✅" if success else "❌"

            print(f"{status} {args.browser}: {msg}")

        else:

            installer.create_wrapper_script()

            results = installer.install_all(args.chrome_id)

            print("🔐 VaultKeeper Native Host Installation")

            print("=" * 40)

            for browser, success, msg in results:

                status = "✅" if success else "⏭️ "

                print(f"{status} {browser.title()}: {msg}")

    elif args.action == "uninstall":

        if args.browser:

            success, msg = installer.uninstall_for_browser(args.browser)

            status = "✅" if success else "❌"

            print(f"{status} {args.browser}: {msg}")

        else:

            for browser in installer.get_browser_paths().keys():

                success, msg = installer.uninstall_for_browser(browser)

                status = "✅" if success else "⏭️ "

                print(f"{status} {browser.title()}: {msg}")

    elif args.action == "check":

        print("🔍 Checking Native Host Installation")

        print("=" * 40)

        results = installer.check_installation()

        for browser, installed, msg in results:

            status = "✅" if installed else "❌"

            print(f"{status} {browser.title()}: {msg}")

if __name__ == "__main__":

    main()

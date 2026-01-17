"""
VaultKeeper - Native Host Installer
Automatically installs the native messaging host for browser extensions.

This module can be called:
1. During app installation
2. From the app's settings UI
3. Via command line: python -m app.native.installer
"""

import sys
import os
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

# Extension IDs
FIREFOX_EXTENSION_ID = "vaultkeeper@example.com"

# Chrome Extension ID - This is a FIXED ID generated from the "key" in manifest.json
# DO NOT CHANGE THIS - it must match the key in extension/manifest.json
# The key ensures the extension always has this same ID on any computer
CHROME_EXTENSION_ID = "bklgfpmbbpfboanbdjakcgmlldhmlkco"

HOST_NAME = "com.vaultkeeper.host"
HOST_DESCRIPTION = "VaultKeeper Native Messaging Host"


def get_chrome_extension_id() -> Optional[str]:
    """Get Chrome extension ID from various sources."""
    # 1. Check if it's hardcoded
    if CHROME_EXTENSION_ID:
        return CHROME_EXTENSION_ID
    
    # 2. Check for .chrome_extension_id file in project root
    project_root = Path(__file__).parent.parent.parent
    id_file = project_root / ".chrome_extension_id"
    if id_file.exists():
        ext_id = id_file.read_text().strip()
        if ext_id and len(ext_id) == 32:
            return ext_id
    
    # 3. Check environment variable
    env_id = os.environ.get("VAULTKEEPER_CHROME_EXTENSION_ID")
    if env_id and len(env_id) == 32:
        return env_id
    
    return None


class NativeHostInstaller:
    """Handles installation of the Native Messaging Host for all browsers."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = Path(__file__).parent.parent.parent
        self.host_script = self.project_root / "app" / "native" / "host.py"
        self.wrapper_script = self.project_root / "app" / "native" / "vaultkeeper_host.sh"
        
    def get_browser_paths(self) -> dict:
        """Get native messaging host paths for each browser on current OS."""
        home = Path.home()
        
        if self.system == "linux":
            return {
                # Firefox-based browsers
                "firefox": home / ".mozilla" / "native-messaging-hosts",
                "librewolf": home / ".librewolf" / "native-messaging-hosts",
                "waterfox": home / ".waterfox" / "native-messaging-hosts",
                "floorp": home / ".floorp" / "native-messaging-hosts",
                "zen": home / ".zen" / "native-messaging-hosts",
                # Chromium-based browsers
                "chrome": home / ".config" / "google-chrome" / "NativeMessagingHosts",
                "chromium": home / ".config" / "chromium" / "NativeMessagingHosts",
                "brave": home / ".config" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
                "edge": home / ".config" / "microsoft-edge" / "NativeMessagingHosts",
                "vivaldi": home / ".config" / "vivaldi" / "NativeMessagingHosts",
                "opera": home / ".config" / "opera" / "NativeMessagingHosts",
            }
        elif self.system == "darwin":  # macOS
            return {
                # Firefox-based browsers
                "firefox": home / "Library" / "Application Support" / "Mozilla" / "NativeMessagingHosts",
                "librewolf": home / "Library" / "Application Support" / "librewolf" / "NativeMessagingHosts",
                "waterfox": home / "Library" / "Application Support" / "Waterfox" / "NativeMessagingHosts",
                # Chromium-based browsers
                "chrome": home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts",
                "chromium": home / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts",
                "brave": home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
                "edge": home / "Library" / "Application Support" / "Microsoft Edge" / "NativeMessagingHosts",
                "vivaldi": home / "Library" / "Application Support" / "Vivaldi" / "NativeMessagingHosts",
                "opera": home / "Library" / "Application Support" / "com.operasoftware.Opera" / "NativeMessagingHosts",
            }
        elif self.system == "windows":
            # Windows uses registry, but manifests can be stored anywhere
            appdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            return {
                # Firefox-based browsers (all use Mozilla path on Windows)
                "firefox": appdata / "Mozilla" / "NativeMessagingHosts",
                "librewolf": appdata / "librewolf" / "NativeMessagingHosts",
                "waterfox": appdata / "Waterfox" / "NativeMessagingHosts",
                "floorp": appdata / "Floorp" / "NativeMessagingHosts",
                "zen": appdata / "Zen Browser" / "NativeMessagingHosts",
                # Chromium-based browsers
                "chrome": appdata / "Google" / "Chrome" / "User Data" / "NativeMessagingHosts",
                "chromium": appdata / "Chromium" / "User Data" / "NativeMessagingHosts",
                "brave": appdata / "BraveSoftware" / "Brave-Browser" / "User Data" / "NativeMessagingHosts",
                "edge": appdata / "Microsoft" / "Edge" / "User Data" / "NativeMessagingHosts",
                "vivaldi": appdata / "Vivaldi" / "User Data" / "NativeMessagingHosts",
                "opera": appdata / "Opera Software" / "Opera Stable" / "NativeMessagingHosts",
            }
        else:
            return {}
    
    def create_manifest(self, browser: str, chrome_extension_id: Optional[str] = None) -> dict:
        """Create the native messaging host manifest."""
        # Windows needs a .bat/.exe file, Unix needs executable script
        if self.system == "windows":
            # Windows: use the batch wrapper script
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
        
        # Firefox-based browsers use allowed_extensions, Chromium-based use allowed_origins
        firefox_based = {"firefox", "librewolf", "waterfox", "floorp", "zen"}
        
        if browser in firefox_based:
            manifest["allowed_extensions"] = [FIREFOX_EXTENSION_ID]
        else:
            # Use the fixed Chrome extension ID (from the key in manifest.json)
            ext_id = chrome_extension_id or get_chrome_extension_id() or CHROME_EXTENSION_ID
            manifest["allowed_origins"] = [f"chrome-extension://{ext_id}/"]
        
        return manifest
    
    def create_wrapper_script(self):
        """Create a wrapper script that activates venv and runs the host."""
        if self.system == "windows":
            # Windows batch file - use relative paths so it works on any computer
            wrapper_path = self.project_root / "app" / "native" / "vaultkeeper_host.bat"
            # %~dp0 gives the directory of the batch file (app/native/)
            # We need to go up two directories to reach the project root
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
            # Unix shell script
            wrapper_path = self.wrapper_script
            content = f'''#!/bin/bash
# VaultKeeper Native Host Wrapper
# Activates virtual environment and runs the host

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
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
        
        # Make executable on Unix
        if self.system != "windows":
            os.chmod(wrapper_path, 0o755)
        
        return wrapper_path
    
    def install_for_browser(self, browser: str, chrome_extension_id: Optional[str] = None) -> Tuple[bool, str]:
        """Install native host for a specific browser."""
        paths = self.get_browser_paths()
        
        if browser not in paths:
            return False, f"Unknown browser: {browser}"
        
        target_dir = paths[browser]
        
        # Check if browser is installed (directory exists or parent exists)
        if browser == "firefox":
            browser_check = target_dir.parent.parent.exists()  # ~/.mozilla
        else:
            browser_check = target_dir.parent.exists()
        
        if not browser_check:
            return False, f"{browser.title()} not found"
        
        try:
            # Create directory if needed
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create manifest
            manifest = self.create_manifest(browser, chrome_extension_id)
            manifest_path = target_dir / f"{HOST_NAME}.json"
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # On Windows, ALL browsers need registry registration
            if self.system == "windows":
                self._register_windows(browser, manifest_path)
            
            return True, f"Installed to {manifest_path}"
            
        except Exception as e:
            return False, f"Failed to install for {browser}: {e}"
    
    def _register_windows(self, browser: str, manifest_path: Path):
        """Register native host in Windows registry."""
        import winreg
        
        # Firefox-based browsers use Mozilla registry path
        firefox_based = {"firefox", "librewolf", "waterfox", "floorp", "zen"}
        
        if browser in firefox_based:
            key_path = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"
        else:
            # Chromium-based browsers use Google Chrome registry path
            key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Failed to register in Windows registry: {e}")
    
    def install_all(self, chrome_extension_id: Optional[str] = None) -> List[Tuple[str, bool, str]]:
        """Install for all detected browsers."""
        results = []
        
        # Ensure wrapper script exists
        self.create_wrapper_script()
        
        # Make host.py executable
        if self.system != "windows":
            os.chmod(self.host_script, 0o755)
        
        for browser in self.get_browser_paths().keys():
            success, message = self.install_for_browser(browser, chrome_extension_id)
            results.append((browser, success, message))
        
        return results
    
    def uninstall_for_browser(self, browser: str) -> Tuple[bool, str]:
        """Uninstall native host for a specific browser."""
        paths = self.get_browser_paths()
        
        if browser not in paths:
            return False, f"Unknown browser: {browser}"
        
        manifest_path = paths[browser] / f"{HOST_NAME}.json"
        
        try:
            if manifest_path.exists():
                manifest_path.unlink()
                
                # Remove from Windows registry
                if self.system == "windows":
                    self._unregister_windows(browser)
                
                return True, f"Removed {manifest_path}"
            else:
                return False, "Manifest not found"
                
        except Exception as e:
            return False, f"Failed to uninstall: {e}"
    
    def _unregister_windows(self, browser: str):
        """Remove from Windows registry."""
        import winreg
        
        if browser == "firefox":
            key_path = rf"Software\Mozilla\NativeMessagingHosts\{HOST_NAME}"
        else:
            key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except WindowsError:
            pass  # Key doesn't exist
    
    def check_installation(self) -> List[Tuple[str, bool, str]]:
        """Check installation status for all browsers."""
        results = []
        
        for browser, path in self.get_browser_paths().items():
            manifest_path = path / f"{HOST_NAME}.json"
            
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    host_path = Path(manifest.get("path", ""))
                    
                    if host_path.exists():
                        results.append((browser, True, f"Installed: {manifest_path}"))
                    else:
                        results.append((browser, False, f"Manifest exists but host not found: {host_path}"))
                except Exception as e:
                    results.append((browser, False, f"Invalid manifest: {e}"))
            else:
                results.append((browser, False, "Not installed"))
        
        return results


def main():
    """CLI entry point."""
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
            # Ensure wrapper exists first
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

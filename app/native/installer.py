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
CHROME_EXTENSION_ID = None  # Set after extension is published

HOST_NAME = "com.vaultkeeper.host"
HOST_DESCRIPTION = "VaultKeeper Native Messaging Host"


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
                "firefox": home / ".mozilla" / "native-messaging-hosts",
                "chrome": home / ".config" / "google-chrome" / "NativeMessagingHosts",
                "chromium": home / ".config" / "chromium" / "NativeMessagingHosts",
                "brave": home / ".config" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
            }
        elif self.system == "darwin":  # macOS
            return {
                "firefox": home / "Library" / "Application Support" / "Mozilla" / "NativeMessagingHosts",
                "chrome": home / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts",
                "chromium": home / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts",
                "brave": home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
            }
        elif self.system == "windows":
            # Windows uses registry, but manifests can be stored anywhere
            appdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            return {
                "firefox": appdata / "Mozilla" / "NativeMessagingHosts",
                "chrome": appdata / "Google" / "Chrome" / "User Data" / "NativeMessagingHosts",
            }
        else:
            return {}
    
    def create_manifest(self, browser: str, chrome_extension_id: Optional[str] = None) -> dict:
        """Create the native messaging host manifest."""
        # Use wrapper script on Unix to handle venv activation
        if self.system == "windows":
            host_path = str(self.host_script)
        else:
            host_path = str(self.wrapper_script)
        
        manifest = {
            "name": HOST_NAME,
            "description": HOST_DESCRIPTION,
            "path": host_path,
            "type": "stdio"
        }
        
        # Firefox uses allowed_extensions, Chrome/Chromium use allowed_origins
        if browser == "firefox":
            manifest["allowed_extensions"] = [FIREFOX_EXTENSION_ID]
        else:
            if chrome_extension_id:
                manifest["allowed_origins"] = [f"chrome-extension://{chrome_extension_id}/"]
            else:
                # Placeholder - will need to be updated after extension is published
                manifest["allowed_origins"] = ["chrome-extension://EXTENSION_ID/"]
        
        return manifest
    
    def create_wrapper_script(self):
        """Create a wrapper script that activates venv and runs the host."""
        if self.system == "windows":
            # Windows batch file
            wrapper_path = self.project_root / "app" / "native" / "vaultkeeper_host.bat"
            content = f'''@echo off
"{self.project_root / ".venv" / "Scripts" / "python.exe"}" "{self.host_script}"
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
            
            # On Windows, also need to register in registry
            if self.system == "windows" and browser != "firefox":
                self._register_windows(browser, manifest_path)
            
            return True, f"Installed to {manifest_path}"
            
        except Exception as e:
            return False, f"Failed to install for {browser}: {e}"
    
    def _register_windows(self, browser: str, manifest_path: Path):
        """Register native host in Windows registry."""
        import winreg
        
        if browser == "firefox":
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

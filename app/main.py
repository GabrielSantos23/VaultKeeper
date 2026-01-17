#!/usr/bin/env python3
"""
VaultKeeper - Password Manager
Main entry point for the desktop application
"""

import sys
from pathlib import Path

# Add project root to path (parent of 'app' directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_native_host_installation():
    """Check and install/update native host on every run."""
    from app.native.installer import NativeHostInstaller
    
    installer = NativeHostInstaller()
    
    # Always reinstall to ensure the manifest is up-to-date
    # This handles cases where:
    # - Extension ID changed
    # - Host path changed (different install location)
    # - Wrapper script needs updating
    
    try:
        # Create/update wrapper script
        installer.create_wrapper_script()
        
        # Install/update for all detected browsers
        install_results = installer.install_all()
        
        installed_any = False
        for browser, success, msg in install_results:
            if success:
                installed_any = True
                # Only print on first install or if verbose
                # print(f"  ✅ {browser.title()}: Native host ready")
        
        if installed_any:
            print("🔐 Native Host: Ready")
    except Exception as e:
        print(f"⚠️ Native host setup warning: {e}")


def check_pending_reset():
    """Check if a reset was requested and perform it before starting."""
    import shutil
    import sys
    import time
    
    vaultkeeper_dir = Path.home() / '.vaultkeeper'
    reset_marker = vaultkeeper_dir / '.reset_pending'
    
    # Helper to clean a single file
    def clean_file(path):
        if not path.exists(): return True
        try:
            path.unlink()
            return True
        except:
            # Try rename as fallback
            try:
                timestamp = int(time.time())
                path.rename(path.with_suffix(f'.old.{timestamp}'))
                return True
            except:
                return False

    if reset_marker.exists():
        print("🔄 Performing scheduled reset...")
        
        # 1. Remove native host config
        try:
            from app.native.installer import NativeHostInstaller
            installer = NativeHostInstaller()
            for browser, browser_path in installer.get_browser_paths().items():
                manifest_path = browser_path / "com.vaultkeeper.host.json"
                if manifest_path.exists():
                    try: manifest_path.unlink()
                    except: pass
            
            if installer.system == "windows":
                import winreg
                for key_path in [
                    r"Software\Mozilla\NativeMessagingHosts\com.vaultkeeper.host",
                    r"Software\Google\Chrome\NativeMessagingHosts\com.vaultkeeper.host"
                ]:
                    try: winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    except: pass
        except Exception: 
            pass
        
        # 2. Delete data with retry loop
        while True:
            # Try to delete entire directory first
            try:
                if vaultkeeper_dir.exists():
                    shutil.rmtree(vaultkeeper_dir)
                print("  ✅ All data deleted successfully")
                break # Success
            except Exception:
                pass
            
            # If rmtree failed, try individual critical files
            vault_db = vaultkeeper_dir / 'vault.db'
            log_file = vaultkeeper_dir / 'native_host.log'
            auth_file = vaultkeeper_dir / 'auth.json'
            
            # Clean non-critical files silently
            clean_file(log_file)
            clean_file(auth_file)
            clean_file(reset_marker)
            
            # Critical check for vault.db
            if clean_file(vault_db):
                print("  ✅ Vault database deleted/renamed")
                break
                
            print("\n⚠️  FILE LOCKED: Could not delete vault.db")
            print("🛑  Please CLOSE ALL BROWSERS (Chrome, Firefox, Edge, etc) to release the file.")
            
            # Show Native Windows Message Box
            import ctypes
            MB_RETRYCANCEL = 0x05
            MB_ICONWARNING = 0x30
            IDRETRY = 4
            
            msg = (
                "Could not delete database file (vault.db).\n\n"
                "The file is currently in use, likely by a browser extension.\n\n"
                "Please CLOSE ALL BROWSERS (Chrome, Firefox, Edge) and click Retry.\n"
                "If the problem persists, try restarting your computer."
            )
            
            result = ctypes.windll.user32.MessageBoxW(0, msg, "Reset Blocked - File in Use", MB_RETRYCANCEL | MB_ICONWARNING)
            
            if result != IDRETRY:
                # User clicked Cancel
                sys.exit(1)
        
        print("  ✅ All data deleted successfully")
        print("  🔐 Reset complete. Starting fresh...")
        return


def main():
    # Check for pending reset first
    try:
        check_pending_reset()
    except Exception as e:
        print(f"⚠️ Warning: Reset check failed: {e}")
    
    # Check native host installation before starting UI
    try:
        check_native_host_installation()
    except Exception as e:
        print(f"⚠️ Warning: Could not check native host: {e}")
    
    from app.ui.main_window import main as ui_main
    ui_main()


if __name__ == '__main__':
    main()


import sys

from pathlib import Path

project_root = Path(__file__).parent.parent

sys.path.insert(0, str(project_root))

def check_native_host_installation():

    from app.native.installer import NativeHostInstaller

    installer = NativeHostInstaller()

    try:

        installer.create_wrapper_script()

        install_results = installer.install_all()

        installed_any = False

        for browser, success, msg in install_results:

            if success:

                installed_any = True

        if installed_any:

            print("🔐 Native Host: Ready")

    except Exception as e:

        print(f"⚠️ Native host setup warning: {e}")

def check_pending_reset():

    import shutil

    import sys

    import time

    vaultkeeper_dir = Path.home() / '.vaultkeeper'

    reset_marker = vaultkeeper_dir / '.reset_pending'

    def clean_file(path):

        if not path.exists(): return True

        try:

            path.unlink()

            return True

        except:

            try:

                timestamp = int(time.time())

                path.rename(path.with_suffix(f'.old.{timestamp}'))

                return True

            except:

                return False

    if reset_marker.exists():

        print("🔄 Performing scheduled reset...")

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

        while True:

            try:

                if vaultkeeper_dir.exists():

                    shutil.rmtree(vaultkeeper_dir)

                print("  ✅ All data deleted successfully")

                break

            except Exception:

                pass

            vault_db = vaultkeeper_dir / 'vault.db'

            log_file = vaultkeeper_dir / 'native_host.log'

            auth_file = vaultkeeper_dir / 'auth.json'

            clean_file(log_file)

            clean_file(auth_file)

            clean_file(reset_marker)

            if clean_file(vault_db):

                print("  ✅ Vault database deleted/renamed")

                break

            print("\n⚠️  FILE LOCKED: Could not delete vault.db")

            print("🛑  Please CLOSE ALL BROWSERS (Chrome, Firefox, Edge, etc) to release the file.")

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

                sys.exit(1)

        print("  ✅ All data deleted successfully")

        print("  🔐 Reset complete. Starting fresh...")

        return

def main():

    try:

        check_pending_reset()

    except Exception as e:

        print(f"⚠️ Warning: Reset check failed: {e}")

    try:

        check_native_host_installation()

    except Exception as e:

        print(f"⚠️ Warning: Could not check native host: {e}")

    from app.ui.main_window import main as ui_main

    ui_main()

if __name__ == '__main__':

    main()

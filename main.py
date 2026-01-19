
import sys

import customtkinter as ctk

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.ui.main_window import MainWindow

from app.core.config import Config

def main():

    vault_path = None

    if len(sys.argv) > 1:

        vault_path = Path(sys.argv[1])

    else:

        vault_path = Config.get_last_vault_path()

    print("Creating root...")

    root = ctk.CTk()

    try:

        print("Initializing MainWindow...")

        app = MainWindow(root, vault_path)

        print("Starting mainloop...")

        root.mainloop()

        print("Mainloop finished.")

    except KeyboardInterrupt:

        print("\nExiting...")

        sys.exit(0)

    except Exception as e:

        print(f"Fatal error: {e}", file=sys.stderr)

        import traceback

        traceback.print_exc()

        sys.exit(1)

if __name__ == "__main__":

    main()

#!/usr/bin/env python3
"""
VaultKeeper - Secure Password Manager
Main entry point
"""
import sys
import customtkinter as ctk
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.ui.main_window import MainWindow
from app.core.config import Config


def main():
    """Main entry point"""
    # Parse command-line arguments
    vault_path = None
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])
    else:
        # Load last used vault path
        vault_path = Config.get_last_vault_path()
    
    # Create CustomTkinter root
    print("Creating root...")
    root = ctk.CTk()
    
    # Create main window
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

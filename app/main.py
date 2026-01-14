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
    """Check and install native host on first run."""
    from app.native.installer import NativeHostInstaller
    
    installer = NativeHostInstaller()
    results = installer.check_installation()
    
    # Check if any browser has it installed
    any_installed = any(installed for _, installed, _ in results)
    
    if not any_installed:
        print("🔐 First run detected - Installing Native Host...")
        
        # Create wrapper script
        installer.create_wrapper_script()
        
        # Install for all detected browsers
        install_results = installer.install_all()
        
        for browser, success, msg in install_results:
            if success:
                print(f"  ✅ {browser.title()}: Installed")
            # Skip browsers not installed
        
        print("  Native host installation complete!")
        print()


def main():
    # Check native host installation before starting UI
    try:
        check_native_host_installation()
    except Exception as e:
        print(f"⚠️ Warning: Could not check native host: {e}")
    
    from app.ui.main_window import main as ui_main
    ui_main()


if __name__ == '__main__':
    main()

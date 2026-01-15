# -*- mode: python ; coding: utf-8 -*-
"""
VaultKeeper PyInstaller Specification File
Build command: pyinstaller vaultkeeper.spec
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

# Collect all data files
datas = [
    # UI assets (icons, themes, etc.)
    (str(project_root / 'app' / 'ui' / 'icons'), 'app/ui/icons'),
]

# Check if icons directory exists
icons_path = project_root / 'app' / 'ui' / 'icons'
if not icons_path.exists():
    datas = []

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'cryptography',
    'cryptography.hazmat.primitives.ciphers.aead',
    'argon2',
    'argon2.low_level',
    'sqlite3',
]

# Platform-specific settings
if sys.platform == 'win32':
    icon_file = str(project_root / 'app' / 'ui' / 'icons' / 'icon.ico')
    console = False
else:
    icon_file = str(project_root / 'app' / 'ui' / 'icons' / 'icon.png')
    console = False

# Check if icon exists
icon_path = Path(icon_file)
if not icon_path.exists():
    icon_file = None

a = Analysis(
    [str(project_root / 'app' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VaultKeeper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

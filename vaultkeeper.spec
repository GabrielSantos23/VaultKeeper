import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)

datas = [
    (str(project_root / 'app' / 'ui' / 'icons'), 'app/ui/icons'),
]
if (project_root / '.env').exists():
    datas.append((str(project_root / '.env'), '.'))

if not (project_root / 'app' / 'ui' / 'icons').exists():
    datas = [d for d in datas if d[1] != 'app/ui/icons']

hiddenimports = [
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtSvg',
    'cryptography', 'cryptography.hazmat.primitives.ciphers.aead',
    'argon2', 'argon2.low_level', 'sqlite3',
]

a = Analysis(
    [str(project_root / 'app' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL', 'cv2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VaultKeeper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'app' / 'ui' / 'icons' / 'icon.ico') if sys.platform == 'win32' else None,
)

b = Analysis(
    [str(project_root / 'app' / 'native' / 'host.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL', 'cv2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_host = PYZ(b.pure, b.zipped_data, cipher=block_cipher)

exe_host = EXE(
    pyz_host,
    b.scripts,
    [],
    exclude_binaries=True,
    name='vk_host',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    
    exe_host,
    b.binaries,
    b.zipfiles,
    b.datas,
    
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VaultKeeper',
)

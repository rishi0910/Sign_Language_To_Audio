# SignBridgePro.spec
# PyInstaller build spec for SignBridge Pro
# Run: pyinstaller installer/SignBridgePro.spec

import os

block_cipher = None
BASE = os.path.dirname(os.path.abspath(SPEC))   # noqa: F821

a = Analysis(
    [os.path.join(BASE, '..', 'main.py')],
    pathex=[BASE],
    binaries=[],
    datas=[
        (os.path.join(BASE, '..', 'model', '*'),         'model'),
        (os.path.join(BASE, '..', 'config', '*.json'),   'config'),
        (os.path.join(BASE, '..', 'assets', '**', '*'),  'assets'),
    ],
    hiddenimports=[
        'mediapipe',
        'tensorflow',
        'cv2',
        'pyttsx3',
        'PIL',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)   # noqa: F821

exe = EXE(                                               # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SignBridgePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,              # No black console window
    icon=os.path.join(BASE, '..', 'assets', 'icons', 'app_icon.ico'),
)

coll = COLLECT(                                          # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SignBridgePro',
)

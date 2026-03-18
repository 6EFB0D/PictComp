# -*- mode: python ; coding: utf-8 -*-
# PictComp GUI版 PyInstaller設定ファイル（macOS用）

import os

# プロジェクトルートのパス
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
ASSETS_ICON = os.path.join(PROJECT_ROOT, 'assets', 'icon')

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'gui_main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        # ロゴ（GUIで使用）
        (os.path.join(ASSETS_ICON, 'pictcomp_bright.jpg'), 'assets/icon'),
        # ライセンス（法的情報で表示）
        (os.path.join(PROJECT_ROOT, 'LICENSE'), '.'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pillow_heif',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PictComp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ASSETS_ICON, 'pictcomp_bright.icns'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PictComp',
)

app = BUNDLE(
    coll,
    name='PictComp',
    icon=os.path.join(ASSETS_ICON, 'pictcomp_bright.icns'),
    bundle_identifier='com.goplan.pictcomp',
    version='0.1.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'NSHumanReadableCopyright': 'Copyright (c) 2026 Office Go Plan',
    },
)

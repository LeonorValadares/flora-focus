# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\X1605\\Downloads\\flora_focus_complete (1)\\flora_focus_complete\\kivy_app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\X1605\\Downloads\\flora_focus_complete (1)\\flora_focus_complete\\FloraFocus.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FloraFocus',
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
    icon=['C:\\Users\\X1605\\Downloads\\flora_focus_complete (1)\\flora_focus_complete\\FloraFocus.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FloraFocus',
)

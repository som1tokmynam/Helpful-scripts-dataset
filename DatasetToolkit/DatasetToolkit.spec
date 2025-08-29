# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[('D:\\exl2\\.venv\\Lib\\site-packages\\torch\\lib', 'torch\\lib')],
    
    # This list specifies all non-Python files to be included.
    # The format is a list of tuples: (source_path, destination_in_bundle)
    datas=[
        ('D:\\exl2\\.venv\\Lib\\site-packages\\ttkbootstrap', 'ttkbootstrap'),
        ('local_tokenizer', 'local_tokenizer'),
        ('f.txt', '.')  # <-- This line adds the Deslop filter file to the bundle.
    ],
    
    hiddenimports=['transformers', 'torch', 'ttkbootstrap'],
    
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='DatasetToolkit',
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
)
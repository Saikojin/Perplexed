
# PyInstaller Build Script for Roddle/Perplexed
# Usage: pyinstaller build.spec

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys
import os

block_cipher = None

# Collect all backend submodules to ensure nothing is missed
backend_imports = collect_submodules('backend')
# Specifically ensure uvicorn and its loops are included
hidden_imports = backend_imports + [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.threading',
    'passlib.handlers.bcrypt',
    # Explicitly add backend modules if collect_submodules misses them due to missing __init__.py
    'backend.database',
    'backend.llm',
]

# Analysis step
a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/static', 'backend/static'),
        ('backend/models', 'backend/models'),
        # Important: Ensure source files are copied if we rely on dynamic imports or file operations
        # But for imports, hiddenimports should suffice.
    ],
    hiddenimports=hidden_imports,
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
    name='Perplexed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False, # Set to False for production
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Perplexed',
)

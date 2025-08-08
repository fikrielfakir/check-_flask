# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        # Don't include data folder - it should be created by the app
    ],
    hiddenimports=[
        'flask',
        'jinja2',
        'werkzeug',
        'sqlite3',
        'pathlib',
        'threading',
        'webbrowser',
        'openpyxl',  # For Excel operations
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'apscheduler',  # Based on your logs
        'apscheduler.schedulers.background',
        'apscheduler.executors.pool',
        'apscheduler.jobstores.memory',
        'email.mime.multipart',
        'email.mime.text',
        'datetime',
        'json',
        'uuid',
        'secrets',
        'logging.handlers',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt6',
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'torch',
        'IPython',
        'pandas',  # Exclude unless your app specifically uses these
        'PIL',
        'reportlab',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ChequeManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging initially
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
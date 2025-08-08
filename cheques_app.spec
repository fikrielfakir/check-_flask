# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get current directory
current_dir = Path.cwd()

# Define data files and folders to include
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('utils', 'utils'),
    ('routes', 'routes'),
]

# Hidden imports - all modules that PyInstaller might miss
hiddenimports = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'flask_wtf',
    'flask_wtf.csrf',
    'wtforms',
    'wtforms.fields',
    'wtforms.validators',
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.ext.declarative',
    'werkzeug',
    'werkzeug.security',
    'werkzeug.middleware.proxy_fix',
    'jinja2',
    'markupsafe',
    'openpyxl',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'reportlab.lib.pagesizes',
    'apscheduler',
    'apscheduler.schedulers.background',
    'models',
    'forms',
    'app',
    'scheduler',
    'utils.excel_manager',
    'utils.optimized_excel_sync',
    'utils.excel_yearly_manager',
    'routes.auth',
    'routes.dashboard',
    'routes.banks',
    'routes.clients',
    'routes.cheques',
    'routes.exports',
    'routes.excel_manager',
    'routes.analytics',
    'routes.advanced_analytics',
    'psycopg2',
    'pandas',
    'numpy',
    'scikit-learn',
    'sklearn',
    'sklearn.feature_extraction',
    'sklearn.feature_extraction.text',
    'sklearn.metrics',
    'sklearn.metrics.pairwise',
]

# Binaries to exclude to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'PIL.ImageTk',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
]

a = Analysis(
    ['desktop_main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='GestionCheques',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

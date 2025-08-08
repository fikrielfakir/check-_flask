import PyInstaller.__main__
import os
import shutil

# Clean previous builds
shutil.rmtree('build', ignore_errors=True)
shutil.rmtree('dist', ignore_errors=True)

# PyInstaller configuration
params = [
    'main.py',               # Your main script
    '--onefile',
    '--noconsole',
    '--name=GestionCheques',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--add-data=data;data',
    '--hidden-import=flask',
    '--hidden-import=flask_sqlalchemy',
    '--hidden-import=flask_login',
    '--hidden-import=wtforms',
    '--hidden-import=sqlalchemy',
    '--hidden-import=openpyxl',
    '--hidden-import=reportlab',
    '--exclude-module=tkinter',
    '--exclude-module=matplotlib',
    '--exclude-module=PyQt5',
    '--exclude-module=PyQt6'
]

# Run PyInstaller
PyInstaller.__main__.run(params)

print("\nBuild completed! Executable is in the 'dist' folder.")
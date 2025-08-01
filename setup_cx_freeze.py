#!/usr/bin/env python3
"""
Setup script for building executable with cx_Freeze
Alternative to PyInstaller for the Cheque Management System
"""

import sys
import os
from pathlib import Path

try:
    from cx_Freeze import setup, Executable
except ImportError:
    print("cx_Freeze not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cx_Freeze"])
    from cx_Freeze import setup, Executable

# Build options
build_exe_options = {
    "packages": [
        "flask",
        "flask_sqlalchemy", 
        "flask_login",
        "flask_wtf",
        "wtforms",
        "sqlalchemy",
        "werkzeug",
        "jinja2",
        "markupsafe",
        "openpyxl",
        "reportlab",
        "apscheduler",
        "models",
        "forms",
        "app",
        "utils",
        "routes"
    ],
    "include_files": [
        ("templates", "templates"),
        ("static", "static"),
        ("utils", "utils"),
        ("routes", "routes"),
        ("models.py", "models.py"),
        ("forms.py", "forms.py"),
        ("app.py", "app.py"),
        ("scheduler.py", "scheduler.py")
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "PyQt5",
        "PyQt6"
    ],
    "optimize": 2,
    "include_msvcrt": True
}

# Create the executable
base = None
if sys.platform == "win32":
    base = None  # Console application on Windows

executable = Executable(
    script="desktop_main.py",
    base=base,
    target_name="GestionCheques.exe",
    icon=None  # Add icon path here if available
)

setup(
    name="Gestion des Chèques",
    version="1.0.0",
    description="Système de Gestion des Chèques - Application de bureau",
    author="Cheque Management System",
    options={"build_exe": build_exe_options},
    executables=[executable]
)

print("\n" + "="*60)
print("CONSTRUCTION AVEC CX_FREEZE")
print("="*60)
print("Pour construire l'exécutable, exécutez:")
print("python setup_cx_freeze.py build")
print("="*60)
#!/usr/bin/env python3
"""
Improved setup script for building executable with cx_Freeze
for the Cheque Management System
"""

import sys
import os
from pathlib import Path
import subprocess

# Try to import cx_Freeze or install it
try:
    from cx_Freeze import setup, Executable
except ImportError:
    print("cx_Freeze not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cx_Freeze"])
    from cx_Freeze import setup, Executable

# Application base directory
base_dir = Path(__file__).parent

# Build options - updated for cx_Freeze 8.3.0
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
        "itsdangerous",
        "click",
        "openpyxl",
        "reportlab",
        "apscheduler",
        "psycopg2" if os.name == 'posix' else "psycopg2-binary"
    ],
    "include_files": [
        (str(base_dir / "app" / "templates"), "templates"),
        (str(base_dir / "app" / "static"), "static"),
        (str(base_dir / "data"), "data"),
        (str(base_dir / "models.py"), "models.py"),
        (str(base_dir / "forms.py"), "forms.py"),
        (str(base_dir / "config.py"), "config.py")
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "test",
        "unittest"
    ],
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
    "optimize": 2
}

# Base configuration - None for console, "Win32GUI" for no console
base = None if os.getenv("SHOW_CONSOLE", "false").lower() == "true" else "Win32GUI"

executable = Executable(
    script="main.py",  # Changed from desktop_main.py to main.py
    base=base,
    target_name="GestionCheques.exe",
    icon=str(base_dir / "app" / "static" / "favicon.ico") if (base_dir / "app" / "static" / "favicon.ico").exists() else None
)

setup(
    name="Gestion des Chèques",
    version="1.0.0",
    description="Système de Gestion des Chèques - Application de bureau",
    author="Votre Société",
    options={"build_exe": build_exe_options},
    executables=[executable]
)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONSTRUCTION AVEC CX_FREEZE".center(60))
    print("="*60)
    print("Pour construire l'exécutable, exécutez:")
    print(f"python {Path(__file__).name} build")
    print("\nPour inclure la console (débogage):")
    print(f"set SHOW_CONSOLE=true && python {Path(__file__).name} build")
    print("="*60)
    
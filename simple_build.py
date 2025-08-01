#!/usr/bin/env python3
"""
Simple script to build executable using basic PyInstaller commands.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_simple_main():
    """Create a simple main file for the executable."""
    content = '''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set up environment for standalone executable
if getattr(sys, 'frozen', False):
    app_dir = Path(sys.executable).parent
else:
    app_dir = Path(__file__).parent

# Create data directories
data_dir = app_dir / 'data'
data_dir.mkdir(exist_ok=True)
(data_dir / 'excel').mkdir(exist_ok=True)
(data_dir / 'exports').mkdir(exist_ok=True)
(data_dir / 'uploads').mkdir(exist_ok=True)

# Set environment variables
os.environ['DATABASE_URL'] = f'sqlite:///{data_dir}/cheques.db'
os.environ['SESSION_SECRET'] = 'KSr8293NEv711HU16ZIr14Hxp13hv_ghVJVJgAgxkwo'
os.environ['UPLOAD_FOLDER'] = str(data_dir / 'uploads')
os.environ['EXCEL_FOLDER'] = str(data_dir / 'excel')

# Import and run the app
from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("Application started at http://localhost:5000")
    print("Login: manal / manalcedesa")
    app.run(host='127.0.0.1', port=5000, debug=False)
'''
    
    with open('exe_main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Created exe_main.py")

def run_pyinstaller():
    """Run PyInstaller with basic options."""
    create_simple_main()
    
    # Basic PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name=GestionCheques',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--add-data=utils;utils',
        '--add-data=routes;routes',
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=flask_wtf',
        '--hidden-import=wtforms',
        '--hidden-import=sqlalchemy',
        '--hidden-import=werkzeug',
        '--hidden-import=models',
        '--hidden-import=forms',
        '--hidden-import=app',
        '--hidden-import=openpyxl',
        '--clean',
        'exe_main.py'
    ]
    
    print("Running PyInstaller...")
    print(" ".join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("BUILD SUCCESSFUL!")
        print("Executable created at: dist/GestionCheques.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

if __name__ == "__main__":
    success = run_pyinstaller()
    if success:
        print("✅ Executable built successfully!")
    else:
        print("❌ Build failed!")
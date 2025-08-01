#!/usr/bin/env python3
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

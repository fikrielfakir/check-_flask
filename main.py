import os
import sys
from pathlib import Path

# Handle frozen executable paths for desktop mode
if getattr(sys, 'frozen', False):
    app_dir = Path(sys.executable).parent
else:
    app_dir = Path(__file__).parent

# Setup data directories
data_dir = app_dir / 'data'
(data_dir / 'excel').mkdir(parents=True, exist_ok=True)
(data_dir / 'exports').mkdir(exist_ok=True)
(data_dir / 'uploads').mkdir(exist_ok=True)

# Set environment variables only if not already set (for compatibility)
env_defaults = {
    'FLASK_ENV': 'production' if getattr(sys, 'frozen', False) else 'development',
    'UPLOAD_FOLDER': str(data_dir / 'uploads'),
    'EXCEL_FOLDER': str(data_dir / 'excel'),
    'EXPORTS_FOLDER': str(data_dir / 'exports'),
    'DATA_FOLDER': str(data_dir),
    'SESSION_SECRET': 'KSr8293NEv711HU16ZIr14Hxp13hv_ghVJVJgAgxkwo'
}

# Only set SQLite as fallback if no DATABASE_URL is set
if not os.environ.get('DATABASE_URL'):
    env_defaults['DATABASE_URL'] = f'sqlite:///{data_dir}/cheques.db'

for key, value in env_defaults.items():
    if key not in os.environ:
        os.environ[key] = value

# Create the Flask app instance for WSGI (gunicorn)
from app import create_app
app = create_app()

def run_app():
    """Function for running in desktop/development mode"""
    print("=" * 60)
    print("   CHEQUE MANAGEMENT SYSTEM".center(60))
    print("=" * 60)
    print(f"Running from: {app_dir}")
    print("Access at: http://localhost:5000")
    print("Default login: manal / manalcedesa")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    try:
        run_app()
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)
import os
import sys
from pathlib import Path

# Handle frozen executable paths
if getattr(sys, 'frozen', False):
    app_dir = Path(sys.executable).parent
else:
    app_dir = Path(__file__).parent

# Setup data directories
data_dir = app_dir / 'data'
(data_dir / 'excel').mkdir(parents=True, exist_ok=True)
(data_dir / 'exports').mkdir(exist_ok=True)
(data_dir / 'uploads').mkdir(exist_ok=True)

# Set environment variables
os.environ.update({
    'FLASK_ENV': 'production' if getattr(sys, 'frozen', False) else 'development',
    'DATABASE_URL': f'sqlite:///{data_dir}/cheques.db',
    'UPLOAD_FOLDER': str(data_dir / 'uploads'),
    'EXCEL_FOLDER': str(data_dir / 'excel'),
    'EXPORTS_FOLDER': str(data_dir / 'exports'),
    'DATA_FOLDER': str(data_dir),
    'SESSION_SECRET': 'your-secret-key-here'
})

def run_app():
    from app import create_app
    app = create_app()
    
    print("=" * 60)
    print("   CHEQUE MANAGEMENT SYSTEM".center(60))
    print("=" * 60)
    print(f"Running from: {app_dir}")
    print("Access at: http://localhost:5000")
    print("Default login: manal / manalcedesa")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, threaded=True)

if __name__ == '__main__':
    try:
        run_app()
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)
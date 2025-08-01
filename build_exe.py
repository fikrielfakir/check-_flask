#!/usr/bin/env python3
"""
Script to build the Cheque Management Application as a standalone executable.
This script prepares the application for PyInstaller packaging.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_main_entry_point():
    """Create a simplified main entry point for the executable."""
    main_content = '''#!/usr/bin/env python3
"""
Main entry point for the Cheque Management Application executable.
This file is optimized for PyInstaller packaging.
"""

import os
import sys
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_environment():
    """Set up environment for the executable."""
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = Path(sys.executable).parent
        os.environ['FLASK_ENV'] = 'production'
    else:
        # Running as script
        app_dir = Path(__file__).parent
        os.environ['FLASK_ENV'] = 'development'
    
    # Set up data directories relative to executable
    data_dir = app_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    
    (data_dir / 'excel').mkdir(exist_ok=True)
    (data_dir / 'exports').mkdir(exist_ok=True)
    (data_dir / 'uploads').mkdir(exist_ok=True)
    
    # Set environment variables
    os.environ['DATA_FOLDER'] = str(data_dir)
    os.environ['EXCEL_FOLDER'] = str(data_dir / 'excel')
    os.environ['EXPORTS_FOLDER'] = str(data_dir / 'exports')
    os.environ['UPLOAD_FOLDER'] = str(data_dir / 'uploads')
    
    # Use SQLite database for standalone application
    db_path = data_dir / 'cheques.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    # Set session secret
    os.environ['SESSION_SECRET'] = 'KSr8293NEv711HU16ZIr14Hxp13hv_ghVJVJgAgxkwo'
    
    return app_dir

def main():
    """Main entry point."""
    try:
        # Setup environment
        app_dir = setup_environment()
        
        # Import and create the Flask app
        from app import create_app
        app = create_app()
        
        print("=" * 60)
        print("   SYSTÈME DE GESTION DES CHÈQUES")
        print("   Cheque Management System")
        print("=" * 60)
        print(f"Application démarrée depuis: {app_dir}")
        print("Accédez à l'application via: http://localhost:5000")
        print("Utilisateur par défaut: manal / manalcedesa")
        print("=" * 60)
        print("Appuyez sur Ctrl+C pour arrêter l'application")
        print("=" * 60)
        
        # Run the application
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\\nApplication arrêtée par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {e}")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
    
    with open('desktop_main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print("✓ Created desktop_main.py entry point")

def create_pyinstaller_spec():
    """Create PyInstaller specification file."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
'''
    
    with open('cheques_app.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✓ Created cheques_app.spec PyInstaller specification")

def build_executable():
    """Build the executable using PyInstaller."""
    print("\n" + "="*60)
    print("CONSTRUCTION DE L'EXÉCUTABLE")
    print("="*60)
    
    try:
        # Create entry point and spec file
        create_main_entry_point()
        create_pyinstaller_spec()
        
        print("\n🔧 Démarrage de la compilation avec PyInstaller...")
        print("Cela peut prendre plusieurs minutes...")
        
        # Run PyInstaller with the spec file
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'cheques_app.spec']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ COMPILATION RÉUSSIE!")
            print(f"📁 L'exécutable se trouve dans: ./dist/GestionCheques.exe")
            
            # Check if file exists
            exe_path = Path("dist/GestionCheques.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📊 Taille du fichier: {size_mb:.1f} MB")
                
                print("\n" + "="*60)
                print("INSTRUCTIONS D'UTILISATION:")
                print("="*60)
                print("1. Copiez le fichier 'GestionCheques.exe' sur votre ordinateur")
                print("2. Double-cliquez pour lancer l'application")
                print("3. Accédez à http://localhost:5000 dans votre navigateur")
                print("4. Connectez-vous avec: manal / manalcedesa")
                print("="*60)
                
                return True
            else:
                print("❌ Erreur: Fichier exécutable non trouvé après compilation")
                return False
        else:
            print("❌ ERREUR DE COMPILATION:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur durant la compilation: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    if not success:
        print("\n💡 Conseils de dépannage:")
        print("- Vérifiez que tous les modules sont installés")
        print("- Assurez-vous d'avoir les droits d'écriture dans le dossier")
        print("- Essayez de relancer la compilation")
        input("\nAppuyez sur Entrée pour continuer...")
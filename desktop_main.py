#!/usr/bin/env python3
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
        print("\nApplication arrêtée par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {e}")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == '__main__':
    main()

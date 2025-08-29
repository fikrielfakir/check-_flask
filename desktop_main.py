#!/usr/bin/env python3
"""
StockCeramique Desktop Application
Desktop entry point for the Flask-based inventory management system using webview with splash screen
"""

import threading
import time
import webview
import webbrowser
import sys
import os
import socket
import logging
import requests
from tkinter import filedialog
import tkinter as tk
import io

# CRITICAL: Disable stdin for PyInstaller compatibility BEFORE importing Flask
if getattr(sys, 'frozen', False):
    # Create a dummy stdin to prevent input() calls from failing
    sys.stdin = io.StringIO('')

# Now import Flask components after stdin is handled
from flask_app import create_app
from flask_models import db

# Set up logging with file output for compiled version
if getattr(sys, 'frozen', False):
    # For compiled executable, log to file
    log_dir = os.path.join(os.path.expanduser("~"), "StockCeramique", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout) if sys.stdout else logging.NullHandler()
        ]
    )
else:
    # For development, use console logging
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Get base path for PyInstaller and set up database path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Use user's AppData directory for database
    DB_DIR = os.path.join(os.path.expanduser("~"), "StockCeramique")
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Create instance directory for database
    INSTANCE_DIR = os.path.join(DB_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    DB_PATH = os.path.join(INSTANCE_DIR, "stockceramique.db")
    # Set environment variable for Flask app to use SQLite with proper URI format
    os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH.replace(os.sep, "/")}'
    logger.info(f"Database will be created at: {DB_PATH}")
    logger.info(f"Instance directory: {INSTANCE_DIR}")
else:
    # Running as script - use local instance directory
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    INSTANCE_DIR = os.path.join(BASE_PATH, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    DB_PATH = os.path.join(INSTANCE_DIR, "stockceramique.db")
    # Set SQLite database URL for development/script mode with proper URI format
    os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH.replace(os.sep, "/")}'
    logger.info(f"Development database at: {DB_PATH}")

# Additional SQLAlchemy configuration environment variables
os.environ['SQLALCHEMY_ENGINE_OPTIONS'] = '{"pool_pre_ping": true, "pool_recycle": 300}'

class DownloadAPI:
    """API class to handle download operations from webview"""

    def __init__(self, server_port):
        self.server_port = server_port
        self.downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    def download_file(self, url_path, suggested_filename=None):
        """Download a file from the Flask server"""
        try:
            # Create full URL
            full_url = f"http://127.0.0.1:{self.server_port}{url_path}"

            # Get the file from Flask server
            response = requests.get(full_url, stream=True, timeout=30)
            response.raise_for_status()

            # Determine filename
            if not suggested_filename:
                # Try to get filename from Content-Disposition header
                cd_header = response.headers.get('Content-Disposition', '')
                if 'filename=' in cd_header:
                    suggested_filename = cd_header.split('filename=')[1].strip('"\'')
                else:
                    suggested_filename = "download_file"

            # Show file save dialog
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Keep dialog on top

            # Get file extension from suggested filename
            file_ext = os.path.splitext(suggested_filename)[1]
            if file_ext:
                filetypes = [
                    (f"{file_ext.upper()} files", f"*{file_ext}"),
                    ("All files", "*.*")
                ]
            else:
                filetypes = [("All files", "*.*")]

            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save file as...",
                initialdir=self.downloads_dir,
                defaultextension=file_ext,
                filetypes=filetypes
            )

            root.destroy()

            if file_path:
                # Save the file
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"✅ File downloaded successfully: {file_path}")
                return {"success": True, "path": file_path, "message": "File downloaded successfully!"}
            else:
                return {"success": False, "message": "Download cancelled by user"}

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Download request failed: {e}")
            return {"success": False, "message": f"Download failed: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return {"success": False, "message": f"Download failed: {str(e)}"}

    def show_downloads_folder(self):
        """Open the downloads folder in file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.downloads_dir)
            elif os.name == 'posix':  # macOS/Linux
                os.system(f'open "{self.downloads_dir}"' if sys.platform == 'darwin' else f'xdg-open "{self.downloads_dir}"')
            return {"success": True, "message": "Downloads folder opened"}
        except Exception as e:
            logger.error(f"❌ Failed to open downloads folder: {e}")
            return {"success": False, "message": f"Failed to open downloads folder: {str(e)}"}

def find_free_port():
    """Find a free port from a list of common ports"""
    ports_to_try = [5001, 5002, 5003, 8001, 8002, 8003, 8080, 8081, 5000]

    for port in ports_to_try:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                logger.info(f"✅ Using port: {port}")
                return port
        except OSError:
            logger.debug(f"❌ Port {port} is busy")
            continue

    # Find any available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        logger.info(f"✅ Using dynamic port: {port}")
        return port

def run_flask(port):
    """Run Flask server in a separate thread"""
    try:
        logger.info(f"🚀 Starting Flask server on port {port}...")
        
        # Temporarily redirect stdin to prevent any input() calls during Flask startup
        original_stdin = sys.stdin
        if getattr(sys, 'frozen', False):
            sys.stdin = io.StringIO('')
        
        # Set additional Flask configuration for SQLAlchemy
        os.environ['FLASK_ENV'] = 'production'
        os.environ['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
        os.environ['SQLALCHEMY_ENGINE_OPTIONS'] = '{"pool_pre_ping": true}'
        
        app = create_app()

        # Configure SQLAlchemy to avoid connection timeout issues
        with app.app_context():
            # Set database engine options for better SQLite compatibility
            if hasattr(db.engine, 'update_execution_options'):
                db.engine.update_execution_options(
                    pool_pre_ping=True,
                    pool_recycle=300
                )
            
            # Create all database tables
            db.create_all()
            logger.info("✅ Database tables created successfully")
            
            # Database tables are now ready for use
            logger.info("📦 Database initialized and ready")

        # Restore original stdin
        sys.stdin = original_stdin
        
        # Run Flask with minimal options to avoid interactive prompts
        app.run(
            host='127.0.0.1', 
            port=port, 
            debug=False, 
            use_reloader=False, 
            threaded=True,
            use_debugger=False
        )
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        # Log the full traceback for debugging
        import traceback
        logger.error(traceback.format_exc())
        # Restore stdin in case of error
        if 'original_stdin' in locals():
            sys.stdin = original_stdin

def wait_for_server(port, timeout=30):
    """Wait for Flask server to be ready using HTTP requests"""
    start_time = time.time()
    url = f"http://127.0.0.1:{port}"

    logger.info("⏳ Waiting for Flask server to start...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info("✅ Flask server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)

    logger.error("❌ Flask server failed to start within timeout")
    return False

def safe_splash_operation(operation, *args, **kwargs):
    """Safely perform splash screen operations"""
    try:
        import pyi_splash
        if hasattr(pyi_splash, 'is_alive') and not pyi_splash.is_alive():
            return False
        return getattr(pyi_splash, operation)(*args, **kwargs)
    except (ImportError, RuntimeError, AttributeError) as e:
        logger.debug(f"Splash operation '{operation}' failed: {e}")
        return False

def open_with_webview_direct(url, port):
    """Open webview directly to the main application"""
    try:
        logger.info("🖥️ Opening webview with main application...")

        # Create download API instance
        download_api = DownloadAPI(port)

        # Create webview window directly with the main app URL
        webview.create_window(
            "StockCeramique - Inventory Management",
            url,
            width=1200,
            height=800,
            min_size=(800, 600),
            resizable=True,
            maximized=False,
            js_api=download_api  # Expose download API to JavaScript
        )

        # Start webview (this blocks until window is closed)
        webview.start(debug=False)
        return True

    except Exception as e:
        logger.error(f"❌ Webview failed: {e}")
        return False

def open_with_browser(url):
    """Open with default browser"""
    try:
        logger.info("🌐 Opening with default browser...")
        webbrowser.open(url)
        logger.info("✅ Browser opened successfully!")
        logger.info("📋 Keep this console window open to keep the server running")
        logger.info("📋 Close this window or press Ctrl+C to stop the server")
        return True
    except Exception as e:
        logger.error(f"❌ Browser failed: {e}")
        return False

def keep_alive():
    """Keep the application running when using browser"""
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")

def show_error_dialog(title, message):
    """Show error dialog using tkinter"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)
        
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        # If GUI fails, just log the error
        logger.error(f"{title}: {message}")

def main():
    """Main function to run the desktop application"""
    # Set up environment variables for non-interactive mode and SQLAlchemy compatibility
    os.environ['FLASK_ENV'] = 'production'
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    os.environ['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
    os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'
    
    try:
        logger.info("🚀 Starting StockCeramique Desktop Application...")

        # Update PyInstaller splash screen
        safe_splash_operation('update_text', 'Initializing application...')

        # Find available port
        port = find_free_port()

        # Update splash
        safe_splash_operation('update_text', 'Starting Flask server...')

        # Start Flask server
        flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
        flask_thread.start()

        # Update splash
        safe_splash_operation('update_text', 'Waiting for server...')

        # Wait for server to be ready before showing webview
        if wait_for_server(port):
            logger.info("✅ Server is ready!")

            # Update splash one more time
            safe_splash_operation('update_text', 'Loading interface...')
            time.sleep(0.5)  # Brief pause to show the message

            # Close PyInstaller splash screen
            safe_splash_operation('close')

            # Server URL
            url = f"http://127.0.0.1:{port}"
            logger.info(f"🌐 Server ready at: {url}")

            # Try webview first, fallback to browser
            if not open_with_webview_direct(url, port):
                logger.info("🔄 Webview failed, trying browser fallback...")

                if open_with_browser(url):
                    # Keep server running for browser
                    keep_alive()
                else:
                    logger.error("❌ Both webview and browser failed!")
                    error_msg = f"Failed to open interface. Try manually opening: {url}"
                    logger.info(f"📋 {error_msg}")
                    
                    # Show error dialog if possible
                    show_error_dialog("StockCeramique Error", error_msg)
        else:
            logger.error("❌ Flask server failed to start")
            safe_splash_operation('close')
            
            error_msg = "Flask server failed to start. Check the log file for details."
            show_error_dialog("StockCeramique Error", error_msg)

    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Try to close splash screen
        safe_splash_operation('close')

        # Show error dialog
        error_msg = f"Application failed to start: {str(e)}"
        show_error_dialog("StockCeramique Error", error_msg)
        
        sys.exit(1)

if __name__ == '__main__':
    main()
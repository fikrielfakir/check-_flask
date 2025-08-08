import threading
import time
import webview
import webbrowser
from app import app
import sys
import os
import socket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get base path for PyInstaller
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

def find_free_port():
    """Find a free port from a list of common ports"""
    ports_to_try = [8001, 8002, 8003, 8080, 8081, 5000, 5001]
    
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
    try:
        logger.info(f"🚀 Starting Flask server on port {port}...")
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")

def wait_for_server(port, timeout=30):
    """Wait for Flask server to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    logger.info("✅ Flask server is ready!")
                    return True
        except:
            pass
        time.sleep(1)
    
    return False

def open_with_webview(url):
    """Try to open with webview"""
    try:
        logger.info("🖥️ Attempting to open with webview...")
        webview.create_window(
            "Gestion de Chèques",
            url,
            width=1920,
            height=800
        )
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

if __name__ == '__main__':
    try:
        # Close PyInstaller splash screen if it exists
        try:
            import pyi_splash
            pyi_splash.update_text('Starting Flask server...')
        except ImportError:
            pass
        
        # Find available port
        port = find_free_port()
        
        # Start Flask server
        flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
        flask_thread.start()
        
        # Wait for server
        logger.info("⏳ Waiting for Flask server to start...")
        if not wait_for_server(port):
            logger.error("❌ Flask server failed to start")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Server is ready
        url = f"http://127.0.0.1:{port}"
        logger.info(f"🌐 Server ready at: {url}")
        
        # Close splash screen
        try:
            import pyi_splash
            pyi_splash.close()
        except ImportError:
            pass
        
        # Try webview first, fallback to browser
        if not open_with_webview(url):
            logger.info("🔄 Webview failed, trying browser fallback...")
            
            if open_with_browser(url):
                # Keep server running for browser
                keep_alive()
            else:
                logger.error("❌ Both webview and browser failed!")
                logger.info(f"📋 Try manually opening: {url}")
                input("Press Enter to exit...")
        
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            import pyi_splash
            pyi_splash.close()
        except ImportError:
            pass
        input("Press Enter to exit...")
        sys.exit(1)
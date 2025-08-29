"""
SocketIO configuration that works with PyInstaller
"""
import sys
from flask_socketio import SocketIO

def create_socketio(app):
    """
    Create SocketIO instance with PyInstaller-safe configuration
    """
    # Determine the best async mode based on environment
    if getattr(sys, 'frozen', False):
        # For PyInstaller builds, use eventlet if available, else None (auto-detect)
        try:
            import eventlet
            async_mode = 'eventlet'
        except ImportError:
            try:
                import gevent
                async_mode = 'gevent'  
            except ImportError:
                # Let SocketIO auto-detect the best mode
                async_mode = None
    else:
        # For development, use threading
        async_mode = 'threading'
    
    try:
        if async_mode:
            socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)
        else:
            socketio = SocketIO(app, cors_allowed_origins="*")
        
        return socketio
    except Exception as e:
        # Fallback: create without specifying async_mode
        print(f"Warning: SocketIO async_mode failed ({e}), using auto-detection")
        return SocketIO(app, cors_allowed_origins="*")
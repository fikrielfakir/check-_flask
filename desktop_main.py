import threading
import time
import webview
from app import app

def run_flask():
    print("🚀 Starting Flask server...")
    app.run(host='127.0.0.1', port=8001, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)  # wait for server to start
    webview.create_window("Gestion de Chèques", "http://127.0.0.1:8001", width=1920, height=800)
    webview.start(debug=False)

    # THIS is what was missing:
    webview.start(debug=False, gui='qt')  # Use 'qt' or 'tk' depending on your system

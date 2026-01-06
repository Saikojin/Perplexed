import os
import sys
import threading
import uvicorn
import webview
import socket
import time

# Handle path resolution for both dev and PyInstaller environment
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    # In PyInstaller v6+, contents are in _internal for one-dir mode
    base_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(base_dir, '_internal')
    if os.path.exists(internal_dir):
        base_dir = internal_dir
    elif hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
else:
    # Running in a normal Python environment
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Add the base dir (app root) and backend dir to sys.path
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "backend"))

from backend.main import app

def get_free_port():
    # Helper to find a free port if 8000 is taken, or just sticky to 8000 for dev consistency
    return 8000

PORT = get_free_port()

def start_server():
    # Run the uvicorn server programmatically
    # log_level="error" suppresses the banner to keep console clean
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")

def main():
    print(f"Starting Perplexed Launcher on port {PORT}...")
    
    # Start the server in a separate daemon thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Wait a moment for server to spin up
    max_retries = 20
    server_ready = False
    for i in range(max_retries):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.1):
                server_ready = True
                break
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)
            
    if not server_ready:
        print("Server failed to start in time. Check logs.")
        # We continue anyway, webview might show connection error page which is debuggable
    
    # Create the native window pointing to our local server
    webview.create_window(
        title="Roddle - Riddle Master", 
        url=f"http://127.0.0.1:{PORT}/", 
        width=1200, 
        height=900, 
        resizable=True,
        background_color='#1a1a1a' # Dark mode bg
    )
    
    # Start the GUI loop
    webview.start()

if __name__ == '__main__':
    main()

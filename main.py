import sys
import os
import ctypes
import subprocess
import atexit
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

LIBRE = False



from config import SPEAKER_NAME

# Import the GUI class
from frontend.gui import SpotifyGUI

# Global variable to hold the background process
librespot_process = None

def start_librespot():
    """Starts librespot in the background with specific arguments."""
    global librespot_process
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(base_dir, "auth_cache")

    # Ensure cache directory exists
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)

    # COMMAND: librespot -n "My PC Speaker" -c "auth_cache" -b 160 --autoplay on
    cmd = f'librespot -n {SPEAKER_NAME} -c "auth_cache" -b 160 --autoplay on'

    try:
        # Configure startup info to HIDE the console window on Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        print(f"Starting Librespot: {cmd}")
        librespot_process = subprocess.Popen(
            cmd, 
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL, # Hide output (optional)
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"Failed to start librespot: {e}")

def cleanup():
    """Kills the background process when the app closes."""
    global librespot_process
    if librespot_process:
        print("Stopping Librespot...")
        librespot_process.terminate()
        librespot_process = None

# --- MAIN EXECUTION ---

# Define the App ID so Windows Taskbar treats it as a real app
myappid = 'mycompany.redify.player.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if __name__ == "__main__":
    # 1. Start Librespot Background Service
    if LIBRE == True:
        start_librespot()
    
    # 2. Register cleanup function (runs when you close the window)
    atexit.register(cleanup)

    # 3. Start GUI
    app = QApplication(sys.argv)
    
    # Set Global Font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set App Icon
    basedir = os.path.dirname(__file__)
    icon_path = os.path.join(basedir, "assets", "logo.png")
    
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    window = SpotifyGUI()
    window.show()
    
    # 4. Run App Loop
    exit_code = app.exec()
    
    # 5. Cleanup on manual exit
    cleanup()
    sys.exit(exit_code)
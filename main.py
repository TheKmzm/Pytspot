import sys
import os
import ctypes
import subprocess
import atexit
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

LIBRE = True



from backend.config import SPEAKER_NAME

# Import the GUI class
from frontend.gui import SpotifyGUI
from spotify_agent.run_spotify import spotify_process


def cleanup_sp():
    sp.cleanup()





# --- MAIN EXECUTION ---

# Define the App ID so Windows Taskbar treats it as a real app
myappid = 'mycompany.redify.player.1.0' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if __name__ == "__main__":
    # 1. Start Librespot Background Service
    sp = spotify_process()
    if LIBRE == True:
        sp.start_libre(SPEAKER_NAME)
    
    # 2. Register cleanup function (runs when you close the window)
    
    atexit.register(cleanup_sp)

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
    cleanup_sp
    sys.exit(exit_code)
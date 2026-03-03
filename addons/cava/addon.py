import subprocess
import platform
import os
from PyQt6.QtWidgets import QMessageBox

class CavaAddon:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Cava Visualizer"
        self.icon = "📊"

    def on_click(self):
        """Launches the Cava audio visualizer."""
        
        system = platform.system()
        
        try:
            if system == "Windows":
                # On Windows, assuming cava.exe is in the system PATH
                # creationflags=subprocess.CREATE_NEW_CONSOLE opens it in a new window
                subprocess.Popen(["cava"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                
            elif system == "Linux":
                # On Linux, try to open it in a common terminal emulator
                terminals = ["gnome-terminal", "konsole", "xfce4-terminal", "alacritty", "kitty", "xterm"]
                launched = False
                
                for term in terminals:
                    try:
                        # e.g., gnome-terminal -- cava
                        subprocess.Popen([term, "-e", "cava"])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                
                if not launched:
                    raise Exception("Could not find a supported terminal to launch Cava.")
                    
            elif system == "Darwin": # macOS
                # macOS uses Terminal.app
                subprocess.Popen(["open", "-a", "Terminal", "cava"])
                
        except FileNotFoundError:
            # This happens if 'cava' is not installed or not in the PATH
            self.show_error("Cava is not installed or not in your system PATH.\n\n"
                            "Please install Cava first.\n"
                            "See: https://github.com/karlstav/cava")
        except Exception as e:
            self.show_error(f"Failed to launch Cava:\n{e}")

    def show_error(self, message):
        msg = QMessageBox(self.app)
        msg.setWindowTitle("Cava Visualizer Error")
        msg.setText(message)
        msg.setStyleSheet("background-color: #222; color: white;")
        msg.exec()

def setup_addon(main_app):
    return CavaAddon(main_app)
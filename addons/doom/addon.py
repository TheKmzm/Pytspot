import sys
import webbrowser
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QUrl

# Vypíšeme si cestu, abychom měli jistotu, že jsme ve správném prostředí
print(f"Spouštím z prostředí: {sys.executable}")

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except Exception as e:
    # Nyní odchytíme JAKOUKOLIV chybu a vypíšeme ji, abychom věděli, co je špatně!
    print(f"POZOR: WebEngine se nenačetl kvůli chybě: {e}")
    WEB_ENGINE_AVAILABLE = False

class DoomWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DOOM (1993)")
        self.resize(1024, 768)
        self.setStyleSheet("background-color: black;")
        
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Zde už máme jistotu, že WebEngine existuje (ošetřeno v on_click)
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://silentspacemarine.com/"))
        layout.addWidget(self.web_view)
        
        btn_close = QPushButton("🛑 UKONČIT DOOM")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #8B0000; 
                color: white; 
                font-weight: 900; 
                font-size: 16px;
                padding: 15px;
                border: none;
            }
            QPushButton:hover { background-color: #FF0000; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class DoomAddon:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Play DOOM"
        self.icon = "🔥"

    def on_click(self):
        try:
            if self.app.current_player_source == "local":
                self.app.radio_player.pause()
                self.app.btn_play.setIcon(self.app.btn_play.icon())
            else:
                self.app.client.pause_playback()
        except:
            pass 

        print(f"Stav WEB_ENGINE_AVAILABLE je: {WEB_ENGINE_AVAILABLE}")
        
        if WEB_ENGINE_AVAILABLE:
            self.doom_window = DoomWindow(self.app)
            self.doom_window.exec()
        else:
            msg = QMessageBox(self.app)
            msg.setWindowTitle("Chybí WebEngine")
            msg.setText("Chybí modul pro spuštění hry přímo v okně aplikace.\n\n"
                        "Zkontroluj konzoli pro přesnou chybovou hlášku!\n\n"
                        "Pro hraní uvnitř aplikace zkontroluj instalaci:\n"
                        "pip install PyQt6-WebEngine")
            msg.setStyleSheet("background-color: #222; color: white;")
            msg.exec()
            webbrowser.open("https://silentspacemarine.com/")

def setup_addon(main_app):
    return DoomAddon(main_app)
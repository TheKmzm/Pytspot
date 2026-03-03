import webbrowser
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QUrl

# Pokusíme se načíst webový engine. Pokud chybí, nespadne celá aplikace.
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False

class DoomWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DOOM (1993)")
        self.resize(1024, 768) # Pořádné okno pro hraní
        self.setStyleSheet("background-color: black;")
        
        # Odstraníme klasické okraje pro víc "imersivní" zážitek
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Vložený prohlížeč
        self.web_view = QWebEngineView()
        # Použijeme známý a spolehlivý open-source webový port Doomu
        self.web_view.setUrl(QUrl("https://silentspacemarine.com/"))
        layout.addWidget(self.web_view)
        
        # Tlačítko pro ukončení (protože jsme skryli systémový křížek)
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
        self.icon = "🔥" # Tematická ikonka

    def on_click(self):
        """Spustí se při kliknutí na tlačítko v liště."""
        
        # 1. Pauzneme aktuální hudbu (ať už hraje Spotify nebo Lokální)
        try:
            if self.app.current_player_source == "local":
                self.app.radio_player.pause()
                self.app.btn_play.setIcon(self.app.btn_play.icon()) # Update ikony v GUI
            else:
                self.app.client.pause_playback()
        except:
            pass # Ignorujeme, pokud už je pauznuto

        # 2. Spustíme DOOM
        if WEB_ENGINE_AVAILABLE:
            self.doom_window = DoomWindow(self.app)
            self.doom_window.exec()
        else:
            # Fallback: Pokud uživatel nenainstaloval QtWebEngine
            msg = QMessageBox(self.app)
            msg.setWindowTitle("Chybí WebEngine")
            msg.setText("Chybí modul pro spuštění hry přímo v okně aplikace.\n\n"
                        "Hra se nyní otevře ve tvém výchozím prohlížeči.\n\n"
                        "Pro hraní uvnitř aplikace napiš do terminálu:\n"
                        "pip install PyQt6-WebEngine")
            msg.setStyleSheet("background-color: #222; color: white;")
            msg.exec()
            webbrowser.open("https://silentspacemarine.com/")

# Tuto funkci AddonManager hledá a volá, aby addon zaregistroval
def setup_addon(main_app):
    return DoomAddon(main_app)
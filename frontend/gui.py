import sys
import os
import requests
import datetime
import numpy as np
import random
import webbrowser # For Lyrics

if __name__ == "__main__":
    print("Wrong file ;)")
    sys.exit(0)

# GUI Imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QListWidget, QListWidgetItem, QSlider, QFrame, 
                             QStackedWidget, QComboBox, QMenu, QScrollArea, QGridLayout,
                             QCheckBox, QFormLayout,QDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QPixmap, QIcon, QAction, QCursor, QImage

# Multimedia Imports (For Radio)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioBuffer, QAudioBufferOutput, QAudioFormat

# Local Imports
from backend.core import SpotifyClient
from backend.youtube import YouTubeClient
from backend.soundcloud import SoundCloudClient
from backend.settings import SettingsManager
from backend.lyrics import GeniusClient # Add this
from backend.hotkeys import GlobalHotkeys
from backend.addon_manager import AddonManager


# Importujeme THEMES a generátor stylů
from frontend.styles import get_stylesheet, THEMES

try:
    from config import SPEAKER_NAME, increment_version
    VERSION = str(increment_version())
except ImportError:
    print("Fallback")
    SPEAKER_NAME = "My PC Speaker" # Fallback
    VERSION = "0.111"


# PATH TO ASSETS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

try:
    import pyjokes
except ImportError:
    pyjokes = None 

# --- THREADS ---


# --- LYRICS WORKER THREAD ---
class LyricsLoader(QThread):
    lyrics_ready = pyqtSignal(str)
    
    def __init__(self, title, artist):
        super().__init__()
        self.title = title
        self.artist = artist
        self.client = GeniusClient()

    def run(self):
        lyrics = self.client.get_lyrics(self.title, self.artist)
        self.lyrics_ready.emit(lyrics)

# --- LYRICS WINDOW (POP-UP) ---
class LyricsWindow(QDialog):
    def __init__(self, title, artist, theme_accent):
        super().__init__()
        self.setWindowTitle(f"Lyrics: {title}")
        self.resize(500, 700)
        self.setStyleSheet("background-color: #121212; color: white;")
        
        layout = QVBoxLayout(self)
        
        # Header
        lbl_title = QLabel(f"{title}\nby {artist}")
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {theme_accent}; margin-bottom: 10px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        # Scroll Area for long text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        self.lbl_text = QLabel("Fetching lyrics from Genius...")
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("font-size: 16px; line-height: 1.6; color: #ddd; padding: 10px;")
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center aligned lyrics look better
        self.lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) # Allow copying text
        
        content_layout.addWidget(self.lbl_text)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: #222; 
                color: {theme_accent}; 
                border: 1px solid {theme_accent}; 
                padding: 10px; 
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {theme_accent}; color: white; }}
        """)
        layout.addWidget(btn_close)

    def set_lyrics(self, text):
        self.lbl_text.setText(text)

class FactLoader(QThread):
    fact_loaded = pyqtSignal(str)
    def run(self):
        try:
            url = "https://uselessfacts.jsph.pl/random.json?language=en"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.fact_loaded.emit(response.json()['text'])
            else:
                self.fact_loaded.emit("Could not fetch fact.")
        except:
            self.fact_loaded.emit("Internet connection required for facts.")

class IconDownloader(QThread):
    icon_ready = pyqtSignal(QListWidgetItem, QIcon)
    def __init__(self, url, item):
        super().__init__()
        self.url = url
        self.item = item
    def run(self):
        try:
            if self.url:
                data = requests.get(self.url).content
                image = QImage()
                image.loadFromData(data)
                pixmap = QPixmap.fromImage(image).scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.icon_ready.emit(self.item, QIcon(pixmap))
        except: pass

class ImageLoader(QThread):
    image_loaded = pyqtSignal(QPixmap)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            if self.url:
                data = requests.get(self.url).content
                image = QImage()
                image.loadFromData(data)
                self.image_loaded.emit(QPixmap.fromImage(image))
        except: pass

# --- MAIN WINDOW ---

class SpotifyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Load Settings First
        self.settings = SettingsManager()
        
        self.setWindowTitle(f"Redify {VERSION}")
        self.resize(1200, 800)
        
        self.setMinimumSize(900, 600)
        
        # 2. Apply Theme based on settings
        self.apply_theme()

        # State Variables
        self.active_context_uri = None
        self.artist_current_track_list = []
        self.recent_track_list = []
        self.current_track_uri = ""
        self.is_dragging_seek = False
        self.current_duration = 0
        self.icon_threads = [] 
        self.current_player_source = "spotify"

        # --- LIVE RADIO SETUP ---
        self.radio_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.radio_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        
        self.radio_stations = [
            {"name": "Proglas", "url": "http://icecast2.play.cz/proglas128", "color": "#6A1B9A"},
            {"name": "ČR 2 – Praha", "url": "https://api.play.cz/radio/cro2-128.mp3.m3u", "color": "#1565C0"},
            {"name": "Impuls", "url": "http://icecast5.play.cz/impuls128.mp3", "color": "#E53935"},
            {"name": "Dechovka", "url": "http://icecast5.play.cz/dechovka128.mp3", "color": "#8D6E63"},
            {"name": "Krokodýl", "url": "http://icecast4.play.cz/krokodyl128.mp3", "color": "#2E7D32"},
            {"name": "Club Rádio", "url": "http://www.play.cz/radio/clubradio128.mp3.m3u", "color": "#512DA8"},
            {"name": "Kiss Hády", "url": "http://www.play.cz/radio/kisshady128.asx", "color": "#E6007E"},
            {"name": "Classic Praha", "url": "http://icecast8.play.cz/classic128.mp3", "color": "#424242"},
            {"name": "Hip Hop Vibes", "url": "http://mp3stream4.abradio.cz/hiphopvibes128.mp3", "color": "#000000"},
            {"name": "Rock Rádio", "url": "http://ice.abradio.cz/sumava128.mp3", "color": "#212121"},
            {"name": "Fajn Rádio", "url": "http://ice.abradio.cz/fajn128.mp3", "color": "#FF6600"},
            {"name": "Blaník", "url": "http://ice.abradio.cz/blanikfm128.mp3", "color": "#1976D2"},
            {"name": "Rádio Humor", "url": "http://mp3stream4.abradio.cz/humor128.mp3", "color": "#FBC02D"},
            {"name": "FM Plus", "url": "http://ice.abradio.cz/fmplus128.mp3", "color": "#009688"},
            {"name": "Fun Rádio", "url": "http://stream.funradio.sk:8000/fun128.mp3.m3u", "color": "#D32F2F"},
            {"name": "Rádio Jih", "url": "http://www.play.cz/radio/jih128.asx", "color": "#388E3C"},
            {"name": "Rádio Jih – Cimbálka", "url": "http://www.play.cz/radio/jihcimbalka128.asx", "color": "#6D4C41"},
            {"name": "Evropa 2", "url": "https://ice.actve.net/fm-evropa2-128", "color": "#005EB8"},
            {"name": "Rádio Slovensko", "url": "http://live.slovakradio.sk:8000/Slovensko_128.mp3", "color": "#C62828"},

            {"name": "ČRo Jazz", "url": "https://api.play.cz/radio/crojazz256.mp3.m3u", "color": "#4E342E"},
            {"name": "ČRo Plus", "url": "https://api.play.cz/radio/croplus128.mp3.m3u", "color": "#283593"},
            {"name": "Rádio Regina BB", "url": "http://live.slovakradio.sk:8000/Regina_BB_128.mp3", "color": "#455A64"},
            {"name": "ČRo Radiožurnál", "url": "http://icecast8.play.cz:8000/cro1-128.mp3", "color": "#E30613"},
            {"name": "Frekvence 1", "url": "https://ice.actve.net/fm-frekvence1-128", "color": "#FFD600"},
            {"name": "Country Rádio", "url": "https://icecast4.play.cz/country128.mp3", "color": "#795548"},
            {"name": "Kiss Rádio Proton", "url": "https://icecast1.play.cz/kissproton128.mp3", "color": "#AD1457"},
            {"name": "Radio Spin", "url": "https://icecast4.play.cz/spin128.mp3", "color": "#000000"},
            {"name": "ČRo Radio Wave", "url": "https://rozhlas.stream/wave_mp3_128.mp3", "color": "#00ACC1"},
            {"name": "DAB Plus Top 40", "url": "https://icecast6.play.cz/dabplus-top40.mp3", "color": "#EC407A"},
            {"name": "Radio Relax", "url": "https://icecast7.play.cz/relax128.mp3", "color": "#81C784"},
            {"name": "Radio Haná", "url": "https://icecast8.play.cz/hana128.mp3", "color": "#FB8C00"},
            {"name": "BBC World Service", "url": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service", "color": "#B80000"}
        ]

        # Initialize Backend
        try:
            self.client = SpotifyClient()
            print("Backend connected.")
        except Exception as e:
            print(f"Backend Error: {e}")
        
        
        
        
        # --- GLOBAL HOTKEYS ---
        self.hotkeys_thread = GlobalHotkeys()
        self.hotkeys_thread.on_play_pause.connect(self.toggle_play) # Napojíme na naši chytrou funkci
        self.hotkeys_thread.on_next.connect(self.client.next_track) # Nebo vytvořit chytrou funkci pro next
        self.hotkeys_thread.on_prev.connect(self.client.previous_track)
        self.hotkeys_thread.start()
        

        # Initialize Extra Clients
        self.sc_client = SoundCloudClient()
        self.yt_client = YouTubeClient()

        self.setup_ui()
        
        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playback_state)
        self.timer.start(1000)

        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.auto_refresh_queue)
        self.queue_timer.start(5000)
        
        # Auto Connect (Wait 4s for backend to boot)
        QTimer.singleShot(4000, self.attempt_auto_connect)

    # --- HELPERS ---
    def get_current_accent(self):
        """Helper to get the current accent color hex code."""
        theme_name = self.settings.get("theme")
        return THEMES.get(theme_name, THEMES["Red"])["accent"]

    def attempt_auto_connect(self):
        """Tries to find the specific speaker and transfer playback to it."""
        print(f"Attempting auto-connect to: {SPEAKER_NAME}...")
        try:
            devices = self.client.get_devices()
            for dev in devices:
                if dev['name'] == SPEAKER_NAME:
                    print(f"Device found! Transferring to {dev['name']}")
                    self.client.transfer_playback(dev['id'])
                    try: self.client.set_volume(self.settings.get("default_volume")) 
                    except: pass
                    return
            print("Target device not found (yet).")
        except Exception as e:
            print(f"Auto-connect error: {e}")

    def play_radio_station(self, url, name):
        """Switches from Spotify mode to Radio mode."""
        print(f"Switching to Radio: {name}")
        try: self.client.pause_playback()
        except: pass
        
        self.radio_player.setSource(QUrl(url))
        self.radio_player.play()
        
        self.track_label.setText(f"📡 {name}")
        self.artist_label.setText("Live Stream")
        self.btn_play.setText("⏸")
        
        # Use dynamic accent color
        accent = self.get_current_accent()
        self.album_art_label.setStyleSheet(f"background-color: {accent};")

    def stop_radio_if_playing(self):
        if self.radio_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.radio_player.stop()

    def open_lyrics(self):
        """Opens a local dialog window with lyrics fetched from Genius."""
        
        # 1. Determine Song Data based on Source
        title = "Unknown"
        artist = "Unknown"

        if self.current_player_source == "spotify":
            current = self.client.get_current_song_info()
            if current:
                title = current['name']
                artist = current['artist']
        
        elif self.current_player_source == "local":
            # For local (YT/SC/Radio), we parse the UI labels
            title = self.track_label.text()
            # Artist label often has icons like "☁️ Artist", we need to clean it
            raw_artist = self.artist_label.text()
            artist = raw_artist.replace("☁️ ", "").replace("YouTube • ", "").replace("Live Stream", "")

        if title == "Not Playing":
            print("Nothing playing.")
            return

        # 2. Open the Window
        accent = self.get_current_accent()
        self.lyrics_window = LyricsWindow(title, artist, accent)
        
        # 3. Start Background Thread to Fetch Text
        self.lyrics_loader = LyricsLoader(title, artist)
        self.lyrics_loader.lyrics_ready.connect(self.lyrics_window.set_lyrics)
        self.lyrics_loader.start()
        
        # 4. Show Window
        self.lyrics_window.exec()

    # --- UI SETUP ---

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOP AREA (Sidebar + Content) ---
        top_area = QWidget()
        top_layout = QHBoxLayout(top_area)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # 1. SIDEBAR
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #000000;")
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 15, 8, 0)
        sidebar_layout.setSpacing(2)
        
        # --- FIX: DYNAMIC LOGO COLOR ---
        accent = self.get_current_accent()
        logo = QLabel(f" Redify {VERSION}")
        logo.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {accent}; margin-bottom: 10px;")
        sidebar_layout.addWidget(logo)
        
        # Nav Buttons
        btn_home = QPushButton("🏠  Home")
        btn_home.setObjectName("NavBtn")
        btn_search = QPushButton("🔍  Search")
        btn_search.setObjectName("NavBtn")
        btn_queue = QPushButton("sz  Queue")
        btn_queue.setObjectName("NavBtn")
        btn_recent = QPushButton("🕒  Recent")
        btn_recent.setObjectName("NavBtn")
        btn_radio = QPushButton("📻  Live Radio")
        btn_radio.setObjectName("NavBtn")
                
        btn_settings = QPushButton("⚙️  Settings")
        btn_settings.setObjectName("NavBtn")
        
        btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_search.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_queue.clicked.connect(self.load_queue_page)
        btn_recent.clicked.connect(self.load_recently_played)
        btn_radio.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(7))
        
        sidebar_layout.addWidget(btn_home)
        sidebar_layout.addWidget(btn_search)
        sidebar_layout.addWidget(btn_queue)
        sidebar_layout.addWidget(btn_recent)
        sidebar_layout.addWidget(btn_radio)
        sidebar_layout.addWidget(btn_settings)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #282828; margin: 10px 0;")
        sidebar_layout.addWidget(line)

        lbl = QLabel("YOUR LIBRARY")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; margin: 5px;")
        sidebar_layout.addWidget(lbl)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("SidebarList")
        self.playlist_list.setIconSize(QSize(20, 20)) 
        self.playlist_list.itemClicked.connect(self.open_playlist_in_view)
        
        self.load_playlists()
        sidebar_layout.addWidget(self.playlist_list)
        top_layout.addWidget(sidebar)


        # --- ZDE JE ZMĚNA: 2. CENTRAL AREA (Addon Bar + Stack) ---
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # A) Addon Top Bar (Horní panel pro moduly)
        self.addon_bar_widget = QWidget()
        self.addon_bar_widget.setStyleSheet("background-color: #121212; border-bottom: 1px solid #282828;")
        self.addon_bar_widget.setFixedHeight(50)
        
        self.addon_bar = QHBoxLayout(self.addon_bar_widget)
        self.addon_bar.setContentsMargins(20, 0, 20, 0)
        self.addon_bar.setSpacing(10)
        
        # B) Samotný obsah (stránky)
        self.stack = QStackedWidget()
        self.setup_home_page()
        self.setup_search_page()
        self.setup_playlist_page()
        self.setup_artist_page()
        self.setup_queue_page()
        self.setup_saved_page()
        self.setup_radio_page()
        self.setup_settings_page()

        # Složení centrální části
        central_layout.addWidget(self.addon_bar_widget)
        central_layout.addWidget(self.stack)
        top_layout.addWidget(central_widget) # Změna: přidáváme central_widget, ne stack přímo

        main_layout.addWidget(top_area)

        # --- BOTTOM PLAYER BAR ---
        self.setup_player_bar(main_layout)
        
        # --- NAČTENÍ ADDONŮ ---
        self.addon_manager = AddonManager(self)
        self.addon_manager.load_addons()
        self.populate_addon_bar()

    def populate_addon_bar(self):
        """Vygeneruje tlačítka v horním panelu podle načtených addonů."""
        accent = self.get_current_accent()
        
        for addon in self.addon_manager.addons:
            btn = QPushButton(f"{addon.icon}  {addon.name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Pěkný styl tlačítka
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #b3b3b3;
                    font-weight: bold;
                    border: 1px solid #333;
                    border-radius: 15px;
                    padding: 5px 15px;
                }}
                QPushButton:hover {{
                    color: white;
                    border: 1px solid {accent};
                    background: #222;
                }}
            """)
            btn.clicked.connect(addon.on_click)
            self.addon_bar.addWidget(btn)
            
        self.addon_bar.addStretch() # Odstrčí tlačítka doleva
        
        # Pokud nejsou žádné addony, můžeme horní lištu úplně schovat
        if not self.addon_manager.addons:
            self.addon_bar_widget.hide()
        

    # --- PAGE SETUP HELPERS ---
    
    def setup_home_page(self):
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        home_layout.setContentsMargins(40, 40, 40, 40)
        home_layout.setSpacing(20)

        # Accent color for this page
        accent = self.get_current_accent()

        # Greeting
        greeting_card = QFrame()
        greeting_card.setStyleSheet(f"background-color: #181818; border-radius: 15px; border-left: 5px solid {accent};")
        gc_layout = QVBoxLayout(greeting_card)
        hour = datetime.datetime.now().hour
        greeting = "Good Morning" if 5 <= hour < 12 else "Good Afternoon" if 12 <= hour < 18 else "Good Evening" if 18 <= hour < 22 else "Good Night" if 22 <= hour < 1 else "Time to go sleep, good Night!"
        user_name = "User"
        if hasattr(self.client, 'get_user_name'): user_name = self.client.get_user_name()
        
        lbl_greet = QLabel(f"{greeting}, {user_name}.")
        lbl_greet.setStyleSheet("font-size: 32px; font-weight: bold; color: white; border: none;")
        gc_layout.addWidget(lbl_greet)
        gc_layout.addWidget(QLabel("Ready to listen to something new?"))
        home_layout.addWidget(greeting_card)

        # Jokes/Facts Grid
        grid = QHBoxLayout()
        
        # JOKE CARD
        joke_card = QFrame()
        joke_card.setStyleSheet("background-color: #202020; border-radius: 15px; padding: 10px;")
        jc_layout = QVBoxLayout(joke_card)
        
        joke_header = QWidget()
        jh_layout = QHBoxLayout(joke_header)
        jh_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_joke_title = QLabel("🐍 PYTHON JOKE")
        lbl_joke_title.setStyleSheet(f"color: {accent}; font-weight: bold;")
        
        btn_refresh_joke = QPushButton("↻")
        btn_refresh_joke.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh_joke.setFixedWidth(30)
        btn_refresh_joke.setToolTip("New Joke")
        btn_refresh_joke.clicked.connect(self.refresh_joke)
        btn_refresh_joke.setStyleSheet("QPushButton { color: #888; border: none; font-size: 18px; font-weight: bold; } QPushButton:hover { color: white; }")
        
        jh_layout.addWidget(lbl_joke_title)
        jh_layout.addStretch()
        jh_layout.addWidget(btn_refresh_joke)
        jc_layout.addWidget(joke_header)
        
        self.lbl_joke = QLabel()
        self.lbl_joke.setWordWrap(True)
        self.lbl_joke.setStyleSheet("font-size: 18px; font-style: italic; color: #ddd; border: none;")
        self.lbl_joke.setAlignment(Qt.AlignmentFlag.AlignCenter)
        jc_layout.addWidget(self.lbl_joke)
        jc_layout.addStretch()
        self.refresh_joke()

        # FACT CARD
        fact_card = QFrame()
        fact_card.setStyleSheet("background-color: #202020; border-radius: 15px; padding: 10px;")
        fc_layout = QVBoxLayout(fact_card)
        
        fact_header = QWidget()
        fh_layout = QHBoxLayout(fact_header)
        fh_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_fact_title = QLabel("🌍 RANDOM FACT")
        lbl_fact_title.setStyleSheet(f"color: {accent}; font-weight: bold;")
        
        btn_refresh_fact = QPushButton("↻")
        btn_refresh_fact.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh_fact.setFixedWidth(30)
        btn_refresh_fact.setToolTip("New Fact")
        btn_refresh_fact.clicked.connect(self.refresh_fact)
        btn_refresh_fact.setStyleSheet("QPushButton { color: #888; border: none; font-size: 18px; font-weight: bold; } QPushButton:hover { color: white; }")
        
        fh_layout.addWidget(lbl_fact_title)
        fh_layout.addStretch()
        fh_layout.addWidget(btn_refresh_fact)
        fc_layout.addWidget(fact_header)
        
        self.lbl_fact = QLabel("Loading...")
        self.lbl_fact.setWordWrap(True)
        self.lbl_fact.setStyleSheet("font-size: 16px; color: #ddd; border: none;")
        self.lbl_fact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fc_layout.addWidget(self.lbl_fact)
        fc_layout.addStretch()
        self.refresh_fact()
        
        grid.addWidget(joke_card)
        grid.addWidget(fact_card)
        home_layout.addLayout(grid)
        
        # Actions
        btn_liked = QPushButton("❤️  Play Liked Songs")
        btn_liked.setStyleSheet(f"background-color: #282828; padding: 20px; border-radius: 10px; font-size: 16px;")
        btn_liked.clicked.connect(self.client.play_liked_songs)
        home_layout.addWidget(btn_liked)
        home_layout.addStretch()
        self.stack.addWidget(home_page)

    def refresh_joke(self):
        joke_text = "Install 'pyjokes' pip package."
        if pyjokes:
            try: joke_text = pyjokes.get_joke()
            except: joke_text = "No jokes found."
        if hasattr(self, 'lbl_joke'):
            self.lbl_joke.setText(f'"{joke_text}"')

    def refresh_fact(self):
        if hasattr(self, 'lbl_fact'):
            self.lbl_fact.setText("Loading...")
        self.fact_loader = FactLoader()
        self.fact_loader.fact_loaded.connect(lambda text: self.lbl_fact.setText(text))
        self.fact_loader.start()

    def setup_search_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 0)
        
        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Track", "Artist", "Album", "Playlist", "SoundCloud", "YouTube"])
        
        top.addWidget(self.search_input)
        top.addWidget(self.search_type_combo)
        
        self.search_results = QListWidget()
        self.search_results.setObjectName("SidebarList")
        self.search_results.itemClicked.connect(self.handle_search_click)
        self.search_results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_results.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addLayout(top)
        layout.addWidget(self.search_results)
        self.stack.addWidget(page)

    def setup_playlist_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- HEADER SECTION ---
        self.pl_header = QFrame()
        self.pl_header.setFixedHeight(280)
        # Gradient pozadí
        self.pl_header.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #404040, stop:1 #121212); border-bottom: 1px solid #333;")
        
        # Hlavní horizontální layout hlavičky
        hl = QHBoxLayout(self.pl_header)
        hl.setContentsMargins(40, 40, 40, 20)
        hl.setSpacing(30) 

        # 1. Obrázek (Vlevo)
        self.pl_art = QLabel()
        self.pl_art.setFixedSize(200, 200)
        self.pl_art.setScaledContents(True)
        # Nastavíme placeholder barvu
        self.pl_art.setStyleSheet("background-color: #222; border-radius: 5px;")
        
        # --- ZMĚNA ZDE ---
        # Získáme aktuální barvu tématu (např. červená, zelená...)
        accent = self.get_current_accent()

        # 2. Play Tlačítko (Uprostřed)
        self.btn_pl_play = QPushButton(" ▶")
        self.btn_pl_play.setFixedSize(60, 60)
        self.btn_pl_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pl_play.clicked.connect(self.play_current_playlist_context)
        
        # Nastavíme styl přímo s použitím barvy 'accent'#28
        self.btn_pl_play.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent}; 
                color: white; 
                border-radius: 30px; 
                font-size: 50px; 
                border: none;
                padding-bottom: 4px;
            }}
            QPushButton:hover {{
                background-color: white;
                color: {accent};
            }}
        """)
        # -----------------
        
        # 3. Info Sekce (Vpravo)
        info = QVBoxLayout()
        info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        info.setSpacing(5)

        self.pl_type_label = QLabel("PLAYLIST")
        self.pl_type_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ddd; background: transparent;")
        
        self.pl_title_label = QLabel("Loading...")
        self.pl_title_label.setStyleSheet("font-size: 48px; font-weight: 900; color: white; background: transparent;")
        self.pl_title_label.setWordWrap(True)
        
        self.pl_desc_label = QLabel("...")
        self.pl_desc_label.setStyleSheet("font-size: 14px; color: #b3b3b3; background: transparent;")
        
        info.addWidget(self.pl_type_label)
        info.addWidget(self.pl_title_label)
        info.addWidget(self.pl_desc_label)
        
        # Sestavení Layoutu
        hl.addWidget(self.pl_art)
        hl.addWidget(self.btn_pl_play)
        hl.addLayout(info)
        hl.addStretch() 

        layout.addWidget(self.pl_header)

        # --- FILTER & LIST SECTION ---
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 20, 40, 0)
        
        self.pl_filter_input = QLineEdit()
        self.pl_filter_input.setPlaceholderText("Filter playlist...")
        self.pl_filter_input.textChanged.connect(self.filter_playlist_items)
        cl.addWidget(self.pl_filter_input)
        
        self.pl_tracks_list = QListWidget()
        self.pl_tracks_list.setAlternatingRowColors(False) # True pro lepší čitelnost, nebo False pro čistý vzhled
        
        self.pl_tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pl_tracks_list.customContextMenuRequested.connect(self.show_context_menu)
        self.pl_tracks_list.itemDoubleClicked.connect(self.play_item)
        
        cl.addWidget(self.pl_tracks_list)
        layout.addWidget(content)
        self.stack.addWidget(page)

    def setup_artist_page(self):
        page = QWidget()
        page.setStyleSheet("background: #121212;")
        layout = QVBoxLayout(page)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.artist_scroll_content = QWidget()
        self.artist_layout = QVBoxLayout(self.artist_scroll_content)
        self.artist_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll.setWidget(self.artist_scroll_content)
        layout.addWidget(scroll)
        self.stack.addWidget(page)

    def setup_queue_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("UP NEXT QUEUE"))
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("SidebarList")
        layout.addWidget(self.queue_list)
        self.stack.addWidget(page)

    def setup_saved_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(QLabel("📌 SAVED FOR LATER (Local)"))
        
        self.saved_list = QListWidget()
        self.saved_list.setObjectName("SidebarList")
        self.saved_list.itemClicked.connect(self.handle_search_click)
        self.saved_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_list.customContextMenuRequested.connect(self.show_saved_context_menu)
        
        layout.addWidget(self.saved_list)
        self.stack.addWidget(page)

    def setup_radio_page(self):
        page = QWidget()
        # Main layout for the page (Title + Scroll Area)
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(30, 30, 30, 0)
        main_layout.setSpacing(20)

        # 1. Header
        header = QHBoxLayout()
        lbl_title = QLabel("📡  LIVE RADIO STATIONS")
        # Use dynamic accent color from settings
        accent = self.get_current_accent()
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {accent};")
        header.addWidget(lbl_title)
        header.addStretch()
        main_layout.addLayout(header)

        # 2. Scroll Area (The wrapper)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True) # Important: lets the inner widget resize
        scroll.setFrameShape(QFrame.Shape.NoFrame) # No ugly border
        scroll.setStyleSheet("background: transparent;") # Transparent background
        
        # 3. The Content Widget (Holds the grid)
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        
        # The Grid Layout
        grid = QGridLayout(content_widget)
        grid.setSpacing(20) # Space between cards
        grid.setContentsMargins(0, 0, 20, 20) # Right margin for scrollbar
        grid.setAlignment(Qt.AlignmentFlag.AlignTop) # Start from top, don't spread vertically

        # 4. Populate Grid
        columns = 4 # How many items per row?
        row, col = 0, 0
        
        for station in self.radio_stations:
            # Create Card Button
            btn = QPushButton(f"{station['name']}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(100) # Fixed height for uniform look
            
            # Card Style
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {station['color']};
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 12px;
                    text-align: center;
                    padding: 10px;
                    border: 2px solid transparent;
                }}
                QPushButton:hover {{
                    border: 2px solid white;
                    background-color: {station['color']}; /* Keep color, just add border */
                }}
            """)
            
            # Connect Logic
            # We use lambda with checked=False to handle the click signal correctly
            btn.clicked.connect(lambda checked=False, u=station['url'], n=station['name']: self.play_radio_station(u, n))
            
            # Add to Grid
            grid.addWidget(btn, row, col)
            
            # Grid Logic
            col += 1
            if col >= columns:
                col = 0
                row += 1

        # 5. Assemble
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        self.stack.addWidget(page)

    def setup_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 50, 50, 50)
        
        lbl_title = QLabel("⚙️  NASTAVENÍ APLIKACE")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(lbl_title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # 1. Téma
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(THEMES.keys())
        self.combo_theme.setCurrentText(self.settings.get("theme"))
        self.combo_theme.currentTextChanged.connect(self.save_and_apply_settings)
        
        # 2. Checkboxy
        #self.check_light = QCheckBox("☀️ Světlý režim (Light Mode)")
        #self.check_light.setChecked(self.settings.get("light_mode"))
        #self.check_light.toggled.connect(self.save_and_apply_settings)
        #nezapinat svetly rezim

        self.check_compact = QCheckBox("📉 Kompaktní zobrazení")
        self.check_compact.setChecked(self.settings.get("compact_mode"))
        self.check_compact.toggled.connect(self.save_and_apply_settings)

        self.check_ultra = QCheckBox("🤏 Ultra kompaktní knihovna (SideBar)")
        self.check_ultra.setChecked(self.settings.get("ultra_compact"))
        self.check_ultra.toggled.connect(self.save_and_apply_settings)

        self.check_scroll = QCheckBox("🚫 Skrýt posuvníky (Scrollbars)")
        self.check_scroll.setChecked(self.settings.get("hide_scrollbars"))
        self.check_scroll.toggled.connect(self.save_and_apply_settings)
        
        # Styling pro popisky
        lbl_style = "font-size: 14px; font-weight: bold;"
        lbl_col = QLabel("Barevné schéma:"); lbl_col.setStyleSheet(lbl_style)
        lbl_vis = QLabel("Vzhled:"); lbl_vis.setStyleSheet(lbl_style)

        form_layout.addRow(lbl_col, self.combo_theme)
        form_layout.addRow(QLabel("")) # Spacer
        #form_layout.addRow(lbl_vis, self.check_light)
        form_layout.addRow("", self.check_compact)
        form_layout.addRow("", self.check_ultra)
        form_layout.addRow("", self.check_scroll)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        layout.addWidget(QLabel(f"Redify v{VERSION}"))
        self.stack.addWidget(page)

    def save_and_apply_settings(self):
        """Uloží všechna nastavení a překreslí UI."""
        # Uložit hodnoty
        self.settings.set("theme", self.combo_theme.currentText())
        #self.settings.set("light_mode", self.check_light.isChecked())
        self.settings.set("compact_mode", self.check_compact.isChecked())
        self.settings.set("ultra_compact", self.check_ultra.isChecked())
        self.settings.set("hide_scrollbars", self.check_scroll.isChecked())
        
        # Aplikovat
        self.apply_theme()

    def apply_theme(self):
        """Načte config a přegeneruje CSS."""
        new_style = get_stylesheet(
            theme_name=self.settings.get("theme"),
            compact_mode=self.settings.get("compact_mode"),
            ultra_compact=self.settings.get("ultra_compact"),
            light_mode=self.settings.get("light_mode"),
            hide_scrollbars=self.settings.get("hide_scrollbars")
        )
        self.setStyleSheet(new_style)

    def setup_player_bar(self, main_layout):
        player_bar = QFrame()
        player_bar.setFixedHeight(95)
        # Hlavní lišta má pozadí a horní linku
        player_bar.setStyleSheet("background-color: #181818; border-top: 1px solid #333;")
        
        layout = QHBoxLayout(player_bar)
        layout.setContentsMargins(20, 5, 20, 5) 

        # --- LEFT INFO (Vlevo) ---
        left_container = QWidget()
        # TADY: Průhledné pozadí a žádný rám pro kontejner
        left_container.setStyleSheet("background: transparent; border: none;") 
        
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.album_art_label = QLabel()
        self.album_art_label.setFixedSize(56, 56)
        self.album_art_label.setScaledContents(True)
        self.album_art_label.setStyleSheet("background-color: #333; border: none; border-radius: 4px;")
        
        info = QVBoxLayout()
        info.setSpacing(0)
        info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.track_label = QLabel("Not Playing")
        self.track_label.setStyleSheet("background: transparent; border: none; color: white; font-weight: bold; font-size: 13px;")
        
        self.artist_label = QPushButton("")
        self.artist_label.clicked.connect(self.go_to_current_artist)
        self.artist_label.setStyleSheet("background: transparent; border: none; text-align: left; color: #b3b3b3; font-size: 11px; padding: 0px;")
        self.artist_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        info.addWidget(self.track_label)
        info.addWidget(self.artist_label)
        
        left_layout.addWidget(self.album_art_label)
        left_layout.addLayout(info)
        
        layout.addWidget(left_container)
        
        # --- PRUŽINA 1 ---
        layout.addStretch(1)

        # --- CENTER CONTROLS (Uprostřed) ---
        center_widget = QWidget()
        # TADY: Průhledné pozadí a žádný rám pro kontejner
        center_widget.setStyleSheet("background: transparent; border: none;")
        
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Řada tlačítek
        controls_row = QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(15) 
        controls_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_style = "background: transparent; border: none; outline: none;"

        self.btn_shuffle = QPushButton()
        self.btn_shuffle.setIcon(QIcon(os.path.join(ASSETS_DIR, "shuffle.png")))
        self.btn_shuffle.setIconSize(QSize(18, 18))
        self.btn_shuffle.setObjectName("ControlBtn")
        self.btn_shuffle.clicked.connect(self.toggle_shuffle_ui)
        self.btn_shuffle.setStyleSheet(btn_style)
        
        btn_prev = QPushButton()
        btn_prev.setIcon(QIcon(os.path.join(ASSETS_DIR, "prev.png")))
        btn_prev.setIconSize(QSize(20, 20))
        btn_prev.setObjectName("ControlBtn")
        btn_prev.clicked.connect(self.client.previous_track)
        btn_prev.setStyleSheet(btn_style)
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "play.png")))
        self.btn_play.setIconSize(QSize(38, 38))
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setObjectName("ControlBtn")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("background: transparent; border: none; outline: none; border-radius: 20px;")
        
        btn_next = QPushButton()
        btn_next.setIcon(QIcon(os.path.join(ASSETS_DIR, "next.png")))
        btn_next.setIconSize(QSize(20, 20))
        btn_next.setObjectName("ControlBtn")
        btn_next.clicked.connect(self.client.next_track)
        btn_next.setStyleSheet(btn_style)
        
        controls_row.addWidget(self.btn_shuffle)
        controls_row.addWidget(btn_prev)
        controls_row.addWidget(self.btn_play)
        controls_row.addWidget(btn_next)
        
        # 2. Slider
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setFixedWidth(800)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.seek_slider.sliderPressed.connect(self.seek_started)
        self.seek_slider.sliderReleased.connect(self.seek_finished)
        self.seek_slider.setStyleSheet("background: transparent; border: none;")
        
        center_layout.addLayout(controls_row)
        center_layout.addWidget(self.seek_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(center_widget)

        # --- PRUŽINA 2 ---
        layout.addStretch(1)

        # --- RIGHT EXTRA (Vpravo) ---
        right_container = QWidget()
        # TADY: Průhledné pozadí a žádný rám pro kontejner
        right_container.setStyleSheet("background: transparent; border: none;")
        
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        btn_lyrics = QPushButton()
        btn_lyrics.setIcon(QIcon(os.path.join(ASSETS_DIR, "microphone.png")))
        btn_lyrics.setToolTip("See Lyrics")
        btn_lyrics.clicked.connect(self.open_lyrics)
        btn_lyrics.setStyleSheet(btn_style)
        
        btn_saved = QPushButton()
        btn_saved.setIcon(QIcon(os.path.join(ASSETS_DIR, "bookmark.png")))
        btn_saved.clicked.connect(self.load_saved_page)
        btn_saved.setStyleSheet(btn_style)
        
        btn_device = QPushButton()
        btn_device.setIcon(QIcon(os.path.join(ASSETS_DIR, "devices.png")))
        btn_device.clicked.connect(self.show_device_menu)
        btn_device.setStyleSheet(btn_style)
        
        vol_slider = QSlider(Qt.Orientation.Horizontal)
        vol_slider.setFixedWidth(80)
        vol_slider.setRange(0, 100)
        vol_slider.setValue(70)
        vol_slider.sliderReleased.connect(lambda: self.set_master_volume(vol_slider.value()))
        vol_slider.setStyleSheet("background: transparent; border: none;")
        

        right_layout.addWidget(btn_lyrics)
        right_layout.addWidget(btn_saved)
        right_layout.addWidget(btn_device)
        right_layout.addWidget(vol_slider)
        
        layout.addWidget(right_container)
        
        main_layout.addWidget(player_bar)

    # --- ACTION HANDLERS ---

    def load_playlists(self):
        self.playlist_list.clear()
        playlists = self.client.get_user_playlists()
        for p in playlists:
            name = p.get('name', 'Unknown Playlist')
            item = QListWidgetItem(name)
            
            img = None
            images = p.get('images') 
            if images and isinstance(images, list) and len(images) > 0:
                img = images[0].get('url')

            owner = "Unknown"
            if p.get('owner'):
                owner = p['owner'].get('display_name', 'Unknown')

            item_data = {
                "name": name, "id": p.get('id'), "uri": p.get('uri'),
                "image": img, "type": "playlist", "owner": owner
            }
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.playlist_list.addItem(item)

    def open_playlist_in_view(self, item_widget):
        data = item_widget.data(Qt.ItemDataRole.UserRole)
        if not data: return
        
        # Bezpečné rozbalení dat
        if isinstance(data, str):
            playlist_id = data.split(":")[-1]
            name = "Playlist"
            uri = data
            image_url = None
            owner = "Spotify"
        else:
            playlist_id = data.get('id')
            name = data.get('name', 'Unknown')
            uri = data.get('uri')
            image_url = data.get('image')
            owner = data.get('owner', 'Unknown')

        print(f"[DEBUG] Opening Playlist: {name}, Image URL: {image_url}")

        # 1. Texty
        self.pl_title_label.setText(name)
        self.pl_desc_label.setText(f"Playlist • By {owner}")
        self.pl_type_label.setText("PLAYLIST")
        
        # 2. Obrázek (S FALLBACKEM)
        self.pl_art.clear()
        
        if image_url:
            self.pl_art_loader = ImageLoader(image_url)
            self.pl_art_loader.image_loaded.connect(lambda p: self.pl_art.setPixmap(p.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.pl_art_loader.start()
            self.icon_threads.append(self.pl_art_loader)
        else:
            # --- NÁHRADNÍ OBRÁZEK ---
            # Vytvoříme šedý čtverec s ikonou, pokud nemáme URL
            # Můžeš použít i QPixmap("assets/placeholder.png") pokud máš
            self.pl_art.setText("🎵") 
            self.pl_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pl_art.setStyleSheet("background-color: #333; color: #555; font-size: 80px; border-radius: 5px;")
        
        # 3. Skladby
        self.active_context_uri = uri
        self.pl_tracks_list.clear()
        
        if playlist_id:
            tracks = self.client.get_playlist_tracks(playlist_id)
            for t in tracks:
                item = QListWidgetItem(f"{t['name']}   •   {t['artist']}")
                item.setData(Qt.ItemDataRole.UserRole, {"name": t['name'], "artist": t['artist'], "uri": t['uri'], "type": "track", "image": t['image']})
                self.pl_tracks_list.addItem(item)
        
        self.stack.setCurrentIndex(2)

    def open_album_as_playlist(self, data):
        details = self.client.get_album_page(data['uri'])
        if not details: return
        
        self.pl_title_label.setText(details['name'])
        self.pl_desc_label.setText(f"Album • {details['artist']}")
        self.pl_type_label.setText("ALBUM")
        
        if details['image']:
             self.pl_art_loader = ImageLoader(details['image'])
             self.pl_art_loader.image_loaded.connect(lambda p: self.pl_art.setPixmap(p.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)))
             self.pl_art_loader.start()
             
        self.active_context_uri = data['uri']
        self.pl_tracks_list.clear()
        
        for t in details['tracks']:
            item = QListWidgetItem(f"{t['track_number']}.  {t['name']}")
            item.setData(Qt.ItemDataRole.UserRole, {"name": t['name'], "artist": details['artist'], "uri": t['uri'], "type": "track", "image": details['image']})
            self.pl_tracks_list.addItem(item)
        self.stack.setCurrentIndex(2)

    def filter_playlist_items(self, text):
        for i in range(self.pl_tracks_list.count()):
            item = self.pl_tracks_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def play_current_playlist_context(self):
        if self.active_context_uri:
            self.client.play_context(self.active_context_uri)
        elif self.pl_tracks_list.count() > 0:
            self.play_item(self.pl_tracks_list.item(0))

    def toggle_play(self):
        """Rozhodne, koho pauzovat/pustit podle aktivního zdroje."""
        
        if self.current_player_source == "local":
            # --- OVLÁDÁNÍ LOKÁLNÍHO PŘEHRÁVAČE (YT/SC/Radio) ---
            if self.radio_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.radio_player.pause()
                self.btn_play.setText("") # Nebo ikona Play
                self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "play.png")))
            else:
                self.radio_player.play()
                self.btn_play.setText("") # Nebo ikona Pause
                self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "pause.png")))
                
        else:
            # --- OVLÁDÁNÍ SPOTIFY ---
            self.client.play_pause()
            # UI se aktualizuje samo přes timer update_playback_state

    def update_playback_state(self):
        if self.is_dragging_seek: return

        title = ""
        artist = ""
        is_playing = False
        duration = 0
        progress = 0

        # --- A. LOKÁLNÍ PŘEHRÁVAČ ---
        if self.current_player_source == "local":
            if self.radio_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                is_playing = True
                title = self.track_label.text()
                # Vyčistíme jméno umělce od emotikonů
                artist = self.artist_label.text().replace("☁️ ", "").replace("YouTube • ", "")
                duration = self.radio_player.duration() / 1000 # na sekundy
                progress = self.radio_player.position() / 1000
                
                # Update slideru...
                if duration > 0:
                    self.seek_slider.setMaximum(int(duration * 1000))
                    self.seek_slider.setValue(int(progress * 1000))

        # --- B. SPOTIFY ---
        else:
            try:
                current = self.client.get_current_song_info()
                if current:
                    title = current['name']
                    artist = current['artist']
                    is_playing = current['is_playing']
                    duration = current['duration_ms'] / 1000
                    progress = current['progress_ms'] / 1000
                    
                    # ... (tvůj kód pro update slideru a labelů) ...
            except: pass

        # --- B. SPOTIFY REŽIM ---
        try:
            current = self.client.get_current_song_info()
            if not current: return
            
            # ... (tvůj stávající kód pro Spotify update) ...
            self.track_label.setText(current['name'])
            # ... atd ...
            
            if current['duration_ms'] > 0:
                self.seek_slider.setMaximum(current['duration_ms'])
                self.seek_slider.setValue(current['progress_ms'])
        except: pass

    def toggle_shuffle_ui(self):
        state = not getattr(self, "is_shuffle_active", False)
        self.client.toggle_shuffle(state)
        self.update_shuffle_visuals(state)

    def update_shuffle_visuals(self, is_active):
        self.is_shuffle_active = is_active
        accent = self.get_current_accent()
        color = accent if is_active else "transparent"
        self.btn_shuffle.setStyleSheet(f"background: transparent; border-bottom: 2px solid {color};")

    def perform_search(self):
        query = self.search_input.text()
        search_type_text = self.search_type_combo.currentText()
        stype = search_type_text.lower()
        
        if not query: return
        self.search_results.clear()
        
        results = []
        
        # --- ROZCESTNÍK HLEDÁNÍ ---
        if search_type_text == "SoundCloud":
            print(f"Searching SoundCloud: {query}")
            results = self.sc_client.search(query)
            
        elif search_type_text == "YouTube": 
            print(f"Searching YouTube: {query}")
            results = self.yt_client.search(query)
            
        else:
            # Spotify
            results = self.client.search(query, search_type=stype)
        # ---------------------------

        for item in results:
            text = f"{item['name']} - {item.get('artist', 'Unknown')}"
            li = QListWidgetItem(text)
            li.setData(Qt.ItemDataRole.UserRole, item)
            
            if item.get('type') == 'youtube':
                li.setText(f"🟥 {text}") 
            elif item.get('type') == 'soundcloud':
                li.setText(f"☁️ {text}")
            
            self.search_results.addItem(li)

    def handle_search_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if data['type'] == 'soundcloud':
            self.play_soundcloud_track(data['uri'])
            return
        elif data['type'] == 'youtube':
            self.play_youtube_track(data['uri'])
            return

        if data['type'] == 'track': self.client.play_uri(data['uri'])
        elif data['type'] == 'artist': self.open_artist_page(data['uri'])
        elif data['type'] == 'album': self.open_album_as_playlist(data)
        elif data['type'] == 'playlist': self.open_searched_playlist(data)
        elif data['type'] == 'track': self.client.play_uri(data['uri'])

    def play_item(self, item):
        """Spustí položku ze Spotify (Track, Album, Playlist)."""
        # 1. Zastavit lokální přehrávač (pokud běží rádio/YT)
        self.stop_radio_if_playing()
        
        # 2. PŘEPNOUT OVLÁDÁNÍ NA SPOTIFY
        self.current_player_source = "spotify"
        
        data = item.data(Qt.ItemDataRole.UserRole)
        track_uri = data['uri'] if isinstance(data, dict) else data
        
        idx = self.stack.currentIndex()
        # Logika pro kontext (pokud jsme uvnitř playlistu/alba)
        if idx == 2 and self.active_context_uri:
            self.client.play_track_in_context(track_uri, self.active_context_uri)
        elif idx == 3 and self.artist_current_track_list:
            self.client.play_list(self.artist_current_track_list, start_uri=track_uri)
        elif idx == 2 and hasattr(self, 'recent_track_list'): 
             self.client.play_list(self.recent_track_list, start_uri=track_uri)
        else:
            self.client.play_uri(track_uri)

    def play_youtube_track(self, video_url):
        """Vyřeší YouTube URL a spustí přehrávání."""
        print(f"Resolving YouTube Stream: {video_url}")
        
        # 1. Pauza Spotify
        try: self.client.pause_playback()
        except: pass
        
        # 2. PŘEPNOUT OVLÁDÁNÍ NA LOKÁLNÍ PŘEHRÁVAČ
        self.current_player_source = "local" 
        
        info = self.yt_client.get_stream_info(video_url)
        if info and info.get('stream_url'):
            self.radio_player.setSource(QUrl(info['stream_url']))
            self.radio_player.play()
            
            # Update UI
            self.track_label.setText(info['title'])
            self.artist_label.setText(f"YouTube • {info['artist']}")
            
            # Nastavit ikonu na Pause (protože hrajeme)
            self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "pause.png")))
            
            if info['thumbnail']:
                self.art_loader = ImageLoader(info['thumbnail'])
                self.art_loader.image_loaded.connect(lambda p: self.album_art_label.setPixmap(p))
                self.art_loader.start()
        else:
            print("Chyba: Nelze přehrát YouTube video.")

    def play_soundcloud_track(self, web_url):
        """Vyřeší SoundCloud URL a spustí přehrávání."""
        print(f"Resolving SoundCloud Stream: {web_url}")
        
        # 1. Pauza Spotify
        try: self.client.pause_playback()
        except: pass
        
        # 2. PŘEPNOUT OVLÁDÁNÍ NA LOKÁLNÍ PŘEHRÁVAČ
        self.current_player_source = "local"
        
        info = self.sc_client.get_stream_info(web_url)
        if info and info.get('stream_url'):
            self.radio_player.setSource(QUrl(info['stream_url']))
            self.radio_player.play()
            
            # Update UI
            self.track_label.setText(info['title'])
            self.artist_label.setText(f"☁️ {info['artist']}") 
            
            # Nastavit ikonu na Pause
            self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "pause.png")))
            
            if info['thumbnail']:
                self.art_loader = ImageLoader(info['thumbnail'])
                self.art_loader.image_loaded.connect(lambda p: self.album_art_label.setPixmap(p))
                self.art_loader.start()
        else:
            print("Could not resolve SoundCloud stream.")


    def show_context_menu(self, pos):
        sender = self.sender()
        item = sender.itemAt(pos)
        if not item: return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        uri = data['uri'] if isinstance(data, dict) else data

        # Získání aktuální barvy z nastavení
        accent = self.get_current_accent()

        menu = QMenu(self)
        
        # --- DYNAMICKÝ STYL ---
        # QMenu::item:selected zajistí, že když na položku najedeš myší,
        # podbarví se barvou, kterou máš v nastavení (červená, zelená, modrá...)
        menu.setStyleSheet(f"""
            QMenu {{ 
                background-color: #282828; 
                color: white; 
                border: 1px solid #444; 
                padding: 5px 0px;
            }}
            QMenu::item {{ 
                padding: 6px 20px; 
            }}
            QMenu::item:selected {{ 
                background-color: {accent}; 
                color: white; 
            }}
            QMenu::separator {{
                height: 1px;
                background: #444;
                margin: 5px 0px;
            }}
        """)
        
        # 1. Save to Local Library
        save = QAction("📌 Save for Later", self)
        save.triggered.connect(lambda: self.client.save_item_locally(data))
        menu.addAction(save)
        
        # 2. Add to Queue
        q = QAction("sz  Add to Queue", self)
        q.triggered.connect(lambda: self.client.add_to_queue(uri))
        menu.addAction(q)
        
        menu.addSeparator()

        # 3. ADD TO PLAYLIST (Submenu)
        # Zobrazíme jen pokud to není lokální soubor (YouTube/SoundCloud do Spotify playlistu nejde)
        is_spotify_track = True
        if isinstance(data, dict) and data.get('type') in ['youtube', 'soundcloud']:
            is_spotify_track = False

        if is_spotify_track:
            add_to_pl_menu = menu.addMenu("➕  Add to Playlist")
            
            playlists = self.client.get_user_playlists()
            if playlists:
                for pl in playlists:
                    pl_action = add_to_pl_menu.addAction(pl['name'])
                    # Lambda pro zachycení ID playlistu
                    pl_action.triggered.connect(lambda checked, pid=pl['id'], u=uri: self.add_to_playlist_handler(pid, u))
            else:
                dummy = add_to_pl_menu.addAction("No playlists found")
                dummy.setEnabled(False)
        else:
            disabled = menu.addAction("Add to Playlist (Spotify Only)")
            disabled.setEnabled(False)
        
        
        menu.exec(sender.mapToGlobal(pos))

    def show_saved_context_menu(self, pos):
        item = self.saved_list.itemAt(pos)
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet("background: #282828; color: white;")
        rem = QAction("❌ Remove", self)
        rem.triggered.connect(lambda: self.remove_saved_item(data['uri']))
        menu.addAction(rem)
        menu.exec(self.saved_list.mapToGlobal(pos))

    def remove_saved_item(self, uri):
        self.client.remove_item_locally(uri)
        self.load_saved_page()

    def go_to_current_artist(self):
        if hasattr(self, 'artist_id_for_link') and self.artist_id_for_link:
            self.open_artist_page(f"spotify:artist:{self.artist_id_for_link}")

    def load_queue_page(self):
        self.update_queue_ui()
        self.stack.setCurrentIndex(4)

    def auto_refresh_queue(self):
        if self.stack.currentIndex() == 4: self.update_queue_ui()

    def update_queue_ui(self):
        self.queue_list.clear()
        q = self.client.get_queue()
        if q and 'queue' in q:
            for t in q['queue']:
                self.queue_list.addItem(QListWidgetItem(f"{t['name']} - {t['artists'][0]['name']}"))

    def seek_started(self): self.is_dragging_seek = True
    
    def seek_finished(self):
        pos = self.seek_slider.value()
        
        if self.current_player_source == "local":
            # QMediaPlayer bere milisekundy
            self.radio_player.setPosition(pos)
        else:
            # Spotify
            self.client.seek_track(pos)
            
        self.is_dragging_seek = False

    def show_device_menu(self):
        menu = QMenu(self)
        # Use dynamic accent for border
        accent = self.get_current_accent()
        menu.setStyleSheet(f"background: #333; color: white; border: 1px solid {accent};")
        for dev in self.client.get_devices():
            a = QAction(f"{'🔊 ' if dev['is_active'] else ''}{dev['name']}", self)
            a.triggered.connect(lambda c, d=dev['id']: self.client.transfer_playback(d))
            menu.addAction(a)
        menu.exec(QCursor.pos())

    def open_artist_page(self, uri):
        aid = uri.split(":")[-1]
        data = self.client.get_artist_page(aid)
        if not data: return
        
        while self.artist_layout.count():
            item = self.artist_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        h = QWidget()
        hl = QHBoxLayout(h)
        img = QLabel()
        img.setFixedSize(150, 150)
        img.setScaledContents(True)
        if data['image']:
             il = ImageLoader(data['image'])
             il.image_loaded.connect(lambda p: img.setPixmap(p))
             il.start()
             self.icon_threads.append(il)
        hl.addWidget(img)
        lbl = QLabel(data['name'])
        lbl.setStyleSheet("font-size: 50px; font-weight: 900; color: white;")
        hl.addWidget(lbl)
        hl.addStretch()
        self.artist_layout.addWidget(h)
        
        self.artist_layout.addWidget(QLabel("TOP TRACKS"))
        tl = QListWidget()
        tl.setFixedHeight(250)
        tl.setStyleSheet("background: #181818; border-radius: 10px;")
        tl.itemDoubleClicked.connect(self.play_item)
        self.artist_current_track_list = []
        for t in data['top_tracks']:
            item = QListWidgetItem(t['name'])
            item.setData(Qt.ItemDataRole.UserRole, t['uri'])
            tl.addItem(item)
            self.artist_current_track_list.append(t['uri'])
        self.artist_layout.addWidget(tl)
        
        self.artist_layout.addWidget(QLabel("ALBUMS"))
        al = QListWidget()
        al.setFixedHeight(400)
        al.setStyleSheet("background: #181818;")
        al.itemClicked.connect(lambda i: self.open_album_as_playlist(i.data(Qt.ItemDataRole.UserRole)))
        for a in data['albums']:
            item = QListWidgetItem(f"{a['year']} • {a['name']}")
            item.setData(Qt.ItemDataRole.UserRole, a)
            al.addItem(item)
        self.artist_layout.addWidget(al)
        
        self.stack.setCurrentIndex(3)

    def open_searched_playlist(self, data):
        """Otevře playlist z výsledků hledání a načte obrázek."""
        self.active_context_uri = data['uri']
        
        # 1. Texty
        self.pl_title_label.setText(data['name'])
        owner = data.get('owner', 'Spotify')
        self.pl_desc_label.setText(f"Playlist • By {owner}")
        self.pl_type_label.setText("PLAYLIST")

        # 2. Obrázek (To tu chybělo)
        image_url = data.get('image')
        self.pl_art.clear()
        self.pl_art.setStyleSheet("background-color: #222; border-radius: 5px;")
        
        if image_url:
            self.pl_art_loader = ImageLoader(image_url)
            self.pl_art_loader.image_loaded.connect(lambda p: self.pl_art.setPixmap(p.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.pl_art_loader.start()
            self.icon_threads.append(self.pl_art_loader)

        # 3. Načíst skladby
        self.pl_tracks_list.clear()
        print(f"Fetching tracks for playlist: {data['name']}")
        tracks = self.client.get_playlist_tracks(data['id'])
        
        for t in tracks:
            item = QListWidgetItem(f"{t['name']}   •   {t['artist']}")
            # Ukládáme plná data pro přehrávání
            full_data = {
                "name": t['name'],
                "artist": t['artist'],
                "uri": t['uri'],
                "type": "track",
                "image": t['image']
            }
            item.setData(Qt.ItemDataRole.UserRole, full_data)
            self.pl_tracks_list.addItem(item)
            
        self.stack.setCurrentIndex(2)

    def load_recently_played(self):
        tracks = self.client.get_recently_played()
        self.pl_title_label.setText("Recently Played")
        self.pl_tracks_list.clear()
        self.active_context_uri = None
        self.recent_track_list = []
        for t in tracks:
            item = QListWidgetItem(f"{t['name']} - {t['artist']}")
            item.setData(Qt.ItemDataRole.UserRole, t['uri'])
            self.pl_tracks_list.addItem(item)
            self.recent_track_list.append(t['uri'])
        self.stack.setCurrentIndex(2)

    def load_saved_page(self):
        self.saved_list.clear()
        items = self.client.get_saved_items()
        
        for item in items:
            itype = item.get('type', 'track')
            icon_char = "🎵"
            if itype == 'artist': icon_char = "🎤"
            elif itype == 'playlist': icon_char = "📜"
            elif itype == 'album': icon_char = "💿"
            
            artist = item.get('artist', 'Unknown')
            name = item.get('name', 'Unknown')
            
            text = f"{icon_char}  {name} - {artist}"
            
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item) 
            self.saved_list.addItem(list_item)
            
        self.stack.setCurrentIndex(5)

    def set_master_volume(self, value):
        """Nastaví hlasitost buď pro Spotify nebo pro lokální přehrávač."""
        print(f"Volume: {value}% ({self.current_player_source})")
        
        # 1. Vždy nastavíme Spotify (pro jistotu, aby neřvalo, když přepneme)
        try: self.client.set_volume(value)
        except: pass

        # 2. Nastavíme Lokální přehrávač (Qt6 bere float 0.0 - 1.0)
        float_val = value / 100.0
        self.audio_output.setVolume(float_val)

    def smart_next(self):
        if self.current_player_source == "local":
            # U YouTube/Radia můžeme třeba posunout o 10s
            pos = self.radio_player.position()
            self.radio_player.setPosition(pos + 10000)
        else:
            self.client.next_track()

    def smart_prev(self):
        if self.current_player_source == "local":
            pos = self.radio_player.position()
            self.radio_player.setPosition(max(0, pos - 10000))
        else:
            self.client.previous_track()

    # --- Helper funkce pro zpracování přidání ---
    def add_to_playlist_handler(self, playlist_id, track_uri):
        """Zavolá backend a vypíše výsledek."""
        success = self.client.add_track_to_playlist(playlist_id, track_uri)
        if success:
            print(f"Úspěšně přidáno do playlistu: {playlist_id}")
            # Zde by se hodilo třeba malé vyskakovací okno "Added!", ale print stačí
        else:
            print("Chyba při přidávání.")


    def play_local_file_from_list(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        path = data['path']
        
        print(f"Playing Local File: {path}")
        
        # 1. Pauza Spotify
        try: self.client.pause_playback()
        except: pass
        
        # 2. Nastavit lokální režim
        self.current_player_source = "local"
        
        # 3. Přehrát soubor
        # QUrl.fromLocalFile je důležité pro Windows cesty!
        self.radio_player.setSource(QUrl.fromLocalFile(path))
        self.radio_player.play()
        
        # 4. Update UI
        self.track_label.setText(data['name'])
        self.artist_label.setText("Local File • MP3")
        self.album_art_label.setText("📂") 
        self.album_art_label.setStyleSheet("background: #333; color: #777; font-size: 30px; qproperty-alignment: AlignCenter;")
        
        self.btn_play.setIcon(QIcon(os.path.join(ASSETS_DIR, "pause.png")))






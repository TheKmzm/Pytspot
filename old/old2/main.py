import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, 
                             QListView, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QDesktopServices

from backend import SpotifyClient
from threads import Worker, ImageLoader
from gui_parts import Sidebar, PlayerBar, ContentTabs, TrackDelegate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Red Spotify Client")
        self.resize(1200, 800)
        self.setStyleSheet("background: #000;")

        self.client = SpotifyClient()
        self.workers = []
        self.last_track_id = None
        self.is_dragging_slider = False

        # --- HLAVNÍ LAYOUT ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.list.clicked.connect(self.on_playlist_click)
        self.sidebar.search_input.returnPressed.connect(self.perform_search)
        self.sidebar.history_list.clicked.connect(self.on_history_click)
        splitter.addWidget(self.sidebar)
        
        # Taby
        self.tabs = ContentTabs()
        self.tabs.tabCloseRequested.connect(lambda i: self.tabs.removeTab(i))
        splitter.addWidget(self.tabs)
        
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter)
        
        # Player Bar
        self.player = PlayerBar()
        self.connect_player_signals()
        layout.addWidget(self.player)

        # Start
        self.load_playlists()
        self.load_history()
        
        # Timer pro update přehrávání
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playback)
        self.timer.start(1000)

    # --- SIGNÁLY PŘEHRÁVAČE ---
    def connect_player_signals(self):
        self.player.btn_play.clicked.connect(lambda: self.client.control('play' if self.player.btn_play.text() == "▶" else 'pause'))
        self.player.btn_next.clicked.connect(lambda: self.client.control('next'))
        self.player.btn_prev.clicked.connect(lambda: self.client.control('prev'))
        
        self.player.slider.sliderPressed.connect(lambda: setattr(self, 'is_dragging_slider', True))
        self.player.slider.sliderReleased.connect(self.on_seek)
        self.player.vol_slider.valueChanged.connect(lambda v: self.client.control('volume', val=v))

    def on_seek(self):
        pos = self.player.slider.value()
        self.client.control('seek', pos_ms=pos)
        self.is_dragging_slider = False

    # --- VYHLEDÁVÁNÍ A HISTORIE ---
    def perform_search(self):
        query = self.sidebar.search_input.text()
        if not query: return

        self.client.save_search_to_history(query)
        self.load_history()
        self.create_track_tab(f"🔍 {query}", lambda: self.client.search(query))
        self.sidebar.search_input.clear()

    def load_history(self):
        hist = self.client.load_history()
        self.sidebar.update_history(hist)

    def on_history_click(self, index):
        query = index.data().replace("🕒 ", "")
        self.sidebar.search_input.setText(query)
        self.perform_search()

    def on_playlist_click(self, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        playlist_id = data['id']
        playlist_name = data['name']

        self.create_track_tab(f"🎵 {playlist_name}",
                              lambda: self.client.get_playlist_tracks(playlist_id))
    # --- PRÁCE S TABY A SEZNAMY ---
    def create_track_tab(self, title, fetch_method):
        list_view = QListView()
        list_view.setStyleSheet("border: none; outline: none; padding: 0;")
        list_view.setUniformItemSizes(True)
        list_view.setItemDelegate(TrackDelegate())
        
        model = QStandardItemModel()
        list_view.setModel(model)

        list_view.doubleClicked.connect(self.play_track)
        
        # Kontextové menu (pravé tlačítko)
        list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        list_view.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, list_view))

        self.tabs.addTab(list_view, title)
        self.tabs.setCurrentWidget(list_view)

        w = Worker(fetch_method)
        w.finished.connect(lambda res: self.fill_list(model, res))
        w.start()
        self.workers.append(w)

    def fill_list(self, model, tracks):
        if not tracks: return
        for t in tracks:
            item = QStandardItem()
            item.setData(t, Qt.ItemDataRole.UserRole)
            model.appendRow(item)

    # --- KONTEXTOVÉ MENU (Pravý klik) ---
    def show_context_menu(self, pos, list_view):
        index = list_view.indexAt(pos)
        if not index.isValid(): return
        
        data = index.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #222; color: white; border: 1px solid #444; } 
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background: #E60000; }
        """)
        
        act_play = QAction(f"▶ Přehrát", self)
        act_play.triggered.connect(lambda: self.client.control('play_uri', uri=data['uri']))
        
        act_queue = QAction("≡ Do fronty", self)
        act_queue.triggered.connect(lambda: self.client.control('queue', uri=data['uri']))
        
        act_lyrics = QAction("🎤 Najít text (Web)", self)
        act_lyrics.triggered.connect(lambda: self.open_lyrics(data['artist'], data['name']))

        act_analyze = QAction("📊 BPM a Energie", self)
        act_analyze.triggered.connect(lambda: self.show_analysis(data))

        menu.addAction(act_play)
        menu.addAction(act_queue)
        menu.addSeparator()
        menu.addAction(act_analyze)
        menu.addAction(act_lyrics)
        
        menu.exec(list_view.viewport().mapToGlobal(pos))

    # --- LOGIKA EXTRA FUNKCÍ ---
    def open_lyrics(self, artist, track):
        query = f"{artist} {track} lyrics genius"
        url = QUrl(f"https://www.google.com/search?q={query}")
        QDesktopServices.openUrl(url)

    def show_analysis(self, data):
        w = Worker(lambda: self.client.get_audio_features(data['id']))
        w.finished.connect(lambda res: self._display_analysis_popup(data['name'], res))
        w.start()
        self.workers.append(w)

    def _display_analysis_popup(self, name, features):
        if not features: return
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Analýza: {name}")
        msg.setText(f"Informace o skladbě:\n\n"
                    f"🔥 BPM (Tempo): {features['bpm']}\n"
                    f"⚡ Energie: {features['energy']}%\n"
                    f"💃 Tanečnost: {features['dance']}%\n"
                    f"🎹 Tónina: {features['key']}")
        msg.setStyleSheet("QMessageBox { background-color: #222; color: white; } QLabel { color: white; }")
        msg.exec()

    # --- UPDATE UI ---
    def play_track(self, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        self.client.control('play_uri', uri=data['uri'])

    def load_playlists(self):
        w = Worker(self.client.get_playlists)
        w.finished.connect(self.sidebar.add_playlists)
        w.start()
        self.workers.append(w)

    def update_playback(self):
        w = Worker(self.client.get_playback_state)
        w.finished.connect(self.sync_player_ui)
        w.start()
        self.workers.append(w)

    def sync_player_ui(self, data):
        if not data or not data.get('is_active'): 
            return

        self.player.lbl_name.setText(data['name'])
        self.player.lbl_artist.setText(data['artist'])
        self.player.btn_play.setText("⏸" if data['is_playing'] else "▶")
        
        if not self.is_dragging_slider:
            self.player.slider.setMaximum(data['duration'])
            self.player.slider.setValue(data['progress'])
        
        # Načítání coveru jen při změně skladby
        track_key = f"{data['name']}-{data['artist']}"
        if self.last_track_id != track_key and data['cover_url']:
            self.last_track_id = track_key
            il = ImageLoader(self.client.get_cover, data['cover_url'])
            il.loaded.connect(lambda px: self.player.cover_lbl.setPixmap(px.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            il.start()
            self.workers.append(il)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
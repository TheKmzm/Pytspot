import sys
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap
from service import SpotifyService
from workers import DataWorker, ImageLoader
from components import Sidebar, PlayerBar, BrowserTab, COL_BG, COL_BG_DARK, COL_SUB, COL_ITEM, COL_TEXT, COL_ACCENT

# --- ZDE DEJ SVÉ KLÍČE ---
CLIENT_ID = "TVOJE_CLIENT_ID"
CLIENT_SECRET = "TVOJE_CLIENT_SECRET"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Pro")
        self.resize(1200, 800)
        
        self.service = SpotifyService(CLIENT_ID, CLIENT_SECRET)
        
        # UI Structure
        main = QWidget()
        self.setCentralWidget(main)
        layout = QHBoxLayout(main)
        layout.setSpacing(0); layout.setContentsMargins(0,0,0,0)
        
        # Sidebar
        self.sidebar = Sidebar(self, self.on_sb_click, self.on_search)
        layout.addWidget(self.sidebar)
        
        # Right Column (Tabs + Player)
        right_col = QWidget()
        rcl = QVBoxLayout(right_col)
        rcl.setContentsMargins(0,0,0,0); rcl.setSpacing(0)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda i: self.tabs.removeTab(i))
        
        # New Tab Button (v rohu)
        btn_new = QPushButton("+")
        btn_new.setFixedSize(30, 30)
        btn_new.setStyleSheet(f"background: {COL_ACCENT}; color: black; font-weight: bold; border-radius: 5px;")
        btn_new.clicked.connect(lambda: self.open_tab("Nová karta", lambda t: None))
        self.tabs.setCornerWidget(btn_new, Qt.Corner.TopRightCorner)
        
        rcl.addWidget(self.tabs)
        
        # Player
        player_callbacks = {
            'prev': lambda: threading.Thread(target=self.service.control, args=('prev',)).start(),
            'next': lambda: threading.Thread(target=self.service.control, args=('next',)).start(),
            'play_pause': self.toggle_play,
            'set_volume': lambda v: threading.Thread(target=self.service.control, args=('volume',), kwargs={'val': v}).start(),
            'queue': self.open_queue
        }
        self.player = PlayerBar(callbacks=player_callbacks)
        rcl.addWidget(self.player)
        
        layout.addWidget(right_col)
        
        # Styles
        self.setStyleSheet(f"""
            QMainWindow {{ background: {COL_BG}; }}
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{ background: {COL_BG_DARK}; color: {COL_SUB}; padding: 10px; min-width: 100px; }}
            QTabBar::tab:selected {{ background: {COL_ITEM}; color: {COL_TEXT}; border-bottom: 2px solid {COL_ACCENT}; }}
            QLineEdit {{ color: white; }}
        """)

        # Start
        self.load_playlists()
        self.open_tab("Domů", lambda t: None)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(1000)

    def bytes_to_pixmap(self, b):
        p = QPixmap()
        p.loadFromData(b)
        return p

    def load_playlists(self):
        self.worker = DataWorker(self.service.get_playlists)
        self.worker.result.connect(self.fill_sidebar)
        self.worker.start()

    def fill_sidebar(self, items):
        if not items: return
        self.sidebar.model.clear()
        for i in items:
            si = QStandardItem(i['name'])
            si.setData(i, Qt.ItemDataRole.UserRole)
            self.sidebar.model.appendRow(si)

    def on_sb_click(self, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        img = data['images'][0]['url'] if data['images'] else None
        
        # Pokud je aktuální tab prázdný (Domů), použij ho, jinak nový
        curr = self.tabs.currentWidget()
        # Zjednodušení: Vždy přejmenujeme aktuální
        self.tabs.setTabText(self.tabs.currentIndex(), data['name'])
        curr.load_playlist(data['id'], data['name'], data['uri'], img)

    def on_search(self, query, stype):
        self.open_tab(f"🔍 {query}", lambda t: t.search(query, stype))

    def open_tab(self, name, callback):
        t = BrowserTab(self.service, self)
        self.tabs.addTab(t, name)
        self.tabs.setCurrentWidget(t)
        callback(t)

    def open_queue(self):
        self.open_tab("Fronta", lambda t: t.load_queue())

    def toggle_play(self):
        threading.Thread(target=self.service.control, args=('play' if self.player.btn_play.text() == "▶" else 'pause',)).start()

    def update_loop(self):
        threading.Thread(target=self._bg_update, daemon=True).start()

    def _bg_update(self):
        data = self.service.get_playback_state()
        if data and data.get('is_active'):
            QTimer.singleShot(0, lambda: self.update_ui(data))

    def update_ui(self, data):
        self.player.lbl_title.setText(data['name'])
        self.player.lbl_artist.setText(data['artist'])
        self.player.btn_play.setText("⏸" if data['is_playing'] else "▶")
        
        # Update cover only if changed
        if not hasattr(self, 'last_cover') or self.last_cover != data['cover_url']:
            self.last_cover = data['cover_url']
            if self.last_cover:
                self.iw = ImageLoader(self.last_cover)
                self.iw.finished.connect(lambda d: self.player.set_cover(d))
                self.iw.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
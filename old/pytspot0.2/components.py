from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QLineEdit, QComboBox, QFrame, QSlider, QListView, 
                             QAbstractItemView, QStyledItemDelegate, QStyle, QMenu, QApplication)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QPainter, QFont, QPixmap, QLinearGradient
from workers import ImageLoader, DataWorker
import threading
import random

# --- NORD THEME COLORS ---
COL_BG = "#2E3440"
COL_BG_DARK = "#242933"
COL_ITEM = "#3B4252"
COL_ACCENT = "#88C0D0"
COL_TEXT = "#ECEFF4"
COL_SUB = "#D8DEE9"

def ms_to_time(ms):
    if not ms: return "--:--"
    s = int((ms/1000)%60)
    m = int((ms/(1000*60))%60)
    return f"{m}:{s:02d}"

class TrackDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data: 
            painter.restore(); return

        is_hover = option.state & QStyle.StateFlag.State_MouseOver
        is_selected = option.state & QStyle.StateFlag.State_Selected
        bg_color = QColor(COL_ITEM) if is_selected or is_hover else QColor(COL_BG)
        if data.get('is_current'): bg_color = QColor("#434C5E")
        
        painter.fillRect(option.rect, bg_color)

        rect = option.rect
        painter.setPen(QColor(COL_ACCENT if data.get('is_current') else COL_TEXT))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(10, 5, -60, -20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, data['name'])

        painter.setPen(QColor(COL_SUB))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(rect.adjusted(10, 22, -60, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, data.get('artist', ''))
        
        dur = ms_to_time(data.get('duration_ms', 0))
        painter.drawText(rect.adjusted(0,0,-10,0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, dur)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 50)

class Sidebar(QWidget):
    def __init__(self, parent=None, on_click=None, on_search=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(f"background: {COL_BG_DARK};")
        self.on_click = on_click
        self.on_search = on_search
        
        layout = QVBoxLayout(self)
        
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hledat...")
        self.search.setStyleSheet(f"background: {COL_ITEM}; color: white; border: none; padding: 8px; border-radius: 5px;")
        self.search.returnPressed.connect(self.do_search)
        layout.addWidget(self.search)
        
        self.combo = QComboBox()
        self.combo.addItems(["track", "artist", "playlist", "album"])
        self.combo.setStyleSheet(f"background: {COL_ITEM}; color: white;")
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("KNIHOVNA"))
        
        self.list = QListView()
        self.list.setStyleSheet("background: transparent; border: none;")
        self.model = QStandardItemModel()
        self.list.setModel(self.model)
        self.list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list.clicked.connect(self.list_clicked)
        layout.addWidget(self.list)

    def list_clicked(self, index):
        if self.on_click: self.on_click(index)
    
    def do_search(self):
        if self.on_search: self.on_search(self.search.text(), self.combo.currentText())
    
    def load_data(self, items):
        self.model.clear()
        for i in items:
            si = QStandardItem(i['name'])
            si.setData(i, Qt.ItemDataRole.UserRole)
            self.model.appendRow(si)

class PlayerBar(QFrame):
    def __init__(self, parent=None, callbacks=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"background: {COL_BG_DARK}; border-top: 1px solid {COL_ITEM};")
        
        layout = QHBoxLayout(self)
        
        # Info
        self.cover = QLabel()
        self.cover.setFixedSize(60, 60)
        self.cover.setStyleSheet(f"background: {COL_ITEM}; border-radius: 4px;")
        self.cover.setScaledContents(True)
        
        info_l = QVBoxLayout()
        self.lbl_title = QLabel("--")
        self.lbl_title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COL_TEXT};")
        self.lbl_artist = QLabel("--")
        self.lbl_artist.setStyleSheet(f"color: {COL_SUB};")
        info_l.addWidget(self.lbl_title)
        info_l.addWidget(self.lbl_artist)
        
        layout.addWidget(self.cover)
        layout.addLayout(info_l)
        layout.addStretch()
        
        # Controls
        btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setStyleSheet(f"background: {COL_TEXT}; color: black; border-radius: 20px; font-size: 20px;")
        btn_next = QPushButton("⏭")
        self.btn_queue = QPushButton("≡")
        
        if callbacks:
            btn_prev.clicked.connect(callbacks['prev'])
            self.btn_play.clicked.connect(callbacks['play_pause'])
            btn_next.clicked.connect(callbacks['next'])
            self.btn_queue.clicked.connect(callbacks['queue'])

        layout.addWidget(btn_prev)
        layout.addWidget(self.btn_play)
        layout.addWidget(btn_next)
        layout.addWidget(self.btn_queue)
        layout.addStretch()
        
        # Volume
        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setFixedWidth(100)
        if callbacks: self.vol.valueChanged.connect(callbacks['set_volume'])
        layout.addWidget(QLabel("🔊"))
        layout.addWidget(self.vol)

    def update_info(self, data):
        self.lbl_title.setText(data['name'])
        self.lbl_artist.setText(data['artist'])
        self.btn_play.setText("⏸" if data['is_playing'] else "▶")
        # Blokování signálů při update volume aby se neposílaly zpět
        self.vol.blockSignals(True)
        self.vol.setValue(data['volume'])
        self.vol.blockSignals(False)

    def set_cover(self, data):
        # --- OPRAVA: Nastavení obrázku ---
        if not data: 
            self.cover.clear()
            return
        pix = QPixmap()
        pix.loadFromData(data)
        self.cover.setPixmap(pix)

class BrowserTab(QWidget):
    def __init__(self, service, main_app):
        super().__init__()
        self.service = service
        self.main_app = main_app
        self.context_uri = None
        self.offset = 0
        self.playlist_id = None
        self.is_loading = False
        
        layout = QVBoxLayout(self)
        
        # Header
        self.header = QWidget()
        self.header.setFixedHeight(120)
        hl = QHBoxLayout(self.header)
        self.img = QLabel()
        self.img.setFixedSize(100, 100)
        self.img.setStyleSheet(f"background: {COL_ITEM}; border-radius: 5px;")
        self.img.setScaledContents(True)
        
        il = QVBoxLayout()
        self.lbl_title = QLabel("Vítejte")
        self.lbl_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COL_TEXT};")
        self.btn_play = QPushButton("Přehrát kontext")
        self.btn_play.setStyleSheet(f"background: {COL_ACCENT}; color: #2E3440; font-weight: bold; padding: 8px; border-radius: 20px; max-width: 150px;")
        self.btn_play.clicked.connect(self.play_context)
        self.btn_play.hide()
        
        il.addWidget(self.lbl_title)
        il.addWidget(self.btn_play)
        il.addStretch()
        hl.addWidget(self.img)
        hl.addLayout(il)
        hl.addStretch()
        layout.addWidget(self.header)
        
        # List
        self.list = QListView()
        self.model = QStandardItemModel()
        self.list.setModel(self.model)
        self.list.setItemDelegate(TrackDelegate())
        self.list.doubleClicked.connect(self.on_double_click)
        
        # Context Menu
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.context_menu)
        
        layout.addWidget(self.list)

    def load_playlist(self, pid, name, uri, img_url=None):
        self.lbl_title.setText(name)
        self.context_uri = uri
        self.playlist_id = pid
        self.offset = 0
        self.btn_play.show()
        self.model.clear()
        if img_url: self._load_img(img_url)
        
        self.load_more_tracks()

    def load_more_tracks(self):
        # Načítá dalších 100 skladeb
        if self.is_loading: return
        self.is_loading = True
        self.worker = DataWorker(self.service.get_playlist_tracks, self.playlist_id, offset=self.offset, limit=100)
        self.worker.result.connect(self._on_tracks_loaded)
        self.worker.start()

    def _on_tracks_loaded(self, tracks):
        self.is_loading = False
        if not tracks: return
        
        self.populate(tracks)
        
        # Pokud jsme načetli plných 100, zkusíme načíst další
        if len(tracks) == 100:
            self.offset += 100
            self.load_more_tracks()

    def load_queue(self):
        self.lbl_title.setText("Fronta")
        self.context_uri = None
        self.btn_play.hide()
        self.model.clear()
        self.worker = DataWorker(self.service.get_queue)
        self.worker.result.connect(self.populate)
        self.worker.start()

    def search(self, query, stype):
        self.lbl_title.setText(f"Hledání: {query}")
        self.model.clear()
        self.worker = DataWorker(self.service.search, query, stype)
        self.worker.result.connect(self.populate)
        self.worker.start()

    def populate(self, items):
        # Ochrana proti None
        if not items: return
        for item in items:
            si = QStandardItem()
            si.setData(item, Qt.ItemDataRole.UserRole)
            self.model.appendRow(si)

    def _load_img(self, url):
        self.iw = ImageLoader(url)
        self.iw.finished.connect(lambda d: self.img.setPixmap(self.main_app.bytes_to_pixmap(d)))
        self.iw.start()

    def play_context(self):
        if self.context_uri:
            threading.Thread(target=self.service.control, args=('play_uri',), kwargs={'uri': self.context_uri}).start()

    def on_double_click(self, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        type = data.get('type', 'track')
        
        if type == 'track':
            if self.context_uri:
                threading.Thread(target=self.service.control, args=('play_context_track',), kwargs={'context': self.context_uri, 'uri': data['uri']}).start()
            else:
                threading.Thread(target=self.service.control, args=('play_uri',), kwargs={'uri': data['uri']}).start()
        elif type == 'playlist':
            self.main_app.open_tab(data['name'], lambda t: t.load_playlist(data['id'], data['name'], data['uri'], data.get('image_url')))

    def context_menu(self, pos):
        idx = self.list.indexAt(pos)
        if not idx.isValid(): return
        data = idx.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        menu.setStyleSheet(f"QMenu {{ background-color: {COL_BG_DARK}; color: {COL_TEXT}; border: 1px solid {COL_ITEM}; }} QMenu::item:selected {{ background-color: {COL_ACCENT}; color: black; }}")
        
        aq = menu.addAction("Přidat do fronty")
        new_tab = menu.addAction("Otevřít v nové kartě") if data.get('type') != 'track' else None
        
        action = menu.exec(self.list.mapToGlobal(pos))
        
        if action == aq:
            threading.Thread(target=self.service.add_to_queue, args=(data['uri'],)).start()
        elif action == new_tab:
            if data['type'] == 'playlist':
                self.main_app.open_tab(data['name'], lambda t: t.load_playlist(data['id'], data['name'], data['uri'], data.get('image_url')))

class VisualizerView(QWidget):
    # ... (zůstává stejný, není teď prioritou pro opravu chyb) ...
    pass
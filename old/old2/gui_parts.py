from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QListView, QFrame, QSlider, QTabWidget, QStyledItemDelegate, 
                             QLineEdit)
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush, QPen, QFont

BG_COLOR = "#000000"
BG_PANEL = "#121212"
ACCENT = "#E60000"
TEXT_MAIN = "#FFFFFF"
TEXT_SUB = "#B3B3B3"

class TrackDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        data = index.data(Qt.ItemDataRole.UserRole)
        
        # Pozadí při označení
        if option.state & self.State.State_Selected:
            painter.fillRect(option.rect, QColor("#2A2A2A"))

        # Texty
        title = data.get('name', 'Unknown')
        artist = data.get('artist', 'Unknown')
        
        r = option.rect
        painter.setPen(QColor(TEXT_MAIN))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(r.x()+10, r.y()+20, title)
        
        painter.setPen(QColor(TEXT_SUB))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(r.x()+10, r.y()+40, artist)
        
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 60)

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG_COLOR}; border-right: 1px solid #1A1A1A;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 0)
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hledat...")
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{ 
                background: #242424; color: white; border-radius: 4px; 
                padding: 0 10px; border: 1px solid #333; margin: 0 15px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        layout.addWidget(self.search_input)

        # Historie
        lbl_h = QLabel("HISTORIE")
        lbl_h.setStyleSheet(f"color: {TEXT_SUB}; font-weight: bold; font-size: 10px; margin: 15px 0 5px 20px;")
        layout.addWidget(lbl_h)

        self.history_list = QListView()
        self.history_list.setFixedHeight(100)
        self.history_list.setStyleSheet(f"""
            QListView {{ border: none; background: transparent; color: #888; }}
            QListView::item:hover {{ color: {TEXT_MAIN}; }}
        """)
        self.history_model = QStandardItemModel()
        self.history_list.setModel(self.history_model)
        self.history_list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history_list)

        # Playlisty
        lbl_p = QLabel("PLAYLISTY")
        lbl_p.setStyleSheet(f"color: {TEXT_SUB}; font-weight: bold; font-size: 10px; margin: 15px 0 5px 20px;")
        layout.addWidget(lbl_p)
        
        self.list = QListView()
        self.list.setStyleSheet(f"""
            QListView {{ border: none; background: transparent; color: {TEXT_SUB}; font-size: 14px; outline: 0; }}
            QListView::item {{ padding: 8px 20px; }}
            QListView::item:hover {{ color: {TEXT_MAIN}; }}
            QListView::item:selected {{ color: {ACCENT}; background: #1A1A1A; }}
        """)
        self.model = QStandardItemModel()
        self.list.setModel(self.model)
        self.list.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.list)

    def add_playlists(self, items):
        self.model.clear()
        for i in items:
            item = QStandardItem(i['name'])
            item.setData(i, Qt.ItemDataRole.UserRole)
            self.model.appendRow(item)

    def update_history(self, items):
        self.history_model.clear()
        for i in items:
            self.history_model.appendRow(QStandardItem(f"🕒 {i}"))

class ContentTabs(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {BG_PANEL}; }}
            QTabBar::tab {{ background: {BG_COLOR}; color: {TEXT_SUB}; padding: 10px 20px; border: none; }}
            QTabBar::tab:selected {{ color: {TEXT_MAIN}; border-bottom: 2px solid {ACCENT}; }}
            QTabBar::close-button {{ subcontrol-position: right; }}
        """)

class PlayerBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        
        # --- ZDE JE OPRAVA PRO RÁMEČKY ---
        # Nastavíme QFrame zvlášť a QLabelům sebereme border
        self.setStyleSheet(f"""
            QFrame {{ background: {BG_PANEL}; border-top: 1px solid #2A2A2A; }}
            QLabel {{ border: none; background: transparent; color: {TEXT_MAIN}; }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        
        # 1. Info o skladbě
        info_layout = QHBoxLayout()
        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(56, 56)
        self.cover_lbl.setStyleSheet("background: #333; border-radius: 4px;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_name = QLabel("Nepřehrává se")
        self.lbl_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_artist = QLabel("...")
        self.lbl_artist.setStyleSheet(f"color: {TEXT_SUB}; font-size: 12px;")
        
        text_layout.addWidget(self.lbl_name)
        text_layout.addWidget(self.lbl_artist)
        
        info_layout.addWidget(self.cover_lbl)
        info_layout.addLayout(text_layout)
        
        # 2. Ovládání (střed)
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btns_layout = QHBoxLayout()
        self.btn_prev = self.create_btn("⏮")
        self.btn_play = self.create_btn("▶", size=32)
        self.btn_next = self.create_btn("⏭")
        
        btns_layout.addWidget(self.btn_prev)
        btns_layout.addWidget(self.btn_play)
        btns_layout.addWidget(self.btn_next)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFixedWidth(400)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: #535353; border-radius: 2px; }}
            QSlider::sub-page:horizontal {{ background: {TEXT_MAIN}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {TEXT_MAIN}; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
        """)
        
        ctrl_layout.addLayout(btns_layout)
        ctrl_layout.addWidget(self.slider)

        # 3. Hlasitost (vpravo)
        vol_layout = QHBoxLayout()
        vol_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.setMaximum(100)
        self.vol_slider.setValue(50)
        vol_layout.addWidget(QLabel("🔊"))
        vol_layout.addWidget(self.vol_slider)

        # Složení do hlavního
        main_layout.addLayout(info_layout, 2)
        main_layout.addLayout(ctrl_layout, 6)
        main_layout.addLayout(vol_layout, 2)

    def create_btn(self, text, size=16):
        b = QPushButton(text)
        b.setFixedSize(40, 40)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        # Tlačítka musí mít border: none, jinak zdědí styl z QFrame
        b.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; color: {TEXT_MAIN}; border: none; font-size: {size}px; 
            }}
            QPushButton:hover {{ transform: scale(1.1); color: {ACCENT}; }}
        """)
        return b
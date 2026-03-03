# frontend/visualizer.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QCursor
import numpy as np

class AudioVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        
        # Data pro vizualizaci
        self.num_bars = 40 # Více sloupců pro detailnější pohled
        self.data = np.zeros(self.num_bars)
        self.decay = 0.80 
        self.accent_color = QColor("#E50914") 

    def set_accent_color(self, hex_color):
        self.accent_color = QColor(hex_color)

    def update_data(self, new_data):
        if len(new_data) < self.num_bars: return
        
        # Vezmeme potřebný počet vzorků
        raw = new_data[:self.num_bars]
        
        # Normalizace: Hodnoty z FFT jsou v dB (cca -20 až 80).
        # Chceme je převést na rozsah 0.0 až 1.0
        # 1. Ořízneme záporné hodnoty (ticho)
        raw = np.maximum(raw, 0)
        # 2. Vydělíme nějakou konstantou (např. 60), aby byly v rozsahu 0-1
        processed = np.clip(raw / 60, 0, 1)

        # Vyhlazení pohybu (decay)
        self.data = np.maximum(self.data * self.decay, processed)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        # Dynamický výpočet šířky sloupce
        bar_width = width / self.num_bars
        bar_spacing = max(1, bar_width * 0.2) # Mezera je 20% šířky sloupce
        actual_bar_width = bar_width - bar_spacing

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.accent_color))

        for i in range(self.num_bars):
            bar_height = int(self.data[i] * height)
            
            # Kreslíme odspodu
            x = int(i * bar_width + bar_spacing / 2)
            y = height - bar_height
            
            # Zaoblené obdélníky vypadají lépe
            painter.drawRoundedRect(x, y, int(actual_bar_width), bar_height, 3, 3)

class VisualizerWindow(QWidget):
    def __init__(self, accent_color="#E50914"):
        super().__init__()
        self.setWindowTitle("Visualizer")
        self.resize(600, 300)
        
        # --- MODERNÍ FRAMELESS VZHLED ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Hlavní layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Pozadí okna (poloprůhledná černá)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200); 
                border-radius: 15px;
                border: 1px solid #444;
            }
            QLabel { color: white; background: transparent; border: none; font-weight: bold;}
            QPushButton { background: transparent; color: #888; border: none; font-size: 16px; }
            QPushButton:hover { color: white; }
        """)

        # Horní lišta (Titul + Zavřít)
        header = QHBoxLayout()
        header.addWidget(QLabel("  ılıllı Audio Visualizer"))
        header.addStretch()
        
        btn_close = QPushButton("✕")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.hide)
        header.addWidget(btn_close)
        
        layout.addLayout(header)

        # Samotný vizualizér
        self.vis_widget = AudioVisualizerWidget()
        self.vis_widget.set_accent_color(accent_color)
        # Důležité: widget uvnitř musí mít transparentní pozadí a žádný border, aby dědil styl okna
        self.vis_widget.setStyleSheet("background: transparent; border: none;")
        
        layout.addWidget(self.vis_widget)
        
        # Proměnné pro posouvání okna myší
        self.oldPos = None

    def update_audio_data(self, data):
        """Předá data vnitřnímu widgetu."""
        if self.isVisible():
            self.vis_widget.update_data(data)

    def set_color(self, color):
        self.vis_widget.set_accent_color(color)

    # --- LOGIKA PRO POSOUVÁNÍ OKNA MYŠÍ ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.oldPos = None
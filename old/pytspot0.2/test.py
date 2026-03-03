import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QListView, QVBoxLayout, QWidget
from PyQt6.QtCore import QStringListModel

class SpotifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Pro (PyQt6)")
        self.resize(800, 600)

        # 1. DATA (Model) - Zde by byly tvoje skladby
        # Může jich být klidně 100 000 a nesekne se to
        self.playlist_data = [f"Skladba č. {i} - Umělec" for i in range(10000)]
        
        self.model = QStringListModel()
        self.model.setStringList(self.playlist_data)

        # 2. ZOBRAZENÍ (View) - Chytrý seznam
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.list_view)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Stylování (CSS style) - Vypadá to moderně
        self.setStyleSheet("""
            QListView {
                background-color: #121212;
                color: white;
                font-size: 16px;
                border: none;
            }
            QListView::item {
                padding: 10px;
                border-bottom: 1px solid #222;
            }
            QListView::item:selected {
                background-color: #3B8ED0;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpotifyApp()
    window.show()
    sys.exit(app.exec())
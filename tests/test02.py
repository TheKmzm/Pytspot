import webbrowser
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QUrl

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False


print(WEB_ENGINE_AVAILABLE)
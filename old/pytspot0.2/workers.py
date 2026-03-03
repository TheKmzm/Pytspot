from PyQt6.QtCore import QThread, pyqtSignal
import requests
import os
import hashlib

# Složka pro cache obrázků
CACHE_DIR = "img_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class ImageLoader(QThread):
    """Stáhne obrázek a vrátí binární data"""
    finished = pyqtSignal(bytes)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        if not self.url: return
        
        # 1. Zkusit disk
        filename = hashlib.md5(self.url.encode()).hexdigest()
        path = os.path.join(CACHE_DIR, filename)
        
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    self.finished.emit(f.read())
                return
            except: pass
        
        # 2. Stáhnout
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                data = response.content
                # Uložit na disk
                with open(path, "wb") as f:
                    f.write(data)
                self.finished.emit(data)
        except: pass

class DataWorker(QThread):
    """Univerzální worker pro API volání"""
    result = pyqtSignal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            data = self.func(*self.args, **self.kwargs)
            self.result.emit(data)
        except Exception as e:
            print(f"Worker Error: {e}")
            self.result.emit(None)
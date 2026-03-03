from PyQt6.QtCore import QThread, pyqtSignal

class Worker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            print(f"Worker Error: {e}")
            self.finished.emit(None)

class ImageLoader(QThread):
    loaded = pyqtSignal(object)

    def __init__(self, url_func, url):
        super().__init__()
        self.url_func = url_func
        self.url = url

    def run(self):
        pixmap = self.url_func(self.url)
        self.loaded.emit(pixmap)
import keyboard
from PyQt6.QtCore import QThread, pyqtSignal

class GlobalHotkeys(QThread):
    # Signály, které pošleme do GUI
    on_play_pause = pyqtSignal()
    on_next = pyqtSignal()
    on_prev = pyqtSignal()

    def run(self):
        """Běží na pozadí a čeká na stisk kláves."""
        
        # Namapování mediálních kláves
        # 'play/pause media' je standardní klávesa na klávesnici
        keyboard.add_hotkey('play/pause media', self.emit_play_pause)
        keyboard.add_hotkey('next track', self.emit_next)
        keyboard.add_hotkey('previous track', self.emit_prev)
        
        # Udržuje vlákno naživu
        keyboard.wait()

    def emit_play_pause(self):
        self.on_play_pause.emit()

    def emit_next(self):
        self.on_next.emit()

    def emit_prev(self):
        self.on_prev.emit()

    def stop(self):
        # Úklid při vypnutí
        keyboard.unhook_all()
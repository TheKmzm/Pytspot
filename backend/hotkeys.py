import keyboard
from PyQt6.QtCore import QThread, pyqtSignal

class GlobalHotkeys(QThread):
    # Signály, které pošleme do GUI
    on_play_pause = pyqtSignal()
    on_next = pyqtSignal()
    on_prev = pyqtSignal()
    on_volumeup = pyqtSignal()
    on_volumedown = pyqtSignal()
    
    def run(self):
        """Běží na pozadí a čeká na stisk kláves."""
        
        # Namapování mediálních kláves
        # 'play/pause media' je standardní klávesa na klávesnici
        keyboard.add_hotkey('play/pause media', self.emit_play_pause)
        keyboard.add_hotkey('next track', self.emit_next)
        keyboard.add_hotkey('previous track', self.emit_prev)

        #zatim neni namapovane
        keyboard.add_hotkey('volume up', self.emit_volumeup)
        keyboard.add_hotkey('volume down', self.emit_volumedown)

        
        # Udržuje vlákno naživu
        keyboard.wait()

    def emit_play_pause(self):
        self.on_play_pause.emit()

    def emit_next(self):
        self.on_next.emit()

    def emit_prev(self):
        self.on_prev.emit()

    def emit_volumeup(self):
        self.on_volumeup.emit()

    def emit_volumedown(self):
        self.on_volumedown.emit()

    def stop(self):
        # Úklid při vypnutí
        keyboard.unhook_all()
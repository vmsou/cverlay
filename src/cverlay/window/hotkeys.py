import keyboard

from PyQt6 import QtCore


class Signal(QtCore.QObject):
    signal = QtCore.pyqtSignal()

    def __init__(self, callback=None):
        super().__init__()

        if callback: self.connect(callback)

    def connect(self, callback): self.signal.connect(callback)
    
    def emit(self): self.signal.emit()


class KeyboardManager(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self.signals: dict = {}

    def addHotkey(self, hotkey: str, callback, trigger_on_release: bool = False):
        signal = Signal()
        signal.connect(callback)
        self.signals[hotkey] = signal
        keyboard.add_hotkey(hotkey, signal.emit, suppress=True, trigger_on_release=trigger_on_release)
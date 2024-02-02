import win32gui

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

class WindowComboBox(QtWidgets.QComboBox):
    opened = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
    
        self.view().window().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.refresh()

    def mousePressEvent(self, e: QtGui.QMouseEvent | None) -> None:
        self.refresh()
        self.opened.emit()

        return super().mousePressEvent(e)
    
    @staticmethod
    def getWindows() -> list[tuple[int, str]]:
        windows: list[tuple[int, str]] = [(0, "None")]  # (-1, "Active Window")
        def winEnumHandler(winId, ctx):
            if win32gui.IsWindowVisible(winId):
                title = win32gui.GetWindowText(winId)
                if title: windows.append((winId, f"{hex(winId)} - {title}"))

        win32gui.EnumWindows(winEnumHandler, None)   
        return windows
    
    def refresh(self) -> None:
        self.windows = self.getWindows()
        self.clear()
        for _, title in self.windows: self.addItem(title)

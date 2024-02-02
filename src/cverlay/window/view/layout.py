from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget

from cverlay.window.view.scanner import ScannerView


class LayoutView(QtWidgets.QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)

    def boundingRect(self) -> QtCore.QRectF:
        return self.childrenBoundingRect()
    
    def getScanners(self) -> list[ScannerView]:
        return self.childItems()
    
    def setLocked(self, locked: bool):
        for scanner in self.getScanners():
            scanner.setLocked(locked)
    
    def addScanner(self, scannerView: ScannerView):
        scannerView.setParentItem(self)

    def removeScanner(self, scannerView: ScannerView):
        scannerView.setParentItem(None)


    def paint(self, painter: QtGui.QPainter | None, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = ...) -> None:
        pass
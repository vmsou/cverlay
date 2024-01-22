from PyQt6 import QtCore

from cverlay.window.model import Layout, Scanner
from cverlay.window.view.layout import LayoutView


class LayoutController:
    def __init__(self, model: Layout, view: LayoutView):
        self.model = model
        self.view = view

    def setEditing(self, editing: bool):
        self.view.setEditing(editing)
    
    def setHwnd(self, hwnd: int):
        self.model.setHwnd(hwnd)

    def scannerAt(self, pos: QtCore.QPointF):
        return self.model.scannerAt(pos)

    def addScanner(self, scanner: Scanner):
        self.model.addScanner(scanner)

    def removeScanner(self, scanner: Scanner):
        self.model.removeScanner(scanner)

    def start(self): self.model.start()
    def stop(self): self.model.pause()
    def resume(self): self.model.resume()
    def pause(self): self.model.pause()
    def toggle(self): self.model.toggle()

    def updateView(self):
        for view in self.view.childItems(): self.view.removeScanner(view)
        for s in self.model.scanners: 
            self.view.addScanner(s.view)
            s.updateView()

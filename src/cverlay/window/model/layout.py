import re

from PyQt6 import QtCore

from cverlay.detector import Detection
from cverlay.window.capture import WindowCaptureThread
from cverlay.window.model.scanner import Scanner
from cverlay.window.controller.scanner import ScannerController

class Layout:
    def __init__(self, hwnd: int | None = None, maxFPS: int = 1, hardwareAccel: bool = False):
        self.scanners: list[ScannerController] = []
        self.captureThread = WindowCaptureThread(hwnd, maxFPS, hardwareAccel)

    def scannerAt(self, pos: QtCore.QPointF):
        for s in self.scanners:
            if s.view.sceneBoundingRect().contains(pos):
                return s
        return None
    
    def getScannerByName(self, name: str) -> ScannerController:
        # TODO: Maybe store the scanners with a dictionary
        for scanner in self.scanners:
            if scanner.getName() == name: return scanner
        return None
    
    def getScannersByRegex(self, regex: str) -> list[ScannerController]:
        def isMatch(name) -> bool:
            return bool(re.search(regex, name))

        return list(filter(lambda sc: isMatch(sc.getName()), self.scanners))
    
    def getHwnd(self) -> int: return self.captureThread.getHwnd()
    
    def getMaxFPS(self) -> int: return self.captureThread.getMaxFPS()

    def isHardwareAccel(self) -> bool: return self.captureThread.isHardwareAccel()

    def setHwnd(self, hwnd: int): self.captureThread.setHwnd(hwnd)

    def setMaxFPS(self, maxFPS: int): self.captureThread.setMaxFPS(maxFPS)

    def setHardwareAccel(self, hardwareAccel: bool): self.captureThread.setHardwareAccel(hardwareAccel)

    def getDetections(self) -> list[Detection]:
        detections: list[Detection] = []
        for scanner in self.scanners:
            detections.extend(scanner.getDetections())
        return detections

    def addScanner(self, scanner: Scanner):
        scanner.setCaptureAgent(self.captureThread)
        view = scanner.createView()
        controller = ScannerController(scanner, view)
        controller.updateView()
        self.scanners.append(controller)

        if self.isActive(): controller.start()
   
    def removeScanner(self, scanner: Scanner):
        for controller in self.scanners:
            if controller.model == scanner: 
                controller.stop()
                self.scanners.remove(controller)

    def isActive(self) -> bool: return self.captureThread.status()

    def start(self):
        self.captureThread.start(play=False)
        for s in self.scanners: s.start()

    def resume(self):
        self.captureThread.resume()
        for s in self.scanners: s.resume()

    def pause(self):
        self.captureThread.pause()
        for s in self.scanners: s.pause()

    def toggle(self):
        if self.isActive(): self.pause()
        else: self.resume()

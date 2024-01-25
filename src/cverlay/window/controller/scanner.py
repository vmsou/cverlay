from typing import Callable

import numpy as np

from PyQt6 import QtCore

from cverlay.detection import Detection
from cverlay.image.transform import ImageTransformer
from cverlay.window.model import Scanner
from cverlay.window.view.scanner import ScannerView


class ScannerController:
    def __init__(self, model: Scanner, view: ScannerView):
        self.model = model
        self.view = view

        # Updates model when view is updated
        self.model.signals.modelUpdate.connect(self.updateView)

        # Updates view when model is updated
        self.view.signals.viewUpdate.connect(self.updateModel)

    def start(self):
        self.view.setRunning(False)
        self.model.start()

    def stop(self):
        self.view.setRunning(False)
        self.model.stop()

    def resume(self):
        self.view.setRunning(True)
        self.model.resume()

    def pause(self):
        self.view.setRunning(False)
        self.model.pause()

    def toggle(self):
        if self.model.status(): self.pause()
        else: self.resume()

    def getName(self) -> str: return self.model.getName()    
    def getPos(self) -> tuple[int, int]: return self.model.getPos()
    def getRect(self) -> tuple[int, int, int, int]: return self.model.getRect()
    def getFound(self) -> bool: return self.model.getFound()
    def getConfidence(self) -> float: return self.model.getConfidence()
    def getDetections(self) -> list[Detection]: return self.model.getDetections()    
    def getTransformers(self) -> list[ImageTransformer]: return self.model.getTransformers()    
    def getImage(self) -> np.ndarray: return self.model.getImage()    
    def isImageVisible(self) -> bool: return self.view.isImageVisible()

    def setName(self, name: str):
        self.model.setName(name)
        self.view.setName(name)

    def setPos(self, pos: tuple[int, int]):
        self.model.setPos(pos)
        self.view.setPos(pos)

    def setRect(self, rect: tuple[int, int, int, int]):
        self.model.setRect(rect)
        self.view.setRect(rect)

    def setFound(self, found: bool):
        self.model.setFound(found)
        self.view.setFound(found)

    def setConfidence(self, confidence: float):
        self.model.setConfidence(confidence)
        self.view.setConfidence(confidence)

    def setDetector(self, detector: Callable[[np.ndarray], list[Detection]]):
        self.model.setDetector(detector)

    def setImage(self, img: np.ndarray):
        self.model.setImage(img)
        self.view.setImage(img)

    def setImageVisible(self, visible: bool):
        self.view.setImageVisible(visible)
    
    def updateModel(self):
        self.model.setRect(self.view.sceneBoundingRect().toRect().getRect())

    def updateView(self):
        rect = QtCore.QRectF(*self.getRect())
        found = self.getFound()
        confidence = self.getConfidence()
        detections = self.getDetections()
        img = self.getImage()

        self.view.setRect(rect)
        self.view.setFound(found)
        self.view.setConfidence(confidence)
        self.view.setDetections(detections)
        self.view.setImage(img)
        self.view.update()

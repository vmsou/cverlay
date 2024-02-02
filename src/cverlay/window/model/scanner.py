from abc import ABCMeta, abstractmethod
from PIL import Image
from typing import Callable
from threading import Semaphore

import numpy as np

from PyQt6 import QtCore

from cverlay.detection import Detection
from cverlay.image.transform import ImageTransformer
from cverlay.window.capture import WindowCaptureThread
from cverlay.window.view import ScannerView

from cverlay.common.thread import PausableThread


class IScanner(metaclass=ABCMeta):
    def __init__(self, name: str, detector: Callable[[np.ndarray], list[Detection]], rect: tuple[int, int, int, int], transformers: list[ImageTransformer] | None = None) -> None:
        self._name = name
        self._detector = detector
        self._rect = rect
        self._transformers: list[ImageTransformer] = [] if transformers is None else transformers

        # Data
        self._img = np.zeros((rect[3], rect[2], 3), np.uint8)

        # Results
        self._found = False
        self._confidence = 0.0
        self._detections: list[Detection] = []

    def addTransformer(self, transformer: ImageTransformer):
        self._transformers.append(transformer)

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        transformed = bgr
        for transformer in self._transformers: transformed = transformer(transformed)
        return transformed

    def getName(self) -> str:
        return self._name
    
    def getDetector(self) -> Callable[[np.ndarray], list[Detection]]:
        return self._detector
    
    def getPos(self) -> tuple[int, int]:
        return self._rect[0], self._rect[1]
    
    def getRect(self) -> tuple[int, int, int, int]:
        return self._rect
    
    def getTransformers(self) -> list[ImageTransformer]:
        return self._transformers
    
    def getImage(self) -> np.ndarray:
        return self._img
    
    def getFound(self) -> bool:
        return self._found
    
    def getConfidence(self) -> float:
        return self._confidence

    def getDetections(self) -> list[Detection]:
        return self._detections
    
    def setName(self, name: str):
        self._name = name

    def setDetector(self, detector: Callable[[np.ndarray], list[Detection]]):
        self._detector = detector

    def setPos(self, pos: tuple[int, int]):
        self.setRect([pos[0], pos[1], self._rect[2], self._rect[3]])

    def setRect(self, rect: tuple[int, int, int, int]):
        self._rect = rect
        # self.img = np.zeros((rect[3], rect[2], 3), np.uint8)

    def setTransformers(self, transformers: list[ImageTransformer]):
        self._transformers = transformers

    def setImage(self, img: np.ndarray):
        self._img = img

    def setFound(self, found: bool):
        self._found = found

    def setConfidence(self, confidence: float):
        self._confidence = confidence

    def setDetections(self, detection: list[Detection]):
        self._detections = detection

    @abstractmethod
    def scan(self) -> tuple[bool, float, list[Detection]]: ...

    def update(self):
        found, confidence, detections = self.scan()
        self.setFound(found)
        self.setConfidence(confidence)
        self.setDetections(detections)


class ImageDetectionThread(PausableThread):
    """Waits for image to be received thens updates scanner"""
    def __init__(self, scanner: IScanner) -> None:
        super().__init__(daemon=True)
        self.scanner = scanner
        self.receiveSignal = Semaphore(0)

    def target(self) -> None:
        # Wait for image
        self.receiveSignal.acquire()
        self.scanner.update()
            

class Scanner(IScanner):
    """
    Real Time Scanner based on window (winId)
    - Receives WindowCaptureThread (Sends image based at maxFPS speed)
    - Creates ImageDetectionThread (Receives WindowCaptureThread images and runs the detector with update method)
    """
    class Signals(QtCore.QObject):
        modelUpdate = QtCore.pyqtSignal()         

    def __init__(self, name: str, detector: Callable[[np.ndarray], list[Detection]], rect: tuple[int, int, int, int], minDetections: int = 1, transformers: list[ImageTransformer] | None = None):
        super().__init__(name, detector, rect, transformers=transformers)
        self.signals = self.Signals()
        self.minDetections = minDetections

        # Setup Threads
        self.detectionThread = ImageDetectionThread(self)
        self.captureThread: WindowCaptureThread = None

    def setCaptureAgent(self, captureThread: WindowCaptureThread | None):
        if self.captureThread: self.captureThread.signals.capture.disconnect(self.onCapture)
        self.captureThread = captureThread
        captureThread.signals.capture.connect(self.onCapture) # when captureThread has an img; update model based on scan

    def scan(self) -> tuple[bool, float, list[Detection]]:
        img = self.getImage()
        detections = self.getDetector()(img)
        found = len(detections) >= self.minDetections
        confidence = max(detections, key=lambda d: d.confidence).confidence if detections else 0.0
        return found, confidence, detections
    
    def createView(self) -> ScannerView:
        return ScannerView(self.getName())
    
    def update(self):
        """Runs scan method and updates results (found, confidence and detections). *Sends modelUpdate signal*"""
        super().update()
        self.signals.modelUpdate.emit()

    # Thread Methods
    def status(self): self.detectionThread.status()
    def start(self): self.detectionThread.start()
    def stop(self): self.detectionThread.stop()
    def play(self): self.detectionThread.play()
    def pause(self): self.detectionThread.pause()
    def toggle(self): self.detectionThread.toggle()
    
    def setPos(self, pos: tuple[int, int]): super().setPos(pos)
    def setRect(self, rect: tuple[int, int, int, int]): super().setRect(rect)

    def cropImage(self, img: np.ndarray) -> np.ndarray:
        x, y, w, h = self.getRect()
        return np.array(Image.fromarray(img).crop((x, y, x+w, y+h)))

    def onCapture(self, img: np.ndarray):
        cropped = self.cropImage(img)
        processed = self.transform(cropped)
        # Detect
        self.setImage(processed)  # detectionThread updates scanner from image
        self.detectionThread.receiveSignal.release()
        # self.update()

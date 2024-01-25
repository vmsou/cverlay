from abc import ABCMeta, abstractmethod

import numpy as np

from cverlay.detection import Detection


class Detector(metaclass=ABCMeta):
    """Abstract Class for a Detector. Expects `detect()` method to be overridden. """
    def __init__(self, label: str = "", color: str = "#000000"):
        self._label = label
        self._color = color

    def __call__(self, bgr: np.ndarray) -> list[Detection]: return self.detect(bgr)

    @abstractmethod
    def detect(self, bgr: np.ndarray) -> list[Detection]: ...

    def getLabel(self) -> str: return self._label
    def setLabel(self, label: str): self._label = label

    def getColor(self) -> str: return self._color
    def setColor(self, color: str): self._color = color

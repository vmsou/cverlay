import numpy as np

from cverlay.detector import Detector, Detection

from .color import ColorDetector
from .contour import ContourDetector
from .group import DetectorGroup
from .image import ImageDetector, ScaleImageDetector, FeatureMatchingDetector
from .network import NetDetector
    

class NoDetector(Detector):
    """ Simply returns no detections. """
    def __init__(self):
        super().__init__()

    def detect(self, bgr: np.ndarray) -> list[Detection]: return []
    
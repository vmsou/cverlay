from typing import Literal, Callable

import cv2
import numpy as np

from cverlay.detector import Detector, Detection


class ColorDetector(Detector):
    """Class that is able to detect color ranges

    Confidences are calculate by % of pixel matches for each contour (rectangle)

    Reminder: detections with `__call__()` and `detect()` methods expect BGR Image

    Attributes:
        label: The label of the detection.
        lower: The lower limit of the color range.
        upper: The upper limit of the color range. If not specified the range will default to the lower.
        method: The color method to use. Valid values are : `hsv`, `rgb`, `bgr`.
        color:  Six-digits hex color code. Default is #000000

    Example: 
        .. code-block:: python
        >>> greenDetector = ColorDetector("green", (33, 10, 10), (91, 255, 255), color="#03C03C")
        >>> detections = greenDetector(img)
    """

    def __init__(self, label: str, lower: tuple[int, int, int], upper: tuple[int, int, int] = None, method: Literal['hsv', 'rgb', 'bgr'] = "hsv", color: str = "#000000"):
        super().__init__(label, color=color)
        self.lower = lower
        self.upper = upper
        if upper is None: self.upper = lower
        self.method = method

        self.methodDict: dict[str, Callable[[np.ndarray], np.ndarray]] = {
            "hsv": self._methodHSV,
            "rgb": self._methodRGB,
            "bgr": self._methodBGR,
        } 
        if method not in self.methodDict: raise NotImplementedError(f"Unexpected method: {method}")

    @staticmethod
    def _methodHSV(bgr: np.ndarray) -> np.ndarray: return cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    @staticmethod
    def _methodRGB(bgr: np.ndarray) -> np.ndarray: return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    @staticmethod
    def _methodBGR(bgr: np.ndarray) -> np.ndarray: return bgr

    @staticmethod
    def _calculateConfidence(mask: np.ndarray, rect: tuple[int, int, int, int]) -> float:
        x, y, w, h = rect
        m = mask[y:y+h, x:x+w]
        return np.count_nonzero(m) / np.size(m)
        
    def detect(self, bgr: np.ndarray) -> list[Detection]:
        img = self.methodDict[self.method](bgr)
        mask = cv2.inRange(img, self.lower, self.upper)
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        rectangles = [cv2.boundingRect(c) for c in contours]
        
        detections = [Detection(self.getLabel(), self._calculateConfidence(mask, rect), rect, self.getColor()) for rect in rectangles]
        return detections

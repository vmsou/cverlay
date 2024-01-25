import cv2
import numpy as np

from cverlay.detector import Detector, Detection


class ContourDetector(Detector):
    MethodType = cv2.RETR_EXTERNAL | cv2.RETR_LIST | cv2.RETR_CCOMP | cv2.RETR_TREE | cv2.RETR_FLOODFILL
    ModeType = cv2.CHAIN_APPROX_NONE | cv2.CHAIN_APPROX_SIMPLE | cv2.CHAIN_APPROX_TC89_L1 | cv2.CHAIN_APPROX_TC89_KCOS

    def __init__(self, label: str, method: MethodType = cv2.RETR_EXTERNAL, mode: ModeType = cv2.CHAIN_APPROX_SIMPLE, color: str = "#000000"):
        super().__init__(label=label, color=color)
        self.method = method
        self.mode = mode

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(gray, self.method, self.mode)
        contours = contours[0] if len(contours) == 2 else contours[1]

        return [Detection(self.getLabel(), 1.0, cv2.boundingRect(cnt), self.getColor()) for cnt in contours]
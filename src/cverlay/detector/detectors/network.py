from itertools import cycle

import cv2
import numpy as np

from cverlay.detector import Detector, Detection


class NetDetector(Detector):
    def __init__(self, net: cv2.dnn.Net, classes: list[str], threshold: float = 0.2, colors: list[str] = None, scalefactor: float = 0.007, blob_size: tuple[int, int] = (300, 300), blob_mean: int = 130):
        super().__init__()
        self.net = net
        self.classes = classes
        self.threshold = threshold
        self.scalefactor = scalefactor
        self.blob_size = blob_size
        self.blob_mean = blob_mean

        if colors is None:
            self.colors = self.generateColors(len(classes))
        else:
            # Repeat colors until its the same as classes
            cycledColors = cycle(colors)
            self.colors = [next(cycledColors) for _ in range(len(classes))]

    @staticmethod
    def rgb2hex(color: tuple[int, int, int]) -> str:
        r, g, b = color
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def generateColors(n: int) -> list[str]:
        colors: list[tuple[int, int, int]] = np.random.random_integers(0, 180, size=(n, 3))
        return [NetDetector.rgb2hex(color) for color in colors]
    
    def detect(self, bgr: np.ndarray) -> list[Detection]:
        imgH, imgW = bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(bgr, self.blob_size), self.scalefactor, self.blob_size, self.blob_mean)
        self.net.setInput(blob)
        detectedObjs = self.net.forward()

        detections: list[Detection] = []
        for obj in detectedObjs[0][0]:
            _, classIdx, conf, left, top, right, bottom = obj

            if conf < self.threshold: continue
            classIdx = int(classIdx)
            left, top, right, bottom = int(left * imgW), int(top * imgH), int(right * imgW), int(bottom * imgH)
            rect = left, top, right - left, bottom - top

            detection = Detection(self.classes[classIdx], conf, rect, self.colors[classIdx])
            detections.append(detection)

        return detections
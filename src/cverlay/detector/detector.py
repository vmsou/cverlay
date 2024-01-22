import os

from abc import ABCMeta, abstractmethod
from typing import Any, Literal, Callable

import cv2
import imutils
import numpy as np

from cv2.typing import MatLike

from cverlay.image.transform import ImageTransformer
from cverlay.detector.detection import Detection

from .detection.filter import DetectionFilter

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


class ImageDetector(Detector):
    """Class for template matching images

    Works by providing an image that will be considered a needle to be found inside a haystack (image to be detected)

    Reminder: detections with `__call__()` and `detect()` methods expect BGR Image

    Attributes:
        label: The label of the detection.
        pathOrImage: Path to the image or a MatLike similar to np.ndarray
        threshold: minimum confidence for match
        method: Template matching method. Valid values are : `CCOEFF`, `CCORR`, `CCOEFF`.
        color:  Six-digits hex color code. Default is #000000

    Example: 
        .. code-block:: python
        >>> waldoDetector = ImageDetector("Waldo", "assets/waldo.png", threshold=0.7)
        >>> detections = waldoDetector(img)
    """
    def __init__(self, label: str, pathOrImage: str | MatLike, threshold: float = 0.2, method: Literal["CCOEFF", "CCORR", "SQDIFF"] = "CCOEFF", color: str = "#000000"):
        super().__init__(label, color=color)

        if isinstance(pathOrImage, str):
            path: str = pathOrImage
            if not os.path.exists(path): raise FileNotFoundError(f"image not found ('{path}')")
            self.needle = cv2.imread(pathOrImage, cv2.IMREAD_UNCHANGED)
        else:
            image: MatLike = pathOrImage
            self.needle = image

        if self.needle.shape[2] >= 3: self.needle = cv2.cvtColor(self.needle, cv2.COLOR_BGRA2BGR)

        self.threshold = threshold
        self.method = method
        self.methodDict: dict[str, Callable[[np.ndarray, np.ndarray], tuple[float, tuple[int, int]]]] = {
            "CCOEFF": self._matchCCOEFF,
            "CCORR": self._matchCCORR,
            "SQDIFF": self._matchSQDIFF
        }

        if method not in self.methodDict: raise NotImplementedError(f"Unexpected method: {method}")

    @staticmethod
    def _matchCCOEFF(haystack: np.ndarray, needle: np.ndarray) -> tuple[float, tuple[int, int]]:
        res = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
        _, maxVal, _, maxLoc = cv2.minMaxLoc(res)
        return maxVal, maxLoc
     
    @staticmethod
    def _matchCCORR(haystack: np.ndarray, needle: np.ndarray) -> tuple[float, tuple[int, int]]:
        res = cv2.matchTemplate(haystack, needle, cv2.TM_CCORR_NORMED)
        _, maxVal, _, maxLoc = cv2.minMaxLoc(res)
        return maxVal, maxLoc
    
    @staticmethod
    def _matchSQDIFF(haystack: np.ndarray, needle: np.ndarray) -> tuple[float, tuple[int, int]]:
        res = cv2.matchTemplate(haystack, needle, cv2.TM_SQDIFF_NORMED)
        minVal, _, minLoc, _ = cv2.minMaxLoc(res)
        return 1 - minVal, minLoc
    
    def setImage(self, bgr: np.ndarray):
        self.needle = bgr

        # Converts to 3 channels if needed
        if self.needle.shape[2] >= 3: self.needle = cv2.cvtColor(self.needle, cv2.COLOR_BGRA2BGR)

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        needle = self.needle
        haystack = bgr
        
        # Haystack image must be larger than needle image
        if haystack.shape[0] <= needle.shape[0] or haystack.shape[1] <= needle.shape[1]: return []

        val, loc = self.methodDict[self.method](haystack, needle)
        h, w = needle.shape[:2]

        detections = [Detection(self.getLabel(), val, (loc[0], loc[1], w, h), self.getColor())] if val >= self.threshold else []
        return detections


class ScaleImageDetector(Detector):
    """Class for template matching images with multiple scales. Good for images that change sizes

    Works by scaling the haystack image to different sizes and template matching the needle image

    Reminder: detections with `__call__()` and `detect()` methods expect BGR Image

    Attributes:
        label: The label of the detection.
        pathOrImage: Path to the image or a MatLike similar to np.ndarray
        threshold: minimum confidence for match
        scaleLow: Lowest multiplier for scaling haystack image
        scaleHigh: Highest multiplier for scaling haystack image
        nScales: Number of steps from scaleLow to scaleHigh
        color:  Six-digits hex color code. Default is #000000

    Example: 
        .. code-block:: python
        >>> waldoDetector = ScaleImageDetector("Waldo", "assets/waldo.png", threshold=0.5, scaleLow=0.1, scaleHigh=2.0, nScales=15)
        >>> detections = waldoDetector(img)
    """

    def __init__(self, label: str, pathOrImage: str | MatLike, threshold: float = 0.6, scaleLow: float = 0.2, scaleHigh: float = 1.5, nScales: int = 5, color: str = "#000000"):
        super().__init__(label, color=color)

        if isinstance(pathOrImage, str):
            path: str = pathOrImage
            if not os.path.exists(path): raise FileNotFoundError(f"image not found ('{path}')")
            self.needle = cv2.imread(pathOrImage, cv2.IMREAD_UNCHANGED)
        else:
            image: MatLike = pathOrImage
            self.needle = image

        self.threshold = threshold
        self.scaleLow = scaleLow
        self.scaleHigh = scaleHigh
        self.nScales = nScales

    def detect(self, bgr: np.ndarray) -> bool:
        needle = self.needle
        haystack = bgr

        tH, tW = needle.shape[:2]
        found = 0.0, (0, 0), 1.0
        for scale in np.linspace(self.scaleLow, self.scaleHigh, num=self.nScales)[::-1]:
            resized = imutils.resize(haystack, width=int(haystack.shape[1] * scale))
            r = haystack.shape[1] / float(resized.shape[1])

            if resized.shape[0] < tH or resized.shape[1] < tW: break

            result = cv2.matchTemplate(resized, needle, cv2.TM_CCOEFF_NORMED)
            _, maxVal, _, maxLoc = cv2.minMaxLoc(result)

            if maxVal > found[0]:
                found = maxVal, maxLoc, r

        if found[0] == 0.0: []
        maxVal, maxLoc, r = found

        startX, startY = int(maxLoc[0] * r), int(maxLoc[1] * r)
        w, h = tW * r, tH * r

        detections = [Detection(self.getLabel(), maxVal, (startX, startY, w, h), self.getColor())] if maxVal >= self.threshold else []
        return detections
    

class FeatureMatchingDetector(Detector):
    def __init__(self, label: str, pathOrImage: str | MatLike, threshold: float = 0.2, color: str = "#000000"):
        super().__init__(label, color=color)

        if isinstance(pathOrImage, str):
            path: str = pathOrImage
            if not os.path.exists(path): raise FileNotFoundError(f"image not found ('{path}')")
            self.needle = cv2.imread(pathOrImage, cv2.IMREAD_UNCHANGED)
        else:
            image: MatLike = pathOrImage
            self.needle = image
            
        if self.needle.shape[2] >= 3: self.needle = cv2.cvtColor(self.needle, cv2.COLOR_BGRA2BGR)

        self.threshold = threshold
    
    def setImage(self, bgr: np.ndarray):
        self.needle = bgr

        # Converts to 3 channels if needed
        if self.needle.shape[2] >= 3: self.needle = cv2.cvtColor(self.needle, cv2.COLOR_BGRA2BGR)

        self.flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=10), dict())

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        needle = self.needle
        haystack = bgr

        sift = cv2.SIFT_create()

        kp1, dsc1 = sift.detectAndCompute(needle, None)
        kp2, dsc2 = sift.detectAndCompute(haystack, None)

        if np.size(dsc1) == 0 or np.size(dsc2) == 0: return []

        matches = self.flann.knnMatch(dsc1, dsc2, k=2)

        match_points = []

        for p, q in matches:
            if p.distance < 0.1 * q.distance: match_points.append(p)

        keypoints = len(kp1)
        score = len(match_points) / keypoints if keypoints > 0 else 0.0
        if score > self.threshold and len(match_points) > 4:
            src_pts = np.float32([ kp1[m.queryIdx].pt for m in match_points]).reshape(-1,1,2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in match_points]).reshape(-1,1,2)
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)

            pts = dst_pts[mask==1]
            if len(pts) <= 0: return []
            x0, y0 = np.int32(pts.min(axis=0))
            x1, y1 = np.int32(pts.max(axis=0))
            rect = (x0, y0, x1 - x0, y1 - y0)
            detections = [Detection(self.getLabel(), score, rect, self.getColor())]
        else: detections = []
        return detections
    

class ContourDetector(Detector):
    MethodType = cv2.RETR_EXTERNAL | cv2.RETR_LIST | cv2.RETR_CCOMP | cv2.RETR_TREE | cv2.RETR_FLOODFILL
    ModeType = cv2.CHAIN_APPROX_NONE | cv2.CHAIN_APPROX_SIMPLE | cv2.CHAIN_APPROX_TC89_L1 | cv2.CHAIN_APPROX_TC89_KCOS

    def __init__(self, label: str, method: MethodType = cv2.RETR_EXTERNAL, mode: ModeType = cv2.CHAIN_APPROX_SIMPLE, imageFilters: list[ImageTransformer] = None, detectionFilters: list[DetectionFilter] = None, color: str = "#000000"):
        super().__init__(label, imageFilters=imageFilters, detectionFilters=detectionFilters, color=color)
        self.method = method
        self.mode = mode

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(gray, self.method, self.mode)
        contours = contours[0] if len(contours) == 2 else contours[1]

        return [Detection(self.getLabel(), 1.0, cv2.boundingRect(cnt), self.getColor()) for cnt in contours]
    

class NetDetector(Detector):
    def __init__(self, net: cv2.dnn.Net, classes: list[str], threshold: float = 0.2, scalefactor: float = 0.007, blob_size: tuple[int, int] = (300, 300), blob_mean: int = 130):
        super().__init__()
        self.net = net
        self.classes = classes
        self.threshold = threshold
        self.scalefactor = scalefactor
        self.blob_size = blob_size
        self.blob_mean = blob_mean

        self.colors = self.generateColors(len(classes))

    @staticmethod
    def rgb2hex(color: tuple[int, int, int]) -> str:
        r, g, b = color
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def generateColors(n: int) -> list[str]:
        colors: list[tuple[int, int, int]] = np.random.random_integers(0, 255, size=(n, 3))
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


class SourceDetector(Detector):
    """ Simply returns the source rect. """
    def __init__(self):
        super().__init__()

    def detect(self, bgr: np.ndarray) -> list[Detection]:
        return [Detection("source", 0, (0, 0, bgr.shape[1], bgr.shape[0]))]
    

class NoDetector(Detector):
    """ Simply returns no detections. """
    def __init__(self):
        super().__init__()

    def detect(self, bgr: np.ndarray) -> list[Detection]: return []
    

class DetectorGroup(Detector):
    def __init__(self, detectors: list[Detector], transformers: list[ImageTransformer] | None = None, filters: list[DetectionFilter] = None):
        super().__init__()
        self.detectors = detectors
        self.transformers = transformers
        self.filters = filters

    def __call__(self, bgr: np.ndarray) -> list[Detection]:
        return self.filter(self.detect(self.transform(bgr)))

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        transformed = bgr
        for transformer in self.transformers: transformed = transformer.transform(transformed)
        return transformed
    
    def filter(self, detections: list[Detection]) -> list[Detection]:
        filtered = detections
        for filter in self.filters: filtered = filter(filtered)
        return filtered
    
    def detect(self, bgr: np.ndarray) -> list[Detection]:
        detections: list[Detection] = []
        for detector in self.detectors:
            childDetections = detector(bgr)
            detections.extend(childDetections)
        return detections

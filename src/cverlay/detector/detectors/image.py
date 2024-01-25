import os
from typing import Literal, Callable

import cv2
import numpy as np

from cv2.typing import MatLike
from cverlay.detector import Detector, Detection


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

    @staticmethod
    def resize(self, img: np.ndarray, width: int) -> np.ndarray: ...

    def detect(self, bgr: np.ndarray) -> bool:
        needle = self.needle
        haystack = bgr

        tH, tW = needle.shape[:2]
        found = 0.0, (0, 0), 1.0
        for scale in np.linspace(self.scaleLow, self.scaleHigh, num=self.nScales)[::-1]:
            # resized = imutils.resize(haystack, width=int(haystack.shape[1] * scale))  # TODO: New Resize Func
            resized = self.resize(haystack, width=int(haystack.shape[1] * scale))
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
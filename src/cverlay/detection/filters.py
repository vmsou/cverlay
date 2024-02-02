from typing import Literal

import cv2

from .detection import Detection
from .filter import DetectionFilter


class AreaFilter(DetectionFilter):
    """Filters detections by minimum area and maximum area"""
    def __init__(self, minArea: int = 0, maxArea: int = None) -> None:
        super().__init__()

        self.minArea = minArea
        self.maxArea = maxArea

    def __call__(self, detections: list[Detection]) -> list[Detection]:
        if not self.maxArea: return [d for d in detections if d.area >= self.minArea]
        return [d for d in detections if d.area >= self.minArea and d.area <= self.maxArea]
    

class ConfidenceFilter(DetectionFilter):
    """Filters detections by minimum threshold (confidence)"""
    def __init__(self, threshold: float) -> None:
        super().__init__()
        self.threshold = threshold

    def __call__(self, detections: list[Detection]) -> list[Detection]:
        return [d for d in detections if d.confidence >= self.threshold]
    

class BestFilter(DetectionFilter):
    """Sorts detections (DESC) by confidence then return 'n' best."""
    def __init__(self, n: int = 1) -> None:
        super().__init__()
        self.n = n

    def __call__(self, detections: list[Detection]) -> list[Detection]:
        ordered = sorted(detections, key=lambda d: d.confidence, reverse=True)
        return ordered[:self.n]


class GroupRectangles(DetectionFilter):
    """Groups close rectangles into one.
    uses `cv2.groupRectangles()`
    """
    def __init__(self, threshold: int, eps: float = 0.5) -> None:
        super().__init__()
        self.threshold = threshold
        self.eps = eps

    def __call__(self, detections: list[Detection]) -> list[Detection]:
        # TODO: A way to measure confidence (maybe max or avg from grouped rectangles? also see which rectangles where grouped)
        rectsByKey: dict[str, list[tuple[int, int, int, int]]] = {}
        colorsByKey: dict[str, list[str]] = {}

        for d in detections:
            if d.label not in rectsByKey: rectsByKey[d.label] = []
            if d.label not in colorsByKey: colorsByKey[d.label] = []
            rectsByKey[d.label].append(d.rect)
            rectsByKey[d.label].append(d.rect)
            colorsByKey[d.label].append(d.color)

        colorByKey: dict[str, str] = {k: max(set(v), key=v.count) for k, v in colorsByKey.items()}  # most repeated color for label

        newDetections: list[Detection] = []
        for label, rects in rectsByKey.items():
            result, weights = cv2.groupRectangles(rects, self.threshold, self.eps)

            for r in result:
                d = Detection(label, 1, r, color=colorByKey[label])
                newDetections.append(d)
        return newDetections
from abc import ABCMeta, abstractmethod

from .detection import Detection

class DetectionFilter(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, detections: list[Detection]) -> list[Detection]: ...


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
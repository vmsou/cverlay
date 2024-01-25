import numpy as np

from cverlay.detector import Detector, Detection
from cverlay.image.transform import ImageTransformer
from cverlay.detection.filter import DetectionFilter


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
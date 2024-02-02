from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from cverlay.detector import Detector
from cverlay.detection.filter import DetectionFilter
from cverlay.image.transform import ImageTransformer

from cverlay.detector.detectors import DetectorGroup, ColorDetector, ImageDetector
from cverlay.detection.filters import *


@dataclass
class DetectorBuilder:
    """This class works as a helper tool to build detectors

    Use methods that helps building detectors, image transformers and detection filters, then call `build()` for finished detector

    Detectors:
        - color
        - image

    Filters:
        - minArea : minimum area for each detection
        - threshold : minimum confidence for each detection
        - best : select n best detections
        - groupRectangles : groups close rectangles into one
    
    Example: 
    .. code-block:: python
        RGBDetector = (
            DetectorBuilder()
            .color("red", (0, 50, 50), (10, 255, 255), color="#E60012").color("red", (170, 50, 50), (180, 255, 255), color="#E60012")
            .color("green", (33, 10, 10), (91, 255, 255), color="#03C03C")
            .color("blue", (80, 44, 0), (121, 255, 255), color="#000080")
        ).build()
    """

    _detectors: list[Detector] = field(default_factory=list)
    _transformers: list[ImageTransformer] = field(default_factory=list)
    _filters: list[DetectionFilter] = field(default_factory=list)
    
    def detectors(self, detectors: list[Detector]) -> DetectorBuilder:
        self._detectors = detectors
        return self
    
    def transformers(self, transformers: list[ImageTransformer]) -> DetectorBuilder:
        self._transformers = transformers
        return self
    
    def filters(self, filters: list[DetectionFilter]) -> DetectorBuilder:
        self._filters = filters
        return self
    
    # Detection Filters
    def filter(self, filter: DetectionFilter) -> DetectorBuilder:
        self._filters.append(filter)
        return self

    def minArea(self, area: int) -> DetectorBuilder:
        filter = AreaFilter(area)
        return self.filter(filter)
    
    def threshold(self, threshold: float) -> DetectorBuilder:
        filter = ConfidenceFilter(threshold)
        return self.filter(filter)
    
    def best(self, n: int = 1) -> DetectorBuilder:
        filter = BestFilter(n)
        return self.filter(filter)
    
    def groupRectangles(self, groupThreshold: float, eps: float = 0.5) -> DetectorBuilder:
        filter = GroupRectangles(groupThreshold, eps)
        return self.filter(filter)

    # Detectors
    def detector(self, detector: Detector) -> DetectorBuilder:
        self._detectors.append(detector)
        return self

    def color(self, label: str, lower: tuple[int, int, int], upper: tuple[int, int, int] = None, method: Literal['hsv', 'rgb', 'bgr'] = "hsv", color: str = "#000000") -> DetectorBuilder:
        """
        Adds an instance of `ColorDetector` to the builder pipeline
         
        Args:
            label: The label of the detection.
            lower: The lower limit of the color range.
            upper: The upper limit of the color range. If not specified the range will default to the lower.
            method: The color method to use. Valid values are : `hsv`, `rgb`, `bgr`.
            color: Color for detection. Default is #000000
         
        Returns: 
            The builder instance for chaining commands together. 
        
        Example: 
        .. highlight:: python
        .. code-block:: python
            >>> detector = DetectorBuilder().color("green", (33, 10, 10), (91, 255, 255), color="#03C03C").build()
            
        """
        detector = ColorDetector(label, lower, upper, method, color)
        return self.detector(detector)
    
    def image(self, label: str, pathOrImage: str | np.ndarray, threshold: float = 0.2, method: Literal["CCOEFF", "CCORR", "SQDIFF"] = "CCOEFF", color: str = "#000000") -> DetectorBuilder:
        """
        Adds an instance of `ImageDetector` to the builder pipeline
         
        Args:
            label: LThe label of the detection.
            pathOrImage: Path to the image file or an ndarray image
            threshold: Threshold for detecting image. Default is 0. 2
            method: Method for detecting image features. Default is CCOEFF
            color: Color for detection. Default is #000000
         
        Returns: 
            The builder instance for chaining commands together. 

        Example: 
        .. highlight:: python
        .. code-block:: python
            >>> DetectorBuilder().image("target", "assets/target.png", threshold=0.7).build()
            
        """
        detector = ImageDetector(label, pathOrImage, threshold, method, color)
        return self.detector(detector)
        
    def build(self) -> Detector:
        """
        Build and returns a ` DetectorGroup ` encopassing all the detectors, transformers, and filters. This is the method that can be used to build a ` Detector ` from the configuration provided to the constructor.
        
        
        Returns: 
            A ` Detector ` built from the configuration provided to the constructor or None if there were errors
        """

        return DetectorGroup(self._detectors, self._transformers, self._filters)

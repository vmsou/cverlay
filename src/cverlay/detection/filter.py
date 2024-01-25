from abc import ABCMeta, abstractmethod

from .detection import Detection


class DetectionFilter(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, detections: list[Detection]) -> list[Detection]: ...

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

@dataclass
class ImageTransformer(ABC):
    enabled: bool = field(default=True, init=False)

    def __str__(self) -> str:
        return self.__class__.__name__ + "({})"
    
    def __call__(self, bgr: np.ndarray) -> np.ndarray: 
        if not self.enabled: return bgr
        return self.transform(bgr)

    @abstractmethod
    def transform(self, bgr: np.ndarray) -> np.ndarray: 
        """Transforms a bgr image into another bgr image"""
        ...

    def save(self) -> str: return str(self)

    def isEnabled(self) -> bool: return self.enabled
    def setEnabled(self, flag: bool) -> None: self.enabled = flag

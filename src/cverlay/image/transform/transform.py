from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

import cv2

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


@dataclass
class GrayFilter(ImageTransformer):
    def __str__(self) -> str:
        return super().__str__().format("")

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    
    
@dataclass
class CannyFilter(ImageTransformer):
    canny1: int = 0
    canny2: int = 0

    def __str__(self) -> str:
        args = [self.canny1, self.canny2]
        return super().__str__().format(', '.join(map(str, args)))

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        return cv2.Canny(bgr, self.canny1, self.canny2)


@dataclass
class EdgeFilter(ImageTransformer):
    kernelSize: int = 0
    erodeIter: int = 0
    dilateIter: int = 0
    canny1: int = 0
    canny2: int = 0

    def __str__(self) -> str:
        args = [self.kernelSize, self.erodeIter, self.dilateIter, self.canny1, self.canny2]
        return super().__str__().format(', '.join(map(str, args)))

    def setKernelSize(self, value: int): self.kernelSize = value
    def setErodeIter(self, value: int): self.erodeIter = value
    def setDilateIter(self, value: int): self.dilateIter = value
    def setCanny1(self, value: int): self.canny1 = value
    def setCanny2(self, value: int): self.canny2 = value

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        kernel = np.ones((self.kernelSize, self.kernelSize), np.uint8)
        erodedImage = cv2.erode(bgr, kernel, iterations=self.erodeIter)
        dilatedImage = cv2.dilate(erodedImage, kernel, iterations=self.dilateIter)
        img = cv2.Canny(dilatedImage, self.canny1, self.canny2)

        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


@dataclass
class HSVFilter(ImageTransformer):
    hsvMin: tuple[int, int, int] = (0, 0, 0)
    hsvMax: tuple[int, int, int] = (179, 255, 255)
    sAdd: int = 0
    sSub: int = 0
    vAdd: int = 0
    vSub: int = 0

    def __str__(self) -> str:
        args = [self.hsvMin, self.hsvMax, self.sAdd, self.sSub, self.vAdd, self.vSub]
        return super().__str__().format(', '.join(map(str, args)))

    def setHMin(self, value: int): self.hsvMin = (value, self.hsvMin[1], self.hsvMin[2])
    def setSMin(self, value: int): self.hsvMin = (self.hsvMin[0], value, self.hsvMin[2])
    def setVMin(self, value: int): self.hsvMin = (self.hsvMin[0], self.hsvMin[1], value)
    def setHMax(self, value: int): self.hsvMax = (value, self.hsvMax[1], self.hsvMax[2])
    def setSMax(self, value: int): self.hsvMax = (self.hsvMax[0], value, self.hsvMax[2])
    def setVMax(self, value: int): self.hsvMax = (self.hsvMax[0], self.hsvMax[1], value)
    def setSAdd(self, value: int): self.sAdd = value
    def setSSub(self, value: int): self.sSub = value
    def setVAdd(self, value: int): self.vAdd = value
    def setVSub(self, value: int): self.vSub = value

    @classmethod
    def shiftChannel(cls, c, amount):
        if amount > 0:
            lim = 255 - amount
            c[c >= lim] = 255
            c[c < lim] += amount
        elif amount < 0:
            amount = -amount
            lim = amount
            c[c <= lim] = 0
            c[c > lim] -= amount
        return c

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # add/subtract saturation and value
        h, s, v = cv2.split(hsv)
        s = self.shiftChannel(s, self.sAdd)
        s = self.shiftChannel(s, -self.sSub)
        v = self.shiftChannel(v, self.vAdd)
        v = self.shiftChannel(v, -self.vSub)
        hsv = cv2.merge([h, s, v])

        # Set minimum and maximum HSV values to display
        lower = np.array(self.hsvMin)
        upper = np.array(self.hsvMax)
        # Apply the thresholds
        mask = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(hsv, hsv, mask=mask)

        # convert back to BGR for imshow() to display it properly
        img = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)

        return img
    
@dataclass
class RGBFilter(ImageTransformer):
    lower: tuple[int, int, int] = (0, 0, 0)
    upper: tuple[int, int, int] = field(default=None)

    def __post_init__(self):
        if self.upper is None: self.upper = self.lower

    def __str__(self) -> str:
        args = [self.lower, self.upper]
        return super().__str__().format(', '.join(map(str, args)))

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mask = cv2.inRange(rgb, self.lower, self.upper)
        result = cv2.bitwise_and(rgb, rgb, mask=mask)
        img = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)

        return img


@dataclass
class FillFilter(ImageTransformer):
    color: tuple[int, int, int] = (255, 255, 255)
    method: cv2.RETR_EXTERNAL | cv2.RETR_LIST | cv2.RETR_CCOMP | cv2.RETR_TREE | cv2.RETR_FLOODFILL = cv2.RETR_EXTERNAL
    mode: cv2.CHAIN_APPROX_NONE | cv2.CHAIN_APPROX_SIMPLE | cv2.CHAIN_APPROX_TC89_L1 | cv2.CHAIN_APPROX_TC89_KCOS = cv2.CHAIN_APPROX_SIMPLE

    def __str__(self) -> str:
        args = [self.color]
        return super().__str__().format(', '.join(map(str, args)))
    
    def setMethod(self, method: cv2.RETR_EXTERNAL | cv2.RETR_LIST | cv2.RETR_CCOMP | cv2.RETR_TREE | cv2.RETR_FLOODFILL):
        self.method = method

    def setMode(self, mode: cv2.CHAIN_APPROX_NONE | cv2.CHAIN_APPROX_SIMPLE | cv2.CHAIN_APPROX_TC89_L1 | cv2.CHAIN_APPROX_TC89_KCOS):
        self.mode = mode

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(gray, self.method, self.mode)
        contours = contours[0] if len(contours) == 2 else contours[1]

        for c in contours:
            cv2.drawContours(gray, [c], 0, self.color, -1)

        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    

@dataclass
class TransformerGroup(ImageTransformer):
    _transformers: list[ImageTransformer] = field(default_factory=list)

    def __str__(self) -> str:
        args = self._transformers
        return super().__str__().format(', '.join(map(str, args)))

    def transform(self, bgr: np.ndarray) -> np.ndarray:
        transformed = bgr
        for transformer in self._transformers: transformed = transformer(transformed)
        return transformed


def main() -> None:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    filters: list[ImageTransformer] = []
    #filters.append(HSVFilter())
    filters.append(EdgeFilter())
    #filters.append(GrayFilter())

    processed = img
    for filter in filters:
        print(processed.shape)
        processed = filter.transform(processed)
        print(processed.shape)
        print()


if __name__ == "__main__":
    main()

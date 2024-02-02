from abc import ABC

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Detection(ABC):
    """This class represents a Labeled Detection

    Attributes:
        label : str
            Text that identifies the detection
        confidence : float
            Detection confidence (0 to 1)
        rect : tuple[int, int, int, int]
            Detection rectangle (x, y, width, height)
        color : str
            Six-digits hex color code

    Properties:
        x : int
            Returns x-coordinate from rect[0]
        y : int
            Returns y-coordinate from rect[1]
        width : int
            Returns width from rect[2]
        height : int
            Returns height from rect[3]
        area : int
            Calculates area based on width and height
        contour : list[tuple[int, int]]
            Provides list of x and y coordinates that represents the detection
        bbox : list[int, int, int, int]
            Detection bbox (left, top, right, bottom)
    """
    label: str
    confidence: float
    rect: tuple[int, int, int, int]
    color: str = field(default="#000000")

    @property
    def x(self) -> int: return self.rect[0]

    @property
    def y(self) -> int: return self.rect[1]

    @property
    def width(self) -> int: return self.rect[2]

    @property
    def height(self) -> int: return self.rect[3]

    @property
    def area(self) -> int: return self.width * self.height

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return [self.x, self.y, self.x + self.width, self.y + self.height]

    @property
    def contour(self) -> list[tuple[int, int]]:
        return [
            (self.x, self.y), 
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]

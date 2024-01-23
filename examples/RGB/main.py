from cverlay import Overlay, Scanner
from cverlay.detector.builder import DetectorBuilder


def main() -> None:
    overlay = Overlay(maxFPS=2, hardwareAccel=True)

    RGBDetector = (
        DetectorBuilder()
        .color("red", (0, 50, 50), (10, 255, 255), color="#E60012").color("red", (170, 50, 50), (180, 255, 255), color="#E60012")
        .color("green", (33, 10, 10), (91, 255, 255), color="#03C03C")
        .color("blue", (80, 44, 0), (121, 255, 255), color="#000080")
        .minArea(100)
    ).build()
           
    
    RGBScanner = Scanner("RGB", RGBDetector, (50, 50, 100, 100))

    overlay.addScanner(RGBScanner)
    overlay.exec()


if __name__ == "__main__":
    main()
    
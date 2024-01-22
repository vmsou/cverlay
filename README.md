# cverlay

## Introduction
`cverlay` is a framework developed in python for creating and testing computer visions tools in real-time. This framework can be used for automation and is intended to interact with images that appear on your screen.

## Demo
This video shows how cverlay works when running a Deep Neural Network

https://github.com/vmsou/cverlay/assets/73619111/b5cc1b84-bec2-4de7-a1e4-79615eab8c12

### Demo Code
```python
import cv2

from cverlay import Overlay

from cverlay.detector import NetDetector
from cverlay.scanner import Scanner


def main() -> None:
    overlay = Overlay(maxFPS=5, hardwareAccel=True)

    prototxt_path = "PATH_TO_PROTOTXT"
    model_path = "PATH_TO_CAFFEMODEL"
    classes = [
        "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car",
        "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant",
        "sheep", "sofa", "train", "tvmonitor"
    ]

    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

    objectDetector = NetDetector(net, classes, threshold=0.6)
    objectScanner = Scanner("DNN", objectDetector, (100, 100, 100, 100))
    overlay.addScanner(objectScanner)

    overlay.exec()


if __name__ == "__main__":
    main()

```

## Controls
You can control the application through its GUI, tray icon, and shortcuts

- F8 - Hide/Show Application (doesn't show detections)
- F9 - Hide/Show Scanners (still shows detections)
- F10 - Run/Pause Detectors

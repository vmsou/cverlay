# cverlay

## Introduction
`cverlay`, short for Computer Vision Overlay, is a Python framework designed for creating and testing real-time computer vision tools. This framework can be used for automation and is intended to interact with images displayed on your screen.

## Demo
This video shows how cverlay works when running a Deep Neural Network

https://github.com/vmsou/cverlay/assets/73619111/4f28b36f-559d-46a9-9cfc-bf2c3dafd8c0

### Demo Code
```python
import cv2

from cverlay import Overlay, Scanner
from cverlay.detector.detectors import NetDetector


def main() -> None:
    overlay = Overlay(visionMaxFPS=5, hardwareAccel=True)

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

- `CTRL+R` Play/Pause Detections
- `CTRL+L` Lock/Unlock
- `CTRL+H` Hide/Show
- `CTRL+Q` Quit

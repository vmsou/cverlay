import cv2

from cverlay import Overlay

from cverlay.detector import NetDetector
from cverlay.scanner import Scanner


def main() -> None:
    overlay = Overlay(maxFPS=5, hardwareAccel=True)

    # source: https://github.com/chuanqi305/MobileNet-SSD/
    prototxt_path = "examples/DNN/models/MobileNetSSD_deploy.prototxt"
    model_path = "examples/DNN/models/MobileNetSSD_deploy.caffemodel"
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

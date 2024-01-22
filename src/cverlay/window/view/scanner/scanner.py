import numpy as np

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

from cverlay.window.view.scanner.resizer import SizeGripGraphicsItem, MoveGripGraphicsItem
from cverlay.detector import Detection

class ScannerView(QtWidgets.QGraphicsRectItem):
    class Signals(QtCore.QObject):
        viewUpdate = QtCore.pyqtSignal()

    MIN_WIDTH = 40
    MIN_HEIGHT = 40
    PREVIEW_SCALE = 0.5

    def __init__(self, name: str, parent: QtWidgets.QGraphicsItem | None = None):
        super().__init__(parent)
        self.signals = self.Signals()

        self.dragPos = QtCore.QPointF()

        # Flags
        self.hovering = False
        self.editing = True
        self.running = False
        self.imageVisible = False

        self.name = name
        self.found = False
        self.confidence = 0.0
        self.detections: list[Detection] = []
        self.img: np.ndarray = None
        self.pixmapItem = QtWidgets.QGraphicsPixmapItem(self)
        self.pixmapItem.setVisible(self.imageVisible)
        self.pixmapItem.setOpacity(0.5)

        self.setPen(QtGui.QPen(Qt.PenStyle.NoPen))

        # Formatters
        self.margin = 5
        self.font1 = QtGui.QFont("Arial", 10)
        self.fm1 = QtGui.QFontMetrics(QtGui.QFont(self.font1))

        self.font2 = QtGui.QFont("Arial", 7)
        self.fm2 = QtGui.QFontMetrics(QtGui.QFont(self.font2))

        self.sizeGrip = SizeGripGraphicsItem(self.margin, self)
        self.moveGrip = MoveGripGraphicsItem(self.margin, self)

        self.signals.viewUpdate.connect(self.sizeGrip.updateShape)
        self.signals.viewUpdate.connect(self.moveGrip.updateShape)
    
        self.setFlags(self.GraphicsItemFlag.ItemIsFocusable | self.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

    def signalUpdate(self) -> None: self.signals.viewUpdate.emit()

    def getName(self) -> str:
        return self.name

    def getFound(self) -> bool:
        return self.found

    def getConfidence(self) -> float:
        return self.confidence

    def getDetections(self) -> list[Detection]:
        return self.detections

    def getImage(self) -> np.ndarray:
        return self.img
    
    def isImageVisible(self) -> bool:
        return self.imageVisible
    
    def getPos(self) -> tuple[int, int]:
        return self.pos().x(), self.pos.y()

    def setPos(self, pos: QtCore.QPointF) -> None:
        super().setPos(pos)
        self.signalUpdate()

    def setRect(self, rect: QtCore.QRectF) -> None:
        x, y, w, h = rect.getRect()
        if w <= self.MIN_WIDTH:
            x = self.x()
            w = self.rect().width()
        if h <= self.MIN_HEIGHT:
            y = self.y()
            h = self.rect().height()
        super().setRect(0, 0, max(self.MIN_WIDTH, w), max(self.MIN_HEIGHT, h))
        self.setPos(QtCore.QPointF(x, y))

    def setEditing(self, editing: bool):
        self.editing = editing
        self.setImageVisible(False)

    def setRunning(self, running: bool):
        self.running = running

    def setName(self, name: str):
        self.name = name

    def setFound(self, found: bool):
        self.found = found

    def setConfidence(self, confidence: float):
        self.confidence = confidence

    def setDetections(self, detections: list[Detection]):
        self.detections = detections

    def setImage(self, img: np.ndarray):
        self.img = img
        if img is None: return

        h, w, c = img.shape[:3]

        qimg = QtGui.QImage(self.img.data.tobytes(), w, h, c * w, QtGui.QImage.Format.Format_RGB888)
        qimg.rgbSwap()
        
        pixmap = QtGui.QPixmap(qimg).scaled(self.rect().size().toSize() * self.PREVIEW_SCALE, Qt.AspectRatioMode.KeepAspectRatio)

        self.pixmapItem.setPixmap(pixmap)
        self.pixmapItem.setPos(self.rect().bottomRight() - QtCore.QPointF(pixmap.width() + self.margin, pixmap.height() + self.margin))
        
    def setImageVisible(self, visible: bool):
        self.imageVisible = visible
        self.pixmapItem.setVisible(self.imageVisible)

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(0, 0, self.rect().width(), self.rect().height())

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent | None) -> None:
        self.hovering = True
        self.prepareGeometryChange()
        return super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent | None) -> None:
        self.hovering = False
        self.prepareGeometryChange()
        return super().hoverLeaveEvent(event)

    def colorScheme(self) -> tuple[QtGui.QColor, QtGui.QColor]:
        if self.editing:
            if not self.running: return QtGui.QColor(134, 132, 130, 75), QtGui.QColor(53, 50, 47, 75)
            if self.found:
                return QtGui.QColor(0, 128, 0, 100), QtGui.QColor(0, 255, 0, 50)
            return QtGui.QColor(128, 0, 0, 100), QtGui.QColor(255, 0, 0, 50)
        else:
            #if not self.running: return QtGui.QColor(134, 132, 130, 25), QtGui.QColor(53, 50, 47, 50)
            #if self.found:
            #    return QtGui.QColor(0, 128, 0, 50), QtGui.QColor(0, 255, 0, 25)
            #return QtGui.QColor(128, 0, 0, 50), QtGui.QColor(255, 0, 0, 25)
            return QtGui.QColor(134, 132, 130, 0), QtGui.QColor(53, 50, 47, 0)
        

    def paintBorder(self, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        painter.setPen(QtGui.QPen(scheme[0 if self.editing else self.hovering], 2, Qt.PenStyle.SolidLine))
        painter.drawRect(self.boundingRect())

    def paintFill(self, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        painter.fillRect(self.boundingRect(), scheme[1])

    def paintName(self, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        painter.setPen(QtGui.QPen(scheme[0 if self.editing else self.hovering], 2, Qt.PenStyle.SolidLine))
        painter.setFont(self.font1)
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, self.name)
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, f"{self.confidence:.2f}")

    def paintRectInfo(self, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        painter.setPen(QtGui.QPen(scheme[0 if self.editing else self.hovering], 2, Qt.PenStyle.SolidLine))
        painter.setFont(QtGui.QFont("Arial", 6))
        painter.drawText(self.boundingRect().adjusted(4, 2, -4, -2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"{self.sceneBoundingRect().toRect().getRect()}")

    def paintDetection(self, detection: Detection, boundingRect: QtCore.QRectF, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        rect = QtCore.QRectF(*detection.rect)
        if not boundingRect.contains(rect): return

        # Detection Info
        confidence = detection.confidence
        color = QtGui.QColor(detection.color)
        label = f"{detection.label} {confidence:.2f}"
        
        # Detection Rectangle
        poly = QtGui.QPolygonF()
        for x, y in detection.contour: poly.append(QtCore.QPointF(x, y))

        painter.setPen(QtGui.QPen(color, 2, Qt.PenStyle.SolidLine))
        painter.drawPolygon(poly)

        # painter.drawRect(rect)

        # Label Box's Fill
        size = self.fm1.boundingRect(label).size().toSizeF()
        size.setWidth(size.width() - 7)

        labelRect = QtCore.QRectF(rect.topLeft() + QtCore.QPointF(-1, -size.height()), size)
        if not boundingRect.contains(labelRect): 
            labelRect = QtCore.QRectF(rect.topLeft() + QtCore.QPointF(-1, 0), size)
            if not boundingRect.contains(labelRect): return

        painter.fillRect(labelRect, color)
        
        # Label Box's Text
        textRect = labelRect.adjusted(2, 0, -2, 0)
        painter.setFont(self.font2)
        painter.setPen(scheme[1])
        painter.drawText(textRect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

    def paintDetections(self, painter: QtGui.QPainter, scheme: tuple[QtGui.QColor, QtGui.QColor]):
        if not self.detections: return

        boundingRect = self.rect().adjusted(-1, -1, 1, 1)
        for d in self.detections: self.paintDetection(d, boundingRect, painter, scheme)
        
    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None, widget: QtWidgets.QWidget | None = ...) -> None:
        scheme = self.colorScheme()
        # Draw Border
        self.paintBorder(painter, scheme)

        # Draw Fill
        self.paintFill(painter, scheme)

        # Paint Scanner name
        self.paintName(painter, scheme)

        # Paint Rect Info (coordinates, size, etc.)
        self.paintRectInfo(painter, scheme)

        # Painter Detections
        self.paintDetections(painter, (Qt.GlobalColor.black, Qt.GlobalColor.white))

        super().paint(painter, option, widget)

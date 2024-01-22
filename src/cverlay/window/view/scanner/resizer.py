from typing import Callable, Literal 

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt


class MoveGripGraphicsItem(QtWidgets.QGraphicsItem):
    def __init__(self, margin: int, target: QtWidgets.QGraphicsRectItem):
        super().__init__(target)

        self.margin = margin
        self.target = target

        rect = target.boundingRect().adjusted(margin, margin, -margin, -margin)
        self.setRect(rect)

        # Flags
        self.hovering = False
        self.moving = False

        self.dragPos = QtCore.QPointF()

        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemSendsGeometryChanges | self.GraphicsItemFlag.ItemHasNoContents)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def updateShape(self) -> None:
        rect = self.target.boundingRect().adjusted(self.margin, self.margin, -self.margin, -self.margin)
        self.setRect(rect)

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(0, 0, self.size.width(), self.size.height())
    
    def setRect(self, rect: QtCore.QRectF):
        self.setPos(rect.topLeft())
        self.size = rect.size()
    
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.moving = True
        self.dragPos = event.scenePos() - self.target.sceneBoundingRect().topLeft()
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        if self.moving:
            movePos = event.scenePos()
            rect = self.target.sceneBoundingRect()
            rect.setTopLeft(movePos - self.dragPos)
            self.target.setPos(rect.topLeft())
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.moving = False
        self.dragPos = QtCore.QPointF()
        return super().mouseReleaseEvent(event)
    
    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None, widget: QtWidgets.QWidget | None = ...) -> None:
        pass


class ResizeGraphicsItem(QtWidgets.QGraphicsItem):
    def __init__(self, side: Literal['top', 'bottom', 'left', 'right', 'topleft', 'topright', 'bottomleft', 'bottomright'], margin: int, target: QtWidgets.QGraphicsRectItem):
        super().__init__(target)

        self.side = side
        self.margin = margin
        self.target = target
        self.size = target.rect().size()

        # Flags
        self.hovering = False
        self.resizing = False

        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemSendsGeometryChanges | self.GraphicsItemFlag.ItemHasNoContents)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        self.updateRect: Callable[[QtCore.QRectF, QtCore.QPointF], None]
        self.updateShape: Callable[['ResizeGraphicsItem'], None]
        self.setupResizer(side)  # Sets cursor & update functions

    def setHitboxVisibility(self, flag: bool):
        self.setFlag(self.GraphicsItemFlag.ItemHasNoContents, not flag)

    def updateTop(self):
        rect = self.target.boundingRect()
        pos = rect.topLeft() + QtCore.QPointF(self.margin, -self.margin)
        size = QtCore.QSizeF(rect.width() - (2 * self.margin), 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def updateBottom(self):
        rect = self.target.boundingRect()
        pos = rect.bottomLeft() + QtCore.QPointF(self.margin, -self.margin)
        size = QtCore.QSizeF(rect.width() - (2 * self.margin), 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def updateLeft(self):
        rect = self.target.boundingRect()
        pos = rect.topLeft() + QtCore.QPointF(-self.margin, self.margin)
        size = QtCore.QSizeF(2 * self.margin, rect.height() - (2 * self.margin))
        self.setRect(QtCore.QRectF(pos, size))

    def updateRight(self):
        rect = self.target.boundingRect()
        pos = rect.topRight() + QtCore.QPointF(-self.margin, self.margin)
        size = QtCore.QSizeF(2 * self.margin, rect.height() - (2 * self.margin))
        self.setRect(QtCore.QRectF(pos, size))

    def updateTopLeft(self):
        rect = self.target.boundingRect()
        pos = rect.topLeft() + QtCore.QPointF(-self.margin, -self.margin)
        size = QtCore.QSizeF(2 * self.margin, 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def updateBottomLeft(self):
        rect = self.target.boundingRect()
        pos = rect.bottomLeft() + QtCore.QPointF(-self.margin, -self.margin)
        size = QtCore.QSizeF(2 * self.margin, 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def updateBottomRight(self):
        rect = self.target.boundingRect()
        pos = rect.bottomRight() + QtCore.QPointF(-self.margin, -self.margin)
        size = QtCore.QSizeF(2 * self.margin, 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def updateTopRight(self):
        rect = self.target.boundingRect()
        pos = rect.topRight() + QtCore.QPointF(-self.margin, -self.margin)
        size = QtCore.QSizeF(2 * self.margin, 2 * self.margin)
        self.setRect(QtCore.QRectF(pos, size))

    def setupResizer(self, side: Literal['top', 'bottom', 'left', 'right', 'topleft', 'topright', 'bottomleft', 'bottomright']) -> None:
        match side:
            case "top":
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self.updateRect = lambda rect, movePos: rect.setTop(movePos.y())
                self.updateShape = self.updateTop

            case "bottom":
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self.updateRect = lambda rect, movePos: rect.setBottom(movePos.y()) 
                self.updateShape = self.updateBottom

            case "left":
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.updateRect = lambda rect, movePos: rect.setLeft(movePos.x())
                self.updateShape = self.updateLeft

            case "right":
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self.updateRect = lambda rect, movePos: rect.setRight(movePos.x())
                self.updateShape = self.updateRight

            case "topleft":
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self.updateRect = lambda rect, movePos: rect.setTopLeft(movePos)
                self.updateShape = self.updateTopLeft

            case "bottomleft":
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self.updateRect = lambda rect, movePos: rect.setBottomLeft(movePos)
                self.updateShape = self.updateBottomLeft

            case "bottomright":
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self.updateRect = lambda rect, movePos: rect.setBottomRight(movePos)
                self.updateShape = self.updateBottomRight

            case "topright":
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self.updateRect = lambda rect, movePos: rect.setTopRight(movePos)
                self.updateShape = self.updateTopRight
            case _:
                def updateRectNotImplemented(rect: QtCore.QRectF, movePos: QtCore.QPointF): raise NotImplementedError(f"updateRect not implemented for side: {side}")
                def updateShapeNotImplemented(self): raise NotImplementedError(f"updateShape not implemented for side: {side}")
                self.updateRect = updateRectNotImplemented
                self.updateShape = updateShapeNotImplemented
    
    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(0, 0, self.size.width(), self.size.height())
    
    def setRect(self, rect: QtCore.QRectF):
        self.setPos(rect.topLeft())
        self.size = rect.size()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.resizing = True
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        if self.resizing:
            movePos = event.scenePos()
            sceneRect = self.parentItem().sceneBoundingRect()
            self.updateRect(sceneRect, movePos)
            self.target.setRect(sceneRect)

        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.resizing = False
        return super().mouseReleaseEvent(event)
    
    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None, widget: QtWidgets.QWidget | None = ...) -> None:
        painter.setPen(Qt.GlobalColor.red if self.hovering else Qt.GlobalColor.black)
        painter.drawRect(self.boundingRect())
        # super().paint(painter, option, widget)
        

class SizeGripGraphicsItem(QtWidgets.QGraphicsItem):
    def __init__(self, margin: int, target: QtWidgets.QGraphicsRectItem | None = None):
        super().__init__(target)
        self.margin = margin
        self.target = target

        self.handles: list[ResizeGraphicsItem] = [
            ResizeGraphicsItem('top', self.margin, target),
            ResizeGraphicsItem('bottom', self.margin, target),
            ResizeGraphicsItem('left', self.margin, target),
            ResizeGraphicsItem('right', self.margin, target),
            ResizeGraphicsItem('topleft', self.margin, target),
            ResizeGraphicsItem('bottomleft', self.margin, target),
            ResizeGraphicsItem('topright', self.margin, target),
            ResizeGraphicsItem('bottomright', self.margin, target),
        ]

    def updateShape(self):
        for handle in self.handles: handle.updateShape()

    def boundingRect(self) -> QtCore.QRectF:
        return self.target.boundingRect().adjusted(-self.margin, -self.margin, self.margin, self.margin)
    
    def paint(self, painter: QtGui.QPainter | None, option: QtWidgets.QStyleOptionGraphicsItem | None, widget: QtWidgets.QWidget | None = ...) -> None:
        painter.setOpacity(0.01)
        painter.fillRect(self.boundingRect(), Qt.GlobalColor.black)
        painter.setOpacity(1)
        # super().paint(painter, option, widget)
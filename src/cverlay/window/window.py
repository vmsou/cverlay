import time
from PyQt6.QtGui import QCloseEvent

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

from cverlay.agent import Agent
from cverlay.window.combobox import WindowComboBox
from cverlay.window.hotkeys import KeyboardManager
from cverlay.window.tray import SystemTrayIcon
from cverlay.window.controller.layout import LayoutController


class GUIWindow(QtWidgets.QMainWindow):
    def __init__(self, cverlay: 'CverlayWindow'):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon("res/icon.png"))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.cverlay = cverlay
        windowToolbar = QtWidgets.QToolBar("Window")
        windowToolbar.setMovable(False)
        windowToolbar.setIconSize(QtCore.QSize(14, 14))
        self.addToolBar(windowToolbar)

        self.runCheckbox = QtWidgets.QCheckBox()
        self.runCheckbox.setChecked(cverlay.running)
        self.runCheckbox.setStyleSheet("QCheckBox::indicator { height: 14px; width: 14px; } QCheckBox::indicator:unchecked { image: url(res/play.png); } QCheckBox::indicator:checked { image: url(res/pause.png); }")
        self.runCheckbox.clicked.connect(self.cverlay.setRunning)
        windowToolbar.addWidget(self.runCheckbox)

        self.lockCheckbox = QtWidgets.QCheckBox()
        self.lockCheckbox.setChecked(cverlay.locked)
        self.lockCheckbox.setStyleSheet("QCheckBox::indicator { height: 14px; width: 14px; } QCheckBox::indicator:unchecked { image: url(res/unlock.png); } QCheckBox::indicator:checked { image: url(res/lock.png); }")
        self.lockCheckbox.clicked.connect(cverlay.setLocked)
        windowToolbar.addWidget(self.lockCheckbox)

        class UpdateWindowsEventFilter(QtCore.QObject):
            """Updates QComboBox when opening"""
            def __init__(self, gui: GUIWindow) -> None:
                super().__init__(gui)
                self.gui = gui

            def eventFilter(self, a0: QtCore.QObject | None, a1: QtCore.QEvent | None) -> bool:
                if (a1.type() == QtCore.QEvent.Type.MouseButtonPress): self.gui.update()
                return super().eventFilter(a0, a1)

        self.windowSelector = QtWidgets.QComboBox()
        self.windowSelector.installEventFilter(UpdateWindowsEventFilter(self))
        self.windowSelector.currentIndexChanged.connect(self.cverlay.selectWindow)
        windowToolbar.addWidget(self.windowSelector)

        self.update()

    def setRunning(self, running: bool): self.runCheckbox.setChecked(running)

    def setLocked(self, locked: bool):
        self.lockCheckbox.setChecked(locked)
        self.windowSelector.setEnabled(not locked)

    def update(self):
        self.cverlay.update()
        self.windowSelector.clear()
        self.windowSelector.addItems([window[1] for window in self.cverlay.windows])

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.cverlay.quit()
        return super().closeEvent(a0)


class OverlayView(QtWidgets.QGraphicsView):
    def __init__(self, cverlay: 'CverlayWindow', maxFPS: int = 30):
        super().__init__()
        self.cverlay = cverlay
        self.maxFPS = maxFPS
        
        self.setupWindow()
        self.setupScene()

    def setupWindow(self):
        self.setStyleSheet("background: transparent; border: 0px;")
        self.setSceneRect(self.contentsRect().toRectF())  # remove scrollbar
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setBackgroundBrush(QtGui.QBrush(Qt.BrushStyle.NoBrush))
        self.showMaximized()

    def setupScene(self):
        self.setScene(QtWidgets.QGraphicsScene(QtGui.QGuiApplication.primaryScreen().geometry().toRectF()))

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent | None) -> None:
        # print("WINDOW CONTEXT")

        menu = QtWidgets.QMenu()
        # menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint)
        # menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        pos = event.pos()

        item = self.cverlay.layoutController.scannerAt(event.pos().toPointF())

        scene = self.scene()
    
        if item:
            # print("ITEM:", item.model._name)
            # print(item.view.sceneBoundingRect(), item.model._rect)

            toggleImage = menu.addAction("Hide Image" if item.isImageVisible() else "Show Image")
            toggleImage.triggered.connect(lambda: item.setImageVisible(not item.isImageVisible()))

            deleteAction = menu.addAction("Delete Scanner")
            deleteAction.triggered.connect(lambda: scene.removeItem(item.view))

        else:
            newAction = menu.addAction("New Scanner")
            newAction.triggered.connect(lambda: self.cverlay.layoutController.addScanner(f"Scanner #{len(self.cverlay.layoutController.view.childItems())}", lambda: (False, 0), (pos.x(), pos.y(), 100, 100)))

        deleteLayoutAction = menu.addAction("Delete Layout")
        deleteLayoutAction.triggered.connect(lambda: self.scene().removeItem(self.cverlay.layoutController.view))

        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(self.cverlay.quit)

        menu.exec(pos)
        return super().contextMenuEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent | None) -> None:
        clock = time.perf_counter() * self.maxFPS

        sleep = int(clock) + 1 - clock
        time.sleep(sleep / self.maxFPS)

        self.currTime = time.time()
        #fps = round(1 / (self.currTime - self.prevTime))
        #print("FPS:", fps)
        self.prevTime = self.currTime
        return super().paintEvent(event)


class CverlayWindow(QtWidgets.QMainWindow):
    def __init__(self, maxFPS: int = 30) -> None:
        super().__init__()
        self.maxFPS = maxFPS
        self.windows: list[tuple[int, str]] = self.getWindows()
        self.locked = False
        self.running = False
        self.layoutController: LayoutController = None
        self.agent: Agent = None

        self.setup()

        self.selectWindow(0)
        
    def setup(self):
        self.setupWindow()
        self.setupTray()
        self.setupHotkeys()

        self.view = OverlayView(self, self.maxFPS)
        self.gui = GUIWindow(self)

        self.setCentralWidget(self.view)
        self.gui.show()

    def setupWindow(self):
        self.setGeometry(QtGui.QGuiApplication.primaryScreen().geometry())
        self.setWindowFlags(Qt.WindowType.Tool|Qt.WindowType.X11BypassWindowManagerHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

    def setupTray(self):
        self.tray = SystemTrayIcon(QtGui.QIcon("res/icon.png"), self)
        self.tray.show()

    def setupHotkeys(self):
        self.manager = KeyboardManager(self)
        self.manager.addHotkey("CTRL+H", self.toggleHide)
        self.manager.addHotkey("CTRL+L", self.toggleLocked)
        self.manager.addHotkey("CTRL+R", self.toggleRun)
        self.manager.addHotkey("CTRL+Q", self.quit)
        # self.manager.addHotkey("F5", lambda: self.setRunning(True))
        # self.manager.addHotkey("F5", lambda: self.setRunning(False), trigger_on_release=True)

    def playAgent(self):
        if not self.agent: return
        self.agent.play()

    def pauseAgent(self):
        if not self.agent: return
        self.agent.pause()

    def playScanners(self):
        if not self.layoutController: return
        self.layoutController.play()

    def pauseScanners(self):
        if not self.layoutController: return
        self.layoutController.pause()

    def stop(self):
        if self.agent: self.agent.stop()
        if self.layoutController: self.layoutController.stop()

    def setLayoutController(self, controller: LayoutController):
        if self.layoutController:
            self.layoutController.stop()
            self.view.scene().removeItem(self.layoutController.view)

        self.layoutController = controller
        self.layoutController.start()
        self.setLocked(self.locked)

        self.view.scene().addItem(self.layoutController.view)
        
        self.layoutController.updateView()

    def setAgent(self, agent: Agent):
        if self.agent: self.agent.pause()
        self.agent = agent
    
    def setRunning(self, running: bool):
        if self.running == running: return
        
        self.running = running
        self.gui.runCheckbox.setChecked(running)

        if running:
            self.playScanners()
            if self.locked or not self.isVisible(): self.playAgent()
        else:
            self.pauseScanners()
            self.pauseAgent()

    def toggleRun(self): self.setRunning(not self.running)

    def toggleHide(self):
        visible = not self.isVisible()
        self.setVisible(visible)

        if self.running:
            if not visible: self.playAgent()
            else: self.pauseAgent()
        
    def setLocked(self, locked: bool):
        self.hide()
        self.locked = locked
        self.gui.setLocked(locked)
        self.layoutController.setLocked(locked)

        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, locked)    
        self.showMaximized()

        if self.running:
            if not locked: self.playAgent()
            else: self.pauseAgent()
            
    def toggleLocked(self): self.setLocked(not self.locked)

    def getWindows(self) -> list[tuple[int, str]]:
        return WindowComboBox.getWindows()
    
    def update(self):
        self.windows = self.getWindows()

    def quit(self):
        self.stop()
        self.tray.deleteLater()
        QtCore.QCoreApplication.quit()

    def selectWindow(self, index: int):
        print("Window:", index, self.windows[index])
        winId = self.windows[index][0]
        if self.layoutController: self.layoutController.setWinId(winId)
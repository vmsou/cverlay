import time
import win32gui

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

from cverlay.agent import Agent
from cverlay.window.combobox import WindowComboBox
from cverlay.window.hotkeys import KeyboardManager
from cverlay.window.tray import SystemTrayIcon
from cverlay.window.controller.layout import LayoutController


class AutomationView(QtWidgets.QGraphicsView):
    def __init__(self, scene: QtWidgets.QGraphicsScene, parent: QtWidgets.QMainWindow, maxFPS: int = 30):
        super().__init__(scene, parent)
        self.maxFPS = maxFPS
        self.currTime = self.prevTime = 0

        # Flags
        self.holdingShift = False

        self.setupView()

    def setupView(self):
        self.setStyleSheet("background: transparent; border: 0px;")
        self.setSceneRect(self.contentsRect().toRectF())  # remove scrollbar
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setBackgroundBrush(QtGui.QBrush(Qt.BrushStyle.NoBrush))
        self.showMaximized()
    
    def keyReleaseEvent(self, event: QtGui.QKeyEvent | None) -> None:
        if event.key() == Qt.Key.Key_Shift: 
            self.setBackgroundBrush(QtGui.QBrush(Qt.BrushStyle.NoBrush))

        return super().keyPressEvent(event)
    
    def paintEvent(self, event: QtGui.QPaintEvent | None) -> None:
        clock = time.perf_counter() * self.maxFPS

        sleep = int(clock) + 1 - clock
        time.sleep(sleep / self.maxFPS)

        self.currTime = time.time()
        #fps = round(1 / (self.currTime - self.prevTime))
        #print("FPS:", fps)
        self.prevTime = self.currTime
        return super().paintEvent(event)
    

class AutomationWindow(QtWidgets.QMainWindow):
    windowChanged = QtCore.pyqtSignal(int)

    def __init__(self, maxFPS: int = 30):
        super().__init__()
        self.maxFPS = maxFPS
        self.editable = True
        self.running = False
        self.layoutController: LayoutController = None
        self.agent: Agent = None

        self.setupWindow()
        self.createView()
        self.createTray()
        self.createHotkeys()

        self.refresh()

    def setupWindow(self):
        self.setGeometry(QtGui.QGuiApplication.primaryScreen().geometry())
        self.setWindowFlags(Qt.WindowType.Tool|Qt.WindowType.X11BypassWindowManagerHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.showMaximized()

    def createView(self):
        self.scene = QtWidgets.QGraphicsScene(QtGui.QGuiApplication.primaryScreen().geometry().toRectF())

        self.combobox = WindowComboBox()
        # self.combobox.opened.connect(self.refresh)
        self.combobox.activated.connect(self.onComboboxChange)

        self.runningCheckbox = QtWidgets.QCheckBox()
        self.runningCheckbox.setChecked(self.running)
        self.runningCheckbox.toggled.connect(self.onRunningCheckbox)

        self.scene.addWidget(self.runningCheckbox)
        self.scene.addWidget(self.combobox)
        
        self.view = AutomationView(self.scene, self, maxFPS=self.maxFPS)

        self.setCentralWidget(self.view)
    
    def createTray(self):
        self.tray = SystemTrayIcon(QtGui.QIcon("res/icon.png"), self.view)
        self.tray.show()

    def createHotkeys(self):
        self.manager = KeyboardManager(self)
        self.manager.addHotkey("F8", self.toggleHide)
        self.manager.addHotkey("F9", self.toggleEdit)
        self.manager.addHotkey("F10", self.toggleRun)
        # self.manager.addHotkey("F5", lambda: self.setRunning(True))
        # self.manager.addHotkey("F5", lambda: self.setRunning(False), trigger_on_release=True)

    def startAgent(self):
        if not self.agent: return
        self.agent.start()

    def stopAgent(self):
        if not self.agent: return
        self.agent.stop()

    def resumeScanners(self):
        if not self.layoutController: return
        self.layoutController.resume()

    def pauseScanners(self):
        if not self.layoutController: return
        self.layoutController.pause()

    def stop(self):
        if self.agent: self.agent.stop()
        if self.layoutController: self.layoutController.stop()

    def setWindowFromTitle(self, title: str):
        hwnd = win32gui.FindWindow(None, title)
        text = win32gui.GetWindowText(hwnd)
        self.combobox.setCurrentText(text)
        # print(title, hwnd, text)
        self.windowChanged.emit(hwnd)

    def onComboboxChange(self, index: int):
        hwnd = self.combobox.windows[index][0]
        self.windowChanged.emit(hwnd)

    def onRunningCheckbox(self, flag: bool):
        self.setRunning(flag)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent | None) -> None:
        # print("WINDOW CONTEXT")

        menu = QtWidgets.QMenu()
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        pos = event.pos()

        item = self.layoutController.scannerAt(event.pos().toPointF())

        scene = self.scene
    
        if item:
            # print("ITEM:", item.model._name)
            # print(item.view.sceneBoundingRect(), item.model._rect)

            toggleImage = menu.addAction("Hide Image" if item.isImageVisible() else "Show Image")
            toggleImage.triggered.connect(lambda: item.setImageVisible(not item.isImageVisible()))

            deleteAction = menu.addAction("Delete Scanner")
            deleteAction.triggered.connect(lambda: scene.removeItem(item.view))

        else:
            newAction = menu.addAction("New Scanner")
            newAction.triggered.connect(lambda: self.layoutController.addScanner(f"Scanner #{len(self.layoutController.view.childItems())}", lambda: (False, 0), (pos.x(), pos.y(), 100, 100)))

        deleteLayoutAction = menu.addAction("Delete Layout")
        deleteLayoutAction.triggered.connect(lambda: self.scene.removeItem(self.layoutController.view))

        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(self.quit)

        menu.exec(pos)
        return super().contextMenuEvent(event)
    
    def setLayoutController(self, controller: LayoutController):
        if self.layoutController:
            self.layoutController.stop()
            self.windowChanged.disconnect(self.layoutController.setHwnd)
            self.scene.removeItem(self.layoutController.view)

        self.layoutController = controller
        self.layoutController.start()
        self.setEdit(self.editable)
        self.windowChanged.connect(self.layoutController.setHwnd)

        self.scene.addItem(self.layoutController.view)
        
        self.layoutController.updateView()

    def setAgent(self, agent: Agent):
        if self.agent: self.agent.stop()
        self.agent = agent

    def quit(self):
        self.stop()
        self.tray.deleteLater()
        QtCore.QCoreApplication.quit()

    def setRunning(self, running: bool):
        if self.running == running: return
        
        self.running = running

        self.runningCheckbox.blockSignals(True)
        self.runningCheckbox.setChecked(running)
        self.runningCheckbox.blockSignals(False)

        if running:
            self.resumeScanners()
            if not self.editable or not self.view.isVisible(): self.startAgent()
        else:
            self.pauseScanners()
            self.stopAgent()


    def toggleRun(self):
        self.setRunning(not self.running)

    def toggleHide(self):
        visible = not self.view.isVisible()
        self.view.setVisible(visible)

        if self.running:
            if not visible: self.startAgent()
            else: self.stopAgent()
        

    def setEdit(self, edit: bool):
        self.hide()
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not edit)
        self.editable = edit
        self.combobox.setEnabled(edit)
        self.runningCheckbox.setEnabled(edit)
        self.layoutController.setEditing(edit)
        self.showMaximized()

        if self.running:
            if not edit: self.startAgent()
            else: self.stopAgent()
            

    def toggleEdit(self):
        self.setEdit(not self.editable)

    def refresh(self):
        # print("[REFRESH]")
        if self.layoutController: self.layoutController.updateView()
        self.combobox.setFixedWidth(QtGui.QGuiApplication.primaryScreen().geometry().width() // 2)
        self.combobox.move(int(self.scene.sceneRect().center().x() - self.combobox.rect().width() // 2), 0)
        self.runningCheckbox.move(self.combobox.geometry().topRight() + QtCore.QPoint(5, 0))

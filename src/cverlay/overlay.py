import sys

from PyQt6 import QtWidgets

from cverlay.window.window import AutomationWindow
from cverlay.window.model import Scanner, Layout
from cverlay.window.controller.layout import LayoutController
from cverlay.window.view.layout import LayoutView

from cverlay.agent import Agent


class Overlay:
    """This class represents and manages the scanners on the screen.

    Able to choose scanners layout with `setLayout()` (overlay has a default layout, which can be updated using `addScanner`)
    
    You can also attach an Agent for automation with `setAgent()` method.
    
    Attributes:
        window_title : str
            Searches for window to attach scanners to. If set to None, window must be manually set through Application GUI
        maxFPS : int
            FPS at which screen captures occurs
        appMaxFPS : int
            Application FPS (Drawings on the screen). Defaults to 30 FPS, but it can be lowered for better performance
        hardwareAccel : bool
            Some application may appear as blank images with traditional screen capture methods. If set to true; screen capture handles hardware acceleration

    Example: 
        .. code-block:: python

        # see more examples at examples folder
        from cverlay import Overlay, Scanner
        from cverlay.detector.builder import DetectorBuilder

        overlay = Overlay(maxFPS=2, hardwareAccel=True)
        blueDetector =  DetectorBuilder().color("blue", (80, 44, 0), (121, 255, 255), color="#000080").build()
        blueScanner = Scanner("Blue", blueDetector, (500, 500, 100, 100))
        overlay.addScanner(blueScanner)
        overlay.exec()
    """

    def __init__(self, window_title: str | None = None, maxFPS: int = 1, appMaxFPS: int = 30, hardwareAccel: bool = False):
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.window = AutomationWindow(appMaxFPS)

        if window_title: self.window.setWindowFromTitle(window_title)

        self._load()

        self.setLayout(Layout(None, maxFPS, hardwareAccel))

    def _load(self, filepath="res/style.qss"):
        """file = QtCore.QFile(filepath)
        file.open(file.OpenModeFlag.ReadOnly)
        qd = QtCore.QStringDecoder(QtCore.QStringConverter.Encoding.Latin1)
        styleSheet = qd.decode(file.readAll())
        self.app.setStyleSheet(styleSheet)
        """
        with open(filepath) as f:
            self.app.setStyleSheet(f.read())

    def getLayout(self) -> Layout:
        return self.layoutController.model

    def setLayout(self, layout: Layout):
        view = LayoutView()
        controller = LayoutController(layout, view)
        self.layoutController = controller
        self.window.setLayoutController(controller)

    def addScanner(self, scanner: Scanner):
        self.layoutController.addScanner(scanner)
        self.layoutController.updateView()

    def getAgent(self) -> Agent | None: return self.agent

    def setAgent(self, agent: Agent):
        self.agent = agent
        self.window.setAgent(agent)

    def exec(self) -> int: return self.app.exec()

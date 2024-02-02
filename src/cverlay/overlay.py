import sys

from PyQt6 import QtWidgets, QtCore

from cverlay.window.window import OverlayView, CverlayWindow
from cverlay.window.model import Scanner, Layout
from cverlay.window.controller.layout import LayoutController
from cverlay.window.view.layout import LayoutView

from cverlay.agent import Agent


class Overlay:
    """This class represents and manages the scanners on the screen.

    Able to choose scanners layout with `setLayout()` (overlay has a default layout, which can be updated using `addScanner`)
    
    You can also attach an Agent for automation with `setAgent()` method.
    
    Attributes:
        visionMaxFPS : int
            FPS at which screen captures occurs
        drawMaxFPS : int
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

    def __init__(self, visionMaxFPS: int = 1, drawMaxFPS: int = 30, hardwareAccel: bool = False):
        self.app = QtWidgets.QApplication(sys.argv)
        QtCore.QCoreApplication.setOrganizationName("vmsou")
        QtCore.QCoreApplication.setApplicationName("cverlay")
        QtCore.QCoreApplication.setApplicationVersion("0.1")

        self.app.setQuitOnLastWindowClosed(False)
        self.window = CverlayWindow(drawMaxFPS)

        self.setLayout(Layout(None, visionMaxFPS, hardwareAccel))

        self.window.show()

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

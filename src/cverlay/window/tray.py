from PyQt6 import QtWidgets, QtGui, QtCore


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon: QtGui.QIcon,  view: QtWidgets.QGraphicsView = None):
        super().__init__(icon)
        self.view = view
        self.menu = QtWidgets.QMenu()

        hideAction = self.menu.addAction("Hide")
        exitAction = self.menu.addAction("Exit")

        def menuUpdate():
            visible = self.view.isVisible()
            hideAction.setText("Hide" if visible else "Show")

        def hideToggle():
            visible = not self.view.isVisible()
            self.view.setVisible(visible)

        self.activated.connect(menuUpdate)
        hideAction.triggered.connect(hideToggle)
        exitAction.triggered.connect(QtCore.QCoreApplication.quit)

        self.setContextMenu(self.menu)
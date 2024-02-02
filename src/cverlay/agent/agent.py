import time

from abc import ABC, abstractmethod
from threading import Thread

import win32api, win32con

from cverlay.layout import Layout


class Agent(ABC):
    def __init__(self, layout: Layout | None = None):
        self.layout: Layout = layout
        self.status = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    @abstractmethod
    def run(self): ...

    def getStatus(self) -> bool:
        return self.status

    def setLayout(self, layout: Layout):
        self.layout = layout

    def play(self):
        self.status = True

    def pause(self):
        self.status = False

    def stop(self):
        self.status = False

    def toggle(self):
        if self.status: self.pause()
        else: self.play()

    def sleep(self, secs: float):
        time.sleep(secs)

    def click(self, pos: tuple[int, int]):
        win32api.SetCursorPos(pos)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def clickRegionPos(self, targetPos: tuple[int, int], regionRect: tuple[int, int, int, int]):
        self.click((regionRect[0] + targetPos[0], regionRect[1] + targetPos[1]))

    def clickRegionRect(self, targetRect: tuple[int, int, int, int], regionRect: tuple[int, int, int, int]):
        dW = targetRect[2] // 2
        dH = targetRect[3] // 2
        x = regionRect[0] + targetRect[0] + dW
        y = regionRect[1] + targetRect[1] + dH
        self.click((x, y))

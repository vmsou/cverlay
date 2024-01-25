import math
import time

from ctypes import windll
from PIL import Image

import cv2
import numpy as np
import win32api, win32gui, win32ui, win32con

from PyQt6 import QtCore

from cverlay.common.thread import PausableThread


class WindowCapture:
    BORDER_PIXELS = 8
    def __init__(self, hwnd: int = None, hardwareAccel: bool = False):
        super().__init__()
        self.screenSize: tuple[int, int] = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)  # TODO: DPI Scaling
        self.setHwnd(hwnd)  # updates windowRect
        self.setHardwareAccel(hardwareAccel)
        self.img = np.zeros((self.screenSize[0], self.screenSize[1], 3), np.uint8)

        if hardwareAccel:
            # windll.user32.SetProcessDPIAware()
            self.screenshotFunc = self.hardwareScreenshot
        else:
            self.screenshotFunc = self.normalScreenshot

    def getHwnd(self) -> int: return self.hwnd

    def isHardwareAccel(self) -> int: return self.hardwareAccel

    def setHwnd(self, hwnd: int | None):
        if hwnd is None: hwnd = win32gui.GetDesktopWindow()
        self.hwnd = hwnd

    def setHardwareAccel(self, hardwareAccel: bool): self.hardwareAccel = hardwareAccel

    def setWindowRect(self, rect: tuple[int, int, int, int]):
        self.windowRect = rect
        self.img = np.zeros((rect[3], rect[2], 3), np.uint8)

    def screenshot(self) -> np.ndarray:
        """Screenshots screen whether it is hardware accelerated or not."""
        return self.screenshotFunc()

    def normalScreenshot(self) -> np.ndarray:
        if not win32gui.IsWindow(self.hwnd): return self.img
        
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        x, y, w, h = left, top, right - left, bottom - top

        # Capture Window
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (w, h), dcObj, (0, 0), win32con.SRCCOPY)
        # dataBitMap.SaveBitmapFile(cDC, "res/out.bmp")

        # Convert to Array
        bmpinfo = dataBitMap.GetInfo()
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        # arr: np.ndarray = np.frombuffer(signedIntsArray, dtype="uint8")
        # arr.shape = (h, w, 4)
        im = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), signedIntsArray, 'raw', 'RGBA', 0, 1)

        # Black background (Screensize)
        bbox = -x, -y, self.screenSize[0] - x, self.screenSize[1] - y
        arr = np.array(im.crop(bbox))

        # Release
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # return arr[:,:,:3] 
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    
    def hardwareScreenshot(self) -> np.ndarray:
        """Able to Screenshot Windows with Hardware Acceleration. (Slower Performance)"""
        if not win32gui.IsWindow(self.hwnd): return self.img

        # TODO: Find better way to get correct dimensions
        x_margin = 8
        y_margin = 0
        if win32gui.GetWindowPlacement(self.hwnd)[1] == win32con.SW_SHOWMAXIMIZED:
            x_margin = 8
            y_margin = 8

        #rect = wintypes.RECT()
        #DWMWA_EXTENDED_FRAME_BOUNDS = 9
        #windll.dwmapi.DwmGetWindowAttribute(wintypes.HWND(self.hwnd),  wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS), ctypes.byref(rect), ctypes.sizeof(rect))
        #x, y, w, h = rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top

        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        x, y, w, h = left, top, right - left, bottom - top
        
        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bitmap)

        windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 3)

        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
              
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        im = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'RGBA', 0, 1)
        bbox = -x - x_margin, -y - y_margin, self.screenSize[0] - x, self.screenSize[1] - y
        arr = np.array(im.crop(bbox))
        
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)


class WindowCaptureThread(PausableThread):
    class Signals(QtCore.QObject):
        capture = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, hwnd: int = None, maxFPS: int = 1, hardwareAccel: bool = False):
        super().__init__(daemon=True)
        self.signals = self.Signals()

        self.wc = WindowCapture(hwnd, hardwareAccel)
        self.maxFPS: int = maxFPS

        self.active = False
        self.img = self.wc.img

        # Timing
        self.currTime = self.prevTime = self.fps = self.prevUpdateTime = 0

    def getHwnd(self) -> int:
        return self.wc.getHwnd()

    def getMaxFPS(self) -> int:
        return self.maxFPS

    def isHardwareAccel(self) -> bool:
        return self.wc.isHardwareAccel()
    
    def setHwnd(self, hwnd: int):
        self.wc.setHwnd(hwnd)

    def setMaxFPS(self, maxFPS):
        self.maxFPS = maxFPS
    
    def setHardwareAccel(self, hardwareAccel: bool):
        self.wc.setHardwareAccel(hardwareAccel)

    def setRect(self, rect: tuple[int, int, int, int]):
        self.wc.setWindowRect(rect)

    def screenshot(self) -> np.ndarray:
        return self.wc.screenshot()
    
    def getImage(self) -> np.ndarray:
        return self.img

    def onImage(self, img: np.ndarray):
        self.img = img
        self.signals.capture.emit(img)

    def target(self):
        clock = time.perf_counter() * self.maxFPS
        sleep = int(clock) + 1 - clock
        time.sleep(sleep / self.maxFPS)

        self.currTime = time.time()
        if (self.currTime - self.prevUpdateTime) > 1:
            fps = math.ceil(1/(self.currTime - self.prevTime))
            fps = int(fps)
            self.prevUpdateTime = self.currTime
            # print(fps)

        img = self.screenshot()
        self.onImage(img)

        self.prevTime = self.currTime

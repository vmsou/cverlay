import time

from collections.abc import Callable, Iterable, Mapping
from threading import Thread, Event
from typing import Any

class PausableThread(Thread):
    def __init__(self, group: None = None, target: Callable[..., object] | None = None, name: str | None = None, args: Iterable[Any] = (), kwargs: Mapping[str, Any] | None = None, *, daemon: bool | None = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self._runEvent = Event()
        self._statusEvent = Event()

        if target:
            self.target: Callable[[], None] = lambda: target(*self._args, **self._kwargs)

    def status(self) -> bool: return self._runEvent.is_set()

    def target(self) -> None:
        raise NotImplementedError("'target' must be implemented or defined at constructor")
    
    # Thread Methods
    def start(self, play: bool = True) -> None:
        # Set Loop and Unpaused to True
        self._runEvent.set()
        if play: self._statusEvent.set()
        return super().start()
    
    def stop(self):
        self._statusEvent.clear()
        self._runEvent.clear()

    # Playback status
    def isRunning(self): return self._runEvent.is_set()
    def isPlaying(self) -> bool: return self._statusEvent.is_set()
    def isPaused(self) -> bool: return not self.isPlaying()

    # Playback methods
    def resume(self): self._statusEvent.set()
    def pause(self): self._statusEvent.clear()
    def toggle(self):
        if self.isPlaying(): self.pause()
        else: self.resume()

    def run(self) -> None:
        super().run
        while self.isRunning():
            self._statusEvent.wait()
            self.target()


class PrintThread(PausableThread):
    def target(self) -> None:
        print("Hello, World!")
        time.sleep(0.5)
        

def main() -> None:
    def target():
        print("Hello, World!")
        time.sleep(0.5)

    t = PausableThread(target=target)
    t = PrintThread()
    print("[WAIT] 1s")
    time.sleep(1)
    print("[RUN] 2s")
    t.start(play=False)
    time.sleep(2)
    t.resume()
    print("[WAIT] 2s")
    t.pause()
    time.sleep(2)
    print("[RUN] 3s")
    t.resume()
    time.sleep(3)
    print("[STOP]")
    t.stop()


if __name__ == "__main__":
    main()
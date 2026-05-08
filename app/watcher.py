import os
import threading
from typing import Callable, Optional


class FileWatcher:
    def __init__(self, file_path: str, callback: Callable, interval: float = 1.0):
        self._file_path = file_path
        self._callback = callback
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_mtime: Optional[float] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._last_mtime = self._get_mtime()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _get_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self._file_path)
        except FileNotFoundError:
            return None

    def _run(self) -> None:
        # wait returns True when stop_event is set, False on timeout
        while not self._stop_event.wait(self._interval):
            mtime = self._get_mtime()
            if mtime != self._last_mtime:
                self._last_mtime = mtime
                self._callback()

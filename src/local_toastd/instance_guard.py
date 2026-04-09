from __future__ import annotations

import ctypes
import os
from pathlib import Path

from PySide6.QtCore import QLockFile

APP_NAME = "local-toastd"
LOCK_FILE_NAME = "instance.lock"


def resolve_lock_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = Path(local_app_data)
    else:
        base_dir = Path.home() / ".local" / "state"
    return base_dir / APP_NAME / LOCK_FILE_NAME


class SingleInstanceGuard:
    def __init__(self, lock_path: Path | None = None) -> None:
        self.lock_path = lock_path or resolve_lock_path()
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = QLockFile(str(self.lock_path))
        self._lock_file.setStaleLockTime(1000)

    def acquire(self) -> bool:
        return self._lock_file.tryLock(0)

    def release(self) -> None:
        if self._lock_file.isLocked():
            self._lock_file.unlock()


def show_already_running_message() -> None:
    if os.name != "nt":
        return

    user32 = ctypes.windll.user32
    user32.MessageBoxW(
        None,
        "local-toastd は既に起動しています。",
        APP_NAME,
        0x00000040,
    )

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .app import ToastDaemon
from .instance_guard import SingleInstanceGuard, show_already_running_message


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    guard = SingleInstanceGuard()
    if not guard.acquire():
        logging.getLogger(__name__).warning("local-toastd is already running")
        show_already_running_message()
        return 1

    app = QApplication(sys.argv)
    try:
        daemon = ToastDaemon(app)
        daemon.start()
        return app.exec()
    finally:
        guard.release()


if __name__ == "__main__":
    raise SystemExit(main())

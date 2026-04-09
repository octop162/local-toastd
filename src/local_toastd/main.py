from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .app import ToastDaemon


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    daemon = ToastDaemon(app)
    daemon.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

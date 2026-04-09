from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


def resolve_app_icon_path(*, project_root: Path | None = None) -> Path | None:
    root = project_root or Path(__file__).resolve().parents[2]
    dev_icon = root / "icons" / "icon.ico"
    if dev_icon.exists():
        return dev_icon

    packaged_icon = (
        files("local_toastd")
        .joinpath("assets")
        .joinpath("icons")
        .joinpath("app.ico")
    )
    packaged_icon_path = Path(str(packaged_icon))
    if packaged_icon_path.exists():
        return packaged_icon_path

    return None


def load_app_icon(*, project_root: Path | None = None) -> QIcon:
    icon_path = resolve_app_icon_path(project_root=project_root)
    if icon_path is not None:
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            return icon
    return build_fallback_icon()


def build_fallback_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#0ea5e9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 28, 28, 8, 8)
    painter.setBrush(QColor("#f8fafc"))
    painter.drawEllipse(9, 8, 14, 14)
    painter.end()

    return QIcon(pixmap)

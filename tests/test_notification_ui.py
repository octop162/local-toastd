from __future__ import annotations

from typing import cast

from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from local_toastd.models import NotificationPayload
from local_toastd.notification_ui import (
    ToastNotificationWidget,
    palette_for_level,
    stack_notification_geometries,
)
from local_toastd.queue_manager import ManagedNotification


def make_widget() -> ToastNotificationWidget:
    payload = NotificationPayload.from_mapping(
        {
            "title": "test",
            "message": "click me",
            "duration_ms": 30_000,
        }
    )
    notification = ManagedNotification(notification_id=1, payload=payload)
    return ToastNotificationWidget(notification, theme_name="dark")


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def test_stack_notification_geometries_places_toasts_top_right() -> None:
    screen = QRect(0, 0, 1920, 1080)
    sizes = [QSize(450, 120), QSize(450, 140), QSize(450, 100)]

    geometries = stack_notification_geometries(screen, sizes, margin=16, spacing=12)

    assert [(rect.x(), rect.y(), rect.width(), rect.height()) for rect in geometries] == [
        (1454, 16, 450, 120),
        (1454, 148, 450, 140),
        (1454, 300, 450, 100),
    ]


def test_palette_for_level_returns_distinct_visual_tokens() -> None:
    success = palette_for_level("dark", "success")
    error = palette_for_level("light", "error")

    assert success.accent == "#22c55e"
    assert error.accent == "#dc2626"
    assert success.background != error.background


def test_left_click_dismisses_notification_once() -> None:
    app = get_app()
    widget = make_widget()
    dismissed_ids: list[int] = []
    widget.dismissed.connect(dismissed_ids.append)
    widget.show()
    app.processEvents()

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(20, 20),
        QPointF(20, 20),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)
    widget.close()
    app.processEvents()

    assert dismissed_ids == [1]


def test_right_click_does_not_dismiss_notification() -> None:
    app = get_app()
    widget = make_widget()
    dismissed_ids: list[int] = []
    widget.dismissed.connect(dismissed_ids.append)

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(20, 20),
        QPointF(20, 20),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    assert dismissed_ids == []

    widget.close()
    app.processEvents()

    assert dismissed_ids == [1]

from __future__ import annotations

from typing import cast

from PySide6.QtCore import QPointF, QRect, QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from local_toastd.models import NotificationPayload
from local_toastd.notification_types import NOTIFICATION_TYPE_B, NOTIFICATION_TYPE_D
from local_toastd.notification_ui import (
    ToastNotificationWidget,
    palette_for_type,
    stack_notification_geometries,
    toast_width_for_font_size,
)
from local_toastd.queue_manager import ManagedNotification


def make_widget(*, font_size: int = 13) -> ToastNotificationWidget:
    payload = NotificationPayload.from_mapping(
        {
            "title": "test",
            "message": "click me",
            "duration_ms": 30_000,
        }
    )
    notification = ManagedNotification(notification_id=1, payload=payload)
    return ToastNotificationWidget(notification, theme_name="dark", font_size=font_size)


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def test_stack_notification_geometries_places_toasts_top_right() -> None:
    screen = QRect(0, 0, 1920, 1080)
    sizes = [QSize(450, 120), QSize(450, 140), QSize(450, 100)]

    geometries = stack_notification_geometries(
        screen,
        sizes,
        position="top_right",
        margin=16,
        spacing=12,
    )

    assert [(rect.x(), rect.y(), rect.width(), rect.height()) for rect in geometries] == [
        (1454, 16, 450, 120),
        (1454, 148, 450, 140),
        (1454, 300, 450, 100),
    ]


def test_stack_notification_geometries_places_toasts_top_center() -> None:
    screen = QRect(0, 0, 1920, 1080)
    sizes = [QSize(450, 120), QSize(450, 140)]

    geometries = stack_notification_geometries(
        screen,
        sizes,
        position="top_center",
        margin=16,
        spacing=12,
    )

    assert [(rect.x(), rect.y(), rect.width(), rect.height()) for rect in geometries] == [
        (735, 16, 450, 120),
        (735, 148, 450, 140),
    ]


def test_stack_notification_geometries_places_toasts_bottom_right() -> None:
    screen = QRect(0, 0, 1920, 1080)
    sizes = [QSize(450, 120), QSize(450, 140), QSize(450, 100)]

    geometries = stack_notification_geometries(
        screen,
        sizes,
        position="bottom_right",
        margin=16,
        spacing=12,
    )

    assert [(rect.x(), rect.y(), rect.width(), rect.height()) for rect in geometries] == [
        (1454, 944, 450, 120),
        (1454, 792, 450, 140),
        (1454, 680, 450, 100),
    ]


def test_palette_for_type_returns_distinct_visual_tokens() -> None:
    success = palette_for_type("dark", NOTIFICATION_TYPE_B)
    error = palette_for_type("light", NOTIFICATION_TYPE_D)

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


def test_apply_theme_updates_font_sizes() -> None:
    widget = make_widget(font_size=16)

    assert "font-size: 18px;" in widget.styleSheet()
    assert "font-size: 16px;" in widget.styleSheet()
    assert widget.width() == toast_width_for_font_size(16)


def test_toast_width_scales_with_font_size() -> None:
    small = toast_width_for_font_size(13)
    large = toast_width_for_font_size(30)

    assert small == 450
    assert large == 858
    assert large > small


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

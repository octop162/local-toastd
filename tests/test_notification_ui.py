from __future__ import annotations

from PySide6.QtCore import QRect, QSize

from local_toastd.notification_ui import palette_for_level, stack_notification_geometries


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

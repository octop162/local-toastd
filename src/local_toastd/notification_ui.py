from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QMouseEvent, QShowEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .notification_types import (
    NOTIFICATION_TYPE_A,
    NOTIFICATION_TYPE_B,
    NOTIFICATION_TYPE_C,
    NOTIFICATION_TYPE_D,
    NotificationType,
)
from .queue_manager import ManagedNotification
from .settings import DEFAULT_FONT_SIZE, ThemeName, ToastPosition

TOAST_MARGIN = 16
TOAST_SPACING = 12
TOAST_BASE_WIDTH = 450
TOAST_WIDTH_PER_FONT_SIZE = 24
TITLE_FONT_DELTA = 2
FADE_IN_MS = 180
FADE_OUT_MS = 220


@dataclass(frozen=True, slots=True)
class LevelPalette:
    accent: str
    background: str
    border: str
    title: str
    body: str


THEME_TYPE_PALETTES: dict[ThemeName, dict[NotificationType, LevelPalette]] = {
    "dark": {
        NOTIFICATION_TYPE_A: LevelPalette(
            accent="#0ea5e9",
            background="#0f172a",
            border="#0369a1",
            title="#f8fafc",
            body="#e0f2fe",
        ),
        NOTIFICATION_TYPE_B: LevelPalette(
            accent="#22c55e",
            background="#052e16",
            border="#15803d",
            title="#f0fdf4",
            body="#dcfce7",
        ),
        NOTIFICATION_TYPE_C: LevelPalette(
            accent="#f59e0b",
            background="#451a03",
            border="#b45309",
            title="#fffbeb",
            body="#fef3c7",
        ),
        NOTIFICATION_TYPE_D: LevelPalette(
            accent="#ef4444",
            background="#450a0a",
            border="#b91c1c",
            title="#fef2f2",
            body="#fee2e2",
        ),
    },
    "light": {
        NOTIFICATION_TYPE_A: LevelPalette(
            accent="#0284c7",
            background="#f8fafc",
            border="#7dd3fc",
            title="#0f172a",
            body="#1e3a8a",
        ),
        NOTIFICATION_TYPE_B: LevelPalette(
            accent="#16a34a",
            background="#f0fdf4",
            border="#86efac",
            title="#14532d",
            body="#166534",
        ),
        NOTIFICATION_TYPE_C: LevelPalette(
            accent="#d97706",
            background="#fffbeb",
            border="#fcd34d",
            title="#78350f",
            body="#92400e",
        ),
        NOTIFICATION_TYPE_D: LevelPalette(
            accent="#dc2626",
            background="#fef2f2",
            border="#fca5a5",
            title="#7f1d1d",
            body="#991b1b",
        ),
    },
}


def palette_for_type(theme_name: ThemeName, notification_type: NotificationType) -> LevelPalette:
    return THEME_TYPE_PALETTES[theme_name][notification_type]


def toast_width_for_font_size(font_size: int) -> int:
    return TOAST_BASE_WIDTH + ((font_size - DEFAULT_FONT_SIZE) * TOAST_WIDTH_PER_FONT_SIZE)


def stack_notification_geometries(
    screen_rect: QRect,
    sizes: Sequence[QSize],
    position: ToastPosition = "top_right",
    margin: int = TOAST_MARGIN,
    spacing: int = TOAST_SPACING,
) -> list[QRect]:
    geometries: list[QRect] = []
    if position == "bottom_right":
        current_y = screen_rect.y() + screen_rect.height() - margin
        for size in sizes:
            current_y -= size.height()
            x = _notification_x(screen_rect, size, position, margin)
            geometries.append(QRect(x, current_y, size.width(), size.height()))
            current_y -= spacing
        return geometries

    current_y = screen_rect.y() + margin
    for size in sizes:
        x = _notification_x(screen_rect, size, position, margin)
        geometries.append(QRect(x, current_y, size.width(), size.height()))
        current_y += size.height() + spacing

    return geometries


def _notification_x(
    screen_rect: QRect,
    size: QSize,
    position: ToastPosition,
    margin: int,
) -> int:
    if position == "top_center":
        return screen_rect.x() + (screen_rect.width() - size.width()) // 2
    return screen_rect.x() + screen_rect.width() - margin - size.width()


class ToastNotificationWidget(QFrame):
    dismissed = Signal(int)

    def __init__(
        self,
        notification: ManagedNotification,
        theme_name: ThemeName,
        font_size: int = 13,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.notification = notification
        self.theme_name = theme_name
        self.font_size = font_size
        self._dismissed = False
        self._visible_once = False
        self._closing = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        self.setWindowOpacity(0.0)
        self._fade_in = self._create_animation(0.0, 1.0, FADE_IN_MS)
        self._fade_out = self._create_animation(1.0, 0.0, FADE_OUT_MS)
        self._fade_in.finished.connect(self._start_lifetime_timer)
        self._fade_out.finished.connect(super().close)

        self.setObjectName("toastNotification")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._sync_width()
        self._build_ui()
        self.apply_theme(self.theme_name, font_size=self.font_size)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._visible_once:
            return
        self._visible_once = True
        self._fade_in.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._emit_dismissed_once()
        super().closeEvent(event)

    def dismiss(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._timer.stop()
        self._fade_out.start()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dismiss()
            event.accept()
            return
        super().mousePressEvent(event)

    def _emit_dismissed_once(self) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        self.dismissed.emit(self.notification.notification_id)

    def apply_theme(self, theme_name: ThemeName, *, font_size: int | None = None) -> None:
        self.theme_name = theme_name
        if font_size is not None:
            self.font_size = font_size
        self._sync_width()
        palette = palette_for_type(
            self.theme_name,
            self.notification.payload.notification_type,
        )
        title_font_size = self.font_size + TITLE_FONT_DELTA
        self.setStyleSheet(
            f"""
            QFrame#toastCard {{
                background-color: {palette.background};
                border-radius: 16px;
                border: 1px solid {palette.border};
            }}
            QFrame#toastAccentBar {{
                background-color: {palette.accent};
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
            }}
            QLabel#toastTitle {{
                color: {palette.title};
                font-size: {title_font_size}px;
                font-weight: 700;
            }}
            QLabel#toastBody {{
                color: {palette.body};
                font-size: {self.font_size}px;
            }}
            """
        )

    def _build_ui(self) -> None:

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        card = QFrame(self)
        card.setObjectName("toastCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        root_layout.addWidget(card)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        accent_bar = QFrame(card)
        accent_bar.setObjectName("toastAccentBar")
        accent_bar.setFixedWidth(6)
        accent_bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        card_layout.addWidget(accent_bar)

        content = QWidget(card)
        content.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(6)

        if self.notification.payload.title:
            title_label = QLabel(self.notification.payload.title, content)
            title_label.setObjectName("toastTitle")
            title_label.setWordWrap(True)
            title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            content_layout.addWidget(title_label)

        body_label = QLabel(self.notification.payload.message, content)
        body_label.setObjectName("toastBody")
        body_label.setWordWrap(True)
        body_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        content_layout.addWidget(body_label)
        card_layout.addWidget(content)

    def _create_animation(
        self,
        start_value: float,
        end_value: float,
        duration_ms: int,
    ) -> QPropertyAnimation:
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(duration_ms)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    def _sync_width(self) -> None:
        self.setFixedWidth(toast_width_for_font_size(self.font_size))

    def _start_lifetime_timer(self) -> None:
        self._timer.start(self.notification.payload.duration_ms)

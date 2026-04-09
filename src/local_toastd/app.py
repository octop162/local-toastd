from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .http_server import LocalHttpServer
from .models import NotificationPayload
from .notification_ui import ToastNotificationWidget, stack_notification_geometries
from .queue_manager import ManagedNotification, NotificationManager, NotificationUpdate
from .sound import play_notification_sound

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 8765


class NotificationBridge(QObject):
    notification_received = Signal(object)


class ToastDaemon(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.bridge = NotificationBridge()
        self.manager = NotificationManager(max_visible=4)
        self.active_widgets: dict[int, ToastNotificationWidget] = {}
        self.tray_icon = self._create_tray_icon()
        self.pause_action: QAction | None = None
        self.resume_action: QAction | None = None
        self.http_server = LocalHttpServer(HOST, PORT, self._receive_from_http)

        self.bridge.notification_received.connect(self._handle_notification_on_ui_thread)
        self.app.aboutToQuit.connect(self.shutdown)

    def start(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("System tray is not available on this system.")

        self._build_tray_menu()
        self.tray_icon.show()
        self.http_server.start()
        self._refresh_tooltip()
        logger.info("local-toastd is running")

    def shutdown(self) -> None:
        self.http_server.stop()
        self._clear_widgets()
        self.tray_icon.hide()

    def _receive_from_http(self, payload: NotificationPayload) -> int:
        update = self.manager.enqueue(payload)
        self.bridge.notification_received.emit(update)
        return update.snapshot.total_count

    def _handle_notification_on_ui_thread(self, update: NotificationUpdate) -> None:
        self._apply_notification_update(update)
        state = "paused" if update.snapshot.paused else "running"
        logger.info(
            "Notification update on UI thread (state=%s active=%s waiting=%s activated=%s)",
            state,
            update.snapshot.active_count,
            update.snapshot.waiting_count,
            len(update.activated),
        )
        self._refresh_tooltip()

    def _build_tray_menu(self) -> None:
        menu = QMenu()

        self.pause_action = QAction("Pause notifications", self.app)
        self.pause_action.triggered.connect(self.pause_notifications)
        menu.addAction(self.pause_action)

        self.resume_action = QAction("Resume notifications", self.app)
        self.resume_action.triggered.connect(self.resume_notifications)
        self.resume_action.setEnabled(False)
        menu.addAction(self.resume_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def pause_notifications(self) -> None:
        snapshot = self.manager.pause()
        if self.pause_action is not None:
            self.pause_action.setEnabled(False)
        if self.resume_action is not None:
            self.resume_action.setEnabled(True)
        self._refresh_tooltip()
        logger.info(
            "Notifications paused (active=%s waiting=%s)",
            snapshot.active_count,
            snapshot.waiting_count,
        )

    def resume_notifications(self) -> None:
        update = self.manager.resume()
        if self.pause_action is not None:
            self.pause_action.setEnabled(True)
        if self.resume_action is not None:
            self.resume_action.setEnabled(False)
        self._refresh_tooltip()
        logger.info(
            "Notifications resumed (active=%s waiting=%s activated=%s)",
            update.snapshot.active_count,
            update.snapshot.waiting_count,
            len(update.activated),
        )
        self._apply_notification_update(update)

    def _refresh_tooltip(self) -> None:
        snapshot = self.manager.snapshot()
        status = "paused" if snapshot.paused else "running"
        self.tray_icon.setToolTip(
            "local-toastd"
            f" ({status})\nHTTP: http://{HOST}:{PORT}\n"
            f"Active: {snapshot.active_count}\nWaiting: {snapshot.waiting_count}"
        )

    def _apply_notification_update(self, update: NotificationUpdate) -> None:
        if update.completed is not None:
            self._remove_widget(update.completed.notification_id)

        for notification in update.activated:
            self._ensure_widget(notification)

        self._restack_widgets()
        self._refresh_tooltip()

    def _ensure_widget(self, notification: ManagedNotification) -> None:
        if notification.notification_id in self.active_widgets:
            return

        widget = ToastNotificationWidget(notification)
        widget.dismissed.connect(self._dismiss_notification)
        self.active_widgets[notification.notification_id] = widget
        play_notification_sound(
            notification.payload.level,
            enabled=notification.payload.sound,
        )
        widget.show()

    def _dismiss_notification(self, notification_id: int) -> None:
        if notification_id not in self.active_widgets:
            return

        update = self.manager.complete(notification_id)
        self._apply_notification_update(update)

    def _remove_widget(self, notification_id: int) -> None:
        widget = self.active_widgets.pop(notification_id, None)
        if widget is None:
            return
        widget.dismissed.disconnect(self._dismiss_notification)
        widget.deleteLater()

    def _clear_widgets(self) -> None:
        for notification_id in list(self.active_widgets):
            self._remove_widget(notification_id)

    def _restack_widgets(self) -> None:
        snapshot = self.manager.snapshot()
        ordered_widgets: list[ToastNotificationWidget] = []
        sizes = []

        for notification in snapshot.active:
            widget = self.active_widgets.get(notification.notification_id)
            if widget is None:
                continue
            widget.adjustSize()
            size = widget.sizeHint()
            size.setWidth(widget.width())
            widget.resize(size)
            ordered_widgets.append(widget)
            sizes.append(size)

        if not ordered_widgets:
            return

        screen = self.app.primaryScreen()
        if screen is None:
            return

        geometries = stack_notification_geometries(screen.availableGeometry(), sizes)
        for widget, geometry in zip(ordered_widgets, geometries, strict=False):
            widget.setGeometry(geometry)

    def _create_tray_icon(self) -> QSystemTrayIcon:
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

        return QSystemTrayIcon(QIcon(pixmap), self.app)

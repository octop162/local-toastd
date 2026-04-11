from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .http_server import LocalHttpServer
from .icons import load_app_icon
from .models import NotificationPayload
from .notification_types import NotificationType, display_label_for_type
from .notification_ui import ToastNotificationWidget, stack_notification_geometries
from .queue_manager import ManagedNotification, NotificationManager, NotificationUpdate
from .settings import (
    AppSettings,
    SoundType,
    ThemeName,
    ToastPosition,
    load_settings,
    resolve_settings_path,
    save_settings,
)
from .settings_window import AppSettingsDialog
from .sound import play_notification_sound

logger = logging.getLogger(__name__)


class NotificationBridge(QObject):
    notification_received = Signal(object)


class ToastDaemon(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setWindowIcon(load_app_icon())
        self.settings_path = resolve_settings_path()
        self.settings = load_settings(self.settings_path)
        self.bridge = NotificationBridge()
        self.manager = NotificationManager(max_visible=self.settings.max_visible)
        self.active_widgets: dict[int, ToastNotificationWidget] = {}
        self.notification_settings_overrides: dict[int, AppSettings] = {}
        self.tray_icon = self._create_tray_icon()
        self.settings_action: QAction | None = None
        self.pause_action: QAction | None = None
        self.resume_action: QAction | None = None
        self.settings_dialog: AppSettingsDialog | None = None
        self.http_server = LocalHttpServer(
            self.settings.bind_host,
            self.settings.port,
            self._build_payload_from_http,
            self._receive_from_http,
        )

        # HTTP callbacks arrive from the Flask worker thread, so force queued delivery
        # to keep all widget work on the Qt UI thread.
        self.bridge.notification_received.connect(
            self._handle_notification_on_ui_thread,
            Qt.ConnectionType.QueuedConnection,
        )
        self.app.aboutToQuit.connect(self.shutdown)

    def start(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("System tray is not available on this system.")

        self._build_tray_menu()
        self.tray_icon.activated.connect(self._handle_tray_icon_activated)
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

        self.settings_action = QAction("設定...", self.app)
        self.settings_action.triggered.connect(self.open_settings_dialog)
        menu.addAction(self.settings_action)

        menu.addSeparator()

        self.pause_action = QAction("通知を一時停止", self.app)
        self.pause_action.triggered.connect(self.pause_notifications)
        menu.addAction(self.pause_action)

        self.resume_action = QAction("通知を再開", self.app)
        self.resume_action.triggered.connect(self.resume_notifications)
        self.resume_action.setEnabled(False)
        menu.addAction(self.resume_action)

        menu.addSeparator()

        quit_action = QAction("終了", self.app)
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
        status = "一時停止中" if snapshot.paused else "動作中"
        port_line = f"HTTP: http://{self.http_server.host}:{self.http_server.port}"
        restart_notes: list[str] = []
        if self.settings.bind_host != self.http_server.host:
            restart_notes.append(f"設定ホスト: {self.settings.bind_host}")
        if self.settings.port != self.http_server.port:
            restart_notes.append(f"設定ポート: {self.settings.port}")
        if restart_notes:
            port_line += "\n" + " / ".join(restart_notes) + " (再起動後に反映)"
        self.tray_icon.setToolTip(
            "local-toastd"
            f" ({status})\n{port_line}\n"
            f"表示中: {snapshot.active_count}\n待機中: {snapshot.waiting_count}\n"
            f"スタック数: {snapshot.max_visible}"
        )

    def _apply_notification_update(self, update: NotificationUpdate) -> None:
        if update.completed is not None:
            self._remove_widget(update.completed.notification_id)

        for notification in update.deactivated:
            self._remove_widget(notification.notification_id)

        for notification in update.activated:
            self._ensure_widget(notification)

        self._restack_widgets()
        self._refresh_tooltip()

    def _ensure_widget(self, notification: ManagedNotification) -> None:
        if notification.notification_id in self.active_widgets:
            return

        widget = ToastNotificationWidget(
            notification,
            theme_name=self._theme_for_notification(notification),
            font_size=self._font_size_for_notification(notification),
        )
        widget.dismissed.connect(self._dismiss_notification)
        self.active_widgets[notification.notification_id] = widget
        play_notification_sound(
            sound_type=self._sound_type_for_notification(notification),
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
        self.notification_settings_overrides.pop(notification_id, None)
        if widget is None:
            return
        widget.dismissed.disconnect(self._dismiss_notification)
        widget.deleteLater()

    def _clear_widgets(self) -> None:
        for notification_id in list(self.active_widgets):
            self._remove_widget(notification_id)

    def _restack_widgets(self) -> None:
        snapshot = self.manager.snapshot()
        widgets_by_position: dict[ToastPosition, list[tuple[ToastNotificationWidget, QSize]]] = {
            "top_right": [],
            "top_center": [],
            "bottom_right": [],
        }

        for notification in snapshot.active:
            widget = self.active_widgets.get(notification.notification_id)
            if widget is None:
                continue
            widget.adjustSize()
            size = widget.sizeHint()
            size.setWidth(widget.width())
            widget.resize(size)
            position = self._position_for_notification(notification)
            widgets_by_position[position].append((widget, size))

        screen = self.app.primaryScreen()
        if screen is None:
            return

        for position, widget_entries in widgets_by_position.items():
            if not widget_entries:
                continue
            sizes = [size for _, size in widget_entries]
            geometries = stack_notification_geometries(
                screen.availableGeometry(),
                sizes,
                position=position,
            )
            for (widget, _), geometry in zip(widget_entries, geometries, strict=False):
                widget.setGeometry(geometry)

    def open_settings_dialog(self) -> None:
        if self.settings_dialog is not None:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        dialog = AppSettingsDialog(self.settings)
        dialog.save_requested.connect(self._save_settings_from_dialog)
        dialog.test_requested.connect(self._test_notification_from_dialog)
        dialog.destroyed.connect(self._on_settings_dialog_destroyed)
        self.settings_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _handle_tray_icon_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings_dialog()

    def _on_settings_dialog_destroyed(self) -> None:
        self.settings_dialog = None

    def _save_settings_from_dialog(self, settings: AppSettings) -> None:
        try:
            save_settings(self.settings_path, settings)
        except OSError as exc:
            logger.exception("Failed to save settings")
            if self.settings_dialog is not None:
                self.settings_dialog.show_error(f"設定の保存に失敗しました: {exc}")
            return

        self.settings = settings
        self._apply_runtime_settings()
        if self.settings_dialog is not None:
            self.settings_dialog.accept()

    def _test_notification_from_dialog(
        self,
        settings: AppSettings,
        notification_type: NotificationType,
    ) -> None:
        label = display_label_for_type(notification_type)
        payload = NotificationPayload(
            title=f"テスト通知（{label}）",
            message="現在の設定内容をプレビューしています。",
            notification_type=notification_type,
            duration_ms=settings.duration_ms,
            sound=True,
            theme_override=settings.theme,
        )
        self._queue_notification_from_ui(payload, settings_override=settings)

    def _apply_runtime_settings(self) -> None:
        update = self.manager.set_max_visible(self.settings.max_visible)
        self._apply_notification_update(update)
        self._refresh_active_widget_appearance()
        self._restack_widgets()
        self._refresh_tooltip()

    def _refresh_active_widget_appearance(self) -> None:
        for widget in self.active_widgets.values():
            widget.apply_theme(
                self._theme_for_notification(widget.notification),
                font_size=self._font_size_for_notification(widget.notification),
            )

    def _queue_notification_from_ui(
        self,
        payload: NotificationPayload,
        *,
        settings_override: AppSettings | None = None,
    ) -> None:
        update = self.manager.enqueue(payload)
        if settings_override is not None and update.enqueued is not None:
            self.notification_settings_overrides[
                update.enqueued.notification_id
            ] = settings_override
        self._handle_notification_on_ui_thread(update)

    def _build_payload_from_http(self, data: object) -> NotificationPayload:
        return NotificationPayload.from_mapping(
            data,
            default_duration_ms=self.settings.duration_ms,
        )

    def _theme_for_notification(self, notification: ManagedNotification) -> ThemeName:
        return notification.payload.theme_override or self.settings.theme

    def _sound_type_for_notification(self, notification: ManagedNotification) -> SoundType:
        if notification.payload.sound_type_override is not None:
            return notification.payload.sound_type_override
        override = self.notification_settings_overrides.get(notification.notification_id)
        if override is not None:
            return override.sound_type_for_notification_type(
                notification.payload.notification_type
            )
        return self.settings.sound_type_for_notification_type(
            notification.payload.notification_type
        )

    def _position_for_notification(self, notification: ManagedNotification) -> ToastPosition:
        override = self.notification_settings_overrides.get(notification.notification_id)
        if override is not None:
            return override.position
        return self.settings.position

    def _font_size_for_notification(self, notification: ManagedNotification) -> int:
        override = self.notification_settings_overrides.get(notification.notification_id)
        if override is not None:
            return override.font_size
        return self.settings.font_size

    def _create_tray_icon(self) -> QSystemTrayIcon:
        return QSystemTrayIcon(load_app_icon(), self.app)

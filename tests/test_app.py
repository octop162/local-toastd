from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from local_toastd import app as app_module
from local_toastd.models import NotificationPayload
from local_toastd.notification_types import (
    NOTIFICATION_TYPE_C,
    display_label_for_type,
)
from local_toastd.queue_manager import ManagedNotification
from local_toastd.settings import AppSettings, NotificationSoundSettings


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def test_test_notification_from_dialog_uses_requested_type(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(app_module, "resolve_settings_path", lambda: tmp_path / "settings.toml")
    monkeypatch.setattr(app_module, "load_settings", lambda path: AppSettings())
    monkeypatch.setattr(app_module, "load_app_icon", lambda: QIcon())

    daemon = app_module.ToastDaemon(get_app())
    settings = AppSettings(theme="light", duration_seconds=7.5)
    queued: list[tuple[NotificationPayload, AppSettings | None]] = []

    monkeypatch.setattr(
        daemon,
        "_queue_notification_from_ui",
        lambda payload, *, settings_override=None: queued.append((payload, settings_override)),
    )

    daemon._test_notification_from_dialog(settings, NOTIFICATION_TYPE_C)

    assert len(queued) == 1
    payload, settings_override = queued[0]
    assert payload.notification_type == NOTIFICATION_TYPE_C
    assert payload.title == f"テスト通知（{display_label_for_type(NOTIFICATION_TYPE_C)}）"
    assert payload.duration_ms == settings.duration_ms
    assert settings_override == settings


def test_sound_type_for_notification_uses_type_specific_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(app_module, "resolve_settings_path", lambda: tmp_path / "settings.toml")
    monkeypatch.setattr(app_module, "load_settings", lambda path: AppSettings())
    monkeypatch.setattr(app_module, "load_app_icon", lambda: QIcon())

    daemon = app_module.ToastDaemon(get_app())
    override = AppSettings(
        notification_sounds=NotificationSoundSettings(type_c="scratch")
    )
    notification = ManagedNotification(
        notification_id=1,
        payload=NotificationPayload(
            message="preview",
            notification_type=NOTIFICATION_TYPE_C,
        ),
    )
    daemon.notification_settings_overrides[notification.notification_id] = override

    assert daemon._sound_type_for_notification(notification) == "scratch"

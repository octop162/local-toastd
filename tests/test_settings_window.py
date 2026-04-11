from __future__ import annotations

from typing import cast

from PySide6.QtWidgets import QApplication

from local_toastd.notification_types import (
    NOTIFICATION_TYPE_A,
    NOTIFICATION_TYPE_B,
    NOTIFICATION_TYPE_C,
    NOTIFICATION_TYPE_D,
)
from local_toastd.settings import AppSettings, NotificationSoundSettings
from local_toastd.settings_window import AppSettingsDialog


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return cast(QApplication, app)


def test_settings_dialog_exposes_type_a_to_d_controls() -> None:
    get_app()
    dialog = AppSettingsDialog(AppSettings())

    assert dialog.test_buttons[NOTIFICATION_TYPE_A].text() == "タイプAをテスト"
    assert dialog.test_buttons[NOTIFICATION_TYPE_B].text() == "タイプBをテスト"
    assert dialog.test_buttons[NOTIFICATION_TYPE_C].text() == "タイプCをテスト"
    assert dialog.test_buttons[NOTIFICATION_TYPE_D].text() == "タイプDをテスト"
    assert set(dialog.sound_combos) == {
        NOTIFICATION_TYPE_A,
        NOTIFICATION_TYPE_B,
        NOTIFICATION_TYPE_C,
        NOTIFICATION_TYPE_D,
    }

    dialog.close()


def test_settings_dialog_emits_test_request_for_selected_type() -> None:
    app = get_app()
    settings = AppSettings(
        notification_sounds=NotificationSoundSettings(
            type_a="gentle",
            type_b="scratch",
            type_c="taiko",
            type_d="off",
        )
    )
    dialog = AppSettingsDialog(settings)
    emitted: list[tuple[AppSettings, str]] = []

    def capture(current_settings: AppSettings, notification_type: str) -> None:
        emitted.append((current_settings, notification_type))

    dialog.test_requested.connect(capture)

    dialog.test_buttons[NOTIFICATION_TYPE_B].click()
    app.processEvents()

    assert len(emitted) == 1
    emitted_settings, emitted_type = emitted[0]
    assert emitted_type == NOTIFICATION_TYPE_B
    assert emitted_settings.notification_sounds.type_b == "scratch"

    dialog.close()


def test_settings_dialog_allows_font_size_up_to_30() -> None:
    get_app()
    dialog = AppSettingsDialog(AppSettings())

    assert dialog.font_size_spin.minimum() == 10
    assert dialog.font_size_spin.maximum() == 30

    dialog.close()

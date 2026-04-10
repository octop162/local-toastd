from __future__ import annotations

from pathlib import Path

from local_toastd.settings import (
    DEFAULT_SETTINGS,
    AppSettings,
    NotificationSoundSettings,
    load_settings,
    resolve_settings_path,
    save_settings,
)
from local_toastd.settings_window import stylesheet_for_theme


def test_load_settings_returns_defaults_when_file_is_missing(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")

    assert settings == DEFAULT_SETTINGS


def test_save_and_load_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    expected = AppSettings(
        theme="light",
        notification_sounds=NotificationSoundSettings(
            info="gentle",
            success="scratch",
            warning="taiko",
            error="zangeki",
        ),
        position="bottom_right",
        font_size=18,
        bind_host="0.0.0.0",
        port=9999,
        duration_seconds=7.5,
        max_visible=6,
    )

    save_settings(path, expected)

    assert load_settings(path) == expected


def test_load_settings_falls_back_on_invalid_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(
        """
[notification]
theme = "solarized"
sound_type = "loud"
position = "left"
font_size = 8
duration_seconds = -1
max_visible = 20

[server]
bind_host = ""
port = 70000
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings == DEFAULT_SETTINGS


def test_load_settings_reads_bind_host_from_server_section(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(
        """
[notification]
theme = "dark"
sound_types = { info = "gentle", success = "scratch", warning = "taiko", error = "off" }
position = "top_center"
font_size = 16
duration_seconds = 5.0
max_visible = 4

[server]
bind_host = "0.0.0.0"
port = 8765
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.bind_host == "0.0.0.0"
    assert settings.position == "top_center"
    assert settings.font_size == 16
    assert settings.notification_sounds == NotificationSoundSettings(
        info="gentle",
        success="scratch",
        warning="taiko",
        error="off",
    )


def test_load_settings_maps_legacy_default_sound_type_to_taiko(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text(
        """
[notification]
theme = "dark"
sound_type = "default"
position = "top_right"
font_size = 13
duration_seconds = 5.0
max_visible = 4

[server]
port = 8765
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(path)

    assert settings.notification_sounds == NotificationSoundSettings(
        info="taiko",
        success="taiko",
        warning="taiko",
        error="taiko",
    )


def test_resolve_settings_path_uses_project_root_in_dev_mode(tmp_path: Path) -> None:
    path = resolve_settings_path(project_root=tmp_path, frozen=False)

    assert path == tmp_path / "settings.toml"


def test_resolve_settings_path_uses_executable_parent_when_frozen(tmp_path: Path) -> None:
    executable_path = tmp_path / "dist" / "local-toastd.exe"
    path = resolve_settings_path(executable_path=executable_path, frozen=True)

    assert path == executable_path.parent / "settings.toml"


def test_stylesheet_for_theme_returns_distinct_dialog_styles() -> None:
    dark = stylesheet_for_theme("dark")
    light = stylesheet_for_theme("light")

    assert "background-color: #0f172a;" in dark
    assert "background-color: #f8fafc;" in light
    assert "QAbstractItemView" in dark
    assert "QAbstractItemView" in light
    assert "QGroupBox" in dark
    assert "QGroupBox" in light
    assert dark != light

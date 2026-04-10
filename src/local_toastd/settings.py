from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeAlias

import tomli
import tomli_w

logger = logging.getLogger(__name__)

ThemeName: TypeAlias = Literal["dark", "light"]
SoundType: TypeAlias = Literal["gentle", "taiko", "zangeki", "scratch", "off"]
ToastPosition: TypeAlias = Literal["top_right", "top_center", "bottom_right"]
NotificationLevel: TypeAlias = Literal["info", "success", "warning", "error"]

VALID_THEMES = frozenset({"dark", "light"})
VALID_SOUND_TYPES = frozenset({"gentle", "taiko", "zangeki", "scratch", "off"})
VALID_POSITIONS = frozenset({"top_right", "top_center", "bottom_right"})
SETTINGS_FILE_NAME = "settings.toml"


@dataclass(frozen=True, slots=True)
class NotificationSoundSettings:
    info: SoundType = "gentle"
    success: SoundType = "gentle"
    warning: SoundType = "taiko"
    error: SoundType = "zangeki"

    def to_toml_data(self) -> dict[str, SoundType]:
        return {
            "info": self.info,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
        }

    def for_level(self, level: str) -> SoundType:
        if level == "success":
            return self.success
        if level == "warning":
            return self.warning
        if level == "error":
            return self.error
        return self.info


@dataclass(frozen=True, slots=True)
class AppSettings:
    theme: ThemeName = "dark"
    notification_sounds: NotificationSoundSettings = field(
        default_factory=NotificationSoundSettings
    )
    position: ToastPosition = "top_right"
    font_size: int = 13
    bind_host: str = "127.0.0.1"
    port: int = 8765
    duration_seconds: float = 5.0
    max_visible: int = 4

    @property
    def sound_type(self) -> SoundType:
        return self.notification_sounds.info

    def sound_type_for_level(self, level: str) -> SoundType:
        return self.notification_sounds.for_level(level)

    @property
    def duration_ms(self) -> int:
        return int(self.duration_seconds * 1000)

    def to_toml_data(self) -> dict[str, Any]:
        return {
            "notification": {
                "theme": self.theme,
                "sound_types": self.notification_sounds.to_toml_data(),
                "position": self.position,
                "font_size": self.font_size,
                "duration_seconds": self.duration_seconds,
                "max_visible": self.max_visible,
            },
            "server": {
                "bind_host": self.bind_host,
                "port": self.port,
            },
        }


DEFAULT_SETTINGS = AppSettings()


def resolve_settings_path(
    *,
    executable_path: Path | None = None,
    project_root: Path | None = None,
    frozen: bool | None = None,
) -> Path:
    is_frozen = frozen if frozen is not None else bool(getattr(sys, "frozen", False))
    if is_frozen:
        base_dir = (executable_path or Path(sys.executable)).resolve().parent
    else:
        base_dir = project_root or Path(__file__).resolve().parents[2]
    return base_dir / SETTINGS_FILE_NAME


def load_settings(path: Path) -> AppSettings:
    if not path.exists():
        return DEFAULT_SETTINGS

    try:
        data = tomli.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomli.TOMLDecodeError) as exc:
        logger.warning("Failed to load settings from %s: %s", path, exc)
        return DEFAULT_SETTINGS

    return _settings_from_data(data)


def save_settings(path: Path, settings: AppSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(tomli_w.dumps(settings.to_toml_data()), encoding="utf-8")
    tmp_path.replace(path)


def _settings_from_data(data: dict[str, Any]) -> AppSettings:
    notification = data.get("notification", {})
    server = data.get("server", {})

    return AppSettings(
        theme=_coerce_theme(notification.get("theme")),
        notification_sounds=_coerce_notification_sounds(
            notification.get("sound_types"),
            notification.get("sound_type"),
        ),
        position=_coerce_position(notification.get("position")),
        font_size=_coerce_font_size(notification.get("font_size")),
        bind_host=_coerce_bind_host(server.get("bind_host")),
        port=_coerce_port(server.get("port")),
        duration_seconds=_coerce_duration(notification.get("duration_seconds")),
        max_visible=_coerce_max_visible(notification.get("max_visible")),
    )


def _coerce_theme(raw: Any) -> ThemeName:
    if raw in VALID_THEMES:
        return raw
    _warn_invalid("theme", raw, DEFAULT_SETTINGS.theme)
    return DEFAULT_SETTINGS.theme


def _coerce_notification_sounds(
    raw: Any,
    legacy_raw: Any,
) -> NotificationSoundSettings:
    if isinstance(raw, dict):
        fallback = NotificationSoundSettings()
        return NotificationSoundSettings(
            info=_coerce_sound_type_with_fallback(
                raw.get("info"),
                fallback.info,
                "sound_types.info",
            ),
            success=_coerce_sound_type_with_fallback(
                raw.get("success"),
                fallback.success,
                "sound_types.success",
            ),
            warning=_coerce_sound_type_with_fallback(
                raw.get("warning"),
                fallback.warning,
                "sound_types.warning",
            ),
            error=_coerce_sound_type_with_fallback(
                raw.get("error"),
                fallback.error,
                "sound_types.error",
            ),
        )

    if legacy_raw is None:
        return NotificationSoundSettings()
    legacy_sound_type: SoundType
    if legacy_raw == "default":
        legacy_sound_type = "taiko"
    elif legacy_raw in VALID_SOUND_TYPES:
        legacy_sound_type = legacy_raw
    else:
        _warn_invalid("sound_type", legacy_raw, NotificationSoundSettings())
        return NotificationSoundSettings()

    return NotificationSoundSettings(
        info=legacy_sound_type,
        success=legacy_sound_type,
        warning=legacy_sound_type,
        error=legacy_sound_type,
    )


def _coerce_sound_type_with_fallback(raw: Any, fallback: SoundType, field_name: str) -> SoundType:
    if raw == "default":
        return "taiko"
    if raw in VALID_SOUND_TYPES:
        return raw
    _warn_invalid(field_name, raw, fallback)
    return fallback


def _coerce_position(raw: Any) -> ToastPosition:
    if raw in VALID_POSITIONS:
        return raw
    _warn_invalid("position", raw, DEFAULT_SETTINGS.position)
    return DEFAULT_SETTINGS.position


def _coerce_font_size(raw: Any) -> int:
    if isinstance(raw, int) and 10 <= raw <= 25:
        return raw
    _warn_invalid("font_size", raw, DEFAULT_SETTINGS.font_size)
    return DEFAULT_SETTINGS.font_size


def _coerce_port(raw: Any) -> int:
    if isinstance(raw, int) and 1 <= raw <= 65535:
        return raw
    _warn_invalid("port", raw, DEFAULT_SETTINGS.port)
    return DEFAULT_SETTINGS.port


def _coerce_bind_host(raw: Any) -> str:
    if isinstance(raw, str):
        bind_host = raw.strip()
        if bind_host:
            return bind_host
    _warn_invalid("bind_host", raw, DEFAULT_SETTINGS.bind_host)
    return DEFAULT_SETTINGS.bind_host


def _coerce_duration(raw: Any) -> float:
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    _warn_invalid("duration_seconds", raw, DEFAULT_SETTINGS.duration_seconds)
    return DEFAULT_SETTINGS.duration_seconds


def _coerce_max_visible(raw: Any) -> int:
    if isinstance(raw, int) and 1 <= raw <= 10:
        return raw
    _warn_invalid("max_visible", raw, DEFAULT_SETTINGS.max_visible)
    return DEFAULT_SETTINGS.max_visible


def _warn_invalid(field_name: str, raw: Any, fallback: Any) -> None:
    if raw is None:
        return
    logger.warning("Invalid settings value for %s=%r, using %r", field_name, raw, fallback)

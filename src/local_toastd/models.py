from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import SoundType, ThemeName

DEFAULT_DURATION_MS = 5000
VALID_LEVELS = frozenset({"info", "success", "warning", "error"})


class PayloadValidationError(ValueError):
    """Raised when an incoming notification payload is invalid."""


@dataclass(frozen=True, slots=True)
class NotificationPayload:
    message: str
    title: str | None = None
    level: str = "info"
    duration_ms: int = DEFAULT_DURATION_MS
    sound: bool = True
    theme_override: ThemeName | None = None
    sound_type_override: SoundType | None = None
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_mapping(
        cls,
        data: object,
        *,
        default_duration_ms: int = DEFAULT_DURATION_MS,
    ) -> NotificationPayload:
        if not isinstance(data, Mapping):
            raise PayloadValidationError("JSON body must be an object.")

        message = data.get("message")
        if not isinstance(message, str) or not message.strip():
            raise PayloadValidationError("'message' must be a non-empty string.")

        title = data.get("title")
        if title is not None:
            if not isinstance(title, str):
                raise PayloadValidationError("'title' must be a string when provided.")
            title = title.strip() or None

        level = data.get("level", "info")
        if not isinstance(level, str) or level not in VALID_LEVELS:
            raise PayloadValidationError(
                f"'level' must be one of: {', '.join(sorted(VALID_LEVELS))}."
            )

        duration_ms = data.get("duration_ms", default_duration_ms)
        if not isinstance(duration_ms, int) or duration_ms <= 0:
            raise PayloadValidationError("'duration_ms' must be a positive integer.")

        sound = data.get("sound", True)
        if not isinstance(sound, bool):
            raise PayloadValidationError("'sound' must be a boolean.")

        return cls(
            message=message.strip(),
            title=title,
            level=level,
            duration_ms=duration_ms,
            sound=sound,
        )

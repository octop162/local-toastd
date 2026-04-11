from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import SoundType, ThemeName

from .notification_types import (
    DEFAULT_NOTIFICATION_TYPE,
    VALID_NOTIFICATION_TYPES,
    NotificationType,
)

DEFAULT_DURATION_MS = 5000


class PayloadValidationError(ValueError):
    """Raised when an incoming notification payload is invalid."""


@dataclass(frozen=True, slots=True)
class NotificationPayload:
    message: str
    title: str | None = None
    notification_type: NotificationType = DEFAULT_NOTIFICATION_TYPE
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

        if "level" in data:
            raise PayloadValidationError(
                "'level' is no longer supported. Use 'type' instead."
            )

        notification_type = data.get("type", DEFAULT_NOTIFICATION_TYPE)
        if (
            not isinstance(notification_type, str)
            or notification_type not in VALID_NOTIFICATION_TYPES
        ):
            raise PayloadValidationError(
                f"'type' must be one of: {', '.join(sorted(VALID_NOTIFICATION_TYPES))}."
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
            notification_type=notification_type,
            duration_ms=duration_ms,
            sound=sound,
        )

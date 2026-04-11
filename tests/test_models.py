from __future__ import annotations

import pytest

from local_toastd.models import (
    DEFAULT_DURATION_MS,
    NotificationPayload,
    PayloadValidationError,
)
from local_toastd.notification_types import DEFAULT_NOTIFICATION_TYPE, NOTIFICATION_TYPE_B


def test_notification_payload_defaults() -> None:
    payload = NotificationPayload.from_mapping({"message": "  hello  "})

    assert payload.message == "hello"
    assert payload.title is None
    assert payload.notification_type == DEFAULT_NOTIFICATION_TYPE
    assert payload.duration_ms == DEFAULT_DURATION_MS
    assert payload.sound is True


def test_notification_payload_uses_custom_default_duration() -> None:
    payload = NotificationPayload.from_mapping(
        {"message": "hello"},
        default_duration_ms=2500,
    )

    assert payload.duration_ms == 2500


def test_notification_payload_accepts_notification_type() -> None:
    payload = NotificationPayload.from_mapping(
        {"message": "hello", "type": NOTIFICATION_TYPE_B}
    )

    assert payload.notification_type == NOTIFICATION_TYPE_B


@pytest.mark.parametrize(
    ("raw_payload", "message"),
    [
        ({}, "'message' must be a non-empty string."),
        ({"message": ""}, "'message' must be a non-empty string."),
        (
            {"message": "ok", "type": "type_e"},
            "'type' must be one of: type_a, type_b, type_c, type_d.",
        ),
        (
            {"message": "ok", "type": 1},
            "'type' must be one of: type_a, type_b, type_c, type_d.",
        ),
        (
            {"message": "ok", "level": "info"},
            "'level' is no longer supported. Use 'type' instead.",
        ),
        ({"message": "ok", "duration_ms": 0}, "'duration_ms' must be a positive integer."),
        ({"message": "ok", "sound": "yes"}, "'sound' must be a boolean."),
    ],
)
def test_notification_payload_validation(raw_payload: dict, message: str) -> None:
    with pytest.raises(PayloadValidationError, match=message):
        NotificationPayload.from_mapping(raw_payload)

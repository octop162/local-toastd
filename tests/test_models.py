from __future__ import annotations

import pytest

from local_toastd.models import (
    DEFAULT_DURATION_MS,
    NotificationPayload,
    PayloadValidationError,
)


def test_notification_payload_defaults() -> None:
    payload = NotificationPayload.from_mapping({"message": "  hello  "})

    assert payload.message == "hello"
    assert payload.title is None
    assert payload.level == "info"
    assert payload.duration_ms == DEFAULT_DURATION_MS
    assert payload.sound is True


@pytest.mark.parametrize(
    ("raw_payload", "message"),
    [
        ({}, "'message' must be a non-empty string."),
        ({"message": ""}, "'message' must be a non-empty string."),
        (
            {"message": "ok", "level": "loud"},
            "'level' must be one of: error, info, success, warning.",
        ),
        ({"message": "ok", "duration_ms": 0}, "'duration_ms' must be a positive integer."),
        ({"message": "ok", "sound": "yes"}, "'sound' must be a boolean."),
    ],
)
def test_notification_payload_validation(raw_payload: dict, message: str) -> None:
    with pytest.raises(PayloadValidationError, match=message):
        NotificationPayload.from_mapping(raw_payload)

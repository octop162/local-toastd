from __future__ import annotations

import pytest

from local_toastd.models import NotificationPayload
from local_toastd.queue_manager import NotificationManager


def make_payload(message: str) -> NotificationPayload:
    return NotificationPayload.from_mapping({"message": message})


def test_enqueue_activates_until_capacity_then_waits() -> None:
    manager = NotificationManager(max_visible=2)

    first = manager.enqueue(make_payload("first"))
    second = manager.enqueue(make_payload("second"))
    third = manager.enqueue(make_payload("third"))

    assert len(first.activated) == 1
    assert len(second.activated) == 1
    assert len(third.activated) == 0
    assert third.snapshot.active_count == 2
    assert third.snapshot.waiting_count == 1
    assert third.snapshot.total_count == 3


def test_complete_promotes_waiting_notification() -> None:
    manager = NotificationManager(max_visible=2)

    first = manager.enqueue(make_payload("first"))
    second = manager.enqueue(make_payload("second"))
    third = manager.enqueue(make_payload("third"))
    assert first.enqueued is not None

    update = manager.complete(first.enqueued.notification_id)

    assert second.snapshot.active_count == 2
    assert third.snapshot.waiting_count == 1
    assert [item.payload.message for item in update.activated] == ["third"]
    assert update.snapshot.active_count == 2
    assert update.snapshot.waiting_count == 0


def test_pause_and_resume_control_promotions() -> None:
    manager = NotificationManager(max_visible=2)

    manager.pause()
    first = manager.enqueue(make_payload("first"))
    second = manager.enqueue(make_payload("second"))
    resumed = manager.resume()

    assert first.snapshot.paused is True
    assert second.snapshot.active_count == 0
    assert second.snapshot.waiting_count == 2
    assert [item.payload.message for item in resumed.activated] == ["first", "second"]
    assert resumed.snapshot.paused is False
    assert resumed.snapshot.active_count == 2
    assert resumed.snapshot.waiting_count == 0


def test_complete_unknown_notification_raises_key_error() -> None:
    manager = NotificationManager(max_visible=1)

    manager.enqueue(make_payload("first"))

    with pytest.raises(KeyError, match="Unknown active notification id: 999"):
        manager.complete(999)


def test_set_max_visible_promotes_waiting_when_increased() -> None:
    manager = NotificationManager(max_visible=1)

    manager.enqueue(make_payload("first"))
    manager.enqueue(make_payload("second"))
    manager.enqueue(make_payload("third"))

    update = manager.set_max_visible(2)

    assert [item.payload.message for item in update.activated] == ["second"]
    assert update.snapshot.active_count == 2
    assert update.snapshot.waiting_count == 1
    assert update.snapshot.max_visible == 2


def test_set_max_visible_moves_overflow_back_to_waiting_when_decreased() -> None:
    manager = NotificationManager(max_visible=3)

    manager.enqueue(make_payload("first"))
    manager.enqueue(make_payload("second"))
    manager.enqueue(make_payload("third"))
    manager.enqueue(make_payload("fourth"))

    update = manager.set_max_visible(2)

    assert [item.payload.message for item in update.deactivated] == ["third"]
    assert [item.payload.message for item in update.snapshot.active] == ["first", "second"]
    assert [item.payload.message for item in update.snapshot.waiting] == ["third", "fourth"]
    assert update.snapshot.max_visible == 2

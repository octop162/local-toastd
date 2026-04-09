from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock

from .models import NotificationPayload


@dataclass(frozen=True, slots=True)
class ManagedNotification:
    notification_id: int
    payload: NotificationPayload


@dataclass(frozen=True, slots=True)
class NotificationSnapshot:
    active: tuple[ManagedNotification, ...]
    waiting: tuple[ManagedNotification, ...]
    paused: bool
    max_visible: int

    @property
    def active_count(self) -> int:
        return len(self.active)

    @property
    def waiting_count(self) -> int:
        return len(self.waiting)

    @property
    def total_count(self) -> int:
        return self.active_count + self.waiting_count


@dataclass(frozen=True, slots=True)
class NotificationUpdate:
    snapshot: NotificationSnapshot
    activated: tuple[ManagedNotification, ...] = ()
    deactivated: tuple[ManagedNotification, ...] = ()
    enqueued: ManagedNotification | None = None
    completed: ManagedNotification | None = None


class NotificationManager:
    """Thread-safe notification state manager.

    Active notifications represent items that the future UI should display.
    Waiting notifications represent items queued until active capacity frees up.
    """

    def __init__(self, max_visible: int = 4) -> None:
        if max_visible <= 0:
            raise ValueError("max_visible must be a positive integer.")

        self._lock = Lock()
        self._max_visible = max_visible
        self._paused = False
        self._next_id = 1
        self._active: list[ManagedNotification] = []
        self._waiting: deque[ManagedNotification] = deque()

    def enqueue(self, payload: NotificationPayload) -> NotificationUpdate:
        with self._lock:
            notification = ManagedNotification(self._next_id, payload)
            self._next_id += 1

            activated: tuple[ManagedNotification, ...] = ()
            if self._paused or len(self._active) >= self._max_visible:
                self._waiting.append(notification)
            else:
                self._active.append(notification)
                activated = (notification,)

            return NotificationUpdate(
                snapshot=self._snapshot_locked(),
                activated=activated,
                enqueued=notification,
            )

    def complete(self, notification_id: int) -> NotificationUpdate:
        with self._lock:
            completed = next(
                (
                    notification
                    for notification in self._active
                    if notification.notification_id == notification_id
                ),
                None,
            )
            if completed is None:
                raise KeyError(f"Unknown active notification id: {notification_id}")

            self._active = [
                notification
                for notification in self._active
                if notification.notification_id != notification_id
            ]
            activated = self._promote_waiting_locked()
            return NotificationUpdate(
                snapshot=self._snapshot_locked(),
                activated=activated,
                completed=completed,
            )

    def pause(self) -> NotificationSnapshot:
        with self._lock:
            self._paused = True
            return self._snapshot_locked()

    def resume(self) -> NotificationUpdate:
        with self._lock:
            self._paused = False
            activated = self._promote_waiting_locked()
            return NotificationUpdate(
                snapshot=self._snapshot_locked(),
                activated=activated,
            )

    def set_max_visible(self, max_visible: int) -> NotificationUpdate:
        if max_visible <= 0:
            raise ValueError("max_visible must be a positive integer.")

        with self._lock:
            self._max_visible = max_visible
            deactivated = self._trim_active_locked()
            activated = self._promote_waiting_locked()
            return NotificationUpdate(
                snapshot=self._snapshot_locked(),
                activated=activated,
                deactivated=deactivated,
            )

    def snapshot(self) -> NotificationSnapshot:
        with self._lock:
            return self._snapshot_locked()

    def clear(self) -> None:
        with self._lock:
            self._active.clear()
            self._waiting.clear()

    def _promote_waiting_locked(self) -> tuple[ManagedNotification, ...]:
        activated: list[ManagedNotification] = []
        while not self._paused and len(self._active) < self._max_visible and self._waiting:
            notification = self._waiting.popleft()
            self._active.append(notification)
            activated.append(notification)
        return tuple(activated)

    def _trim_active_locked(self) -> tuple[ManagedNotification, ...]:
        if len(self._active) <= self._max_visible:
            return ()

        overflow = self._active[self._max_visible :]
        self._active = self._active[: self._max_visible]
        self._waiting = deque(overflow + list(self._waiting))
        return tuple(overflow)

    def _snapshot_locked(self) -> NotificationSnapshot:
        return NotificationSnapshot(
            active=tuple(self._active),
            waiting=tuple(self._waiting),
            paused=self._paused,
            max_visible=self._max_visible,
        )

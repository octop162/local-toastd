from __future__ import annotations

from typing import Final, Literal, TypeAlias

NotificationType: TypeAlias = Literal["type_a", "type_b", "type_c", "type_d"]

NOTIFICATION_TYPE_A: Final[NotificationType] = "type_a"
NOTIFICATION_TYPE_B: Final[NotificationType] = "type_b"
NOTIFICATION_TYPE_C: Final[NotificationType] = "type_c"
NOTIFICATION_TYPE_D: Final[NotificationType] = "type_d"

DEFAULT_NOTIFICATION_TYPE: Final[NotificationType] = NOTIFICATION_TYPE_A
VALID_NOTIFICATION_TYPES: Final[frozenset[NotificationType]] = frozenset(
    {
        NOTIFICATION_TYPE_A,
        NOTIFICATION_TYPE_B,
        NOTIFICATION_TYPE_C,
        NOTIFICATION_TYPE_D,
    }
)
NOTIFICATION_TYPES: Final[tuple[NotificationType, ...]] = (
    NOTIFICATION_TYPE_A,
    NOTIFICATION_TYPE_B,
    NOTIFICATION_TYPE_C,
    NOTIFICATION_TYPE_D,
)
NOTIFICATION_TYPE_DISPLAY_LABELS: Final[dict[NotificationType, str]] = {
    NOTIFICATION_TYPE_A: "タイプA",
    NOTIFICATION_TYPE_B: "タイプB",
    NOTIFICATION_TYPE_C: "タイプC",
    NOTIFICATION_TYPE_D: "タイプD",
}


def display_label_for_type(notification_type: NotificationType) -> str:
    return NOTIFICATION_TYPE_DISPLAY_LABELS[notification_type]

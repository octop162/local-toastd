from __future__ import annotations

import logging
import threading
from types import ModuleType

logger = logging.getLogger(__name__)

try:
    import winsound as _winsound
except ImportError:  # pragma: no cover - Windows target, fallback kept for portability.
    winsound: ModuleType | None = None
else:
    winsound = _winsound


LEVEL_TONES = {
    "info": ((900, 45), (1200, 55)),
    "success": ((980, 50), (1320, 65)),
    "warning": ((760, 70), (620, 80)),
    "error": ((540, 85), (420, 120)),
}


def play_notification_sound(level: str, enabled: bool = True) -> None:
    if not enabled:
        return

    if winsound is None:
        logger.info("winsound is unavailable; skipping notification sound")
        return

    tones = LEVEL_TONES[level]
    thread = threading.Thread(
        target=_play_tone_sequence,
        args=(tones,),
        name="local-toastd-sound",
        daemon=True,
    )
    thread.start()


def _play_tone_sequence(tones: tuple[tuple[int, int], ...]) -> None:
    if winsound is None:
        return

    for frequency, duration in tones:
        try:
            winsound.Beep(frequency, duration)
        except RuntimeError:
            winsound.MessageBeep()
            break

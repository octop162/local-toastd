from __future__ import annotations

import logging
from importlib.resources import files
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import SoundType

logger = logging.getLogger(__name__)

try:
    import winsound as _winsound
except ImportError:  # pragma: no cover - Windows target, fallback kept for portability.
    winsound: ModuleType | None = None
else:
    winsound = _winsound


SOUND_TYPE_FILES = {
    "gentle": "se2.wav",
    "taiko": "se1.wav",
    "zangeki": "se3.wav",
}


def play_notification_sound(
    level: str,
    *,
    sound_type: SoundType = "gentle",
    enabled: bool = True,
) -> None:
    if not enabled or sound_type == "off":
        return

    if winsound is None:
        logger.info("winsound is unavailable; skipping notification sound")
        return

    sound_path = resolve_sound_path(sound_type)
    if sound_path is None:
        logger.warning("Sound file for '%s' is unavailable; skipping playback", sound_type)
        return

    winsound.PlaySound(
        str(sound_path),
        winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
    )


def resolve_sound_path(sound_type: SoundType) -> Path | None:
    if sound_type == "off":
        return None

    filename = SOUND_TYPE_FILES.get(sound_type)
    if filename is None:
        return None

    asset = files("local_toastd").joinpath("assets").joinpath("sounds").joinpath(filename)
    asset_path = Path(str(asset))
    if asset_path.exists():
        return asset_path

    return None

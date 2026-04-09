from __future__ import annotations

from local_toastd.sound import LEVEL_TONES


def test_level_tones_cover_all_supported_levels() -> None:
    assert set(LEVEL_TONES) == {"info", "success", "warning", "error"}
    assert all(tones for tones in LEVEL_TONES.values())

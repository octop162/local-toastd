from __future__ import annotations

from local_toastd.sound import SOUND_TYPE_FILES, resolve_sound_path


def test_sound_profiles_map_to_wav_files() -> None:
    assert SOUND_TYPE_FILES == {
        "gentle": "se2.wav",
        "taiko": "se1.wav",
        "zangeki": "se3.wav",
    }


def test_resolve_sound_path_finds_packaged_assets() -> None:
    taiko_path = resolve_sound_path("taiko")
    gentle_path = resolve_sound_path("gentle")
    zangeki_path = resolve_sound_path("zangeki")

    assert taiko_path is not None
    assert gentle_path is not None
    assert zangeki_path is not None
    assert taiko_path.name == "se1.wav"
    assert gentle_path.name == "se2.wav"
    assert zangeki_path.name == "se3.wav"
    assert taiko_path.exists()
    assert gentle_path.exists()
    assert zangeki_path.exists()

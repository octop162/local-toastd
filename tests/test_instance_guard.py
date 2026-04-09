from __future__ import annotations

from pathlib import Path

import pytest

from local_toastd.instance_guard import SingleInstanceGuard, resolve_lock_path


def test_resolve_lock_path_uses_localappdata(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_base = Path("C:/Users/test/AppData/Local")
    monkeypatch.setenv("LOCALAPPDATA", str(expected_base))

    assert resolve_lock_path() == expected_base / "local-toastd" / "instance.lock"


def test_single_instance_guard_blocks_second_lock(tmp_path: Path) -> None:
    lock_path = tmp_path / "instance.lock"
    first = SingleInstanceGuard(lock_path)
    second = SingleInstanceGuard(lock_path)

    assert first.acquire() is True
    assert second.acquire() is False

    first.release()

    assert second.acquire() is True
    second.release()

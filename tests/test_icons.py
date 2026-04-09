from __future__ import annotations

from pathlib import Path

from local_toastd.icons import resolve_app_icon_path


def test_resolve_app_icon_path_prefers_project_icon(tmp_path: Path) -> None:
    icon_dir = tmp_path / "icons"
    icon_dir.mkdir(parents=True)
    icon_path = icon_dir / "icon.ico"
    icon_path.write_bytes(b"ico")

    resolved = resolve_app_icon_path(project_root=tmp_path)

    assert resolved == icon_path


def test_resolve_app_icon_path_falls_back_to_packaged_asset() -> None:
    resolved = resolve_app_icon_path(project_root=Path("Z:/missing-project-root"))

    assert resolved is not None
    assert resolved.name == "app.ico"
    assert resolved.exists()

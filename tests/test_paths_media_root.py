from __future__ import annotations

from pathlib import Path

from openstarry_code.paths import media_root_from_config


class _Config:
    attachments = None
    state_dir = None
    config_path = None


def test_default_media_root_uses_opensquilla_home_not_cwd(
    monkeypatch, tmp_path: Path
) -> None:
    home = tmp_path / "home" / ".openstarry-code"
    long_cwd = tmp_path / ("nested-" + "x" * 24) / ("worktree-" + "y" * 24)
    long_cwd.mkdir(parents=True)
    monkeypatch.setenv("OPENSTARRY_CODE_STATE_DIR", str(home))
    monkeypatch.chdir(long_cwd)

    assert media_root_from_config(_Config()) == home / "media"


def test_default_media_root_prefers_config_state_root(tmp_path: Path) -> None:
    class Config:
        attachments = None
        state_dir = str(tmp_path / "runtime-home" / "state")
        config_path = None

    assert media_root_from_config(Config()) == tmp_path / "runtime-home" / "media"


def test_relocated_state_dir_keeps_media_inside_state_tree(tmp_path: Path) -> None:
    # A state_dir not following the default "<home>/state" layout must keep its
    # media inside the operator-provisioned tree, not escape to a sibling dir.
    class Config:
        attachments = None
        state_dir = str(tmp_path / "srv" / "opensquilla-state")
        config_path = None

    state = Path(Config.state_dir)
    state.mkdir(parents=True)

    media = media_root_from_config(Config())

    assert media == state / "media"
    assert media.is_relative_to(state)


def test_explicit_media_root_is_preserved(tmp_path: Path) -> None:
    class Attachments:
        media_root = str(tmp_path / "custom-media")

    class Config:
        attachments = Attachments()
        state_dir = str(tmp_path / "runtime-home" / "state")
        config_path = None

    assert media_root_from_config(Config()) == tmp_path / "custom-media"

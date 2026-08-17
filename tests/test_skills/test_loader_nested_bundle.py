"""Regression coverage for imported nested Skill packs."""

from __future__ import annotations

from pathlib import Path

from openstarry_code.skills.loader import SkillLoader


def _write_skill(root: Path, relative: str, name: str) -> None:
    skill_dir = root / relative
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n\nBody for {name}.\n",
        encoding="utf-8",
    )


def test_bundled_loader_discovers_nested_manifests(tmp_path: Path) -> None:
    bundled = tmp_path / "bundled"
    _write_skill(bundled, "top", "top")
    _write_skill(bundled, "router/child", "router-child")
    _write_skill(bundled, ".system/hidden", "hidden")

    loader = SkillLoader(bundled_dir=bundled, snapshot_path=tmp_path / "snapshot.json")
    names = {skill.name for skill in loader.load_all()}

    assert names == {"top", "router-child"}

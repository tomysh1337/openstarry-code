from __future__ import annotations

from pathlib import Path

from openstarry_code.skills.loader import SkillLoader


def test_bundled_skill_visibility_baseline_is_stable(tmp_path: Path) -> None:
    bundled = Path(__file__).parents[1] / "src" / "openstarry_code" / "skills" / "bundled"
    loader = SkillLoader(
        bundled_dir=bundled,
        snapshot_path=tmp_path / "bundled-snapshot.json",
    )

    skills = loader.load_all()

    assert loader.snapshot().errors == ()
    # The bundled catalog is extensible: imported Skill packs and nested
    # manifests are part of the release surface. Guard against dropped files
    # without freezing the test to the historical 75-skill catalog.
    on_disk = {
        path.parent
        for path in bundled.rglob("SKILL.md")
        if not any(part.startswith(".") for part in path.relative_to(bundled).parts)
    }
    assert len(loader.snapshot().candidates) == len(on_disk)
    assert len(skills) <= len(on_disk)
    assert len(skills) >= 75
    assert loader.get_by_name("code-task") is not None
    assert loader.get_by_name("memory") is not None

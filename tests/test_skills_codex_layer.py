from __future__ import annotations

from pathlib import Path

from openstarry_code.skills.loader import MAX_SKILLS_PER_SOURCE, SkillLoader
from openstarry_code.skills.types import SkillLayer


def _write_skill(root: Path, name: str, description: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )


def _write_nameless_skill(root: Path, directory: str) -> None:
    skill_dir = root / directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "description: Codex manifest without an explicit name\n"
        "---\n\n"
        "# Nameless Codex skill\n",
        encoding="utf-8",
    )


def _write_invalid_utf8_skill(root: Path, name: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_bytes(
        b"---\n"
        + f"name: {name}\n".encode()
        + b"description: Damaged UTF-8 marker \xe2\x80?\n"
        + b"---\n\n# Body\n"
    )


def test_codex_layer_observes_skills_added_after_loader_construction(
    tmp_path: Path,
) -> None:
    codex_dir = tmp_path / "codex" / "skills"
    loader = SkillLoader(
        personal_codex_dir=codex_dir,
        snapshot_path=tmp_path / "snapshot.json",
    )

    assert loader.get_by_name("codex-shared") is None

    _write_skill(codex_dir, "codex-shared", "Shared through CODEX_HOME")
    result = loader.refresh_if_changed("test.codex-created")

    assert result.success is True
    assert result.added == ("codex-shared",)
    skill = loader.get_by_name("codex-shared")
    assert skill is not None
    assert skill.layer is SkillLayer.CODEX


def test_codex_layer_uses_directory_name_when_frontmatter_omits_name(
    tmp_path: Path,
) -> None:
    codex_dir = tmp_path / "codex"
    _write_nameless_skill(codex_dir, "directory-fallback")
    loader = SkillLoader(
        personal_codex_dir=codex_dir,
        snapshot_path=tmp_path / "snapshot.json",
    )

    skill = loader.get_by_name("directory-fallback")

    assert skill is not None
    assert skill.layer is SkillLayer.CODEX
    assert skill.description == "Codex manifest without an explicit name"


def test_codex_layer_replaces_invalid_utf8_without_dropping_the_skill(
    tmp_path: Path,
) -> None:
    codex_dir = tmp_path / "codex"
    _write_invalid_utf8_skill(codex_dir, "damaged-encoding")
    loader = SkillLoader(
        personal_codex_dir=codex_dir,
        snapshot_path=tmp_path / "snapshot.json",
    )

    skill = loader.get_by_name("damaged-encoding")

    assert skill is not None
    assert skill.layer is SkillLayer.CODEX
    assert "\ufffd" in skill.description


def test_codex_layer_precedence_is_between_managed_and_personal(
    tmp_path: Path,
) -> None:
    managed_dir = tmp_path / "managed"
    codex_dir = tmp_path / "codex"
    personal_dir = tmp_path / "personal"
    _write_skill(managed_dir, "shared-name", "Managed version")
    _write_skill(codex_dir, "shared-name", "Codex version")
    _write_skill(personal_dir, "shared-name", "Personal version")
    loader = SkillLoader(
        managed_dir=managed_dir,
        personal_codex_dir=codex_dir,
        personal_agents_dir=personal_dir,
        snapshot_path=tmp_path / "snapshot.json",
    )

    winner = loader.get_by_name("shared-name")

    assert winner is not None
    assert winner.layer is SkillLayer.PERSONAL
    assert [skill.layer for skill in loader.snapshot().shadowed] == [
        SkillLayer.MANAGED,
        SkillLayer.CODEX,
    ]

    (personal_dir / "shared-name" / "SKILL.md").unlink()
    result = loader.refresh_if_changed("test.personal-removed")

    assert result.success is True
    winner = loader.get_by_name("shared-name")
    assert winner is not None
    assert winner.layer is SkillLayer.CODEX


def test_codex_layer_can_load_more_than_the_standard_layer_limit(
    tmp_path: Path,
) -> None:
    codex_dir = tmp_path / "codex"
    for index in range(MAX_SKILLS_PER_SOURCE + 1):
        name = f"codex-{index:03d}"
        _write_skill(codex_dir, name, f"Codex skill {index}")
    loader = SkillLoader(
        personal_codex_dir=codex_dir,
        snapshot_path=tmp_path / "snapshot.json",
    )

    skills = loader.load_all()

    assert len(skills) == MAX_SKILLS_PER_SOURCE + 1
    assert all(skill.layer is SkillLayer.CODEX for skill in skills)

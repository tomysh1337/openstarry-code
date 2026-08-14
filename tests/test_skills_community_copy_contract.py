from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = [
    ROOT / "src" / "openstarry_code" / "cli" / "skills_cmd.py",
    ROOT / "openstarry-code-webui" / "src" / "locales" / "en.json",
    ROOT
    / "openstarry-code-webui"
    / "src"
    / "components"
    / "skills"
    / "SkillsAddDrawer.vue",
    ROOT / "src" / "openstarry_code" / "skills" / "hub" / "__init__.py",
    ROOT / "src" / "openstarry_code" / "skills" / "hub" / "clawhub.py",
    ROOT / "src" / "openstarry_code" / "skills" / "hub" / "source.py",
]


def test_clawhub_copy_uses_community_source_language() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SURFACES)
    lower = combined.lower()

    assert "official marketplace" not in lower
    assert "openstarry-code marketplace" not in lower
    assert "marketplace" not in lower
    assert "community" in lower
    assert "clawhub community source" in lower

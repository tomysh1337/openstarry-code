"""Reverse Skill dependency metadata must not hide Skills from tool filtering."""

from __future__ import annotations

from pathlib import Path

import pytest

from openstarry_code.skills.loader import SkillLoader

BUNDLED = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "openstarry_code"
    / "skills"
    / "bundled"
)

EXPECTED_BINS = {
    "artifact-reverse-orchestrator": {"recaf", "enigma-mcp", "debugger"},
    "java-reverse-toolchain": {"java", "javap", "recaf", "enigma-mcp"},
    "native-residue-triage": {"strings", "rg", "ida", "debugger"},
    "vmp-3x-native-deobfuscation": {"ida", "debugger", "python"},
    "android-reverse-engineering-complete": {"jadx", "recaf", "enigma-mcp", "ida"},
}


@pytest.fixture
def loader(tmp_path: Path) -> SkillLoader:
    loader = SkillLoader(bundled_dir=BUNDLED, snapshot_path=tmp_path / "snapshot.json")
    loader.invalidate_cache()
    loader.load_all()
    return loader


def test_reverse_skills_remain_visible_without_external_bins(loader: SkillLoader) -> None:
    """External binaries belong to readiness metadata, not tool-gating metadata."""

    builtin_tools = {"exec_command", "subagents", "read_file", "write_file"}
    visible = {skill.name for skill in loader.filter_by_tools(builtin_tools)}

    for name, expected_bins in EXPECTED_BINS.items():
        spec = loader.get_by_name(name)
        assert spec is not None
        assert set(spec.requires_tools) <= builtin_tools
        assert name in visible
        assert not {"recaf", "ida", "enigma-mcp"} & set(spec.requires_tools)

        assert spec.metadata is not None
        assert spec.metadata.requires is not None
        assert expected_bins <= set(spec.metadata.requires.bins)

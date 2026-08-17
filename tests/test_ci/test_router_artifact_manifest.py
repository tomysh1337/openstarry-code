from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "update_router_artifact_manifest.py"
BUNDLE_DIR = (
    REPO_ROOT
    / "src"
    / "openstarry_code"
    / "squilla_router"
    / "models"
    / "v4.2_phase3_inference"
)
MANIFEST_PATH = BUNDLE_DIR / "artifact_manifest.json"
PROVENANCE_PATH = BUNDLE_DIR / "PROVENANCE.md"
NOTICES_PATH = REPO_ROOT / "THIRD_PARTY_NOTICES.md"


def _load_manifest_module():
    spec = importlib.util.spec_from_file_location("update_router_artifact_manifest", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_router_artifact_manifest_is_fresh() -> None:
    module = _load_manifest_module()

    expected = module.build_manifest()
    actual = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert actual == expected


def test_router_bundle_provenance_and_notices_exist() -> None:
    assert PROVENANCE_PATH.is_file()
    assert NOTICES_PATH.is_file()

    provenance = PROVENANCE_PATH.read_text(encoding="utf-8")
    notices = NOTICES_PATH.read_text(encoding="utf-8")

    assert "BAAI/bge-small-zh-v1.5" in provenance
    assert "joblib.load" in provenance
    assert "artifact_manifest.json" in provenance
    assert "BAAI/bge-small-zh-v1.5" in notices
    assert "Copyright (c) 2022 staoxiao" in notices
    assert "Treat these artifacts as executable-code-equivalent" in notices

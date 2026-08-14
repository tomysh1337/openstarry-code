"""Regenerate the SquillaRouter V4 Phase 3 artifact manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_REL = Path("src/openstarry_code/squilla_router/models/v4.2_phase3_inference")
BUNDLE_DIR = REPO_ROOT / BUNDLE_REL
MANIFEST_PATH = BUNDLE_DIR / "artifact_manifest.json"

ASSET_SUFFIXES = {
    ".bin",
    ".joblib",
    ".json",
    ".onnx",
    ".pkl",
    ".txt",
    ".yaml",
    ".yml",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _kind(rel_path: str) -> str:
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".bin":
        return "lightgbm_model"
    if suffix == ".onnx":
        return "onnx_model"
    if suffix in {".pkl", ".joblib"}:
        return "pickle_joblib_artifact"
    if suffix == ".json":
        return "json_metadata"
    if suffix in {".yaml", ".yml"}:
        return "yaml_config"
    if suffix == ".txt":
        return "text_asset"
    return "asset"


def _source_note(rel_path: str) -> str:
    if rel_path.startswith("bge_onnx/"):
        return "Derived from BAAI/bge-small-zh-v1.5; see PROVENANCE.md."
    if rel_path.startswith("features/"):
        return "Router runtime feature extraction artifact."
    if rel_path.startswith("mlp/"):
        return "Router runtime MLP head artifact."
    if rel_path.startswith("lgbm_"):
        return "Router runtime LightGBM head artifact."
    return "Router V4 Phase 3 bundle metadata or runtime configuration."


def iter_asset_paths() -> list[Path]:
    paths: list[Path] = []
    for path in BUNDLE_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path == MANIFEST_PATH:
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in ASSET_SUFFIXES:
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(BUNDLE_DIR).as_posix())


def build_manifest() -> dict[str, object]:
    files = []
    for path in iter_asset_paths():
        rel_path = path.relative_to(BUNDLE_DIR).as_posix()
        files.append(
            {
                "path": rel_path,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "kind": _kind(rel_path),
                "source_note": _source_note(rel_path),
            }
        )

    return {
        "schema_version": 1,
        "bundle": BUNDLE_REL.as_posix(),
        "description": "Checksums and provenance notes for SquillaRouter V4 Phase 3 assets.",
        "files": files,
    }


def main() -> None:
    manifest = build_manifest()
    content = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


if __name__ == "__main__":
    main()

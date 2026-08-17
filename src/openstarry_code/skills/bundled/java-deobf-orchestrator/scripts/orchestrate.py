#!/usr/bin/env python3
"""Stateful dispatcher for reproducible Java JAR recovery."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
PROBE = SKILL_ROOT.parent / "advanced-java-reverse-deobf" / "scripts" / "jar_probe.py"
RESIDUAL = SKILL_ROOT / "scripts" / "residual_audit.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_state(case: Path) -> dict:
    return json.loads((case / "state.json").read_text(encoding="utf-8"))


def save_state(case: Path, state: dict) -> None:
    (case / "state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_event(case: Path, event: dict) -> None:
    state = load_state(case)
    event["at"] = now()
    state.setdefault("events", []).append(event)
    save_state(case, state)


def ensure_layout(case: Path) -> None:
    for name in ("original", "stages", "decompiled", "mappings", "reports", "logs"):
        (case / name).mkdir(parents=True, exist_ok=True)


def initialize(input_jar: Path, case: Path) -> None:
    case.mkdir(parents=True, exist_ok=True)
    ensure_layout(case)
    target = case / "original" / input_jar.name
    if target.exists() and sha256(target) != sha256(input_jar):
        raise SystemExit(f"immutable original collision: {target}")
    if not target.exists():
        shutil.copy2(input_jar, target)
    state = {
        "schema": 1,
        "createdAt": now(),
        "original": {"path": str(target.resolve()), "sha256": sha256(target)},
        "authoritative": {"path": str(target.resolve()), "sha256": sha256(target), "verified": False, "label": "original"},
        "stages": [],
        "events": [],
    }
    save_state(case, state)
    mapping = case / "mappings" / "names.csv"
    if not mapping.exists():
        mapping.write_text("old,new,kind,confidence,evidence\n", encoding="utf-8")


def find_jars(roots: list[Path], needles: tuple[str, ...]) -> list[Path]:
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.jar"):
            lowered = path.name.lower()
            if any(needle in lowered for needle in needles):
                candidates.append(path)
    return sorted(set(candidates), key=lambda item: (len(item.parts), -item.stat().st_mtime_ns))


def run_logged(case: Path, label: str, command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    log = case / "logs" / f"{label}.log"
    log.write_text(
        "COMMAND\n" + subprocess.list2cmdline(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
        encoding="utf-8",
    )
    append_event(case, {"type": "command", "label": label, "command": command, "exitCode": completed.returncode, "log": str(log.resolve())})
    return completed


def authoritative(case: Path) -> Path:
    return Path(load_state(case)["authoritative"]["path"])


def probe(case: Path, roots: list[Path], label: str) -> None:
    output = case / "reports" / f"probe-{label}.json"
    command = [sys.executable, str(PROBE), str(authoritative(case)), "--output", str(output)]
    for root in roots:
        command += ["--tool-root", str(root)]
    completed = run_logged(case, f"probe-{label}", command)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def decompile(case: Path, roots: list[Path], label: str) -> None:
    source = authoritative(case)
    tool_roots = roots + [case.parent, Path.home() / ".m2" / "repository"]
    cfrs = find_jars(tool_roots, ("cfr",))
    vines = find_jars(tool_roots, ("vineflower", "fernflower"))
    if not cfrs and not vines:
        raise SystemExit("no CFR or Vineflower JAR discovered; add --tool-root")
    jobs: list[tuple[str, list[str], Path]] = []
    if cfrs:
        output = case / "decompiled" / f"{label}-cfr"
        output.mkdir(parents=True, exist_ok=True)
        jobs.append((f"decompile-{label}-cfr", ["java", "-jar", str(cfrs[0]), str(source), "--outputdir", str(output)], output))
    if vines:
        output = case / "decompiled" / f"{label}-vineflower"
        output.mkdir(parents=True, exist_ok=True)
        jobs.append((f"decompile-{label}-vineflower", ["java", "-jar", str(vines[0]), str(source), str(output)], output))
    for job_label, command, output in jobs:
        completed = run_logged(case, job_label, command)
        append_event(case, {"type": "decompile", "label": job_label, "output": str(output.resolve()), "javaFiles": len(list(output.rglob("*.java")))})
        if completed.returncode:
            print(f"warning: {job_label} exited {completed.returncode}", file=sys.stderr)


def register_stage(case: Path, jar: Path, label: str, verified: bool) -> None:
    state = load_state(case)
    number = len(state["stages"]) + 1
    target = case / "stages" / f"{number:03d}-{label}.jar"
    shutil.copy2(jar, target)
    entry = {"number": number, "label": label, "path": str(target.resolve()), "sha256": sha256(target), "verified": verified, "at": now()}
    state["stages"].append(entry)
    if verified:
        state["authoritative"] = entry.copy()
    state["events"].append({"type": "stage", **entry})
    save_state(case, state)


def audit(case: Path, source: Path, label: str) -> None:
    output = case / "reports" / f"residual-{label}.json"
    completed = run_logged(case, f"audit-{label}", [sys.executable, str(RESIDUAL), str(source), "--output", str(output)])
    if completed.returncode:
        raise SystemExit(completed.returncode)


def handoff(case: Path) -> None:
    state = load_state(case)
    reports = sorted((case / "reports").glob("*.json"))
    residuals = []
    for report in reports:
        if not report.name.startswith("residual-"):
            continue
        payload = json.loads(report.read_text(encoding="utf-8"))
        residuals.append((report.name, payload.get("javaFiles", 0), payload.get("residualTotal", 0)))
    lines = [
        "# Java Deobfuscation Handoff",
        "",
        "## Authoritative Input",
        "",
        f"- Path: `{state['authoritative']['path']}`",
        f"- SHA-256: `{state['authoritative']['sha256']}`",
        f"- Verified: `{state['authoritative'].get('verified', False)}`",
        f"- Label: `{state['authoritative'].get('label', 'unknown')}`",
        "",
        "## Inventory",
        "",
        f"- Registered stages: {len(state.get('stages', []))}",
        f"- Reports: {len(reports)}",
        f"- Decompiled trees: {len([path for path in (case / 'decompiled').iterdir() if path.is_dir()])}",
        "",
        "## Residual Audit",
        "",
    ]
    lines += [f"- `{name}`: {files} Java files, {count} residual signals" for name, files, count in residuals] or ["- No residual audit recorded."]
    lines += [
        "",
        "## Next Actions",
        "",
        "1. Read the newest probe and residual reports.",
        "2. Select one evidence-backed bytecode or source-recovery pass.",
        "3. Verify the output before registering it as authoritative.",
        "4. Re-run both decompilers, compile audit, metadata-reference audit, and residual audit.",
        "5. Update mappings with confidence and evidence; keep unresolved names neutral.",
        "",
        "## Replay",
        "",
        f"`py -3 {Path(__file__).resolve()} status --case {case.resolve()}`",
        f"`py -3 {Path(__file__).resolve()} probe --case {case.resolve()}`",
        f"`py -3 {Path(__file__).resolve()} decompile --case {case.resolve()}`",
        "",
    ]
    (case / "HANDOFF.md").write_text("\n".join(lines), encoding="utf-8")


def status(case: Path) -> None:
    state = load_state(case)
    print(json.dumps({
        "case": str(case.resolve()),
        "authoritative": state["authoritative"],
        "stages": len(state.get("stages", [])),
        "reports": len(list((case / "reports").glob("*.json"))),
        "decompiledTrees": len([path for path in (case / "decompiled").iterdir() if path.is_dir()]),
    }, indent=2, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("init", "run"):
        item = commands.add_parser(name)
        item.add_argument("input", type=Path)
        item.add_argument("--case", required=True, type=Path)
        item.add_argument("--tool-root", action="append", default=[], type=Path)
    for name in ("probe", "decompile"):
        item = commands.add_parser(name)
        item.add_argument("--case", required=True, type=Path)
        item.add_argument("--tool-root", action="append", default=[], type=Path)
        item.add_argument("--label", default="current")
    item = commands.add_parser("stage")
    item.add_argument("jar", type=Path)
    item.add_argument("--case", required=True, type=Path)
    item.add_argument("--label", required=True)
    item.add_argument("--verified", action="store_true")
    item = commands.add_parser("audit")
    item.add_argument("--case", required=True, type=Path)
    item.add_argument("--source", required=True, type=Path)
    item.add_argument("--label", default="current")
    for name in ("status", "handoff"):
        item = commands.add_parser(name)
        item.add_argument("--case", required=True, type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    case = args.case.resolve()
    if args.command in ("init", "run"):
        initialize(args.input.resolve(), case)
        if args.command == "init":
            return 0
        probe(case, args.tool_root, "original")
        decompile(case, args.tool_root, "original")
        for tree in sorted((case / "decompiled").iterdir()):
            if tree.is_dir():
                audit(case, tree, tree.name)
        handoff(case)
    elif args.command == "probe":
        probe(case, args.tool_root, args.label)
    elif args.command == "decompile":
        decompile(case, args.tool_root, args.label)
    elif args.command == "stage":
        register_stage(case, args.jar.resolve(), args.label, args.verified)
    elif args.command == "audit":
        audit(case, args.source.resolve(), args.label)
    elif args.command == "status":
        status(case)
    elif args.command == "handoff":
        handoff(case)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

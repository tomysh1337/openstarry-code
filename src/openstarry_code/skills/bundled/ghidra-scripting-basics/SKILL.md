---
name: ghidra-scripting-basics
description: >
  Ghidra headless (analyzeHeadless) and Jython/Python scripting basics for
  authorized binary reverse engineering: project import, post-scripts, function
  and decompiler export, xrefs, and batch automation. Use when writing or
  debugging Ghidra scripts, analyzeHeadless pipelines, or headless decompilation
  — not for unauthorized targets.
---

# Ghidra Scripting Basics

Automate **authorized** static RE with Ghidra headless and scripts. Prefer the
smallest script that answers the question over full GUI rebuilds.

## Scope And Authorization

- **In scope:** owned binaries, lab/CTF samples, written engagement scope.
- **Out of scope:** third-party production without authorization; crack kits.
- Keep originals **immutable**; projects/scripts/exports under `derived/`.
- Redact secrets from shared script output.

## Use When

- Ghidra scripts, Jython, `analyzeHeadless`, batch decompile/export
- Function lists, string/xref dumps, or selective decompiler C
- Evidence-backed rename/bookmark at known addresses
- Reproducible lab/CI re-analysis of a fixed sample set

| Need instead | Prefer |
| --- | --- |
| Full Ghidra/IDA product workflow | `Ghidra_IDAReverseEngineeringSkill` |
| General binary triage | `binary-re` |
| r2-centric static (no Ghidra) | `binary-re/static-analysis` (`binary-re-static-analysis`) |
| Tools missing | `binary-re/tool-setup` |
| IDAPython | `ida-python-basics` |

## Repo Config First

1. Search for `GHIDRA_INSTALL_DIR`, `analyzeHeadless`, `ghidra_scripts/`, and
   processor overrides in repo/lab notes.
2. Reuse team export dirs, schemas, and naming before inventing new ones.
3. Honor engagement host rules (e.g. no outbound network).
4. New scripts only under `derived/ghidra/scripts/`.

```bash
echo "$GHIDRA_INSTALL_DIR"; which analyzeHeadless 2>/dev/null
```

## Workflow

### 1. Preserve sample

```bash
mkdir -p derived/ghidra/{projects,scripts,export,logs}
cp -n sample.bin derived/ghidra/sample.bin
sha256sum sample.bin | tee derived/ghidra/sample.bin.sha256
file sample.bin
```

### 2. Headless import + post-script

Processors: `x86:LE:64:default`, `x86:LE:32:default`, `AARCH64:LE:64:v8A`,
`ARM:LE:32:v7`, `MIPS:BE:32:default`.

```bash
analyzeHeadless derived/ghidra/projects lab_proj \
  -import derived/ghidra/sample.bin \
  -processor x86:LE:64:default \
  -analysisTimeoutPerFile 600 \
  -scriptPath derived/ghidra/scripts \
  -postScript export_functions.py \
  -deleteProject
```

`-preScript` before analysis; `-postScript` after. Drop `-deleteProject` to keep
a reusable project. Set `-processor` when arch is known.

### 3. Minimal post-script (Jython)

```python
# derived/ghidra/scripts/export_functions.py  # @category Analysis
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import os
out = os.environ.get("GHIDRA_EXPORT", "derived/ghidra/export")
if not os.path.isdir(out): os.makedirs(out)
prog, fm, mon = currentProgram, currentProgram.getFunctionManager(), ConsoleTaskMonitor()
iface = DecompInterface(); iface.openProgram(prog)
with open(os.path.join(out, "functions.txt"), "w") as f:
    for fn in fm.getFunctions(True):
        f.write("%s\t%s\n" % (fn.getEntryPoint(), fn.getName()))
        n = fn.getName()
        if n in ("main", "entry") or "crypt" in n.lower():
            res = iface.decompileFunction(fn, 60, mon)
            if res and res.decompileCompleted():
                open(os.path.join(out, "decomp_%s.c" % n), "w").write(
                    res.getDecompiledFunction().getC())
```

### 4. Common tasks

| Task | API direction |
| --- | --- |
| Functions | `FunctionManager.getFunctions(True)` |
| Xrefs | `getReferencesTo` / `getReferencesFrom` |
| Rename | `fn.setName(name, SourceType.USER_DEFINED)` |
| Strings/imports | listing data + external symbols |

Rename only with evidence (string xref, import callers). Batch samples with a
loop of `analyzeHeadless ... -import $f -postScript ...`. Debug via headless
logs + GUI Script Manager; pin Ghidra version; spot-check with
`binary-re/static-analysis`.

## Routing

| Need | Skill |
| --- | --- |
| Broader Ghidra/IDA RE | `Ghidra_IDAReverseEngineeringSkill` |
| End-to-end binary RE | `binary-re` |
| Deep static / r2 | `binary-re/static-analysis` (`binary-re-static-analysis`) |
| Install Ghidra | `binary-re/tool-setup` |
| IDAPython | `ida-python-basics` |

**Primary:** headless/Jython → this skill. Product methodology →
`Ghidra_IDAReverseEngineeringSkill`. Campaign → `binary-re`. Non-Ghidra static →
`binary-re/static-analysis`.

## Checklist

- [ ] Authorization recorded; original sample immutable
- [ ] SHA-256 + arch; processor justified; repo Ghidra paths checked first
- [ ] Exports under `derived/ghidra/`; postScript documented
- [ ] Selective decomp; evidence-backed renames; version + logs saved
- [ ] Hand-off to `Ghidra_IDAReverseEngineeringSkill` / `binary-re` as needed

## Rules

Authorized RE only. Prefer post-scripts after auto-analysis; log/skip bad
functions. Redact secrets; validate critical functions with a second tool.

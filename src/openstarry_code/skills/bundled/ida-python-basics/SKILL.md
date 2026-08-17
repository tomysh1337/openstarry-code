---
name: ida-python-basics
description: >
  IDAPython scripting basics for authorized binary reverse engineering: batch
  idat/idat64 runs, function and xref enumeration, names/comments, Hex-Rays
  decompiler export when licensed, and reproducible IDB hygiene. Use when writing
  or debugging IDAPython, idaapi/idc/idautils scripts, or headless IDA automation
  — not for unauthorized targets.
---

# IDAPython Scripting Basics

Automate **authorized** static RE in IDA Pro with IDAPython and optional headless
`idat`/`idat64`. Prefer the smallest script that answers the question.

## Scope And Authorization

- **In scope:** owned binaries, lab/CTF samples, written engagement scope.
- **Out of scope:** third-party production without authorization; cracks/bypass.
- Keep originals **immutable**; IDBs/scripts/exports under `derived/`.
- Redact secrets from logs and decompiler dumps.

## Use When

- IDAPython, `idaapi` / `idc` / `idautils`, or IDA batch scripts
- Function lists, xrefs, renames, comments, or Hex-Rays export
- Headless re-analysis on a fixed IDA version
- Exporting findings to notes (text/JSON/CSV)

| Need instead | Prefer |
| --- | --- |
| Full Ghidra/IDA product workflow | `Ghidra_IDAReverseEngineeringSkill` |
| Ghidra headless/Jython only | `ghidra-scripting-basics` |
| General binary triage | `binary-re` |
| r2-centric static (no IDA) | `binary-re/static-analysis` (`binary-re-static-analysis`) |
| IDA missing | `binary-re/tool-setup` or Ghidra path |

## Repo Config First

1. Search for `IDADIR`, `idat64`, `ida_scripts/`, `idapythonrc.py`, team exporters.
2. Reuse naming, output dirs, and license-safe decompiler assumptions.
3. Match engagement IDA major version (7.x vs 8.x/9.x API drift).
4. New scripts only under `derived/ida/scripts/`.

```bash
echo "$IDADIR"; which idat64 idat 2>/dev/null
```

## Workflow

### 1. Preserve sample

```bash
mkdir -p derived/ida/{idb,scripts,export,logs}
cp -n sample.bin derived/ida/sample.bin
sha256sum sample.bin | tee derived/ida/sample.bin.sha256
file sample.bin
```

### 2. Interactive vs batch

| Mode | When |
| --- | --- |
| GUI Script file | Develop/debug API |
| `idat64 -A -Sscript.py sample` | Batch after auto-analysis |
| Existing IDB | Re-run exporters |

```bash
idat64 -A -Lderived/ida/logs/batch.log \
  -S"derived/ida/scripts/export_functions.py" \
  derived/ida/sample.bin
# Keep IDB under derived/ida/idb/; match idat vs idat64 to bitness
```

### 3. Minimal export script

No Hex-Rays → export functions/xrefs only (never invent pseudo-C). Adjust imports
for your IDA major.

```python
# derived/ida/scripts/export_functions.py
import idaapi, idautils, idc, os
try: idaapi.auto_wait()
except Exception: pass
out = os.environ.get("IDA_EXPORT", "derived/ida/export")
if not os.path.isdir(out): os.makedirs(out)
with open(os.path.join(out, "functions.txt"), "w") as f:
    for ea in idautils.Functions():
        f.write("0x%X\t%s\n" % (ea, idc.get_func_name(ea)))
try:
    import ida_hexrays
    if ida_hexrays.init_hexrays_plugin():
        for ea in idautils.Functions():
            name = idc.get_func_name(ea)
            if name in ("main", "WinMain") or "crypt" in name.lower():
                cfunc = ida_hexrays.decompile(ea)
                if cfunc:
                    open(os.path.join(out, "decomp_%s.c" % name), "w").write(str(cfunc))
except Exception as e:
    open(os.path.join(out, "hexrays_skip.txt"), "w").write(str(e))
idc.qexit(0)
```

### 4. Common tasks and failures

| Task | Direction |
| --- | --- |
| Functions | `idautils.Functions()`, `idc.get_func_name` |
| Xrefs / strings | `XrefsTo`/`XrefsFrom`, `idautils.Strings()` |
| Rename / comment | `idc.set_name`, `idc.set_cmt` |

Rename only with evidence. Empty funcs → wait analysis / wrong bitness. Import
errors → align IDA major. Hang → missing `qexit` or no `-A`. Spot-check with
Ghidra or `binary-re/static-analysis`.

## Routing

| Need | Skill |
| --- | --- |
| Broader Ghidra/IDA RE | `Ghidra_IDAReverseEngineeringSkill` |
| Ghidra headless/Jython | `ghidra-scripting-basics` |
| End-to-end binary RE | `binary-re` |
| Deep static / r2 | `binary-re/static-analysis` (`binary-re-static-analysis`) |
| Tool install | `binary-re/tool-setup` |

**Primary:** IDAPython/batch → this skill. Product methodology →
`Ghidra_IDAReverseEngineeringSkill`. Campaign → `binary-re`. Non-IDA static →
`binary-re/static-analysis`.

## Checklist

- [ ] Authorization recorded; original sample immutable
- [ ] SHA-256 + bitness; correct `idat`/`idat64`; repo paths first
- [ ] IDB/exports under `derived/ida/`; auto-analysis waited
- [ ] Hex-Rays only if licensed; evidence-backed renames; batch log + `qexit`
- [ ] Hand-off to `Ghidra_IDAReverseEngineeringSkill` / `binary-re` as needed

## Rules

Authorized RE only. No license/protection bypass outside written scope. Prefer
evidence over mass renaming; treat IDBs as derived; redact secrets; second-tool
check for critical findings.

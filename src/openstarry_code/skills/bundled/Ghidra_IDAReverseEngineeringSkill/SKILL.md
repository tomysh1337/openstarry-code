---
name: Ghidra_IDAReverseEngineeringSkill
description: >
  Ghidra and IDA Pro workflows for binary analysis: headless analysis, decompiler
  output, scripting, function recovery, types, signatures, and xrefs. Use when the
  user asks for Ghidra, IDA, analyzeHeadless, IDAPython, Ghidra scripts, or
  database-driven reverse engineering.
---

# Ghidra / IDA Reverse Engineering

## When To Use

- User names Ghidra or IDA Pro specifically.
- Need headless batch decompilation or project databases.
- Need type recovery, function signatures, or scripted xref walks.

For general binary triage without a Ghidra/IDA focus, use `binary-re` first.
For r2-centric static work, use `binary-re/static-analysis`.

## Prerequisites

| Tool | Check |
| --- | --- |
| Ghidra | `analyzeHeadless` on PATH or `$GHIDRA_INSTALL_DIR/support/analyzeHeadless` |
| Java | JRE/JDK required by installed Ghidra |
| IDA (optional) | `idat` / `idat64` or IDAPython available |
| r2 bridge (optional) | only if combining with `binary-re/static-analysis` |

If tools are missing, route to `binary-re/tool-setup` before continuing.

## Workflow

1. **Scope**
   - Record binary path, SHA-256, arch/OS from `file` / `rabin2 -I` if available.
   - Confirm authorization for the sample and analysis environment.

2. **Prefer Ghidra headless for automation**
   - Create a project under a **derived** work dir (never overwrite the original sample).
   - Import, auto-analyze, export decompilation or JSON/CSV listings.

```bash
# Example: headless import + analyze (adjust paths)
analyzeHeadless "$PROJECT_DIR" "$PROJECT_NAME" \
  -import "$SAMPLE" \
  -processor "$PROCESSOR" \
  -analysisTimeoutPerFile 600 \
  -deleteProject
```

3. **Scripted recovery (Ghidra)**
   - Enumerate functions, strings, imports/exports.
   - Dump decompiler C for high-interest functions.
   - Apply or create data types only when evidence supports them (xrefs, usage, known structs).

4. **IDA path (when user requires IDA)**
   - Open/load the binary in a disposable IDB under the work dir.
   - Use IDAPython for function lists, xrefs, and decompiler (Hex-Rays if licensed).
   - Export notes; keep IDB as derived artifact.

5. **Correlate**
   - Cross-check Ghidra/IDA names against strings, imports, and runtime evidence.
   - Mark findings as observed / code-backed / speculative.

6. **Hand off**
   - Protocol behavior → `protocol-reverse-engineering` or network codec skills.
   - Further static graph work without Ghidra focus → `binary-re/static-analysis`.
   - Report → `binary-re/synthesis` pattern (evidence table + confidence).

## Output Checklist

- [ ] Project/IDB path and sample hash
- [ ] Processor / compiler guess and confidence
- [ ] Entry points and interesting functions (name, address, reason)
- [ ] Decompiler excerpts for core logic (not whole binary dump)
- [ ] Types/signatures applied and evidence for each
- [ ] Open questions and next experiments

## Rules

- Do not claim full recovery without multi-sample or controlled-input validation when protocol fields are involved.
- Prefer smallest script that answers the question over full-project rebuilds.
- Keep originals immutable; store projects, scripts, and exports separately.

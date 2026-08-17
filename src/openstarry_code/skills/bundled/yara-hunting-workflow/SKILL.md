---
name: yara-hunting-workflow
description: >
  Practical YARA hunting loop against authorized corpora: scope, baselining,
  scan, triage hits, reduce false positives, and promote durable detections.
  Use when hunting malware/family matches with existing or draft rules — not as
  a full rule-authoring textbook (see yara-rule-authoring when available).
  Keywords: YARA scan, rule hunt, corpus match, FP reduction.
---

# YARA Hunting Workflow

## Scope And Authorization

- **Authorized only:** owned corpora, malware lab shares, CTF packs, IR cases with written scope, vendor samples you may process.
- **Out of scope:** scanning third-party estates without authorization; attacking live hosts from hits; leaking sample identities beyond the engagement.
- Keep sample trees **read-only**. Logs, drafts, and excerpts go under `derived/`.
- Unpack/detonate only in `security-sandbox`. Treat hits as malicious until proven otherwise.

## Use When

| Situation | This skill? |
| --- | --- |
| Rules (or drafts) + corpus to scan | Yes — hunt loop |
| Production-quality rule from zero | Prefer `yara-rule-authoring`, then re-hunt here |
| Single unknown PE/ELF identity | `binary-re` first; optional YARA for family ID |
| Memory-only family search | Extract modules/dumps, then scan |
| Network IOCs only (no files) | Not primary — use IOC/intel path |

**Hunt loop only:** scope → baseline → scan → triage → refine → promote. Not a full YARA language guide.

## Workflow

### 1. Scope

1. **Question:** family, capability, campaign, or packer+payload pattern.
2. **Corpus:** path, types in scope (PE/ELF/script), exclusions.
3. **Ruleset:** source + version/commit pinned.
4. **Success:** seed malware must hit; clean baseline must not (when available).

### 2. Baseline

```bash
yara --version
yara -r rules/hunt.yar clean_baseline/ 2> derived/yara-clean.err | tee derived/yara-clean.out
```

Fix noisy rules before scanning malware piles. Record full command lines and timestamps.

### 3. Scan (cheap → targeted)

```bash
yara -r -w rules/hunt.yar corpus/ 2> derived/yara-hunt.err | tee derived/yara-hunt.out
# Optional type filter via find + xargs yara rules/hunt.yar
```

1. Broad family/packer rules (or stratified sample).
2. Cluster hits by rule + fuzzy hash (`ssdeep`/`tlsh`); human-triage 1–3 per cluster.
3. Stricter rules on survivors only.
4. Re-scan after every rule edit.

### 4. Hit triage (minimum)

| Field | Record |
| --- | --- |
| Rule / tags | name, tags |
| Identity | path, SHA-256, `file` type |
| Match reason | `yara -s` string/hex ids |
| Disposition | TP / FP / unpack / needs RE |

- **FP signals:** short strings, lone common APIs, packer stubs without malware anchors.
- **TP signals:** multi-condition matches, seed agreement, IOC story via `strings-and-ioc-triage`.

### 5. FP reduction and promote

- Prefer **≥2 independent anchors** (distinctive string + structural bound).
- Split `hunt_` (wide) vs `detect_` (tight); promote `detect_` only after clean baseline + multi-sample TP.
- Deep modules/`pe.*`/performance tuning → **`yara-rule-authoring`** when present; return here to validate.

### 6. Handoff

| Observation | Next |
| --- | --- |
| Packed/crypted only | `security-sandbox` unpack → re-YARA payload |
| Need code/behavior | `binary-re` or `deep-analysis` |
| Need IOC list | `strings-and-ioc-triage` |
| Memory implant | YARA on dump/extracted region |

### 7. Report

Scope, ruleset ID, commands, counts by rule, example TP/FP hashes, rule diffs, open questions.

## Routing

| Need | Skill |
| --- | --- |
| Full rule authoring / detection eng. | `yara-rule-authoring` (elsewhere/bundle if installed) |
| Disasm, unpack methodology | `binary-re` (+ nested phases) |
| Contained lab | `security-sandbox` |
| Depth-first hard binary | `deep-analysis` (when available) |
| Per-sample strings/IOCs | `strings-and-ioc-triage` |
| RAM before file hunt | `memory-forensics-volatility` |

## Checklist

- [ ] Authorization + corpus path recorded
- [ ] Read-only samples; outputs in `derived/`
- [ ] Ruleset version pinned
- [ ] Clean baseline done or N/A justified
- [ ] Scan command reproducible
- [ ] Hits clustered; samples triaged (hash + match reason)
- [ ] FP fixed or hunt/detect split; seeds still match
- [ ] Packed hits re-scanned post-unpack
- [ ] Handoff: authoring / binary-re / deep-analysis / IOC
- [ ] Report redacts secrets; lists open questions

## Rules

- Authorized hunting only.
- No execution on production OS — use `security-sandbox`.
- One short-string hit ≠ family attribution.
- Evidence over rule-name folklore; re-validate after every edit.

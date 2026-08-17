---
name: strings-and-ioc-triage
description: >
  Authorized malware sample strings and IOC triage: extract ASCII/UTF-16 strings,
  classify URLs/IPs/paths/mutexes/registry keys, score confidence, and export a
  minimal IOC set for IR/YARA handoff. Use when doing first-pass static clues on
  PE/ELF/dumps/scripts — not full RE or unauthorized third-party scanning.
---

# Strings and IOC Triage

## Scope And Authorization

- **Authorized only:** lab/CTF/training samples, IR artifacts under written scope, files you own or are contracted to analyze.
- **Out of scope:** unauthorized host collection; using recovered C2/credentials against live systems; publishing unredacted victim data.
- Keep the sample immutable. Extracts and IOC lists under `derived/`.
- Do not execute on production OS; dynamic work → `security-sandbox`.

## Use When

| Situation | This skill? |
| --- | --- |
| First static pass for IOCs on a sample | Yes |
| URLs, IPs, mutexes, paths, registry, emails | Yes |
| Draft YARA string candidates from one file | Yes → then hunt/author |
| Full disasm / control flow | `binary-re` / `deep-analysis` |
| Corpus rule hunting | `yara-hunting-workflow` |
| Memory-only (no file yet) | Dump first, then this skill |

**Triage only:** extract → classify → de-noise → confidence → export. Not unpacking or behavioral analysis by itself.

## Workflow

### 1. Preserve and type

```bash
mkdir -p derived/strings
sha256sum sample.bin | tee derived/sample.sha256
file sample.bin
```

If packed (UPX/high entropy), still capture stub strings; plan unpack in `security-sandbox` and re-run on payload.

### 2. Extract (multiple encodings)

```bash
strings -a -n 6 sample.bin > derived/strings/ascii.txt
strings -a -n 6 -el sample.bin > derived/strings/utf16le.txt
rabin2 -zz sample.bin > derived/strings/rabin2-zz.txt 2>/dev/null
# Optional PE: floss -n 6 sample.bin > derived/strings/floss.txt
```

Use min length 6 for hunting; raise to 8–10 for high-confidence export strings.

### 3. Bucket IOCs

```bash
rg -NoN 'https?://[^\s"<>]+' derived/strings/*.txt | sort -u > derived/ioc-urls.txt
rg -NoN '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' derived/strings/*.txt | sort -u > derived/ioc-ipv4.txt
rg -i 'HKEY_|CurrentVersion\\|Software\\\\' derived/strings/*.txt | sort -u > derived/ioc-registry.txt
rg -i 'mutex|Global\\\\|Local\\\\' derived/strings/*.txt | sort -u > derived/ioc-mutex.txt
rg -i 'api[_-]?key|bearer |password|secret|token' derived/strings/*.txt \
  | sort -u > derived/ioc-secrets-REDACT.txt
```

Also note: domains, user-agents, emails, named pipes, services, `-enc`/base64 blobs, paths (`C:\`, `/tmp/`).

### 4. De-noise

Default low value unless context supports: compiler banners, lone generic APIs (`CreateFileW`, `socket`), `127.0.0.1`/`0.0.0.0`, copyright boilerplate, single English words. Prefer long, distinctive, or multi-part strings (URL + path + unique typo).

### 5. Confidence

| Score | Criteria | Action |
| --- | --- | --- |
| High | Full URL+path, unique mutex, multi-encoding agree | Export; YARA candidate |
| Medium | Domain-only, FLOSS-only decode | Investigate further |
| Low | Short token, private IP alone, common API | RE note only |

Always attach sample **SHA-256** to any IOC set.

### 6. Bounded decode

```bash
rg -NoN '[A-Za-z0-9+/]{40,}={0,2}' derived/strings/ascii.txt | head -50 > derived/b64-cands.txt
```

Decode candidates offline; `file`/re-strings results. Stop on pure high-entropy garbage → RE path.

### 7. Export package

```text
# derived/ioc-export.txt
sample_sha256: <hash>
file_type: <file(1)>
high:
  - url: ...
  - mutex: ...
medium:
  - domain: ...
notes: packed=?; re-run after unpack
```

Draft ≥3 distinctive strings (len ≥ 8) for `yara-rule-authoring` / `yara-hunting-workflow`. Strings alone ≠ family attribution.

## Routing

| Need | Skill |
| --- | --- |
| Corpus YARA hunt | `yara-hunting-workflow` |
| Durable rule craft | `yara-rule-authoring` (elsewhere/bundle if present) |
| Static/dynamic RE | `binary-re` (+ nested phases) |
| Depth-first hard sample | `deep-analysis` (when available) |
| Unpack / detonate | `security-sandbox` |
| Process memory strings | `memory-forensics-volatility` → this skill |
| Stego carrier (not PE malware) | `steganography-techniques` |

## Checklist

- [ ] Authorization confirmed; hash + `file` recorded
- [ ] Immutable original; extracts in `derived/strings/`
- [ ] ASCII + UTF-16 (as relevant); FLOSS/rabin2 if available
- [ ] Buckets filled; noise filtered; High/Med/Low applied
- [ ] Packed? unpack + re-triage planned/done in sandbox
- [ ] Secrets redacted in shared reports
- [ ] IOC export includes SHA-256 + notes
- [ ] Handoff: YARA hunt/author or binary-re/deep-analysis

## Rules

- Authorized analysis only; no out-of-scope C2/credential use.
- Strings are **hints** — validate important IOCs with RE, sandbox, or multi-sample agreement.
- Redact tokens, cookies, PII, victim identifiers.
- Prefer distinctive multi-byte strings; never sole IOC from one generic API name.

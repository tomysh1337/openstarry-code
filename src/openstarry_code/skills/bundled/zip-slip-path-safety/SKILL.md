---
name: zip-slip-path-safety
description: >-
  Zip slip and archive path-traversal on extract: detect, prove, and prevent
  unsafe zip/tar/7z extraction that writes outside the intended directory via
  ../ or absolute entry names. Use when zip slip, archive extract, unzip path
  traversal, tar slip, malicious archive entry names, or safe extract review
  for authorized assessments and owned code.
---

# Zip Slip / Archive Path Safety

Secure archive extraction and authorized testing for **zip slip** (and tar/7z
equivalents): archive entry names that escape the extract root and overwrite or
create files outside the intended directory.

## Scope And Authorization

- **In scope:** Applications, libraries, CI jobs, and services you own or are
  explicitly authorized to test; local lab proof-of-concepts with archives **you**
  craft; defensive code review of extract paths.
- **Out of scope:** Weaponizing archives against third parties; overwriting
  production configs, web roots, or shared storage without written approval and
  a rollback plan; bulk exfiltration via malicious extract chains.
- Prefer **canary files** with unique names/content (`zipslip-canary-<uuid>.txt`)
  outside the extract root — never plant webshells unless RCE is explicitly in
  scope and limited to a disposable lab.
- Keep crafted archives offline, immutable originals separate from test copies.
  Redact secrets if an extract proof accidentally touches credential files.
- Closely related: classic URL/query `../` → `path-traversal-lfi`; broader
  read/write file access → `file-access-vuln`. This skill is primary when the
  **sink is archive entry name → extract path**.

## Use When

- Features: upload+unzip, import project from zip, theme/plugin install from
  archive, backup restore, log/bundle extract, CI artifact unpack, container
  layer unpack, “download and extract” jobs.
- Libraries: `ZipInputStream`, `zipfile`, `tarfile`, `adm-zip`, `yauzl`,
  `SharpCompress`, `archive/zip`, `unzip`, `tar -x`, custom extract loops.
- Symptoms: extract creates files above intended dir; entry names with `../`,
  absolute paths (`/etc/...`, `C:\...`), or mixed separators; symlink entries.
- User mentions: zip slip, zip path traversal, tar slip, archive extract path,
  unsafe unzip, Zip Slip CVE class, malicious zip entry names.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Classic `../` in URL/query/include (no archive) | `path-traversal-lfi` |
| Arbitrary file read/write without extract | `file-access-vuln` |
| Upload MIME/extension/polyglot only | `upload-insecure-files` |
| XXE file read | `xxe-xml-external-entity` |
| Secrets found after escape write | `secrets-management-hygiene` (remediate exposure) |

## Threat Model

| Vector | Entry name pattern | Typical impact |
| --- | --- | --- |
| Relative escape | `../../evil.txt`, nested `a/../../b` | Write outside extract root |
| Absolute path | `/tmp/pwned`, `C:\Windows\Temp\x` | Write to fixed system paths |
| Separator mix | `..\..\evil`, `..\/..\/x` | Bypass naive `../` string checks |
| Encoding | URL-encoded names if decoded before join | Double-decode filter bypass |
| Symlink / hardlink | Link entry then write through it | Read/write via link follow (lab) |
| Nested archive | Outer safe, inner slip | Second-stage extract miss |
| Overwrite | Escape to app config, cron, webroot | Persistence / RCE if executable path |

Root cause pattern (almost always):

```text
join(extractRoot, entry.Name)  // without canonicalization + prefix check
```

## Workflow

### 1. Find extract sinks

Inventory code and features that:

1. Accept an archive upload or download a remote zip/tar.
2. Call extract APIs (`ZipFile.ExtractToDirectory`, `zipfile.extractall`,
   `tar.extractall`, shell `unzip`/`tar -xf`).
3. Loop entries and open `File.Create(path)` / `open(path, "wb")` with a path
   derived from the entry name.

Record: language, library, whether destination is temp or durable, privilege of
the process, and whether extract runs as a privileged CI or container user.

### 2. Baseline safe extract

1. Craft a **benign** archive with only `ok/hello.txt` under a single top folder.
2. Extract via the product path; note final tree, ownership, and that nothing
   appears outside the destination.
3. Save hashes of destination root before/after.

### 3. Prove zip slip (authorized lab / engagement)

Build **your own** test archives (do not download untrusted “exploit zips” from
random sites into production networks).

**Minimum entry names to try** (one canary per archive keeps attribution clear):

```text
../../zipslip-canary-REL.txt
../../../zipslip-canary-REL2.txt
..\\..\\zipslip-canary-WIN.txt
....//....//zipslip-canary-DOT.txt
/tmp/zipslip-canary-ABS.txt
C:/Windows/Temp/zipslip-canary-ABS-WIN.txt
subdir/../../zipslip-canary-NEST.txt
```

**Construction sketches (lab only)**

Python (`zipfile`) — relative escape:

```python
import zipfile
from io import BytesIO

buf = BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    # Malicious name; body is a unique canary string
    zf.writestr("../../zipslip-canary.txt", b"ZIPSLIP-CANARY-UNIQUE")
open("poc-zipslip.zip", "wb").write(buf.getvalue())
```

Python tar (often worse defaults historically):

```python
import tarfile, io
data = io.BytesIO(b"TAR-SLIP-CANARY")
info = tarfile.TarInfo(name="../tarslip-canary.txt")
info.size = len(data.getvalue())
with tarfile.open("poc-tarslip.tar", "w") as tf:
    tf.addfile(info, data)
```

Shell checks after upload/extract:

```text
# Did canary appear outside intended extract dir?
find /path/to/parent -name 'zipslip-canary*' 2>/dev/null
# Windows: dir /s zipslip-canary*
```

**Success criteria:** canary content readable **outside** the intended extract
root, or library throws/rejects and no outside write occurs (secure).

**Stop rules:** do not overwrite system binaries, SSH keys, or app secrets for
“stronger” demos. One canary path is enough for the report.

### 4. Encoding, filter, and platform edge cases

When simple `../` is rejected:

| Technique | Notes |
| --- | --- |
| Nested collapse | `safe/../../outside` after path normalize still escapes if only string-strip once |
| Mixed `\` / `/` | Windows APIs accept both; Unix may keep backslash as filename char |
| Absolute entries | Leading `/` or drive letter — reject entirely |
| Duplicate strips | Filter removes `../` once → `....//` becomes `../` |
| Unicode dots / NFKC | Rare; normalize then re-check |
| Zip64 / large archives | DoS via bomb is separate; still validate names first |
| Symlink entries | Extractors that follow links: only lab; document if followed |
| Nested zip | Extract outer, then auto-extract inner without re-validation |

For general traversal encoding matrices (URL, double encode), import payloads
from `path-traversal-lfi` only if the product **decodes** entry names before
join (unusual but seen in custom zip parsers).

### 5. Secure extract design (defense)

**Required control:** after resolving the final path, ensure it is still under
the extract root using **canonical** paths (not string prefix alone on relative
paths).

**Algorithm (language-agnostic)**

1. Choose empty destination dir `root` (create with restrictive permissions).
2. For each entry:
   - Reject if name is empty, contains NUL, or is absolute.
   - Reject symlink/hardlink entries unless policy explicitly allows and
     targets are also constrained under `root`.
   - `candidate = join(root, name)` with OS path API (not raw string concat).
   - `real = canonicalize(candidate)` (resolve `.` / `..`; optional: do not
     follow symlinks when creating parents).
   - Allow only if `real == root` or `real` starts with `root + separator`.
   - Create parent dirs under `root` only; write file; apply safe permissions.
3. Prefer libraries with **safe extract** helpers or audited wrappers over
   ad-hoc loops.
4. Run extract as least-privilege user; destination on a volume without
   execute if content is untrusted (`upload-insecure-files` + OS controls).
5. Optional: max entry count, max uncompressed size, max depth (zip bomb).

**Language notes (concrete)**

| Stack | Prefer | Avoid |
| --- | --- | --- |
| Java | Validate each `ZipEntry.getName()`; Apache Commons Compress with checks; never trust `ZipInputStream` path alone | `zip.new File(dest, entry.getName())` without prefix check |
| .NET | Check `Path.GetFullPath(combined)` starts with `Path.GetFullPath(root)` | `ZipFile.ExtractToDirectory` on untrusted input without latest runtime patches / validation |
| Python | Manual validate before `extract`; avoid naive `extractall` on untrusted tar | `tarfile.extractall` without `filter=` (use `"data"` filter on modern Python) |
| Node | `path.resolve` + `path.relative` must not start with `..`; audited libs | `zip.extractAllTo(dest, true)` without name checks |
| Go | `filepath.IsLocal` (Go 1.20+) / manual `filepath.Clean` + prefix | `filepath.Join(dest, hdr.Name)` only |
| Shell | `unzip` into empty dir; avoid `tar -xf` as root on untrusted input | Extract as root into `/` or app home |

**Good — prefix check after canonicalize (Python sketch)**

```python
from pathlib import Path

def safe_join(root: Path, entry_name: str) -> Path:
    root = root.resolve()
    # Reject absolute and drive-like names early
    p = Path(entry_name)
    if p.is_absolute() or ".." in p.parts:
        # Still re-check after resolve — ".." in parts is a fast reject
        pass
    dest = (root / entry_name).resolve()
    if dest != root and root not in dest.parents:
        raise ValueError(f"zip-slip blocked: {entry_name!r}")
    return dest
```

**Good — relative check (Node sketch)**

```javascript
const path = require("path");
function safeResolve(root, entryName) {
  const dest = path.resolve(root, entryName);
  const rel = path.relative(path.resolve(root), dest);
  if (rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error("zip-slip blocked: " + entryName);
  }
  return dest;
}
```

**Bad**

```python
# Trusts entry name entirely
zipfile.ZipFile(f).extractall("/var/app/uploads")
```

```java
// Classic vulnerable pattern
File out = new File(destDir, entry.getName());
// missing: out.getCanonicalPath().startsWith(destDir.getCanonicalPath())
```

### 6. Test and CI gates

1. Unit tests with fixtures: benign zip, relative slip, absolute slip, nested
   `..`, Windows separators if on Windows CI.
2. Assert extract throws or skips and destination parent has **no** canary.
3. Fuzz entry names in lab only (authorized); cap archive size.
4. Code review: every extract call site listed; privileged CI extract flagged.

### 7. Incident / finding notes

If slip is confirmed:

1. Record archive entry name, extract root, canary path, process user.
2. Check whether escape can reach config, keys, webroot, or cron — without
   further exploitation if out of scope.
3. Remediate with canonicalize+prefix (or library upgrade); add regression test.
4. If secrets were writable/readable, rotate per `secrets-management-hygiene`.

## Concrete Techniques Cheat Sheet

| Phase | Action |
| --- | --- |
| Recon | Grep `extractall`, `ExtractToDirectory`, `unzip`, `ZipEntry`, `tar -x` |
| PoC | One zip with `../../canary-UUID.txt` unique body |
| Verify | Filesystem search outside root; compare mtime/hash |
| Bypass | Nested `..`, abs paths, `..\`, symlink (lab), nested zip |
| Fix | Canonical path + root prefix; reject abs/symlink; least priv |
| Harden | Size limits; no exec mount; non-root (`dockerfile-best-practices`) |
| Quality | Shared safe-extract helper + tests (`code-quality-standards`) |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Zip/tar/7z extract path escape | **This skill** | — |
| Non-archive `../` / LFI / PHP wrappers | `path-traversal-lfi` | this skill if upload+unzip chain |
| Broad AFR/AFW, object keys, overwrite | `file-access-vuln` | this skill for archive-specific proof |
| Upload type/MIME/polyglot without extract | `upload-insecure-files` | this skill when server unzips |
| Safe extract implementation / review | `code-quality-standards` | **always** when coding the fix |
| Secrets exposed via escaped write/read | `secrets-management-hygiene` | this skill for the extract root cause |
| Extract in container image build/runtime | `dockerfile-best-practices` | non-root, no secrets in layers |
| CI unpack of untrusted artifacts | `ci-cd-pipeline-patterns` | this skill for path checks |

### Routing notes (required helpers)

- **`path-traversal-lfi`:** encoding matrices and non-archive path sinks; chain when the same product has both download path params and unzip.
- **`file-access-vuln`:** broader read/write and IDOR on files; use when impact is arbitrary file write beyond “extract root escape” framing.
- **`code-quality-standards`:** baseline for implementing shared validators, error handling, and tests around extract.
- **`secrets-management-hygiene`:** rotation and leak hygiene if canaries or bugs touch credential paths.
- **`dockerfile-best-practices`:** container user, writable paths, and avoiding privileged extract as root in images.

## Checklist

- [ ] Extract sinks inventoried (app, CI, admin import, restore)
- [ ] Authorization/lab scope confirmed; canary-only proofs
- [ ] Benign archive baseline under intended root
- [ ] Relative `../` slip tested; absolute entry tested
- [ ] Platform separators / nested `..` considered
- [ ] Symlink policy documented (reject vs lab-only follow)
- [ ] Nested archive second extract covered if product auto-unzips
- [ ] Fix: canonicalize + root prefix (or safe library filter) on **every** entry
- [ ] Absolute paths, NUL, and `..` rejected; regression tests added
- [ ] Process runs least privilege; destination not world-executable when untrusted
- [ ] `code-quality-standards` applied on the safe-extract helper
- [ ] Cross-links: upload skill if type checks weak; secrets hygiene if exposure
- [ ] Report includes entry name, paths, redacted proof, remediation

## Rules

- Only archives **you** build for offensive proofs; never deploy destructive
  overwrites on shared production systems.
- Prefer canary create over canary overwrite of existing files.
- Zip bombs (compression ratio DoS) are related but distinct — enforce size
  limits; do not confuse with path slip.
- Shelling out to `unzip`/`tar` as root on untrusted input is high risk — drop
  privileges and validate first.
- Defense and **authorized** assessment only; no third-party exploitation.
---

# Note

This skill owns **archive entry path safety** (zip slip / tar slip). Pair with
`path-traversal-lfi` for non-archive traversal, `file-access-vuln` for general
file read/write impact, `code-quality-standards` when implementing extractors,
and `dockerfile-best-practices` when extract runs in containers.

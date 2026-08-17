---
name: path-traversal-defenses
description: >-
  Defend filesystem path sinks against traversal and escape: canonicalize
  (resolve) then prefix-check under a fixed root, prefer openat/O_NOFOLLOW,
  chroot-like jail roots, and reject ".." segments and null bytes. Use when
  hardening download, include, template, attachment, or static-file path joins;
  reviewing safe path APIs; or remediating LFI/AFR findings in owned code.
---

# Path Traversal Defenses

Design and verify **defenses** that keep user-influenced paths inside an intended
root. Offensive proof catalogs belong elsewhere; this skill owns **safe path
construction, open policy, and regression checks**.

## Scope And Authorization

- **In scope:** Owned apps/libraries and authorized remediation of path sinks
  (download, include, template load, log view, static serve).
- **Out of scope:** Third-party attacks; bulk secret exfil “for proof”; webshells.
- Prefer unit/integration tests with canary paths under a temp root. Redact host
  paths and credentials in reports.
- Offensive LFI/traversal → `path-traversal-lfi`. Archive extract escape →
  `zip-slip-path-safety`. This skill is primary for **fix design**.

## When To Use

- Code joins a base directory with user input (`file=`, `path=`, `template=`,
  `lang=`, download/export names, static routers, resizers).
- Review or implement “safe join”, path jail, `realpath` + prefix, `openat`, or
  reject of `..` / NUL / absolute paths.
- Remediating traversal/LFI with a durable control (not only a `../` denylist).
- Mentions: path traversal defense, canonicalization, chroot-like root, prefix
  check after resolve, `O_NOFOLLOW`, allowlist under base dir.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Offensive `../` / LFI / PHP wrappers / encoding bypass | `path-traversal-lfi` |
| Zip/tar entry name escape on extract | `zip-slip-path-safety` |
| Broad AFR/AFW without path-root design focus | `file-access-vuln` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

### 1. Inventory sinks and roots

1. Find every path derived from request, header, cookie, or stored user data.
2. Record the intended **root** and OS (Windows drive/`\` vs POSIX).
3. Note APIs: string concat, `path.join`, `open`, `include`, `sendfile`, shell
   helpers — string filters alone are not a complete control.

### 2. Required algorithm: resolve + prefix check

Apply on **every** open/read/write of user-influenced paths:

1. **Decode once** in framework order; never re-decode after validation.
2. **Reject early:** empty; embedded **NUL** (`\0`); absolute paths; Windows
   drive/UNC (`C:\...`, `\\server\share`) when a relative child is required.
3. **Reject raw `..` segments** in the untrusted relative part (fast fail). Do
   not rely on this alone — still canonicalize.
4. `candidate = join(root, relative)` via OS path APIs (never raw string glue).
5. `real = resolve(candidate)` and resolve `root` the same way.
6. **Allow only if** `real == root` or `real` is strictly under `root` with a
   **separator boundary** (avoid `/var/www-evil` matching prefix `/var/www`).
7. Open the **resolved** path (or fd-relative APIs below). Fail closed on resolve
   errors (broken symlink, permission, race).

```text
root = resolve(configured_root)
real = resolve(join(root, user_relative))
allow iff real == root OR real starts with root + SEPARATOR
```

**Bad:** strip `"../"` once; `contains("..")` only; prefix-check unresolved
strings; open first, check later.

### 3. openat, O_NOFOLLOW, and chroot-like roots

| Control | Intent |
| --- | --- |
| Fixed root fd + `openat` | Opens stay relative to root fd; no absolute re-escape |
| `O_NOFOLLOW` / no symlink follow | Blocks symlink jailbreak to outside |
| Process/container chroot or mount NS | Defense in depth — still resolve+prefix in app |
| Opaque IDs instead of user paths | Map `id → storage key`; clients never send segments |
| Basename/extension allowlist | Extra constraint after jail for templates/downloads |

- Prefer downloads by **server-side ID** → relative key under root. If symlinks
  inside root are allowed: resolve final target, re-check prefix, document policy.
- Least privilege: process must not need host secrets outside the jail.

### 4. Rejects that must not be the only defense

Implement explicit rejects for clear failures/metrics; always pair with §2:

| Input | Action |
| --- | --- |
| `..` as a path segment | Reject before join |
| NUL byte | Reject (truncation / extension-bypass class) |
| Absolute / UNC / drive | Reject when relative child expected |
| Mixed `\` / `/` | Normalize with OS APIs, then re-validate |
| Encoded dots/slashes | Decode **once**, then full algorithm |

“We blocked `../`” without resolve + boundary prefix is incomplete.

### 5. Tests and verification

1. Temp-root fixtures: legit child; `../outside`; `a/../../outside`; absolute;
   NUL; Windows separators on Windows CI.
2. Assert reject **and** no open outside root; cover symlink-to-outside in lab.
3. Live retest → `path-traversal-lfi` (authorized); archive extract →
   `zip-slip-path-safety`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Design/review path jail, resolve+prefix, openat | **This skill** | `code-quality-standards` |
| Authorized offensive traversal / LFI / wrappers | `path-traversal-lfi` | this skill for fix |
| Zip/tar extract entry escape | `zip-slip-path-safety` | this skill for shared safe-join |
| Broader AFR/AFW impact framing | `file-access-vuln` | this skill for root policy |
| Implement shared helper + tests | `code-quality-standards` | **always** when coding |

- **`path-traversal-lfi`:** prove/bypass catalog; remediate design here.
- **`zip-slip-path-safety`:** same resolve+prefix on **archive entry names**.
- **`code-quality-standards`:** typing, errors, tests on the safe-join API.
- **`file-access-vuln`:** broader AFR/AFW beyond path-root escape.

## Output Checklist

- [ ] Path sinks and intended roots inventoried (OS noted)
- [ ] Decode-once policy; no post-check re-decode
- [ ] Reject: `..` segments, NUL, absolute/UNC/drive when relative required
- [ ] join → canonicalize root + candidate → separator-safe prefix check
- [ ] Open via resolved path or `openat` + `O_NOFOLLOW`/symlink policy
- [ ] Prefer opaque IDs over client-supplied path strings
- [ ] Regression tests: legit child, `../`, nested escape, absolute, NUL
- [ ] Retest → `path-traversal-lfi`; zip extract → `zip-slip-path-safety`
- [ ] `code-quality-standards` on shared safe-path helper
- [ ] No secrets in fixtures; host paths redacted

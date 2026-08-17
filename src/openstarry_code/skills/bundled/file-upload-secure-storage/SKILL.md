---
name: file-upload-secure-storage
description: >
  Design and review secure storage for user file uploads: random object keys,
  cookie-less separate domain, content-type/magic validation, antivirus hooks,
  size quotas, and non-executable permissions. Use when implementing or auditing
  upload landing zones, object-store keys, disk mounts, presigned PUT policies,
  or hardening post-accept storage for owned apps and authorized assessments.
---

# File Upload Secure Storage

Harden **where and how accepted uploads are stored and keyed**: opaque names,
isolated origin, type/size gates, AV hooks, and no execute rights. Attack-matrix
testing → `upload-insecure-files`. Serve/download headers →
`download-attribute-security`. Archive extract paths → `zip-slip-path-safety`.

## Scope And Authorization

- **In scope:** Owned apps, labs, CTFs, written-scope review of upload storage
  (disk, S3/GCS/Azure Blob, CDN), presigned policies, quarantine paths, IAM/ACL.
- **Out of scope:** Real malware on shared scanners; quota/ZIP bombs; third-party
  public-bucket abuse; webshells outside explicit RCE lab scope.
- Prefer canary bodies (`UPLOAD-STORE-CANARY-<uuid>`) and disposable keys. Cap
  size/count; delete test objects. Redact signed URLs, credentials, and PII.
  Do not infer authorization from sandbox-looking UIs.

## When To Use

- Building/reviewing avatar, CMS media, attachments, chat files, imports, or
  direct-to-cloud multipart/presigned uploads.
- Storage still uses user filenames, same-origin webroot, world-executable
  modes, missing size limits, or no AV stage.
- Hardening asks for: random keys, separate file host, magic/MIME allowlist,
  ClamAV/cloud AV hooks, non-exec mounts, private buckets + app-mediated serve.
- **Not primary:** polyglots → `file-upload-polyglot-detection`; disposition/
  sniff XSS → `download-attribute-security`; unzip escape → `zip-slip-path-safety`;
  bucket public ACL only → cloud storage skills; classic `../` download without
  storage design → `path-traversal-lfi` / `file-access-vuln`.

## Workflow

### 1. Map the storage pipeline

1. Stages: client → edge body limit → app accept → **validate** → optional AV
   quarantine → durable store → transform → serve URL.
2. Record backend (FS path, object prefix, DB meta), who chooses the key, and
   whether bytes land under an executable/web-root tree.
3. Note write auth (session, signed policy) and read model (public vs gated).

### 2. Random names and path isolation

| Control | Why | Verify |
| --- | --- | --- |
| CSPRNG key / UUID | Stops guess and overwrite-by-name | Key ≠ user filename |
| Allowlisted extension only | Avoid `.php` / double-ext traps | Suffix is policy-driven |
| User name as display meta only | Path must not embed raw name | No `../` or absolute key segments |
| Prefix per tenant/app | Limits blast radius | Cross-tenant key access denied |

Never `join(uploadRoot, userFilename)` without sanitize + reject. Canonicalize
and keep the final path under the upload root.

### 3. Separate domain / cookie-less host

- Serve user content from a **distinct origin** without app session cookies, or
  use gated handlers that never execute HTML/SVG on the app cookie domain.
- Object storage: private by default; short-lived signed GET; public-read only
  when product requires and isolation holds.
- Hand **serve headers**, disposition, and sniffing to `download-attribute-security`.

### 4. Content-type validation (storage gate)

1. **Ignore client `Content-Type` for security** — server magic (libmagic or
   equivalent) **and** extension allowlist must both agree.
2. Reject decode failures / trailing garbage for strict codecs.
3. Persist server-detected MIME; serve that fixed type later with `nosniff`.
4. Prefer image re-encode; allow SVG only with sanitization or separate-origin preview.

### 5. Size limits and quotas

| Layer | Typical control |
| --- | --- |
| Edge / proxy | `client_max_body_size` / LB max body |
| App | Max bytes before full buffer |
| Presigned policy | `content-length-range` |
| Account | Per-user/day quota and file count |
| Worker | Max decompress / pixel dimensions |

Fail closed; log rejections without storing full hostile bodies. Size limits
are not authorization substitutes.

### 6. Antivirus hooks

1. Quarantine prefix → AV scan → promote to live or reject/delete.
2. Never expose quarantine URLs; never execute scanned content.
3. On hit/error: block publish; alert ops; retain only per policy.
4. AV is defense-in-depth — still require type allowlist, noexec, isolation.
   Dual-parse → `file-upload-polyglot-detection`.

### 7. No execute permissions

- **Disk:** `noexec` mount when possible; modes `0640`/`0600`; not under CGI/PHP
  or static script roots.
- **Object storage:** no public website hosting of upload prefix; least-privilege
  put/get roles; no shell-out on raw user paths.
- If product **extracts** archives after store → `zip-slip-path-safety` first.

### 8. Remediation bar (with `code-quality-standards`)

Shared helpers: generate key, validate magic+ext, enforce size, enqueue AV,
write with safe perms/ACL, return opaque id. Unit-test path-like names, oversize,
MIME mismatch, and “canary HTML must not be executable on app origin.”

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Secure storage: random keys, separate domain, type/size/AV, noexec | **This skill** | — |
| Offensive upload matrix | `upload-insecure-files` | this for storage fix |
| Polyglot dual-parse | `file-upload-polyglot-detection` | this for isolation |
| Disposition / `download` / sniff serve XSS | `download-attribute-security` | **serve handoff** |
| Zip/tar extract path escape | `zip-slip-path-safety` | **unpack handoff** |
| File IDOR on object ids | `idor-broken-object-authorization` | this for key opacity |
| S3/GCS/Blob public ACL / IAM | matching cloud storage skill | this for app keys |
| Implementing validators/tests | `code-quality-standards` | **always** on code |

**Handoff:** storage/key/ACL/noexec/AV/size → **this skill**. Browser delivery →
`download-attribute-security`. Archive entry paths → `zip-slip-path-safety`.

## Output Checklist

- [ ] Scope/authorization; canary keys; size/count caps
- [ ] Pipeline: accept → validate → AV/quarantine → store → serve
- [ ] Keys random/opaque; user filename not in path
- [ ] Cookie-less origin or gated non-exec serve
- [ ] Magic + extension allowlist; client Content-Type untrusted
- [ ] Edge/app/presigned size limits and quotas
- [ ] AV: quarantine → scan → promote/reject; no public quarantine
- [ ] FS noexec / private ACL / non-webroot path
- [ ] Serve → `download-attribute-security`; extract → `zip-slip-path-safety`
- [ ] Attack residuals → `upload-insecure-files`; code via CQS
- [ ] Redacted URLs/policies; test objects cleaned

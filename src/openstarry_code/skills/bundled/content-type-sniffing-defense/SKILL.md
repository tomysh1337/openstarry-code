---
name: content-type-sniffing-defense
description: >
  Defend against MIME / content-type sniffing: enforce X-Content-Type-Options
  nosniff, accurate Content-Type, safe user-upload serve paths, and polyglot
  body risks that browsers re-interpret as HTML/script. Use when hardening or
  auditing response headers for user content, static hosts, CDN file origins,
  missing nosniff, wrong MIME on uploads, or MIME-confusion XSS on owned apps
  and authorized assessments.
---

# Content-Type Sniffing Defense

Stop browsers from **reinterpreting** responses as HTML, script, or media other
than the declared type. Owns **MIME correctness + nosniff + serve-time policy**.
Storage keys/AV → `file-upload-secure-storage`. Disposition / `download` →
`download-attribute-security`. Script execution impact → `xss-cross-site-scripting`.

## Scope And Authorization

- **In scope:** Owned apps, labs, CTFs, written-scope review of response headers,
  user-file hosts, CDN/object GET, exports, previews that may sniff or mislabel.
- **Out of scope:** Drive-by malware, phishing, or third-party origins without
  authorization.
- Prefer canary bodies (`MIME-SNIFF-CANARY-<uuid>`) and lab browser profiles.
  Prove sniff/execute with markers only. Keep originals immutable; store captures
  under derived paths. Redact cookies, signed URLs, tokens, PII. Do not infer
  authorization from sandbox-looking UIs.

## When To Use

- Missing `X-Content-Type-Options: nosniff` (site-wide or on user-content hosts).
- Served `Content-Type` is wrong, generic (`text/plain`, `application/octet-stream`),
  client-supplied, or disagrees with magic/extension.
- User uploads (HTML, SVG, XML, PDF, images) re-served **inline** on the app
  cookie origin without isolation.
- Polyglot/dual-parse files may be treated as HTML/JS when type/nosniff is weak.
- Hardening: global nosniff, fixed server MIME map, attachment defaults, separate
  file origin, tests that canary HTML never runs on the app origin.

**Not primary:** storage/AV/noexec → `file-upload-secure-storage`; disposition /
HTML `download` → `download-attribute-security`; full XSS sink mapping →
`xss-cross-site-scripting`; zip extract → `zip-slip-path-safety`; edge-only
header inventory → `nginx-security-headers` (use this for MIME/sniff depth).

## Workflow

### 1. Inventory sniff-sensitive surfaces

1. Map static assets, user-file GET, thumbnails, exports, CDN mirrors, error pages
   that echo attacker-influenced bodies.
2. Per surface: status, `Content-Type`, charset, `X-Content-Type-Options`,
   `Content-Disposition`, origin (cookie vs cookie-less), who chose type/bytes.
3. Note frameworks that pass through client MIME or guess from extension only.

### 2. Enforce nosniff

| Control | Expectation | Failure |
| --- | --- | --- |
| `X-Content-Type-Options: nosniff` | All responses with user/untrusted bytes; prefer site-wide | Browser may ignore declared type → HTML/JS |
| Edge + app consistency | CDN/proxy must not strip the header | Origin sets it; edge drops it |
| Error / 404 bodies | Same policy as success | Sniffable reflected error HTML |

Verify with HTML-shaped body under wrong type (e.g. `image/png` / `text/plain`);
confirm no script execute when nosniff is set. Record browser/version.

### 3. Correct, server-owned Content-Type

1. **Never trust client `Content-Type` for security.** Persist server magic **and**
   allowlisted extension at accept; serve that fixed type later.
2. Prefer explicit types (`image/png`, `application/pdf`) over vague
   `application/octet-stream` when product needs correct handling — still send nosniff.
3. Set known `charset` on text types you control; block attacker-chosen charset tricks.
4. Treat `image/svg+xml` as active content; sanitize + isolate or force attachment.

### 4. User-upload serving policy

| Policy | Purpose |
| --- | --- |
| Cookie-less / separate origin | User HTML/SVG cannot read app session |
| Default `Content-Disposition: attachment` | Reduce inline open for untrusted types |
| Allowlist inline types only | Re-encoded images etc.; never raw HTML/JS on app origin |
| nosniff always | Block MIME confusion even if type is wrong once |
| Authz on every object id | Sniff defenses do not fix IDOR |

Storage keys, private buckets, AV, noexec → `file-upload-secure-storage`.
Filename injection / `<a download>` → `download-attribute-security`.

### 5. Polyglot and dual-parse risks

1. Multi-format bodies (image+HTML, PDF gadgets) may bypass naïve extension checks.
2. Defense-in-depth: magic+ext at store; **fixed serve type + nosniff**; separate
   origin; re-encode images; no inline SVG on app origin.
3. Deep ingest dual-parse → `file-upload-polyglot-detection`. This skill covers
   **serve-time** sniff outcomes when polyglot bytes reach the browser.

### 6. Prove impact and remediate

1. Lab-only: serve canary HTML/SVG under mislabeled type; check execute vs download
   vs blocked with/without nosniff on target origin.
2. Script in victim session → MIME-confusion XSS; hand exploit depth to
   `xss-cross-site-scripting`; keep header/MIME fixes here.
3. With `code-quality-standards`: always set nosniff; Content-Type from server map
   only; untrusted default `attachment`; isolate user-content host; test missing
   nosniff, wrong MIME, and “canary HTML must not run on app origin.”

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| nosniff, correct MIME, sniff XSS, upload serve policy | **This skill** | — |
| Upload keys, domain isolation store, AV, noexec | `file-upload-secure-storage` | this for serve headers |
| `download` attr, Content-Disposition, filename | `download-attribute-security` | this for type/nosniff |
| XSS sinks beyond MIME vector | `xss-cross-site-scripting` | this for sniff root cause |
| Polyglot dual-parse at ingest | `file-upload-polyglot-detection` | this when serve fails |
| nginx/edge header inventory only | `nginx-security-headers` | this for MIME policy |
| File IDOR on download URLs | `idor-broken-object-authorization` | this for type headers |
| Implementing middleware/tests | `code-quality-standards` | **always** on code |

**Handoff:** storage → `file-upload-secure-storage`. Disposition/download UX →
`download-attribute-security`. Execution impact → `xss-cross-site-scripting`.
Keep this skill for **declared type, nosniff, and browser reinterpretation**.

## Output Checklist

- [ ] Scope/authorization; canary-only proofs; browser versions
- [ ] Surfaces mapped (user files, static, CDN, exports, errors)
- [ ] Per surface: Content-Type, charset, nosniff, disposition, origin
- [ ] Client MIME untrusted; server map / magic documented
- [ ] nosniff present and not stripped at edge
- [ ] Inline vs attachment policy for untrusted types
- [ ] Polyglot/serve interaction noted or handed to polyglot skill
- [ ] Storage → `file-upload-secure-storage`; disposition → `download-attribute-security`
- [ ] XSS impact → `xss-cross-site-scripting` when execution proven
- [ ] Remediation + retest; CQS if code changed
- [ ] Redacted headers, URLs, artifact paths

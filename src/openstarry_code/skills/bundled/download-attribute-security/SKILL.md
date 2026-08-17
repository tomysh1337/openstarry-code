---
name: download-attribute-security
description: >
  Assess and harden HTML download attribute usage, Content-Disposition filenames,
  content-type sniffing on file responses, and XSS or path risks via user-facing
  downloads. Use when reviewing <a download>, attachment/inline disposition,
  filename injection, user-content CDN/download endpoints, or sandboxing served
  files under authorized application security work.
---

# Download Attribute And File-Serve Security

Secure **how browsers and clients save or open** files: HTML `download`,
`Content-Disposition`, served `Content-Type`, sniffing, and isolation of
user-supplied content. Upload validation belongs to upload skills; this skill
owns **serve / download / disposition** surfaces.

## Scope And Authorization

- **In scope:** Owned apps, labs, CTFs, and written-scope assessments of download
  links, export endpoints, object-storage signed URLs, and user-file viewers.
- **Out of scope:** Malware distribution, third-party drive-by downloads, or
  phishing attachments outside authorized targets.
- Prefer canary names/bodies (`DL-CANARY-<uuid>`). Prove impact with markers,
  forced save-as, or isolated lab browser profiles — not weaponized scripts.
- Keep original responses immutable; store captures under derived paths. Redact
  cookies, signed URLs, tokens, and PII. Do not infer authorization from sandbox-looking UIs.

## When To Use

- Markup uses `<a download>` / `download="name"` (same- or cross-origin, blob/data URLs).
- APIs or static hosts set `Content-Disposition: attachment|inline` with
  attacker-influenced **filename** or body.
- User content is re-served with weak `Content-Type`, missing `nosniff`, or on
  the app’s cookie origin.
- Topics: download-attribute abuse, filename header injection, content sniffing,
  XSS via download/open-as-HTML, path-like filenames, file-host sandbox gaps.
- Hardening: safe disposition builders, separate file origin, CSP/sandbox previews.

**Not primary:** upload allowlist/ACL → `upload-insecure-files`; polyglot ingest →
`file-upload-polyglot-detection`; non-file XSS → `xss-cross-site-scripting`;
archive extract escape → `zip-slip-path-safety`; CSV formulas → `csv-formula-injection`.

## Workflow

### 1. Inventory download surfaces

1. UI: `<a href download>`, fetch→blob→`createObjectURL`, “Save as,” signed CDN links.
2. Server: `/download`, `/files/:id`, `/export`, thumbnail vs original streams.
3. Per surface: who controls **name** and **bytes**, same- vs cross-origin, auth
   (cookie vs signed query), intended mode (force download vs preview).

### 2. HTML `download` attribute

| Check | Risk if weak | Verify |
| --- | --- | --- |
| Cross-origin `download` | Often ignored → navigate/open instead of save | Behavior matches security expectation |
| Filename override | Trusted-looking name over hostile `href`/blob | User-controlled `download` sanitized |
| Data/blob HTML | Open executes; save may not | No auto-open of untrusted HTML |
| Path/RTL/double ext | Misleading or path-like saved names | Basename + safe charset only |

Treat client `download` as **UX only**. Direct fetches must still have correct
server headers.

### 3. Content-Disposition and filename injection

1. Capture full header (`inline` vs `attachment`; `filename` / `filename*`).
2. If filename is user-influenced: try CR/LF, quotes, `;`, `../`, `..\`, NUL,
   long UTF-8. Watch for **header injection/response splitting** and quote breakouts.
3. Server-chosen safe basename only; strip path components; allowlist
   `[A-Za-z0-9._-]` (or equivalent); use RFC 5987 `filename*` when encoding needed.
4. Prefer **`attachment`** for untrusted types; `inline` only with isolation (step 5).

### 4. Content-Type, sniffing, XSS via downloads

1. Compare served `Content-Type` vs magic vs extension; require
   `X-Content-Type-Options: nosniff` on user content.
2. User HTML/SVG/XML/JS as `text/html` or `image/svg+xml` (or sniffed HTML) **on
   the app cookie origin** → stored XSS; prove with a lab canary, not real-user theft.
3. `application/octet-stream` without nosniff/attachment may still open/sniff on
   some clients — note browser/version.
4. After proving **serve** impact, hand weak **upload** root cause to upload skills.

### 5. Sandbox user files

| Control | Purpose |
| --- | --- |
| Cookie-less / separate origin | User HTML cannot read app session |
| CSP on file host | Constrain scripts if HTML preview exists |
| Sandboxed iframe viewer | Preview without full-page privileges |
| Forced `attachment` + nosniff | Reduce in-browser execute |
| Authz on every file id | Block IDOR downloads |

Do not rely on the `download` attribute alone to make files safe.

### 6. Remediation bar

With `code-quality-standards`: disposition from sanitized basename only; fixed
allowlisted `Content-Type` + always `nosniff`; default `attachment` for untrusted
blobs; isolate previews; ignore client Content-Type for security; unit-test
header injection, path-like names, and “canary HTML must not run on app origin.”

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| `download` attr, disposition, sniffing, file-host sandbox | **This skill** | — |
| Upload MIME/extension/path/exec | `upload-insecure-files` | this for serve side |
| Polyglot dual-parse at ingest | `file-upload-polyglot-detection` | this when serve headers fail |
| HTML/JS execution in victim session | `xss-cross-site-scripting` | this for download vector |
| File IDOR | `idor-broken-object-authorization` | this for disposition |
| Archive extract after download | `zip-slip-path-safety` | — |
| CSV formula on open in Excel | `csv-formula-injection` | — |
| CSP review on file/app origin | `content-security-policy-bypass` | this for isolation design |
| Implementing headers/sanitizers/tests | `code-quality-standards` | **always** on code changes |

**Handoff:** upload allowlists/storage → `upload-insecure-files` (+ polyglot when
dual-parse). Keep this skill for **delivery headers, download UX, and browser
interpretation** of served files.

## Output Checklist

- [ ] Scope/authorization; canary-only proofs
- [ ] Surfaces mapped (`download`, export APIs, CDN/signed URLs)
- [ ] Per surface: origin, auth, who controls name/bytes
- [ ] Disposition/filename sanitization evidence or injection proof
- [ ] `Content-Type` + `nosniff` + inline vs attachment documented
- [ ] Sniffing/XSS-via-file: browser, origin, canary result
- [ ] Isolation: separate origin / sandbox preview / gap noted
- [ ] Upload issues handed to `upload-insecure-files` / polyglot skill
- [ ] Remediation + retest; CQS if code changed
- [ ] Redacted headers, URLs, artifact paths

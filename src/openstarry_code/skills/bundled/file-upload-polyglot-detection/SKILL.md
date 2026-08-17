---
name: file-upload-polyglot-detection
description: >
  Authorized methodology to detect and mitigate polyglot file uploads — one
  byte stream valid as multiple formats (image+HTML/JS, PDF+ZIP, SVG/XML dual
  parse, Office ZIP+XML). Use when assessing dual interpretation, stored XSS
  via polyglots, or building magic/multi-parser detection and re-encode
  defenses. Not for distributing malware polyglots.
---

# File Upload Polyglot Detection (Authorized)

Find, prove, and detect **polyglot uploads**: accepted as a safe type yet
interpreted differently by another parser, browser, or converter. General
upload controls → `upload-insecure-files`; this skill deepens dual-parse paths.

## Scope And Authorization

- Owned apps, labs, CTFs, written-scope upload/preview/convert/CDN assessments.
- No real malware polyglots, third-party attacks, ZIP bombs, or quota DoS.
- Prefer minimal lab polyglots with unique canaries (`POLYGLOT-CANARY-<uuid>`).
- Cap size/count; clean up test objects; redact signed URLs and credentials.
- Authorization is not implied by sandbox-looking UIs.

## Use When

- Focus is polyglot, dual MIME/magic, image+script, PDF/ZIP chimera, or
  “valid image that is also HTML/XML.”
- Server or browser re-parses uploads (thumbnailer, Office convert, SVG
  sanitizer, PDF renderer, archive extract) after a type check.
- Building detection (magic vs claim, multi-parser agree) or re-encode barriers.

## When To Use

- Avatar, CMS media, chat files, document import, or inline preview features.
- Upload matrix shows magic/extension mismatch or multiple processors per object.
- Suspected XSS via SVG/HTML-in-image, XXE via Office/SVG, or zip slip after
  “document” accept — hand off class skills after polyglot confirmed.
- **Not primary:** extension-only bypass without dual parse; pure download
  traversal (`path-traversal-lfi`); archive path escape alone (`zip-slip-path-safety`).

## Workflow

### 1. Map consumers

List every reader after upload: validation (extension/magic/client MIME),
storage ACL, transforms (resize, AV, Office→PDF, unpack), serve headers
(inline vs attachment, nosniff, origin), downstream (browser, WebView, mail).
Polyglots matter only where **two+** interpreters disagree.

| Class | Secondary risk |
| --- | --- |
| Image + HTML/JS | Stored XSS if inline / sniffed |
| SVG dual-parse | XSS, SSRF, XXE |
| PDF/image + ZIP | Nested payload, zip slip |
| OOXML (ZIP+XML) | XXE / SSRF |
| Client MIME lie | Wrong handler selection |

**Good proof:** same bytes pass as allowed type **and** secondary consumer
executes/renders/extracts/expands with canary. **Bad proof:** HTTP 200 only.

### 2. Baseline matrix

Upload clean allowed type and disallowed HTML/JS/XML. Record extension, declared
MIME, magic, status, stored key, served `Content-Type` / `Content-Disposition`.

### 3. Detection signals

1. **Magic vs claim:** libmagic vs Content-Type vs extension — flag mismatch.
2. **Strict decode:** claimed codec must fully decode; trailing garbage → quarantine.
3. **Container walk:** PDF/OOXML/ZIP — flag unexpected HTML/JS/XML/active streams.
4. **SVG/XML:** hardened parse (`xxe-billion-laughs-defenses` /
   `xxe-xml-external-entity`); strip script/`foreignObject`/external refs — or block SVG.
5. **Serve alerts:** user content as `text/html` or `image/svg+xml` inline on
   cookie origin; raw re-serve when policy required re-encode.

### 4. Authorized probes (one variable; embed canary)

1. Allowed magic + HTML trailer where sniff/execute is plausible.
2. Valid image + trailing ZIP — any worker unzip?
3. PDF header + ZIP structure — converters/extractors.
4. SVG with script or lab-OAST entity; browser vs server renderer.
5. OOXML: patch `document.xml`, rezip — entity/SSRF → XXE skills.
6. MIME spoof: correct magic / wrong Content-Type, and reverse.

Record **which consumer** triggered secondary behavior. Severity follows
interpreter + origin/cookie context, not polyglot novelty.

### 5. Impact handoff and remediation

| Observation | Route |
| --- | --- |
| HTML/JS in victim session | `xss-cross-site-scripting` |
| DTD / entity / XInclude | `xxe-xml-external-entity` (+ defenses skill) |
| Archive entry escapes root | `zip-slip-path-safety` |
| Server fetch from file content | `ssrf-server-side-request-forgery` |
| Type/storage gaps only | `upload-insecure-files` |

Remediate with `code-quality-standards`: allowlist extension **and** server
magic; ignore client Content-Type for security; re-encode images; reject decode
failure; non-exec storage + random keys; fixed Content-Type + `nosniff` +
`attachment` when preview unused; **separate origin** for user content; block
or strict-sanitize SVG; treat Office as untrusted ZIP+XML; no naive extract.
AV alone is not a polyglot detector.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Polyglot dual-parse detect/proof | **This skill** | — |
| Full upload allowlist/path/ACL/exec | `upload-insecure-files` | this skill for dual-format depth |
| XXE via SVG/Office XML side | `xxe-xml-external-entity` | this skill for upload stage |
| Parser hardening / entity bombs | `xxe-billion-laughs-defenses` | after polyglot feeds XML |
| Stored XSS impact | `xss-cross-site-scripting` | after serve/execute proven |
| Detection/re-encode implementation | `code-quality-standards` | **always** when coding controls |

**Required routes:** `upload-insecure-files` (end-to-end upload methodology);
`xxe-xml-external-entity` (secondary interpreter is XML); `code-quality-standards`
(validators, serve headers, re-encode tests).

## Checklist

- [ ] Scope confirmed; canary-only polyglots; size/count caps
- [ ] Consumers mapped; allowed/denied baselines; magic vs MIME vs extension matrix
- [ ] Dual-interpretation canary proof; served headers/origin documented
- [ ] Impact handed to XSS / XXE / zip-slip / SSRF as needed
- [ ] Detection: multi-signal agree + quarantine; re-encode / separate origin / non-exec storage
- [ ] Residual gaps via `upload-insecure-files`; implementation via `code-quality-standards`
- [ ] Artifacts cleaned; secrets/URLs redacted

## Rules

- Authorized only; no real malware polyglots. Prove **two interpreters**, not upload 200 alone.
- One variable per trial; minimal canaries; no converter/bucket DoS; no client-only trust.
---

# Note

Owns polyglot dual-interpretation. Pair with `upload-insecure-files`,
`xxe-xml-external-entity` / `xxe-billion-laughs-defenses` (XML secondary), and
`code-quality-standards` for detection/re-encode implementation.

---
name: svg-xss-hardening
description: >
  Harden SVG handling against XSS and related active-content risks: script,
  event handlers, foreignObject, animation/set attributes, javascript:/data:
  URLs, external resource loads, and unsafe serve headers. Use when apps
  accept, sanitize, inline, or serve user-controlled SVG (uploads, avatars,
  icons, CMS media, data URLs, or DOM insertion of SVG markup).
---

# SVG XSS Hardening

Reduce XSS impact from **SVG as active XML/HTML hybrid content**. General
markup XSS → `xss-cross-site-scripting`. Upload pipeline → `upload-insecure-files`.
Implementation → `code-quality-standards`.

## When To Use

- Features accept `.svg` / `image/svg+xml`, paste SVG markup, or render icons
  from untrusted XML (avatar, sticker, CMS media, email HTML, design import).
- SVG is **inlined** into HTML, or embedded via `<img>`, `<object>`, `<embed>`,
  `<iframe>`, CSS `url()`, or `data:` URLs.
- Sanitizer or “image-only” policy allows SVG; retest after suspected stored XSS.
- Browser vs server rasterizer differ (thumbnailer safe, browser unsafe).
- **Not primary:** generic HTML XSS without SVG; non-SVG XXE; full upload matrix
  without SVG focus (`upload-insecure-files`).

Authorized apps/labs/CTFs only. Prefer canaries (`svgXssC4nary-<id>`); no real-user
weaponization; cap size/count; clean up artifacts; redact signed URLs and PII.

## Workflow

### 1. Map every SVG surface

1. **Ingress:** multipart, base64 JSON, paste editor, URL-fetch-to-store, import.
2. **Transforms:** client strip, server sanitizer (name/version), AV, rasterize, CDN.
3. **Egress:** same-origin vs CDN; `Content-Type`; `Content-Disposition`; `nosniff`; CSP.
4. **Client sinks:** `innerHTML` / raw HTML, SVG-as-component, `<img>`, CSS, WebView.

Chain: source → stored bytes → serve headers/origin → browser context.

### 2. Threat model by embedding mode

| Mode | Script/event impact | Notes |
| --- | --- | --- |
| Inline SVG in HTML | High | Same origin as page |
| `<object>` / `<embed>` / `<iframe>` | High if same site | Cookie scope matters |
| `<img>` / CSS image | Lower classic script | Still external loads; treat untrusted |
| Server raster → PNG/WebP only | Low XSS | Ensure raw SVG not still public inline |
| `attachment` + `nosniff` | Lower drive-by | Unsafe if later inlined elsewhere |

Severity follows **execution context and cookie origin**, not “SVG exists.”

### 3. Active-content probes (authorized)

One class per trial; unique canary. Prove **execution or forbidden network load**,
not upload HTTP 200 alone.

1. **Script:** `<script>`, CDATA, namespaced variants.
2. **Handlers:** `onload` / `onerror` / `onclick` / `onfocus` on `<svg>`, `<image>`,
   `<use>`, shapes; encoding tricks only if filters look weak.
3. **SMIL:** `<animate>`, `<set>`, begin/onbegin-style handlers under test sanitizer.
4. **`foreignObject`:** nested HTML (`iframe`, `script`, forms).
5. **URL schemes:** `javascript:`, `data:text/html` in `href` / `xlink:href` / `src`.
6. **External refs:** `<use href="https://…">`, `<image href>`, CSS `url()`/`@import`.
7. **DTD/entity/XInclude** on server parse → XXE skills.
8. **mXSS:** active after sanitize + browser reparse; retest after library upgrades.

### 4. Defense design (layered)

Document which layer failed:

1. **Policy:** block SVG if unused; else restrict roles/paths.
2. **Prefer raster:** hardened decode → PNG/WebP for display; avoid re-serving raw
   uploader bytes on a cookie origin.
3. **Sanitize (if raw required):** maintained allowlist library; strip script,
   handlers, `foreignObject`, scripted animation, dangerous URLs, external refs,
   DTD/entities; fail closed on parse error; keep patched.
4. **Store:** random keys; non-executable storage; no user path segments.
5. **Serve:** fixed type; `X-Content-Type-Options: nosniff`; `attachment` when
   preview unused; **separate origin** for user content.
6. **CSP on viewers:** tight `script-src` / `object-src` / `img-src` — not a
   substitute for sanitization when SVG is inlined.
7. **Client:** never `innerHTML` untrusted SVG without server-grade allowlist.

### 5. Verification

1. Retest PoC + alternate vector (e.g. `foreignObject` if `<script>` blocked).
2. Cover thumbnail/CDN and direct object URLs.
3. Add corpus fixtures (strip/reject) via `code-quality-standards`.
4. Upload MIME/extension/path gaps → `upload-insecure-files`. Session XSS framing
   beyond SVG → `xss-cross-site-scripting`.

## Routing

| Need | Skill |
| --- | --- |
| SVG accept/sanitize/serve/inline hardening | **svg-xss-hardening** (this) |
| Prove stored/reflected/DOM XSS and general sinks | `xss-cross-site-scripting` |
| Upload MIME/extension/path/ACL/serve pipeline | `upload-insecure-files` |
| Sanitizer, headers, re-encode, tests | `code-quality-standards` |
| Server entity/DTD from SVG XML | `xxe-xml-external-entity` |
| Image+SVG polyglot dual-parse | `file-upload-polyglot-detection` |
| CSP after an SVG execution path | `content-security-policy-bypass` |

**Required handoffs:** `xss-cross-site-scripting` for general XSS proof/severity;
`upload-insecure-files` for upload/storage pipeline gaps; `code-quality-standards`
when implementing or reviewing sanitizer, serve headers, or re-encode controls.

## Output Checklist

- [ ] SVG surfaces mapped (ingress, transform, serve, client sink)
- [ ] Embedding mode and origin/cookie impact stated
- [ ] Active-content classes tested (script, handlers, foreignObject, URLs, external)
- [ ] Minimal canary PoC or explicit “no execution under current controls”
- [ ] Served Content-Type, disposition, nosniff, origin documented
- [ ] Sanitizer / rasterize / block decision (library/version if any)
- [ ] Handoffs: XSS, upload, code-quality (XXE if parser fetches)
- [ ] Remediation + retest; fixtures recommended
- [ ] Artifacts cleaned; secrets/URLs redacted

## Rules

- Authorized only; canary proofs over session-theft demos.
- Do not call SVG “safe” because `<img>` blocked script once — cover inline,
  object/embed, and direct URL paths.
- Upload 200 without a dangerous consumer is not a finding; link a sink.
- Prefer block or rasterize over complex sanitizers when product allows.
- Fail closed on parse/sanitize errors; never trust client-only SVG filters.

---
name: html-sanitizer-selection
description: >
  Choose and configure HTML sanitizers (DOMPurify, bleach/nh3, sanitize-html,
  OWASP Java HTML Sanitizer) for untrusted markup: allowlists vs strip-all,
  SVG/MathML policy, HTML vs attribute vs URL context, and CSP as defense in
  depth. Use when picking or reviewing a rich-text/HTML sanitizer library,
  hardening innerHTML / |safe / dangerouslySetInnerHTML sinks, or deciding
  whether plain-text encoding is enough in owned or authorized applications.
---

# HTML Sanitizer Selection

Pick the **right sanitizer and policy** when product code accepts or emits HTML
from untrusted authors. Prefer **fail-closed allowlists**, context-correct sinks,
and **CSP** — not regex strip of `<script>`. Defensive / authorized work only.
XSS → `xss-cross-site-scripting`; Markdown → `markdown-xss-sanitization`;
non-HTML encoding → `output-encoding-patterns`.

## Scope And Authorization

- Owned apps, staging, labs, and **explicitly authorized** assessments only.
- No sanitizer-bypass testing against third-party production users; redact PII/tokens.
- Prefer non-destructive fixtures. Client-only sanitize is **not** enough for
  multi-user HTML — sanitize server-side before store or first cross-user render.

## When To Use

- Choosing **DOMPurify**, **bleach** / **nh3**, **sanitize-html**, **OWASP Java
  HTML Sanitizer**, or stack-native equivalents for rich text / CMS / comments.
- Reviewing `dangerouslySetInnerHTML`, `v-html`, `|safe`, `innerHTML`, email HTML,
  or admin HTML-preview paths that need a library + policy.
- Deciding **strip-all / plain text** vs **tight allowlist** vs elevated
  trusted-author profiles (SVG, MathML, tables, embeds).
- Fixing mXSS or misconfigured allowlists after upgrades; pairing policy with CSP.

Do **not** use as primary for general XSS methodology (`xss-cross-site-scripting`),
Markdown-first pipelines (`markdown-xss-sanitization`), or non-HTML encoding
(`output-encoding-patterns`).

## Workflow

### 1. Decide if HTML is required

| Need | Control |
| --- | --- |
| Names, titles, plain comments | **No sanitizer** — text encode / auto-escape |
| Bold / lists / links | Sanitizer with **tight allowlist** |
| Full CMS / design HTML | Elevated allowlist + review + CSP; staff/sandbox |
| Untrusted HTML files | Strip, attachment, or sandboxed iframe |

**Good:** store plain text; render with framework escape.  
**Bad:** store raw HTML then blacklist-strip `<script>` later.

### 2. Map source → sanitizer → sink → context

1. Who authors HTML and who views it; multi-user vs self-only.
2. Where sanitize runs: server (preferred multi-user), edge, or browser-only (depth).
3. Sanitizers produce **HTML body** fragments — not a substitute for other contexts:

| Context | Sanitizer role | Still required |
| --- | --- | --- |
| HTML body / fragment | Primary (allowlist) | CSP; no re-parse into JS |
| Attribute value | Do not put full HTML in attrs | Attribute encode / DOM APIs |
| URL (`href`/`src`) | Scheme allowlist inside sanitizer | Deny `javascript:`, hostile `data:` |
| JS string / handlers | **Out of scope** | Never allow `on*`; no string→`eval` |
| CSS `style` | Prefer strip | Avoid user `style` by default |

### 3. Select library by runtime

| Stack | Choice | Notes |
| --- | --- | --- |
| Browser / Node | **DOMPurify** (+ `jsdom` on Node) | `ALLOWED_TAGS` / `ALLOWED_ATTR`; hooks for `rel` |
| Node middleware | **sanitize-html** | `allowedTags` / `allowedAttributes` / `allowedSchemes` |
| Python | **nh3** (prefer) or **bleach** | Explicit allowlists; careful linkify |
| Java / JVM | **OWASP Java HTML Sanitizer** | Policy builders; fail closed |
| Other stacks | Maintained platform sanitizer | One lib; avoid home-grown parsers |

Prefer the monorepo’s existing library. Pin versions; retest fixtures on upgrades.

### 4. Define policy (allowlist > strip-all > blacklist)

1. **Default deny:** minimal tags/attrs; prefer **strip-all** when rich HTML is unnecessary. **Never** blacklist-only (`remove <script>`).
2. **Attrs:** `href`, `title`, `alt`, maybe image `src`; strip `on*`, `style` (default), `srcdoc`, `formaction`, `xlink:href` unless reviewed.
3. **URLs:** allow `https:` (relative/`mailto:` if needed); **deny** `javascript:`, `vbscript:`, `file:`, most `data:` (esp. HTML/SVG). Force `rel="noopener noreferrer"` on anchors (+ `ugc`/`nofollow` per product).
4. **SVG / MathML:** off by default. Enable only with a dedicated tight policy and tests (`onload`, `foreignObject`, animate, `xlink:href`). Prefer raster or sandbox.

**Good:**

```ts
DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ["p", "br", "strong", "em", "ul", "ol", "li", "a", "code"],
  ALLOWED_ATTR: ["href", "title", "rel"],
  ALLOW_DATA_ATTR: false,
});
```

**Bad:** allow-everything profiles; regex `replace(/<script>/gi,"")`; sanitize then interpolate into a JS string without re-encoding.

### 5. Wire sinks, CSP, and verify

1. One path: sanitize → trusted fragment → single `innerHTML` / framework raw API.
2. Markdown: keep source; sanitize **parser output** (`markdown-xss-sanitization`).
3. **CSP** (nonces/hashes; tight `object-src`/`base-uri`) complements policy; high-risk previews use iframe `sandbox` without `allow-scripts` unless reviewed.
4. `code-quality-standards`: typed `SafeHtml`, fail-closed config, fixtures (`script`/`img onerror`/`svg`/`math`, hostile URL schemes, mXSS). Retest as victim under CSP after sanitizer upgrades.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Choose/configure HTML sanitizer + allowlist | **This skill** | — |
| Markdown → HTML XSS harden | `markdown-xss-sanitization` | this for post-parse HTML policy |
| Authorized XSS mapping / PoC methodology | `xss-cross-site-scripting` | this when fix is sanitizer selection |
| Context encoding without rich HTML | `output-encoding-patterns` | this if HTML subset required |
| CSP bypass research | `content-security-policy-bypass` | this for sanitize + CSP pair |
| Implementation types/tests | `code-quality-standards` | **always** on code changes |
| Ingress schema/length only | `input-validation-patterns` | this if output remains HTML |

## Output Checklist

- [ ] HTML required confirmed (else plain text + encode only)
- [ ] Author/viewer trust model and multi-user path documented
- [ ] Library chosen (DOMPurify / nh3|bleach / sanitize-html / OWASP Java / existing)
- [ ] Explicit tag+attr allowlist or strip-all; no blacklist-only
- [ ] SVG/MathML off or reviewed subset; schemes deny `javascript:`/`data:`
- [ ] Server-side sanitize for cross-user HTML; client is depth only
- [ ] HTML-body sink only; attr/JS/URL encoding separate; CSP + optional sandbox
- [ ] Fixtures + upgrade retest; `SafeHtml`/fail-closed in review
- [ ] Handoff: XSS → `xss-cross-site-scripting`; Markdown → `markdown-xss-sanitization`
- [ ] Authorized/owned scope; redacted samples

## Rules

- Allowlists and strip-all beat blacklist “remove script” filters.
- Sanitizers clean **HTML fragments**; they do not fix wrong-context encoding.
- SVG/MathML and `style` default off for untrusted authors; pin one maintained library and retest on upgrades. CSP complements, not replaces. Authorized only.

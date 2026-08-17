---
name: markdown-xss-sanitization
description: >
  Harden Markdown-to-HTML pipelines against XSS: safe renderers, post-parse
  HTML sanitization, link/image URL allowlists, and tests for raw HTML and
  attribute breakouts. Use when user or third-party Markdown is rendered to
  HTML (comments, wikis, READMEs, chat, docs previews, CMS), when reviewing
  marked/markdown-it/CommonMark/GFM configs, or when fixing stored XSS via
  Markdown sinks in owned or authorized applications.
---

# Markdown XSS Sanitization

Secure **Markdown → HTML** so untrusted source cannot become executable markup
or dangerous URLs. Prefer **disable raw HTML + post-render sanitizer + scheme
allowlists**. Defensive coding and authorized review only — not a full XSS
assessment playbook (`xss-cross-site-scripting`).

## When To Use

- Product renders **user, partner, or imported Markdown** to HTML (comments,
  issues, wikis, chat, help centers, email digests, PR previews, CMS).
- Auditing **marked, markdown-it, remark/rehype, Python-Markdown, Goldmark,
  cmark-gfm, Showdown, MDX** (raw HTML, linkify, breaks, embeds).
- Findings or fixes: stored XSS via Markdown, `javascript:` links, `data:`
  images, event-handler attributes after convert, or sanitizer misconfig.
- Implementing **DOMPurify / bleach / nh3 / sanitize-html / OWASP Java HTML
  Sanitizer** (or server equivalent) on Markdown output.
- Choosing plain-text Markdown (encode-only) vs rich Markdown (allowlisted tags).

Do **not** use as primary for general reflected/DOM XSS without a Markdown sink
(`xss-cross-site-scripting`), pure non-Markdown encoding
(`output-encoding-patterns`), or inbound schema-only work
(`input-validation-patterns`).

## Threat Model (Markdown-specific)

| Vector | Example | Risk |
| --- | --- | --- |
| Raw HTML in source | `<script>`, `<img onerror>`, `<svg onload>` | Direct XSS if HTML passthrough |
| Link schemes | `[x](javascript:…)` / `vbscript:` / hostile `data:` | Navigation / click XSS |
| Image / media URLs | `![](javascript:…)` or `data:text/html` | Sink-dependent execution |
| Title / alt / autolink | Attribute breakout if encoder wrong | Attribute XSS |
| mXSS / double render | Sanitize then re-parse or double `innerHTML` | Bypass of “clean” HTML |
| MDX / embeds | JSX, raw HTML blocks | Full HTML app surface |

## Workflow

### 1. Map the pipeline

1. Trace **source** (API, DB, git, import) → **parser** → HTML/AST →
   **sanitizer** → **sink** (`innerHTML`, template `|safe`, email HTML, WebView).
2. Record client vs server render, CSP, cache, and viewers (self vs others /
   admins). Prefer **server-side sanitize** before store or first multi-user
   view; client-only sanitize is defense-in-depth only.

### 2. Choose a safe default policy

| Mode | When | Controls |
| --- | --- | --- |
| **Text-ish** | No rich HTML needed | Escaped text or subset with no raw HTML |
| **Safe rich** | Bold/lists/code/links | No raw HTML; tag/attr allowlist; URL schemes |
| **Trusted author** | Audited staff only | Still sanitize; document elevated allowlist |

**Parser intent:** disable raw HTML blocks/inline and raw attribute passthrough;
allow tables/task lists only if HTML still hits the sanitizer. Never trust a
library “safe mode” label without an explicit allowlist and tests.

### 3. Sanitize HTML after Markdown

1. Sanitize **parser output**, not only raw Markdown, with a maintained library.
2. **Allowlist tags** (e.g. `p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `code`,
   `pre`, `blockquote`, `a`, `h1–h3`; optional `img`/`table`).
3. **Allowlist attrs:** `href`, `title`, `alt` as needed; strip `style`, `on*`,
   `srcdoc`, `formaction`, `xlink:href` unless required and reviewed.
4. **URL policy:** allow `https:` (and `http:`/`mailto:`/relative if needed);
   **deny** `javascript:`, `vbscript:`, `file:`, most `data:` (esp. HTML/SVG).
   Parse/normalize URLs — do not string-prefix check only.
5. User anchors: `rel="noopener noreferrer"` (+ `ugc`/`nofollow` per product).
6. Images: host allowlist or relative uploads; size caps at upload time.
7. Do **not** rely on regex strip of `<script>` or case-sensitive blacklists.

### 4. Encode and sink correctly

- One intentional HTML path after sanitize; CSP in depth. Use
  `output-encoding-patterns` for every non-HTML context.
- Keep source Markdown in the model; avoid HTML-entity-only DB forms if other
  channels need source.
- Ban `dangerouslySetInnerHTML` / `v-html` / `|safe` of **unsanitized** parser
  output. Never put sanitized HTML into JS strings or unquoted attributes
  without re-encoding for that context.

### 5. Test, verify, and depth controls

1. Unit fixtures (neutralized): raw `<script>`/`<img onerror>`;
   `[x](javascript:…)` case variants; hostile images/`data:` if images on;
   nested tags; SVG/MathML if not allowlisted; autolink dangerous schemes.
2. Integration: render as **victim role** under real app CSP.
3. Regression on parser/sanitizer upgrades (mXSS).
4. Implement with `code-quality-standards`: typed sanitize boundary, fail-closed
   config, tests, no silent empty-allowlist misconfig.
5. Depth: CSP nonces/hashes; HttpOnly cookies; sandboxed iframe for high-risk
   previews; input/output size caps; admin review of untrusted imports.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Markdown→HTML XSS harden, MD sanitizer allowlists | **This skill** | — |
| Authorized XSS mapping / general PoC methodology | `xss-cross-site-scripting` | this when sink is Markdown |
| Context encoding for non-Markdown HTML/attr/JS/URL | `output-encoding-patterns` | this for MD pipeline |
| Implementing parsers, sanitizers, tests | `code-quality-standards` | **always** on code changes |
| Inbound length/schema only | `input-validation-patterns` | this if output is still HTML |
| CSP bypass research | `content-security-policy-bypass` | this for app Markdown fix |
| Injection class unknown | `injection-checking` | XSS / this after MD sink found |

**This skill** owns Markdown render policy. Route assessment depth to
`xss-cross-site-scripting`, non-MD sinks to `output-encoding-patterns`,
implementation/review through `code-quality-standards`.

## Output Checklist

- [ ] Pipeline mapped: source → parser → sanitizer → sink → viewers
- [ ] Raw HTML disabled or neutralized by policy
- [ ] Post-render sanitizer with explicit tag/attr allowlist
- [ ] Link/media URL scheme (and host) allowlists tested
- [ ] Anchor `rel` / image policy; not client-only sanitize for multi-user
- [ ] Fixtures: script/img/svg, `javascript:` links, case/encoding variants
- [ ] Browser retest under CSP; mXSS considered on upgrades
- [ ] `output-encoding-patterns` for non-HTML contexts
- [ ] `xss-cross-site-scripting` if assessment proof beyond harden is required
- [ ] `code-quality-standards`: typed boundary, tests, fail-closed sanitizer
- [ ] Redacted samples; authorized scope only

## Rules

- Untrusted Markdown is hostile until tight parse policy + sanitization.
- Allowlists beat blacklist “strip script” filters; disable raw HTML by default.
- Test schemes and attributes, not only `<script>` tags.
- Repo parser/sanitizer choices win; this skill supplies policy and review bar.
- Defensive/authorized work only — no weaponized stored XSS on real third parties.

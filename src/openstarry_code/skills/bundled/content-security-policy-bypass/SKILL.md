---
name: content-security-policy-bypass
description: >
  Authorized Content-Security-Policy (CSP) review and bypass research: parse
  policy directives, assess nonce/hash/'strict-dynamic' posture, source
  expressions, and XSS impact under CSP. Use when responses or meta tags set
  CSP, inline script is blocked, or a confirmed XSS still needs a realistic
  execution path under the deployed policy.
---

# Content-Security-Policy Bypass (Authorized Research)

## When To Use

- Responses or `<meta http-equiv="Content-Security-Policy">` set a CSP (or report-only twin).
- XSS/HTML injection exists but DevTools console shows CSP violations; need impact under the live policy.
- Hardening review: nonces, hashes, `'strict-dynamic'`, allowlists, and missing companion directives.
- Bug bounty / lab / CTF tasks explicitly covering CSP, script gadgets, or “XSS with CSP.”
- Not primary for pure framing (`frame-ancestors` clickjack) — use `clickjacking`; not primary for CORS — use `cors-cross-origin-misconfiguration`. Combine when CSP and cross-origin issues share a page.

## Scope And Authorization

- Authorized apps, staging, labs, CTFs, and explicitly in-scope production only.
- Prefer non-destructive proofs: unique `console` canaries, benign DOM markers, or self-account effects — not session theft against real users.
- Do not host drive-by exploit pages against third-party visitors; use approved exploit hosts or local PoCs under program rules.
- Document **policy as observed** (full header value, which response, which path). Do not invent browser behavior.
- Redact cookies, tokens, nonces tied to live sessions, and PII from reports.
- “Bypass” means a **working script or exfil path under that CSP** with evidence — not a theoretical note that CSP is absent or weak.

## Workflow

### 1. Collect every policy surface

1. Capture `Content-Security-Policy` and `Content-Security-Policy-Report-Only` on:
   - HTML document that hosts the sink
   - SPA shell vs late-loaded routes
   - Error pages, OAuth callbacks, file/SVG responses if in scope
2. Note meta CSP vs HTTP header; if both exist, record which wins in the browser under test.
3. Store the **full** policy string and response URL. Policies often differ by path or CDN.

### 2. Parse directives that matter for XSS impact

Build a table from the policy (high-level — prioritize script and navigation sinks):

| Directive | What to record |
| --- | --- |
| `default-src` | Fallback when more specific directive missing |
| `script-src` / `script-src-elem` / `script-src-attr` | Inline, external, event-handler posture |
| `object-src` / `base-uri` / `frame-src` / `child-src` | Plugin, base tag, frame gadgets |
| `connect-src` | XHR/fetch/WebSocket exfil destinations |
| `img-src` / `font-src` / `style-src` | Side-channel or CSS-assisted tricks (document only if used) |
| `form-action` / `navigate-to` | Form or navigation exfil limits |
| `require-trusted-types-for` / `trusted-types` | Trusted Types enforcement |
| `report-uri` / `report-to` | Reporting only — does not block |

Normalize source expressions you see: `'self'`, `'none'`, `'unsafe-inline'`, `'unsafe-eval'`, `'unsafe-hashes'`, `'strict-dynamic'`, `'nonce-…'`, `'sha256-…'`, hosts, schemes (`https:`, `data:`, `blob:`), and `*`.

### 3. Classify enforcement posture (no exploit yet)

| Pattern | Assessment note |
| --- | --- |
| No CSP / report-only only | XSS impact not CSP-limited; recommend enforce + report |
| `script-src 'unsafe-inline'` (no nonce/hash) | Classic inline/event-handler XSS usually still works |
| Nonce or hash **without** `'unsafe-inline'` | Random inline without correct nonce/hash blocked |
| Nonce + `'strict-dynamic'` | Nonce-marked root scripts may load further scripts; look for attacker-controlled script URL injection into privileged loaders |
| Host allowlist (`cdn.example`, `*.googleapis.com`, etc.) | Check for **script gadgets** / JSONP / angular-like template endpoints on allowed origins (high-level: known class only; prove load + execute under CSP) |
| `'unsafe-eval'` / `wasm-unsafe-eval` | Enables `eval`/`Function`/some compile paths if attacker reaches them |
| `object-src` missing or broad + plugin legacy | Rare modern impact; still note if Flash/PDF plugin paths exist |
| Missing `base-uri` | `<base href>` injection may retarget relative script URLs if script load is otherwise allowed |
| Trusted Types enforced | DOM sinks may throw; need TT bypass or non-TT sink — treat as separate control |

### 4. Nonce and hash methodology (authorized)

**Nonces**

1. Observe how nonces are generated and injected (per-response random vs static/predictable).
2. Confirm reflected/stored injection **cannot** mint a valid `nonce=` on attacker markup unless the app echoes the live nonce into attacker-controlled HTML (self-XSS / template bugs).
3. If attacker HTML can include the **same** nonce the page uses (e.g. nonce printed into a data attribute or JSON the attacker closes into), treat as nonce leak → inline script under CSP.
4. With `'strict-dynamic'`, focus on: can untrusted input become a `src` of a script created by an already-nonced bootstrapper (`createElement('script')`, dynamic import chains, widget loaders)?

**Hashes**

1. List `'sha256-…'` / `'sha384-…'` / `'sha512-…'` entries and which inline blocks they cover.
2. Inline content that **changes** (user id, CSRF token inside script) breaks static hashes — note dual use of nonce+hash or unsafe-inline fallbacks.
3. Do not treat hash presence alone as safe if other script sources remain wide open.

Stay high-level: prove with the app’s real bootstrap code; do not ship generic mass gadget lists as the report body.

### 5. Source-expression and allowlist research

For each host or scheme in `script-src` / `default-src`:

1. **Is it required?** Prefer tightening to exact paths/SRI in remediation notes.
2. **JSONP / callback parameters** on allowed origins that return `Content-Type` executable as script.
3. **Path confusion / open redirects** on allowed hosts that end up serving JS (document chain; route redirect detail to `open-redirect` if needed).
4. **`data:` / `blob:`** in script-src: often enough for inline-equivalent payloads when XSS can create those URLs.
5. **CDN version path control** if the app loads libraries from attacker-influenced version strings (only when input reaches the script URL).

Always close the loop: **CSP allows load** + **attacker controls URL or inline** + **execution observed**.

### 6. Relate to an XSS or markup sink

CSP bypass research almost always needs a sink:

1. Route injection/reflection work to `xss-cross-site-scripting` (or `injection-checking` if class unclear).
2. Re-test the minimal XSS PoC under CSP; capture console CSP errors for failed attempts.
3. Escalate only with context-correct primitives that the policy still permits (e.g. external script to allowed origin, nonce leak, `strict-dynamic` loader, `javascript:` where still relevant to navigation — usually separate from `script-src`).
4. For exfil after execution: check `connect-src` / `img-src` / `form-action`. Restricted connect may still allow DNS or image-beacon style channels if those directives are loose — document which channel worked.

### 7. Companion controls and false confidence

- Cookie `HttpOnly` limits some XSS impact but is not a CSP substitute.
- COOP/COEP/CORP affect isolation; do not call them CSP bypasses.
- `frame-ancestors` is clickjacking surface — `clickjacking` skill.
- CAPTCHA or WAF in front of reflection is orthogonal — `waf-bypass-techniques` only if authorized and needed.

### 8. Remediation verification

After fixes:

1. Retest original PoC and one alternate sink if the app has multiple render paths.
2. Prefer: nonces or hashes, drop `'unsafe-inline'` / `'unsafe-eval'`, tight `script-src`, `object-src 'none'`, `base-uri 'self'`, meaningful `connect-src`, Trusted Types where feasible.
3. Prefer allowlists over broad CDNs; use SRI (`integrity`) for third-party scripts.
4. Keep report-only deployed alongside enforce during rollout; confirm enforce on the document that hosts sinks.
5. Secure coding review of script loaders and HTML sinks → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Find or prove HTML/JS injection sink | `xss-cross-site-scripting` |
| Injection class unclear | `injection-checking` |
| Cross-origin credentialed **read** of APIs | `cors-cross-origin-misconfiguration` |
| Framing / `frame-ancestors` only | `clickjacking` |
| `postMessage` listener trusts bad origin | `postmessage-security` |
| Secure CSP/header and loader implementation | `code-quality-standards` |
| WAF in front of reflected XSS | `waf-bypass-techniques` (authorized) |

## Output Checklist

- [ ] Full CSP (and report-only) strings, URL, header vs meta
- [ ] Directive table: script-related + base-uri/object-src/connect-src/Trusted Types
- [ ] Posture class: unsafe-inline / nonce / hash / strict-dynamic / allowlist / mixed
- [ ] XSS or markup sink linked (request or DOM path); CSP console evidence
- [ ] Working execution or exfil path under policy — or explicit “no bypass found”
- [ ] Nonce/hash notes (static vs per-response; leak or loader issues if any)
- [ ] Allowlist/gadget notes only with proof, not generic lists
- [ ] Browser/version used
- [ ] Remediation recommendations and retest status
- [ ] Redacted evidence paths

## Rules

- Do not claim “CSP bypass” without a **working** script execution or data-exfil path under the enforced policy.
- Absence of CSP is a hardening gap, not a bypass.
- Report-only violations are not enforcement bypasses; label them correctly.
- Prefer minimal, context-correct PoCs over polyglot noise.
- Stay within authorized targets; no real-user drive-by payloads.
- High-level gadget discussion only — prove against the target’s actual allowed sources and loaders.
- Distinguish self-XSS + weak CSP from automatic cross-user impact.

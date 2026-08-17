---
name: jsonp-legacy-risks
description: >-
  Authorized assessment of legacy JSONP endpoints: callback parameter injection,
  cross-origin data exfiltration via script tags with ambient cookies, content-type
  and padding pitfalls, and migration from JSONP to CORS or same-origin APIs.
  Use when responses wrap JSON in a caller-controlled function name, clients load
  APIs with <script src>, or a deprecation/removal checklist for JSONP is needed.
---

# JSONP Legacy Risks And Migration

Focused skill for **JSONP** (`callback`, `jsonp`, `cb` padding). Prefer CORS or
same-origin BFF; treat remaining JSONP as high-risk legacy.

## When To Use

| Situation | Direction |
| --- | --- |
| Body like `callbackName({...})` / `/**/callback({...})` | **This skill** (primary) |
| Query `callback=` / `jsonp=` / `cb=` controls the wrapper | **This skill** |
| Widgets use `<script src>` or cookie-auth JSONP without CORS | **This skill** |
| Migration: remove JSONP → CORS / same-origin | **This skill** + CORS skills |
| Credentialed CORS only (no JSONP) | `cors-credentialed-requests` |
| Classic HTML/JS XSS, not padding injection | `xss-cross-site-scripting` |

Keywords: JSONP, callback injection, script-tag read, jQuery `callback=?`, deprecation.

## Scope And Authorization

- Authorized apps, labs, CTFs, and **explicitly in-scope** targets only.
- Prove impact with **test accounts you control**. No real-user PII/sessions;
  approved PoC hosts under program rules only.
- Redact cookies/bodies; minimize retention; rotate secrets after demos.
- Assessment/hardening only—not drive-by campaigns. Fixes → `code-quality-standards`.

## Workflow

### 1. Discover JSONP surfaces

From proxy history, JS bundles, and docs, flag query `callback` / `jsonp` /
`cb`, `Content-Type: application/javascript` (or `text/javascript`), and body
patterns `name(...)` or `/**/name(...)`. Note old jQuery/maps/ads widgets.
Inventory endpoints that accept a callback and return identity, tokens, PII,
or admin data **with cookies**.

### 2. Threat model (why JSONP is legacy)

SOP blocks `fetch`/XHR body reads, not foreign `<script src>` execution. A
third-party page can load cookie-authenticated JSONP:

```html
<script src="https://api.example/user?callback=exfil"></script>
```

Ambient cookies (subject to SameSite) attach; the script runs on the
**attacker page**, shipping data off-origin without CORS opt-in.

| Risk | Mechanism | Impact |
| --- | --- | --- |
| Script-tag data exfil | Cookie session + JSONP padding | Session / PII theft |
| Callback injection | Unsanitized callback → JS breakout | XSS-like on consumer |
| Content-type / GET side effects | JSON as script; script-loadable mutations | XSS quirks / CSRF-style |
| Over-broad endpoints | Any authenticated GET padded | High blast radius |

### 3. Callback injection probes (authorized)

Vary **only** the callback; keep auth as your test user:

```http
GET /v1/profile?callback=validName HTTP/1.1
Host: api.example
Cookie: session=...
```

Breakout shapes (lab): `alert(1)//`, `foo;alert(1);//`,
`foo});alert(1);(function(){//`, `foo%0aalert(1)//`, `callback[]=x`.

| Observation | Interpretation |
| --- | --- |
| Strict identifier only (`[A-Za-z_][\w.]*`) | Safer padding; still check exfil |
| Arbitrary bytes reflected into script | Treat as script injection |
| Fixed callback or allowlist | Reduces injection; exfil may remain |
| No callback still returns bare JSON | Check CORS separately if sensitive |

Confirm **browser** execution for impact; curl alone is not enough.

### 4. Cookie / SameSite / method constraints

- Record `SameSite`, `Secure`, `Domain`. `Strict` may block cross-site script
  GETs; `Lax`/`None` often still send—**retest target browsers**.
- Script tags load GET only; POST JSONP is not script-loadable. Note
  third-party cookie phase-out; still report first-party/in-scope callability.

### 5. Migration and deprecation checklist

| Step | Action |
| --- | --- |
| 1 | Inventory JSONP params and all first-/third-party consumers |
| 2 | Replace reads with same-origin BFF or exact CORS allowlist APIs |
| 3 | Never enable JSONP on authenticated or sensitive responses |
| 4 | Temporary only: fixed/allowlisted callback names; no free-form JS |
| 5 | Dual-run CORS path; measure traffic; then reject/ignore callbacks |
| 6 | Regression tests: no padding; callback never executes user input |
| 7 | Update clients: `fetch` + credentials policy; remove `callback=?` |

Remediation: delete JSONP; use exact-origin CORS (`cors-cross-origin-misconfiguration`,
`cors-credentialed-requests`) or same-site cookies + same-origin APIs.
Implementation quality → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| JSONP discovery, callback injection, script-tag exfil, deprecation | **This skill** |
| ACAO/ACAC and credentialed CORS reads | `cors-credentialed-requests` |
| Broad CORS matrix | `cors-cross-origin-misconfiguration` |
| HTML/JS XSS not tied to JSONP padding | `xss-cross-site-scripting` / `injection-checking` |
| Cookie flags / SameSite hygiene | `cookie-security-flags` |
| CSRF on state-changing cookie endpoints | `csrf-cross-site-request-forgery` |
| Secure API migration and tests | `code-quality-standards` |

**Selection:** padding/`callback` transport or JSONP removal → **this skill**.
Pure CORS header bugs without JSONP → CORS skills primary.

## Output Checklist

- [ ] Endpoints, callback param names, Content-Type, auth (cookie names)
- [ ] Sample padded response shape (secrets redacted)
- [ ] Injection: allowlist vs reflection; breakout evidence if any
- [ ] Script-tag exfil PoC on approved host with **test** account only
- [ ] Cookie SameSite / browser notes; sensitive field names (values redacted)
- [ ] Deprecation: consumer inventory, CORS/BFF target, disable plan, tests
- [ ] Handoffs: CORS, XSS, CSRF, cookie skills as needed

## Rules

- Authorized testing only; no real-user harvest or unsolicited drive-by PoCs.
- “JSONP exists” is debt—severity needs sensitive data, auth cookies, or confirmed
  callback injection. JSONP ≠ CORS (script read vs XHR opt-in). Redact secrets.

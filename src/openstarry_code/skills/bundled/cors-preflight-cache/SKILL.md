---
name: cors-preflight-cache
description: >-
  Authorized assessment of CORS preflight caching (Access-Control-Max-Age),
  browser OPTIONS cache behavior, ACAO reflection under credentials, and
  preflight/CDN cache-poison risks. Use when debugging CORS failures, tuning
  Max-Age, or validating that cached preflights cannot sticky-trust hostile
  origins across Origin changes.
---

# CORS Preflight Cache And Debugging

Focused skill for **preflight lifetime**, **`Access-Control-Max-Age`**,
**credentialed ACAO**, and **cache confusion** around `OPTIONS`. Hand general
CORS inventory to `cors-cross-origin-misconfiguration`. Hand ACAC-first impact
proofs to `cors-credentialed-requests`.

## Scope And Authorization

- Authorized apps, labs, CTFs, and program-scoped targets only.
- Prefer staging or owned accounts; do not drive-by real users with PoC pages.
- Shared CDN/proxy mis-caching of CORS headers can affect other clients — use
  unique canary paths, short TTL, and purge when allowed; avoid mass-poisoning
  production preflight or API URLs.
- Browser Max-Age is per-profile; claim cross-user impact only with shared-cache
  second-client proof. Redact cookies, tokens, and PII from reports.

## When To Use

- Preflight responses set `Access-Control-Max-Age` on `OPTIONS`.
- SPA/API CORS flaky after deploy, or differs after hard reload vs soft navigation
  (suspect preflight stickiness).
- Need to reason how long a good or bad preflight sticks in the browser.
- Suspected **shared cache** of `Access-Control-*` that varies by `Origin` but
  lacks correct keying / `Vary`.
- Debugging credentialed CORS: `ACAC: true`, reflected `ACAO`, forbidden
  `ACAO: *` + credentials, OPTIONS vs actual response mismatch.
- Keywords: Access-Control-Max-Age, preflight cache, OPTIONS cache poison,
  CORS debug, ACAO reflection, credentialed preflight.

Not primary for full origin-bypass surveys, pure CSRF writes, or JWT-only
`Authorization` abuse — route those below.

## Workflow

1. **Separate caches**

   | Layer | Stored | Cross-user? |
   | --- | --- | --- |
   | Browser preflight cache | Successful OPTIONS per origin/URL/method/headers | No (per profile) |
   | Shared HTTP cache (CDN/proxy) | Cacheable OPTIONS/GET carrying ACAO | Yes if keyed wrong |

   Browser Max-Age and shared-cache poison of CORS headers are in scope.
   Host/XFH HTML poison → `host-header-cache-poison`.

2. **Map preflight surface**  
   Non-simple methods, custom headers, or non-simple `Content-Type` (e.g. JSON)
   trigger preflight. Capture baseline:

   ```http
   OPTIONS /api/me HTTP/1.1
   Host: api.example
   Origin: https://app.example
   Access-Control-Request-Method: GET
   Access-Control-Request-Headers: content-type,x-request-id
   ```

   Record status, `ACAO`, `ACAC`, ACAM, ACAH, `Access-Control-Max-Age`, `Vary`,
   `Cache-Control`, `Age`, CDN HIT/MISS.

3. **Interpret Access-Control-Max-Age**  
   - Seconds the **browser** may reuse this preflight (browsers often clamp large values).
   - Long Max-Age cuts OPTIONS load but **extends the sticky window** after policy
     shrinks (allowlist, credentials, allowed headers).
   - Max-Age `0` (or omit) forces fresher OPTIONS after lockdown; still retest CORS
     on the **actual** response. Preflight cache does not replace correct ACAO/ACAC
     on the real response for JS body reads.

4. **ACAO reflection and credentials under preflight**  
   Replay OPTIONS and the actual request with allowed origin, attacker origin,
   `Origin: null`, and `*` expectations.

   | Pattern | Risk |
   | --- | --- |
   | Reflect any Origin + `ACAC: true` | Credentialed cross-origin **read** |
   | `ACAO: *` + `ACAC: true` | Spec-invalid; browsers block credentialed read — still report |
   | OPTIONS permissive, GET tight (or reverse) | Failures or partial trust |
   | Long Max-Age after reflecting evil Origin | Sticky client trust until expiry |

   Confirm impact with browser PoC when ACAC is involved
   (`cors-credentialed-requests`). Reflection alone is not always critical.

5. **Shared-cache poison of CORS / preflight**  
   Hypothesis: response varies with `Origin` but a shared cache serves one
   client’s ACAO to another. Prefer `Vary: Origin` when ACAO depends on Origin.
   Check CDN caching of OPTIONS and `Cache-Control`. Proof: Client A primes
   permissive ACAO; clean Client B on another Origin gets wrong ACAO. Unique
   paths + second-client verify. Do **not** claim cross-user impact from
   browser-only Max-Age.

6. **Debug CORS failures systematically**  
   Confirm true cross-origin → preflight vs actual failure → exact `Origin`/`ACAO`
   match → if `credentials: 'include'`, require `ACAC: true` and non-`*` ACAO →
   ACAM/ACAH cover method/headers → hard-reload or wait Max-Age after server
   changes → note browser, extensions, WebView differences.

7. **Remediation** (with `code-quality-standards`)  
   Exact-match allowlist; never reflect arbitrary Origin with credentials; never
   `*` or `null` with credentials on cookie APIs. Set `Vary: Origin` when CORS
   headers depend on Origin; avoid public shared cache of origin-specific CORS
   unless keying is correct. Choose Max-Age consciously (shorter after policy
   changes and for sensitive credentialed APIs). Keep OPTIONS and actual policy
   consistent.

## Routing

| Need | Skill |
| --- | --- |
| Full CORS misconfig survey, null/regex bypass | `cors-cross-origin-misconfiguration` |
| ACAC / cookie cross-origin **read** proofs | `cors-credentialed-requests` |
| Cross-site **writes** (CSRF) | `csrf-cross-site-request-forgery` |
| Host/XFH asset or HTML cache poison | `host-header-cache-poison` |
| API discovery / SameSite cookies | `api-recon-and-docs` / `same-site-cookie-pitfalls` |
| Code allowlist and header tests | `code-quality-standards` |

Hand off to **`cors-cross-origin-misconfiguration`** for broad Origin probing,
whitelist bypasses, or general ACAO inventory beyond preflight cache and debugging.
Keep **this skill primary** for Max-Age, OPTIONS stickiness, shared-cache of
`Access-Control-*`, or CORS failure triage.

## Output Checklist

- [ ] Authorization, environment, browser/version for cache observations
- [ ] Preflight endpoints; sample OPTIONS request/response (secrets redacted)
- [ ] `Access-Control-Max-Age` and sticky-window impact
- [ ] ACAO/ACAC/ACAM/ACAH consistency: OPTIONS vs actual response
- [ ] Origin matrix: allowed, attacker, null, `*` — reflection + credentials
- [ ] Shared-cache claims: `Vary`, `Cache-Control`, HIT/Age, second client
- [ ] Debug root cause for any browser block; remediation notes
- [ ] Handoffs: `cors-cross-origin-misconfiguration` / `cors-credentialed-requests`

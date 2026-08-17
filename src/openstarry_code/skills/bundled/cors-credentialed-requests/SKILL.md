---
name: cors-credentialed-requests
description: >
  Authorized assessment of credentialed CORS: Access-Control-Allow-Credentials
  with cookies or client certs, forbidden ACAO *, origin reflection, null origin,
  preflight vs simple requests, and browser PoC requirements. Use when ACAC true,
  credentialed cross-origin fetch, or cookie-authenticated SPA/API splits are in scope.
---

# Credentialed CORS Requests (Authorized Assessment)

Focused assessment of **credentialed** Cross-Origin Resource Sharing: when
browsers attach cookies (or other ambient credentials) cross-origin and the
server’s `Access-Control-*` headers let hostile pages **read** authenticated
responses. Complements broad CORS inventory with a credentials-first threat model.

## Scope And Authorization

- Authorized applications, labs, CTFs, and program-scoped targets **only**.
- PoC pages must run on an approved exploit host or local HTML under program
  rules — do not drive-by real users or phish production victims.
- Prefer proving impact with **your** test account’s PII/tokens. Minimize
  third-party data exposure; redact session values in reports.
- Credentialed CORS issues are **browser** issues. `curl` showing ACAO alone is
  not exploit proof without a credentialed cross-origin read scenario.
- This skill does **not** authorize CSRF-style state changes by itself; pair
  writes with `csrf-cross-site-request-forgery` when cookies enable cross-site
  mutation even without a readable response body.
- Mobile native apps ignore CORS; only assess when a WebView or browser client
  is in scope.
- Redact cookies, tokens, and personal data from tickets and example captures.

## Use When

- Responses set `Access-Control-Allow-Credentials: true` (ACAC)
- SPA on `app.example` calls API on `api.example` (or other site) with cookies
- Cookie or mTLS-backed session; export/account JSON endpoints
- Suspected “HttpOnly cookie but still stealable via loose CORS”
- Keywords: credentialed CORS, ACAC, `credentials: 'include'`, withCredentials,
  ACAO reflection + cookies, `Origin: null` + credentials

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full CORS matrix (wildcard public, general misconfig survey) | `cors-cross-origin-misconfiguration` |
| Cross-site **writes** without needing response body | `csrf-cross-site-request-forgery` |
| JWT only in `Authorization` set by attacker page | `api-auth-and-jwt-abuse` (CORS rarely injects Authorization) |
| postMessage / window messaging | `postmessage-security` |
| Clickjacking / framing | `clickjacking` |

## Workflow

1. **Confirm ambient credentials exist.**
   - Session cookies on the API host (`Domain`, `Path`, `Secure`, `SameSite`)
   - Note `SameSite=Lax/Strict/None`: `None` + `Secure` is required for common
     cross-site credentialed fetches; Lax may still send on top-level GETs but
     not on typical cross-origin XHR/fetch — record actual browser behavior
   - Prefer endpoints that return identity, PII, tokens, or admin JSON

2. **Map CORS on those endpoints.**
   From proxy history, filter `Access-Control-Allow-Origin` and ACAC.
   Replay with controlled `Origin` values while authenticated as a test user:

   ```http
   GET /v1/me HTTP/1.1
   Host: api.example
   Origin: https://evil.example
   Cookie: session=...
   ```

   | Server response | Credentialed impact |
   | --- | --- |
   | `ACAO: https://evil.example` + `ACAC: true` | Critical: evil origin can read response with victim cookies |
   | `ACAO: *` + `ACAC: true` | Spec-invalid; browsers must hide body — still report server bug |
   | Dynamic reflect of any Origin + `ACAC: true` | Treat as arbitrary origin trust |
   | `ACAO: https://app.example` only + `ACAC: true` | Expected for first-party SPA; check whitelist bypasses |
   | ACAO without ACAC | Cookies not exposed to JS reader via CORS (document residual risks) |

3. **Client requirements (both sides must opt in).**
   Browser sends cookies cross-origin only if roughly:

   - Server: `ACAC: true` and **specific** ACAO (not `*`)
   - Client: `fetch(url, { credentials: 'include' })` or XHR `withCredentials = true`

   ```js
   fetch("https://api.example/v1/me", { credentials: "include" })
     .then((r) => r.json())
     .then((j) => { /* exfil for PoC to approved sink */ });
   ```

4. **Null origin and sandbox pitfalls.**
   Whitelisting `null` with credentials enables sandboxed iframe / `data:` PoCs:

   ```http
   Origin: null
   ```

   If `ACAO: null` and `ACAC: true`, demonstrate with an approved sandboxed iframe
   pattern (see `cors-cross-origin-misconfiguration` for HTML sketch). Never use
   against real users.

5. **Whitelist and parser bypasses (credentialed path).**
   When only “trusted” apps are allowlisted, still test:

   ```text
   https://api.example.evil.example
   https://evil.api.example
   https://app.example.attacker.tld
   https://app.example%60.evil.example
   null
   ```

   Prefix/suffix regex mistakes, trusting all `*.example` (XSS on any subdomain),
   HTTP vs HTTPS origin mismatch, and trailing-dot / Unicode lookalikes.
   **Confirmed** only if ACAO echoes the attacker origin **and** ACAC remains true
   **and** a browser read succeeds.

6. **Preflight vs simple requests under credentials.**
   - Simple GET/POST may skip preflight; JS still needs ACAO/ACAC on the **actual**
     response to read the body
   - JSON `Content-Type`, custom headers, or non-simple methods trigger `OPTIONS`
   - Check OPTIONS overly broad (`ACAH` / `ACAM`) while GET is tight, or reverse
   - `Access-Control-Allow-Headers` must not be required for attacker to set
     secrets they do not know; focus on whether **read** of cookie-authenticated
     body is granted to foreign origins

7. **SameSite, third-party cookie phase-out, and residual risk.**
   - Modern browsers may block third-party cookies in some contexts — retest in
     target browsers; still report misconfig if headers trust arbitrary origins
   - First-party SPA subdomain splits often still send cookies
   - Document browser + version used for PoC
   - If cookies are `SameSite=Strict` and never sent cross-site, lower exploitability
     but note header hygiene and non-browser clients

8. **Impact PoC and severity binding.**
   - Victim **test** user visits approved PoC while logged into target
   - Capture sensitive **field names**; redact values
   - Severity: account PII/session tokens/read admin API → high/critical;
     non-sensitive public-with-cookies → lower
   - Chain notes: XSS on a whitelisted origin expands trust; subdomain takeover
     on allowed origin → treat as full credentialed read

9. **Remediation guidance** (implementation with `code-quality-standards`).
   - Explicit allowlist of exact origins; **no** reflection of arbitrary `Origin`
   - Never `ACAO: *` with credentials; never `ACAO: null` with credentials
   - Avoid “all subdomains” unless every subdomain is equally trusted and locked down
   - Prefer exact string match over naive regex; reject null
   - Separate public unauthenticated APIs (maybe open CORS) from cookie APIs
   - For SPAs: tight allowlist; consider CSRF tokens for state-changing cookie APIs

## Credentialed CORS Decision Sketch

```text
Cookie/session auth on API?
  no  → credentialed CORS theft N/A (check token-in-JS storage + open ACAO separately)
  yes → ACAC true + ACAO attacker-controlled?
            no  → document safe config; still note whitelist quality
            yes → browser PoC with credentials: 'include'
                    success → report data theft impact
```

## Anti-Patterns (server)

- Reflecting any `Origin` when `ACAC: true`
- `Access-Control-Allow-Origin: *` together with `ACAC: true`
- Allowlisting `null` for “dev convenience” on production cookie APIs
- Trusting `*.corp.example` while XSS or takeover exists on a sibling subdomain
- Assuming CORS is a substitute for CSRF protection on cookie writes
- Fixing only OPTIONS while the real GET still reflects Origin with ACAC

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Credentialed CORS read risk, ACAC, cookie cross-origin | **This skill** | — |
| Broad CORS survey, non-credentialed reflection matrix | `cors-cross-origin-misconfiguration` | this when ACAC appears |
| Cross-site state change (CSRF) | `csrf-cross-site-request-forgery` | this if body also readable |
| API auth / JWT header abuse | `api-auth-and-jwt-abuse` | — |
| Endpoint discovery | `api-recon-and-docs` | this for cookie JSON APIs |
| XSS expanding origin allowlist | `xss-cross-site-scripting` / `injection-checking` | this for CORS trust |
| Correct allowlist implementation | `code-quality-standards` | **always apply** on fixes |

### Routing to `cors-cross-origin-misconfiguration`

Use **`cors-cross-origin-misconfiguration`** as the general CORS testing skill
when the engagement needs full header inventory, unauthenticated reflection, or
preflight method matrices. Keep **this skill primary** when the core question is
**credentialed** access (`ACAC`, cookies, `credentials: 'include'`). Both may
apply on the same host; avoid duplicate findings — one report with clear
credentialed vs non-credentialed impact.

### Routing to `code-quality-standards`

Always apply **`code-quality-standards`** when fixing or implementing CORS:

- Exact-match allowlists; no unsanitized origin reflection
- Safe defaults in staging/production parity for cookie APIs
- Tests for allowed origin, denied origin, and forbidden `*` + credentials
- No secrets in CORS debug logs

## Checklist

- [ ] Authorization and PoC host constraints recorded
- [ ] Cookie/session (or other ambient) auth confirmed on target API
- [ ] `SameSite` / Secure / Domain attributes noted; browser versions used
- [ ] ACAO/ACAC matrix for attacker, null, allowed app, and `*` origins
- [ ] Reflection or whitelist bypass attempts documented (one variable at a time)
- [ ] Preflight vs actual response header consistency checked
- [ ] Browser PoC with `credentials: 'include'` (or XHR withCredentials)
- [ ] Impact: sensitive field names (values redacted); exploitability caveats
- [ ] CSRF write surface noted if cookies enable state change without read
- [ ] Remediation: exact allowlist, no null/*, no broad subdomain trust
- [ ] Related skills applied: `cors-cross-origin-misconfiguration` for breadth,
      `code-quality-standards` for code fixes

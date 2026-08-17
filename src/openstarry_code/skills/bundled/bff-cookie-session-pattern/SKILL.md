---
name: bff-cookie-session-pattern
description: >-
  Design and review Backend-for-Frontend (BFF) cookie sessions for SPAs:
  server-held tokens, HttpOnly session cookies, same-site edge layout, CSRF,
  and logout/revocation. Use when an SPA must avoid JS-readable access tokens,
  proxy OAuth/OIDC through a BFF, or migrate from localStorage Bearer auth to
  cookie-bound BFF sessions under clear ownership or engagement scope.
---

# BFF Cookie Session Pattern (SPA)

Implement and assess the **Backend-for-Frontend** session model: the browser holds
only an **opaque, HttpOnly** session cookie to a same-site BFF; access/refresh
tokens stay **server-side**. The SPA calls first-party BFF APIs with credentials;
the BFF attaches upstream tokens. Authorized apps, labs, and owned systems only.

## When To Use

| Situation | Direction |
| --- | --- |
| SPA stores access/refresh in `localStorage` / JS memory; harden to cookies | **This skill** |
| OAuth/OIDC code exchange and tokens must move off the SPA into a BFF | **This skill** |
| Cookie session + reverse-proxy API facade for a first-party SPA | **This skill** |
| Cookie **flags only** (Secure/HttpOnly/SameSite matrix) | `cookie-security-flags` |
| Refresh rotation / reuse detection (non-BFF focus) | `jwt-refresh-token-patterns` |
| Credentialed CORS across sites instead of BFF | `cors-credentialed-requests` |
| No authorization for live auth or session APIs | **Do not use** actively |

Keywords: BFF, cookie session, SPA auth, token proxy, HttpOnly session, confidential
client, same-site BFF, avoid localStorage tokens, OIDC BFF.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only.
- Prove with **test accounts** you control. Cap login/refresh rate; avoid lockouts.
- Redact session cookies and tokens; store captures offline; rotate after demos.
  Prefer non-destructive proofs; no mass-revoke without approval.
- Implementation follows `code-quality-standards` (secrets, logging, tests, lifecycle).

## Workflow

### 1. Map architecture

| Layer | Capture |
| --- | --- |
| SPA origin | Host, base path, how API base URL is set |
| BFF | Same-origin path (`/api`) vs sibling host; framework |
| IdP / AS | Auth code; confidential client vs public+PKCE on server |
| Session store | Cookie SID → server session; sealed cookie; Redis/DB |
| Upstream | How BFF injects Bearer / mTLS / service credentials |

**Goal:** SPA never sees access/refresh in JS, storage APIs, or SPA-facing JSON.

### 2. Prefer same-origin / same-site layout

| Layout | Cookie attach | Preference |
| --- | --- | --- |
| Same origin (SPA + BFF paths) | Natural; no CORS | **Best** |
| Same-site siblings under eTLD+1 | Careful Domain/SameSite | OK if required |
| Cross-site SPA ↔ BFF | `SameSite=None; Secure` + CORS ACAC | Avoid for new designs |

Prefer host-only cookie; avoid parent `Domain=` unless documented.

### 3. Session cookie profile

```http
Set-Cookie: __Host-bff_session=<opaque>; Path=/; Secure; HttpOnly; SameSite=Lax
```

- Opaque cryptographically random SID (or sealed blob); `__Host-` when Path=/ and no Domain.
- Idle/absolute lifetime server-side; logout destroys session and clears matching cookie.
- Regenerate SID on login and privilege step-up → `session-fixation-management`.

### 4. Token custody at the BFF

1. Browser hits BFF login/callback; BFF completes code exchange **server-side**.
2. BFF stores access (+ refresh) keyed by session; SPA gets only the session cookie.
3. SPA → BFF with `credentials: 'same-origin'` (or include for same-site); no Bearer in JS.
4. BFF → upstream attaches access token; refresh stays server-held with rotation/reuse
   (`jwt-refresh-token-patterns`). Never return token JSON to the browser; `Cache-Control: no-store`.

### 5. CSRF on cookie sessions

Cookie auth reintroduces CSRF. On POST/PUT/PATCH/DELETE require a synchronizer or
double-submit CSRF token; use `SameSite=Lax`/`Strict` when possible (not sole defense
if `None`); Fetch Metadata as defense-in-depth (`fetch-metadata-sec-headers`). Map
mutating routes; reject missing CSRF. Deep work → `csrf-cross-site-request-forgery`.

### 6. SPA client rules

- Relative `/api` or same-origin base; no third-party API calls with the user session from JS.
- Send CSRF header on mutations; handle BFF `401` with re-auth (no SPA silent refresh).
- Ban tokens in `localStorage`, `sessionStorage`, or globals hydrated from BFF.

### 7. Logout, revoke, assessment

Logout invalidates BFF session and revokes IdP refresh family when available. Password
change / MFA disable kills all user BFF sessions; enforce timeouts server-side.

| Check | Fail signal |
| --- | --- |
| Token leak to SPA | Tokens in storage, SPA JSON, or non-HttpOnly cookie |
| Weak cookie | Missing Secure/HttpOnly; broad Domain; no revoke path |
| CSRF gap | Cross-site POST mutates state with only session cookie |
| Fixation | Pre-login SID valid after auth |
| CORS / proxy | ACAC + reflected origin; user-controlled upstream via BFF |

### 8. Remediation (`code-quality-standards`)

Opaque HttpOnly session; encrypt tokens at rest if persisted; CSRF on mutations;
regenerate on login; no token fields in SPA JSON; tests for cookie flags, CSRF reject,
logout kill, and server-only refresh.

## Routing

| Need | Skill |
| --- | --- |
| Cookie flag matrix, prefixes, Domain/Path | `cookie-security-flags` |
| Refresh rotation / reuse / family revoke | `jwt-refresh-token-patterns` |
| Session fixation / regenerate-on-auth | `session-fixation-management` |
| CSRF token bypass / login CSRF | `csrf-cross-site-request-forgery` |
| Credentialed CORS (non-BFF split) | `cors-credentialed-requests` |
| OAuth redirect / PKCE / AS misconfig | `oauth-oidc-misconfiguration` / `oauth-pkce-checklist` |
| JWT alg/claim forgery on upstream | `api-auth-and-jwt-abuse` |
| Secure implementation baseline | `code-quality-standards` |

**Selection:** SPA + server-held tokens + cookie to BFF → **this skill**. Flags-only →
`cookie-security-flags`. Pure refresh lifecycle without BFF → `jwt-refresh-token-patterns`.

## Output Checklist

- [ ] SPA origin, BFF layout (same-origin / same-site / cross-site), IdP role documented
- [ ] Session cookie name, flags, Domain/Path, lifetime, prefix; logout clear verified
- [ ] Proof tokens are not exposed to SPA (storage, responses, non-HttpOnly cookies)
- [ ] Server-side token store and refresh path described (rotation/reuse noted)
- [ ] CSRF defense on mutating BFF routes evidenced or gap filed
- [ ] Fixation/regenerate-on-login and multi-session revoke checked
- [ ] CORS/SameSite residual risk for chosen layout recorded
- [ ] Remediation and tests listed; credentials redacted in evidence

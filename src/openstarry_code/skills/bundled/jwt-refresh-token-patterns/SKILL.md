---
name: jwt-refresh-token-patterns
description: >-
  Authorized design and assessment of JWT access + refresh token patterns:
  rotation, reuse detection, revocation, and storage (cookie vs localStorage).
  Use when implementing or reviewing refresh endpoints, sliding sessions, or
  long-lived offline tokens under clear ownership or engagement scope.
---

# JWT Refresh Token Patterns

Secure **access + refresh** lifecycle: short-lived access JWTs, rotatable refresh
tokens, server-side reuse detection, and storage matched to the threat model.
For **authorized** apps, labs, and owned systems only.

## Use When

| Situation | Direction |
| --- | --- |
| Access JWT **and** refresh / renew token | **This skill** (primary) |
| `/token/refresh`, logout, “stay signed in”, mobile offline | **This skill** |
| Designing rotation, family IDs, reuse detection, storage | **This skill** |
| Access-token **crypto** only (alg/kid/confusion) | `api-auth-and-jwt-abuse` |
| OAuth AS refresh / PKCE / redirect | `oauth-oidc-misconfiguration` / `oauth-pkce-checklist` |
| No authorization for live auth APIs | **Do not use** actively |

Keywords: refresh rotation, reuse detection, token family, sliding session, refresh cookie, silent renew.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only.
- Prove with **accounts you control**. Cap refresh rate; avoid lockouts.
- Treat refresh as **long-lived credentials**: redact; store captures offline; rotate after demos.
- Prefer non-destructive proofs. No mass-revoke of production sessions without approval.
- Implementation follows `code-quality-standards` (secrets, logging, tests).

## Workflow

### 1. Map the token pair

| Item | Capture |
| --- | --- |
| Access | Claims (`sub`, `exp`, `jti`), TTL, Bearer vs cookie |
| Refresh | Opaque vs JWT; TTL; absolute vs sliding; transport |
| Endpoints | login, refresh, logout, revoke-all, device list |
| Binding / storage | user/device/client; HttpOnly cookie, memory, `localStorage`, Keychain |

### 2. Baseline happy path

Login → `A0` + `R0` → protected resource → refresh with `R0` → `A1` (+ optional `R1`).
Note if old refresh remains valid and which channel the server trusts (body vs cookie).

```http
POST /auth/refresh HTTP/1.1
Host: target.example
Content-Type: application/json
Cookie: refresh=<R0>

{"refresh_token":"<R0>"}
```

### 3. Rotation and reuse detection

| Check | Action | Secure behavior |
| --- | --- | --- |
| Rotate on use | Refresh twice with same `R0` | Second fails; only `R1` works |
| Reuse detection | Present `R0` after `R1` issued | Reject **and** revoke token **family** |
| Parallel refresh | Two concurrent refreshes with `R0` | At most one successor |
| No rotation | Same refresh until exp | Weaker; binding + short TTL + revoke |

**Critical:** stolen refresh works after victim rotated, **or** reuse does not kill the family.

### 4. Revocation and logout

- Logout invalidates refresh **server-side** (delete row / denylist / version bump).
- Password change, reset, MFA disable → revoke refresh families.
- Access JWT may live until `exp` unless denylisted; keep access TTL short.
- “Revoke all devices” must kill other devices’ refresh.

### 5. Storage and transport

| Location | Notes |
| --- | --- |
| HttpOnly + `Secure` + `SameSite` cookie | Prefer for web; defend CSRF on refresh |
| Memory / BFF | Prefer for SPA |
| `localStorage` / URL / logs | Avoid / never for refresh |

Use `Cache-Control: no-store` on auth responses; never log full tokens.

### 6. Binding and hand-offs

- A’s refresh accepted for B → binding bug. Cross-client without policy → document.
- Forgeable refresh JWT → `api-auth-and-jwt-abuse`. OAuth AS refresh → `oauth-oidc-misconfiguration`.

### 7. Remediation (`code-quality-standards`)

- Access: minutes-scale TTL; server-pinned alg/keys. Refresh: opaque handle; **one-time rotate**; **reuse → revoke family**; hash at rest; bind user+client/device.
- Logout/password change: version or delete all refresh rows. Web: BFF or HttpOnly+CSRF; no `localStorage` refresh.
- Tests: rotate-once, reuse-kills-family, logout-invalidates, concurrent refresh.

## Routing

| Need | Skill |
| --- | --- |
| Access JWT alg/kid/jku/claim forgery | `api-auth-and-jwt-abuse` |
| OAuth/OIDC refresh, redirect, state | `oauth-oidc-misconfiguration` |
| PKCE public-client code flow | `oauth-pkce-checklist` |
| Session fixation / concurrent refresh race | `session-fixation-management` / `race-condition` |
| Secure implementation | `code-quality-standards` |

**Selection:** lifecycle/rotation/reuse/storage → **this skill**. Access crypto →
`api-auth-and-jwt-abuse`. OAuth AS → OAuth skills.

## Checklist

- [ ] Access vs refresh TTLs, formats, transports documented
- [ ] Refresh + logout/revoke paths mapped
- [ ] Rotation on use; old refresh rejected
- [ ] Reuse after rotate: reject + family revoke recorded
- [ ] Concurrent refresh; logout/password change invalidates refresh
- [ ] Storage / cookie flags / CSRF / log-leak surface assessed
- [ ] Residual access-JWT window noted; remediation complete; evidence redacted

## Rules

- Authorized dual-account tests only; never replay third-party refresh tokens.
- Do not relabel access-token forgery as refresh lifecycle (route to JWT abuse).
- “Refresh in localStorage” needs XSS or shared-device context in the narrative.
- One clean reuse-detection proof beats bulk spraying. Redact refresh (`len`/hash).

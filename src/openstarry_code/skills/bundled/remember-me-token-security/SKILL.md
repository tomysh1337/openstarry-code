---
name: remember-me-token-security
description: >-
  Design and assess long-lived remember-me / persistent-login tokens: opaque
  selector+validator patterns, hashed storage, rotation, revocation, and cookie
  transport. Use when implementing or reviewing “stay signed in”, persistent
  login cookies, or multi-device remember tokens under clear ownership or
  engagement scope.
---

# Remember-Me Token Security

Secure **persistent login** credentials distinct from short-lived session SIDs:
high-entropy opaque tokens, hashed storage, rotation, and revocable multi-device
records. Authorized apps, labs, and owned systems only.

## When To Use

| Situation | Direction |
| --- | --- |
| “Remember me” / “Stay signed in” / persistent login cookie | **This skill** (primary) |
| Long-lived cookie re-establishes session after browser restart | **This skill** |
| Multi-device “remember this device” tokens | **This skill** |
| Selector+validator, hash-at-rest, rotate/revoke design | **This skill** |
| Session cookie flags only (no long-lived token) | `cookie-security-flags` |
| XSS / network theft of cookie-bound sessions | `session-cookie-theft-defense` |
| JWT alg/kid/claim forgery on access tokens | `api-auth-and-jwt-abuse` |
| API SPA refresh-token rotation families | `jwt-refresh-token-patterns` |
| No authorization for live auth flows | **Do not use** actively |

Keywords: remember-me, persistent login, stay signed in, selector validator, device token.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only.
- Prove with **accounts you control**. Cap issuance; avoid lockouts.
- Treat remember-me values as **long-lived credentials**: redact; offline captures; revoke after demos.
- Prefer non-destructive proofs. No mass-revoke of production devices without approval.
- Implementation follows `code-quality-standards` (secrets, logging, tests).

## Workflow

### 1. Map the persistent credential

| Item | Capture |
| --- | --- |
| Trigger | Checkbox, default-on, device trust UI |
| Format | Opaque random vs signed JWT vs encrypted blob |
| Transport | Cookie name, body field, native secure storage |
| Cookie flags | `Secure`, `HttpOnly`, `SameSite`, `Domain`, `Path`, `Max-Age` |
| Lifetime | Absolute TTL, sliding extend, max devices |
| Endpoints | login (issue), auto-login, logout, revoke-all, device list |
| Server store | Plaintext, hash, selector lookup, user/device bind |

Keep **session SID** (short) separate from **remember token** (long). One immortal cookie for both is a design smell.

### 2. Baseline happy path

1. Login with remember on → note `Set-Cookie` for session **and** remember.
2. Clear session only → revisit → silent re-auth issues a **new** session.
3. Logout → cookie cleared **and** server row invalidated (not cookie-only).
4. Second browser → independent token row if multi-device is supported.

```http
POST /login HTTP/1.1
Host: target.example
Content-Type: application/x-www-form-urlencoded

user=alice&pass=...&remember=1
```

### 3. Token construction

| Pattern | Secure expectation |
| --- | --- |
| **Selector + validator** | Lookup id + secret; store **hash(validator)** only |
| Single opaque secret | ≥128-bit entropy; hash/HMAC index; never plaintext |
| JWT remember | Prefer avoid; if used → absolute exp, denylist/`jti`, pinned alg → else `api-auth-and-jwt-abuse` |

**Critical failures:** predictable tokens; plaintext validator; signed cookie without revocation; clear user id trusted without MAC.

### 4. Rotation, reuse, theft window

| Check | Action | Secure behavior |
| --- | --- | --- |
| Rotate on use | Auto-login twice with same token | Second fails or only successor works |
| Theft after rotate | Present pre-rotate token after victim use | Reject; revoke family / force re-auth |
| Concurrent use | Two clients race same token | At most one successor |
| No rotation | Same token until exp | Weaker — short TTL + binding + easy revoke |

Stolen remember-me ≈ ATO until expiry if not rotatable/revocable. Theft impact → `session-cookie-theft-defense`.

### 5. Revocation and lifecycle

- Logout: invalidate this device’s remember row; clear cookie with matching flags.
- Logout-all / password change / reset / MFA disable: kill **all** user remember rows.
- Device list: last-used metadata; per-device revoke without leaking secrets.
- Remember re-login must **regenerate** SID (`session-fixation-management` if not).

### 6. Transport, binding, remediation

| Topic | Guidance |
| --- | --- |
| Web cookie | HttpOnly + `Secure` + `SameSite=Lax`/`Strict`; host-only; prefer `__Host-` |
| Avoid | `localStorage`, JS-readable long-lived tokens, logging full values |
| Cross-user | Token for A never authenticates B |
| Abuse | Uniform errors; rate-limit auto-login; CSRF still required after silent login |
| Step-up | Sensitive actions may re-prompt even after remember login |

Remediation with `code-quality-standards`: random validator; selector index; **hash at rest**; constant-time compare; **rotate on use**; absolute max age; multi-device caps; full revoke on credential change; separate short session; regenerate SID after remember login; `Cache-Control: no-store`. Tests: issue→reauth, rotate-once, logout-invalidates, password-change-kills-all, cross-user reject. Flag-only audit → `cookie-security-flags`. XSS theft → `session-cookie-theft-defense`.

## Routing

| Need | Skill |
| --- | --- |
| XSS / network / jar theft of session or remember cookies | `session-cookie-theft-defense` |
| JWT alg/kid/jku/claim forgery, Bearer API auth | `api-auth-and-jwt-abuse` |
| Access + refresh rotation families (API SPA) | `jwt-refresh-token-patterns` |
| Cookie flag matrix only | `cookie-security-flags` |
| SID not regenerated after remember login | `session-fixation-management` |
| Secure implementation, storage, tests | `code-quality-standards` |

**Selection:** remember-me design/lifecycle → **this skill**. Cookie theft → `session-cookie-theft-defense`. Access-token crypto → `api-auth-and-jwt-abuse`. Code fixes → `code-quality-standards`.

## Output Checklist

- [ ] Remember vs session credentials distinguished (names, TTLs, stores)
- [ ] Format: opaque selector+validator / other; hash-at-rest confirmed or gap
- [ ] Issue, silent re-auth, logout, revoke-all paths mapped
- [ ] Rotation / reuse evidence (dual-client where possible)
- [ ] Cookie flags, storage location, log-leak surface assessed
- [ ] Cross-user binding; password-change/MFA revoke results
- [ ] SID regenerate after remember login checked
- [ ] Remediation + tests listed; tokens redacted (`len`/hash only)

## Rules

- Authorized dual-account tests only; never replay third-party remember tokens.
- Do not relabel short session theft or JWT access forgery as remember lifecycle (route theft → `session-cookie-theft-defense`, crypto → `api-auth-and-jwt-abuse`).
- One clean rotate/revoke proof beats bulk spraying. Redact full remember values.

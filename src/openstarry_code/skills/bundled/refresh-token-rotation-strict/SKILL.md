---
name: refresh-token-rotation-strict
description: >-
  Strict refresh-token rotation and reuse detection: one-time rotate on use,
  reject previous tokens, revoke entire token family on reuse, concurrent-refresh
  races, grace windows, and storage/hash requirements. Use when assessing or
  implementing refresh endpoints that claim rotation, reuse detection, family
  revoke, sliding sessions, or stolen-refresh ATO resistance under clear
  ownership or engagement scope.
---

# Strict Refresh Token Rotation And Reuse Detection

**Strict** refresh lifecycle: successful refresh **invalidates** the presented token,
issues a successor, and treats later use of a superseded token as **theft** → revoke
the **family**. Complements broader access+refresh design; not access-JWT crypto.

## When To Use

| Situation | Direction |
| --- | --- |
| `/token/refresh`, silent renew, stay-signed-in, mobile offline refresh | **This skill** (primary) |
| Docs claim rotation, reuse detection, or token-family revoke | **This skill** |
| Prove stolen refresh still works after victim refreshed | **This skill** |
| Concurrent double-refresh race / grace period ambiguity | **This skill** |
| Full access+refresh storage/logout map (not only rotate) | `jwt-refresh-token-patterns` |
| Access JWT alg/kid/jku/claim forgery only | `api-auth-and-jwt-abuse` |
| OAuth AS refresh grant / PKCE / redirect | `oauth-oidc-misconfiguration` / `oauth-pkce-checklist` |
| Device/PoP binding of tokens | `device-binding-tokens` |
| No authorization for live auth APIs | **Do not use** actively |

Keywords: refresh rotation, reuse detection, token family, family revoke, one-time
refresh, sliding session, concurrent refresh, grace window, refresh replay.

## Workflow

### 1. Map refresh identity and family model

| Item | Capture |
| --- | --- |
| Refresh form | Opaque handle vs JWT; TTL; absolute vs sliding |
| Transport | Body, `Cookie`, header; HttpOnly / CSRF notes |
| Server state | Row per token, hash-at-rest, family/chain id, version |
| Endpoints | login → refresh → logout → revoke-all / device list |

Prefer hashes only, bind user (+ client/device), login-minted family id.

### 2. Baseline rotate-once path

Login → `A0` + `R0` → refresh with `R0` → `A1` + `R1`. Confirm **`R0` fails** on
second use.

```http
POST /auth/refresh HTTP/1.1
Host: target.example
Content-Type: application/json
Cookie: refresh=<R0>

{"refresh_token":"<R0>"}
```

### 3. Strict rotation matrix (authorized dual-client)

Tokens/accounts **you control** only. Cap rate; avoid production mass-revoke.

| # | Probe | Strict secure behavior |
| --- | --- | --- |
| 1 | Refresh twice serially with same `R0` | Second fails; only `R1` works |
| 2 | After `R0`→`R1`, replay `R0` (theft sim) | Reject **and** revoke **family** (`R1` dies) |
| 3 | After family revoke, try `R1` / siblings | All fail; re-login required |
| 4 | Two concurrent refreshes with `R0` | ≤1 successor; no dual live chains |
| 5 | Expired `R0` | Reject; no new family |
| 6 | Cross-user refresh binding skip | Reject |
| 7 | Logout / password change / revoke-all | Refresh invalidated server-side |
| 8 | Grace reuse window (if any) | Bounded; not indefinite dual use |

**Critical:** superseded refresh still mints tokens without killing the honest chain,
or reuse only 401s without family revoke (stolen token wins).

### 4. Reuse-detection semantics

```
Present R_current → issue R_next, mark R_current consumed
Present consumed R → REUSE → revoke family_id (all descendants)
Present unknown/expired → reject (no family mint)
```

- **Weak:** no rotation until exp — document; short TTL + revoke.
- **Medium:** rotate but reuse does not kill `R_next`.
- **Strict:** reuse → family revoke + metric; honest client re-auths.

Races: atomic CAS / `UPDATE … WHERE status=active`, lock, or short grace → one family.

### 5. Grace, multi-device, storage

- Grace must not leave **two long-lived** valid refresh tokens.
- Multi-device: separate families; reuse in A must not wipe B unless global revoke.
- Sliding use still needs an **absolute** max lifetime.
- Opaque handles; **hash at rest**; bind `sub` + client/device; never log full tokens;
  `Cache-Control: no-store`. Web: HttpOnly+`Secure`+`SameSite` or BFF; no
  `localStorage` refresh. Tests: rotate-once, reuse-kills-family, concurrent
  single-winner, logout/password-change revoke (`code-quality-standards`).

## Routing

| Need | Skill |
| --- | --- |
| Full access+refresh design, storage matrix, logout UX | `jwt-refresh-token-patterns` |
| Access JWT crypto / alg confusion | `api-auth-and-jwt-abuse` |
| Audience/issuer claim checks | `jwt-audience-issuer-checks` |
| DPoP / mTLS sender constraint | `device-binding-tokens` |
| OAuth AS refresh grant, redirect, state | `oauth-oidc-misconfiguration` |
| Multi-vector ATO chaining | `account-takeover-methodology` |
| Cookie flags on refresh cookie | `cookie-security-flags` |
| Secure implementation baseline | `code-quality-standards` |

**Selection:** strict rotate + reuse→family revoke → **this skill**. Broader lifecycle
→ `jwt-refresh-token-patterns`. Access crypto → `api-auth-and-jwt-abuse`. Code →
`code-quality-standards`.

## Output Checklist

- [ ] Refresh format, transport, TTL, family/session model documented
- [ ] Baseline: `R0` → `R1`; second use of `R0` rejected
- [ ] Reuse after rotate: reject **and** family revoke (honest `R1` dead)
- [ ] Concurrent double-refresh: at most one live successor chain
- [ ] Logout / password change / revoke-all invalidates refresh server-side
- [ ] Grace window (if any) bounded; multi-device family isolation noted
- [ ] Hash-at-rest, no full-token logs, storage surface assessed
- [ ] Residual access-JWT window; remediation + tests; evidence redacted

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only.
- Prove with tokens/accounts **you control**. Cap refresh rate; no mass-revoke of
  production sessions without approval.
- Redact refresh (length/hash only in tickets); store captures offline; rotate test
  sessions after demos.
- One clean reuse-detection pair beats bulk spraying. Never replay third-party
  refresh tokens. Implementation pairs with `code-quality-standards`.

---
name: session-timeout-design
description: >-
  Design idle and absolute session timeouts, sliding renewal, server-side TTL,
  and re-auth UX. Use when choosing session lifetime, idle vs absolute expiry,
  sliding windows, remember-me bounds, or timeout middleware for cookie or
  server sessions under clear ownership.
---

# Session Timeout Design

Design **idle** and **absolute** session lifetimes, sliding renewal, and re-auth
UX. Prefer the repo’s session store and auth middleware. Pair theft-hardening
with `session-cookie-theft-defense` and implementation with `code-quality-standards`.

## When To Use

- Choosing **idle** (inactivity) and **absolute** (max age) timeouts
- Sliding renewal, last-activity stamps, or dual clocks on sessions
- Bounding remember-me vs short interactive sessions; timeout UX / step-up
- Aligning cookie `Max-Age` / store TTL with server-enforced policy
- Keywords: session timeout, idle/absolute timeout, session TTL, sliding session,
  inactivity logout, 会话超时, 空闲超时

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Cookie theft flags, binding, rotation architecture | `session-cookie-theft-defense` |
| Set-Cookie flag audit only | `cookie-security-flags` |
| Pre-auth SID kept after login | `session-fixation-management` |
| JWT access/refresh rotation families | `jwt-refresh-token-patterns` |
| Implementation hygiene, tests, secrets | `code-quality-standards` |

## Repo Config First

Repo session libraries, store TTLs, and product auth policy **outrank** defaults.

1. **Session stack:** Express, Django, Rails, ASP.NET, Spring Session, NextAuth,
   Redis/DB SID stores — use their `maxAge` / `rolling` / ticket expiry knobs
2. **Existing clocks:** `last_activity`, `created_at`, `expires_at`, JWT `exp`/`iat`
   — extend; do not dual-write a second scheme
3. **Store TTL:** Redis `EXPIRE`, DB cleanup, signed-cookie expiry — absolute
   must not exceed store retention
4. **Product / compliance:** finance, admin vs consumer baselines in ADRs
5. **Cookie attributes:** keep timeout policy consistent with existing
   `Max-Age`/`Secure`/`HttpOnly`/`SameSite`
6. **SSO / IdP:** document stricter of app vs IdP idle/absolute bounds
7. **Neighboring apps:** match org defaults when monorepo already standardizes

**Precedence:** Follow the repo on conflict. Surface cookie Max-Age vs server
absolute mismatch, or client-only logout enforcement.

## Workflow

1. **Define both clocks (server-enforced).**

   | Clock | Meaning | Resets on activity? | Role |
   | --- | --- | --- | --- |
   | **Idle** | Max since last authenticated activity | Yes (sliding) | Limit abandoned-browser risk |
   | **Absolute** | Max since session creation / full login | **No** | Cap theft / shared-device window |

   Client timers are UX only; never the sole control.

2. **Pick values from risk tier.**

   | Surface | Idle (start) | Absolute (start) | Notes |
   | --- | --- | --- | --- |
   | High-risk admin / finance | 5–15 min | 1–8 h | Step-up for money/admin ops |
   | Standard web app | 15–30 min | 8–24 h | Common baseline |
   | Low-risk content | 30–60 min | 24 h–7 d | Absolute still finite |
   | Remember-me / refresh | Separate token | Days–weeks | Revocable; not immortal SID |

3. **Sliding renewal.**
   - On activity (or throttled heartbeat), update `last_activity` only if still
     under absolute and session is valid
   - Reject when idle exceeded **or** absolute exceeded
   - Throttle store writes (e.g. renew at most every N minutes)
   - Activity must **not** extend absolute expiry
   - Optional SID regenerate on privilege gain; timeout policy still applies

4. **Align cookie, store, and tokens.**
   - Store TTL ≥ absolute; cleanup after idle death
   - Cookie `Max-Age` must not promise longer life than absolute (or use session
     cookie + server clocks)
   - Access JWT short `exp`; refresh/remember: absolute + rotation
     (`jwt-refresh-token-patterns`); idle may apply at refresh
   - Logout / revoke-all deletes server state immediately

5. **Step-up and UX.**
   - High-risk actions (password change, payout, key mint): recent re-auth
     window, independent of idle
   - Optional warn before idle; “Stay signed in” = activity ping if under absolute
   - On expiry: clear client state; safe return URL; stable `session_expired` code
   - Multi-tab sharing one SID is expected; multi-device needs per-session rows

6. **Verify.** Tests: idle expire; activity renews idle; activity does not pass
   absolute; logout kills early. Metrics: `expired_idle`, `expired_absolute`.
   Implement with `code-quality-standards` (atomic check, no SID in logs).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Idle/absolute policy, sliding renewal, TTL align | **This skill** | — |
| Theft: flags, binding, rotation, revoke-all | `session-cookie-theft-defense` | this for lifetimes |
| Cookie attribute audit | `cookie-security-flags` | this for Max-Age |
| Fixation / regenerate-on-login | `session-fixation-management` | — |
| JWT refresh TTLs / reuse detection | `jwt-refresh-token-patterns` | this for idle-at-refresh |
| Middleware, clocks, tests, logging | `code-quality-standards` | **always** on code |

### Routing to `session-cookie-theft-defense`

Keep **this skill primary** for dual-clock policy and numeric lifetimes. Use
**`session-cookie-theft-defense`** for theft resistance: cookie flags,
host-only/`__Host-`, SID rotation, binding, revoke-all. Feed idle/absolute
values into that skill’s theft-window controls.

### Routing to `code-quality-standards`

Always apply **`code-quality-standards`** when implementing timeouts:
authoritative server checks (not SPA-only); atomic `last_activity` updates;
hash SIDs in logs/metrics; tests for idle, absolute, renewal throttle, logout;
clear non-enumerating expiry errors.

## Output Checklist

- [ ] Repo session stack, store TTL, activity/expiry fields inventoried
- [ ] Idle and absolute timeouts documented (per role/tier; absolute finite)
- [ ] Sliding renewal: activity definition, write throttle, absolute not extended
- [ ] Server enforces both clocks; client timers labeled UX-only
- [ ] Cookie Max-Age / store TTL / refresh bounds aligned
- [ ] Remember-me/refresh separated from short interactive SID
- [ ] Step-up re-auth window for high-risk actions defined
- [ ] Expiry UX: optional warn, hard fail, stable code, safe return URL
- [ ] Tests + metrics for idle vs absolute expiry reasons
- [ ] `session-cookie-theft-defense` when hardening theft surface
- [ ] `code-quality-standards` for implementation, atomicity, logging

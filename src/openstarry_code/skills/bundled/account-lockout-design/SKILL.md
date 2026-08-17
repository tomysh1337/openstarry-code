---
name: account-lockout-design
description: >
  Design account lockout and progressive auth-failure controls: attempt counters,
  lock duration, dual keys (account + IP), unlock paths, enumeration-safe UX, and
  lockout vs soft rate limits. Use when login lockout policy, failed-attempt
  thresholds, temporary ban after N passwords, progressive delay, or lockout vs
  rate-limit design for owned applications.
---

# Account Lockout Design

Design **auth failure lockout**: when failed logins/OTP verifies hard-stop an
identity, for how long, how to unlock, and how this differs from soft API rate
limits. Prefer the repo’s IdP, auth middleware, and security ADRs over a second
ad-hoc counter store.

## Scope And Authorization

- Design/implement on systems you **own** or are contracted to change.
- Adversarial keying validation (XFF, path aliases, multi-egress) →
  `rate-limit-bypass-testing` under explicit authorization only.
- Do not lock third-party accounts or run production stuffing. Redact identifiers
  in docs. Password composition/history → `password-policy-design`; this skill
  owns **failure budgets and lock state**.

## When To Use

- Thresholds, lock duration, progressive delay, or CAPTCHA/MFA step-up after fails
- Account- vs IP- vs dual-key lockout for login, OTP, or reset-token redeem
- Unlock paths (time, self-service, admin) without enabling ATO
- Separating **hard lockout** from soft **`429` rate limits**
- Mentions: account lockout, failed login lock, temporary ban, progressive delay,
  账户锁定, 登录失败锁定, brute-force protection, lock vs rate limit

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Soft API quotas / `429` / token-bucket design | `api-rate-limit-design` |
| Authorized bypass / key-split testing | `rate-limit-bypass-testing` |
| Password length, complexity, history, breach lists | `password-policy-design` |
| MFA protocol bugs beyond attempt budgets | `mfa-bypass-methodology` |
| Multi-vector ATO chaining | `account-takeover-methodology` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Repo auth stack and ADRs **outrank** defaults below.

1. **Existing controls:** IdP lockout, framework throttles, Redis fail counters, WAF — configure before inventing a parallel store
2. **Identity normalization:** email case-fold, phone E.164 — same form as login lookup
3. **Trusted client IP:** LB/edge hop only; never sole key on client `X-Forwarded-For`
4. **Related surfaces:** OTP verify, reset redeem, “old password” change — inventory counters
5. **Observability:** lockout metrics, admin unlock audit, mass-lock alerts
6. **Org IdP / neighbors:** align thresholds and unlock SLAs
7. **Config/flags:** dynamic thresholds vs hard-coded constants

**Precedence:** Follow the repo. Flag IP-only password lockout, non-atomic counters,
or “user locked” vs “no such user” oracles beyond intentional threat-model trade-offs.

## Workflow

1. **Lockout vs rate limit (decide per surface).**

   | Dimension | Account lockout | Soft rate limit |
   | --- | --- | --- |
   | Target | Secret-guess on a principal | Request volume / cost |
   | Effect | Auth blocked until unlock/expiry | `429` + `Retry-After` |
   | Keying | Normalized account (+ IP ceiling) | IP, user, API key, route |
   | Abuse | Online password/OTP guess, stuffing | Scraping, quota burn |

   Auth usually needs **both**: dual-key soft limits **and** account-scoped fail policy.

2. **Inventory surfaces.** Login password, OTP/MFA, reset/magic-link redeem, password-change-with-old — each needs a fail budget. Signup: soft limits + CAPTCHA; avoid long locks on non-existent users.

3. **Choose keys.** Primary: `hash(normalized_id)`. Secondary: trusted IP (optional device/session). Composite: trip when **either** budget hits. Count **failed authentications** only; TTL keys; no unbounded keys from raw headers.

4. **Thresholds (starting bands — tune to risk).** Password: delay after ~3–5 fails; hard lock ~5–10 / 15–60 min window. OTP (short codes): 3–5 then invalidate/resend. Prefer time-box + CAPTCHA over permanent lock; permanent only for high-risk with clear unlock.

5. **Unlock.** Time-based auto-unlock; self-service via proof-of-control (not only the failed password); audited admin unlock (dual-control for privileged roles). Successful verified auth **atomically** clears fail counters. Unlock tokens need their own budgets.

6. **UX.** Prefer generic “Invalid credentials” while applying delay/lock. If “temporarily locked” is required, match timing/shape for unknowns where feasible, or document enumeration trade-off. Avoid remaining-attempt oracles. Document legit recovery for support.

7. **Placement.** Enforce in authoritative auth/IdP; normalize path aliases into one bucket; atomic `INCR`/row lock. Document fail-open vs fail-closed if counter store is down (auth often fail-closed or CAPTCHA + strict IP). Metrics: lockouts/hour, hashed top keys, mass-lock alerts.

## Good / Bad

| Topic | Good | Bad |
| --- | --- | --- |
| Keying | Dual: normalized account + trusted IP | IP-only login lock (egress rotation) |
| Counters | Atomic fail count; clear on proven success | TOCTOU read-modify-write |
| Thresholds | Progressive delay before hard lock; tighter OTP | Permanent lock after 3 fails, no unlock |
| Unlock | Time-box + audited admin + proof-of-control | Support unlock by email only, no audit |
| UX | Stable generic errors | Timing/message oracle locked vs missing user |
| vs rate limit | Soft 429 for volume; lockout for secret budget | Only global QPS, no account fail budget |
| IP trust | Edge-overwrite client IP | Sole key on client `X-Forwarded-For` |
| Aliases | One bucket for all login URL variants | Split counters per path casing/version |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Lockout thresholds, keys, unlock, lock vs rate-limit split | **This skill** | — |
| Soft API quota / 429 product design | `api-rate-limit-design` | this for auth hard-stop |
| Authorized bypass / key-split testing | `rate-limit-bypass-testing` | this for intended policy |
| Password strength, history, breach check | `password-policy-design` | this for fail budgets |
| CAPTCHA step-up after N fails | `captcha-bypass-research` | this for when to step up |
| MFA protocol flaws | `mfa-bypass-methodology` | this for verify N |
| ATO multi-vector | `account-takeover-methodology` | this if lockout is one gap |
| Implement counters, unlock, tests, logs | `code-quality-standards` | **always** on code |

- **`rate-limit-bypass-testing`:** switch when proving budgets expand via headers, aliases, methods, or multi-egress; feed findings into dual-keying.
- **`password-policy-design`:** composition/rotation/storage; this skill = how many wrong secrets and how long locked.
- **`code-quality-standards`:** atomic counters, bounded keys, outage behavior, no secrets in logs/labels, tests for threshold/concurrency/unlock/aliases, enumeration-conscious errors.

## Output Checklist

- [ ] Failure surfaces inventoried; lockout vs soft rate-limit roles documented
- [ ] Repo IdP/middleware/counter store and trusted-IP path inventoried
- [ ] Keys: normalized account + trusted IP (session/device if needed)
- [ ] Thresholds, windows, progressive delay, lock duration tunable and recorded
- [ ] Unlock paths (time / self-service / admin) audited where human
- [ ] Success clears counters atomically; path aliases share one bucket
- [ ] UX/enumeration trade-off and support recovery documented
- [ ] Metrics + mass-lock alerts; store-outage fail-open/closed decided
- [ ] Adversarial review via `rate-limit-bypass-testing` when in scope
- [ ] Password rules paired with `password-policy-design`
- [ ] `code-quality-standards` applied for implementation, tests, logging

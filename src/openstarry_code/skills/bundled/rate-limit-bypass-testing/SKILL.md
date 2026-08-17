---
name: rate-limit-bypass-testing
description: >-
  Authorized testing of HTTP rate limits and anti-automation: limit keying
  (IP, user, session, API key), header-based IP trust, path/method aliases,
  protocol quirks, and IP-rotation awareness. Use when login, OTP, reset,
  or API quotas should throttle abuse but may be skippable or mis-keyed.
---

# Rate Limit Bypass Testing (Authorized)

## Scope And Authorization

- Authorized apps, labs, CTFs, and program-scoped APIs **only**. Use test accounts, low parallelism; stop before shared infra degrades. Not a DoS skill.
- Cap bursts (tens to low hundreds per probe class unless load testing is approved). Coordinate before SMS/email/OTP gateways that cost money.
- Prefer reversible actions (failed login, search, resend to **your** sink). No residential rotating proxies on production without written approval.
- Redact API keys, sessions, and IP lists in public notes. **IP rotation awareness** = document per-IP budgets and authorized multi-egress/header effects — not botnet distribution.

## When To Use

- Login, password reset, MFA/OTP, invite, coupon, search, or expensive APIs should throttle after N attempts.
- Keywords: “rate limit bypass”, “OTP unlimited”, “API quota evasion”, “X-Forwarded-For rate limit”, missing lockout.
- You see `429` / `Retry-After` / captcha — or **no** throttle when expected.
- Goal is **auth/abuse-window** effectiveness, not pure performance SLOs. Pair with MFA/reset when the limit should block guessing.

## Workflow

1. **Inventory protected actions**  
   From `api-recon-and-docs` and proxy history:

   | Action | Examples | If unlimited |
   | --- | --- | --- |
   | Password login | `POST /login`, `/oauth/token` | Credential stuffing |
   | MFA verify | `POST /mfa/verify` | OTP online guess |
   | Reset / magic link | `POST /forgot-password` | Email flood / token grind |
   | OTP resend | `POST /mfa/resend` | SMS cost |
   | Signup / expensive API | register, search, export | Account factory / quota theft |

   Note auth state, captcha, documented quotas.

2. **Baseline the limit**  
   Single IP, single account, default headers: send identical failing (or cheap) requests; record first throttle (attempt #, status, body, `Retry-After`, `X-RateLimit-*`); wait for window reset; reconfirm N. No throttle after a safe ceiling → report **missing rate limit** with count and impact — still not DoS.

3. **Identify the limit key**  
   Change **one** dimension after throttle:

   | Dimension | Probe | Fresh budget means |
   | --- | --- | --- |
   | Account | Other test user, same IP | Key includes user |
   | Session / API key | New cookie/key | Session-keyed |
   | IP | Authorized second egress only | Per-IP (rotation relevant) |
   | Route / target | Alias path or other login field | Split buckets |

   Still blocked with new user ⇒ IP/global key. Fresh budget on new IP ⇒ pure per-IP.

4. **Proxy / client-IP headers**  
   From an already-throttled client, one header per test:

   ```http
   POST /login HTTP/1.1
   Host: target.example
   X-Forwarded-For: 203.0.113.10
   Content-Type: application/x-www-form-urlencoded

   user=test%40example&pass=wrong
   ```

   Also try: `X-Real-IP`, `True-Client-IP`, `CF-Connecting-IP`, `X-Client-IP`, `Forwarded: for=…`, `X-Originating-IP`. Prefer documentation-range IPs (`203.0.113.x`) so logs show the spoof. **Confirmed:** effective budget multiplies per spoofed value **and** the app still processes auth normally. Edge overwrite of XFF = safe; origin trusting raw client XFF = weak.

5. **Path, method, protocol aliases**  
   Same body/identity; vary `/Login`, `/login/`, `/api/v1|v2/login`, `/login.json`, `POST` vs `PUT`/method-override, in-scope Host, HTTP/1.1 vs HTTP/2. Low-volume only. Path tricks aimed at ACL skip (not quota) → `401-403-bypass-techniques`.

6. **IP rotation awareness (authorized)**  
   - IP-only login/OTP limits: each egress grants +N — recommend **account-level** lockout + progressive delay.  
   - If program allows ≥2 lab egress IPs, show each getting full N against **your** account.  
   - Dual-stack: test IPv4 and IPv6 once each if in scope. Do not POP-scan CDNs or run commercial rotating proxies unless explicitly permitted.

7. **Edge cases and races**  
   Missing vs invalid vs valid `Authorization` (three buckets?). GraphQL: limit per HTTP vs per `operationName`/cost. Batch endpoints: 1 request × N logical attempts. Parallel burst at window edge admitting >N → `race-condition` for counter atomicity.

8. **Bind impact**  
   Expanded password/OTP guess window; reset email/SMS flood; API cost/scraping. MFA story → `mfa-bypass-methodology`. Reset/token → `password-reset-poisoning`. Token endpoints → `api-auth-and-jwt-abuse`.

9. **Remediation** (with `code-quality-standards`)  
   Key auth limits by **normalized account and IP** (stricter of both); client IP only from trusted LB hop; strip inbound public XFF; one enforcement point after path normalization; atomic counters (e.g. Redis `INCR`+TTL); progressive delay/captcha/hard lockout for login/MFA; cost-based GraphQL/batch limits; `Retry-After` + redacted logs.

## Routing

| Need | Skill |
| --- | --- |
| MFA/OTP logic beyond attempt budget | `mfa-bypass-methodology` |
| Password-reset / magic-link Host or token | `password-reset-poisoning` |
| Token endpoint / API auth surface | `api-auth-and-jwt-abuse` |
| Parallel >N counter TOCTOU | `race-condition` |
| 401/403 path ACL bypass (not quota) | `401-403-bypass-techniques` |
| Endpoint map | `api-recon-and-docs` |
| Implement throttles and IP trust | `code-quality-standards` |

## Output Checklist

- [ ] Endpoint(s), abuse case, auth context
- [ ] Baseline N, window, status/headers, reset
- [ ] Keying: IP / user / session / route
- [ ] Header trust probes and outcomes
- [ ] Alias path/method/protocol results
- [ ] Authorized multi-IP / dual-stack (rotation) notes
- [ ] Effective budget after bypass vs baseline
- [ ] Security impact; remediation (dual key, trusted IP, atomic counters)

## Rules

- Authorized targets only; volume measures N — does not degrade service.
- One variable per probe class; report the minimal successful set.
- Header spoof tests **trust config**; not a license for third-party abuse.
- No unapproved rotating proxy farms or prod credential-stuffing wordlists.
- Missing captcha alone is not high severity without expanded guess/cost impact.
- Redact secrets; stop on shared-user lockout risk; authorized assessment only.

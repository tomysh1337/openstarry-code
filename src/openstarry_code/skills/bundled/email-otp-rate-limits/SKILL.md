---
name: email-otp-rate-limits
description: >
  Design and review rate limits for email one-time passwords (OTP): send/resend
  cooldowns, per-destination and dual keys, verify attempt budgets, enumeration-safe
  UX, and mail-provider cost controls. Use when email OTP throttle, resend cooldown,
  magic-code send limits, inbox flood prevention, verify N for email OTP, or
  邮箱验证码限流 / OTP 发送频率 design on owned apps.
---

# Email OTP Rate Limits

Control **how often email OTPs may be issued and guessed**: send/resend budgets,
per-address and IP/account keys, verify attempt caps, stable UX, and mail-provider
cost protection. Prefer the repo’s auth/IdP OTP stack and security ADRs over a
second ad-hoc counter store.

## When To Use

- Send, resend, and cooldown policy for email OTP / magic codes / email step-up
- Dual keying: normalized destination email **and** trusted IP (or account id)
- Verify-side attempt budgets separate from send budgets
- Enumeration-safe responses when the address is unknown or locked
- Cost and abuse controls against inbox flood, signup spam, and provider rate caps
- Mentions: email OTP rate limit, resend cooldown, 邮箱验证码, magic code throttle,
  OTP send frequency, verify attempts email, mail bombing prevention

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Generic API quota / product `429` design | `api-rate-limit-design` |
| Hard account lockout after failed secrets | `account-lockout-design` |
| Authorized key-split / bypass testing | `rate-limit-bypass-testing` |
| MFA protocol / ATO chaining | `mfa-bypass-methodology` / `account-takeover-methodology` |
| Password-reset Host/token poisoning | `password-reset-poisoning` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

1. **Separate send vs verify budgets.**

   | Control | Protects | Typical effect |
   | --- | --- | --- |
   | Send / resend limit | Inbox flood, $ mail cost, provider bans | Cooldown + daily cap; `429` / soft deny |
   | Verify attempt limit | Online code guessing | Short N then invalidate code / delay / lock |
   | Account / IP ceiling | Multi-target spray, multi-egress | Composite trip when either key hits |

   Never treat “HTTP QPS on `/otp/send`” as enough: attacker can slow-drip many
   destinations. Always key **destination** (and often initiator account).

2. **Inventory surfaces.** Signup email verify, login OTP, step-up MFA, change-email
   confirm, passwordless magic code, “resend code” UI, admin-triggered resend.
   Each path must share **one normalized bucket** per purpose (or document why not).

3. **Normalize and key.**
   - Destination: case-fold + trim; apply same rules as login identity (plus-tag
     policy is product-specific—document if `a+x@` shares or splits budgets)
   - Keys: `hash(normalized_email)` primary for send; **and** trusted client IP;
     after auth, also `account_id` for “resend from session”
   - Trusted IP from edge/LB hop only; never sole key on client `X-Forwarded-For`
   - Atomic counters with TTL; no unbounded keys from raw headers or free-text

4. **Starting send bands (tune to risk and provider).**
   - Cooldown between sends to same address: ~30–120s (UX + anti-spam)
   - Per address / hour: low single digits to ~10; per day: tens, not hundreds
   - Per IP / hour: cap mass multi-target signup and spray
   - Per account (change-email / step-up): stricter than anonymous signup if abused
   - Invalidate prior code on successful resend (one active code) unless product
     requires multi-device; always cap concurrent valid codes

5. **Verify bands.** Short numeric codes need **tight** verify N (often 3–5) then
   invalidate or force resend; progressive delay before hard stop. Pair hard lock
   semantics with `account-lockout-design`. Do not reveal remaining attempts if
   that aids guessing; prefer generic failure + delay.

6. **Code lifecycle.** Entropy adequate for online-guess model under your verify
   budget; short TTL (e.g. 5–15 min); single-use; bind purpose and subject
   (signup vs login vs change-email). Store hashes of codes, not plaintext, when
   feasible. Clear send **and** verify counters on definitive success where safe.

7. **UX and enumeration.** Same response shape/timing for unknown vs known email
   on send where threat model requires anti-enum; still enforce destination and IP
   budgets server-side (silent no-op still consumes budget carefully—document).
   Avoid “user not found” only on OTP paths if login is already generic.
   `Retry-After` / cooldown copy for humans; stable machine error codes.

8. **Placement and resilience.** Enforce in authoritative auth service (not only
   client disable of Resend). Path aliases share one bucket. Decide fail-open vs
   fail-closed if counter store is down (auth/OTP often fail-closed or CAPTCHA +
   strict IP). Metrics: sends/dest (hashed), 429 ratio, verify fails, provider
   errors; alert on mass multi-dest spikes. CAPTCHA step-up after burn → pair
   `captcha-bypass-research` for challenge design.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Email OTP send/resend/verify rate policy | **This skill** | — |
| Soft API quotas outside OTP | `api-rate-limit-design` | this for mail OTP |
| Hard lockout after failed verifies | `account-lockout-design` | this for send side |
| Authorized bypass of keys/cooldowns | `rate-limit-bypass-testing` | this for intended policy |
| CAPTCHA after send/verify burn | `captcha-bypass-research` | this for when to step up |
| Reset link Host/token issues | `password-reset-poisoning` | this if codes emailed |
| MFA protocol bugs | `mfa-bypass-methodology` | this for attempt budgets |
| ATO chaining including OTP gaps | `account-takeover-methodology` | this for rate posture |
| Implement counters, tests, logs | `code-quality-standards` | **always** on code |

- **`api-rate-limit-design`:** general 429 catalog; this skill owns email OTP send/verify dual budgets.
- **`account-lockout-design`:** hard-stop after failed verifies; keep send cooldowns here.
- **`rate-limit-bypass-testing`:** prove cooldowns expand via XFF, aliases, multi-egress.
- **`code-quality-standards`:** atomic TTL counters, no codes in logs, threshold/alias tests.

## Output Checklist

- [ ] OTP surfaces inventoried (signup, login, step-up, change-email, resend)
- [ ] Send vs verify budgets documented separately with windows and effects
- [ ] Keys: normalized email + trusted IP (+ account where authenticated)
- [ ] Cooldown, hourly/daily caps, and concurrent active-code policy set
- [ ] Verify N, progressive delay, invalidate-on-exhaust documented
- [ ] Code TTL, single-use, purpose binding, hash-at-rest as applicable
- [ ] Enumeration UX trade-off and stable error/`Retry-After` documented
- [ ] Path aliases share buckets; edge IP trust path recorded
- [ ] Counter-store outage fail-open/closed decided; metrics and flood alerts
- [ ] Provider limits/cost considered; CAPTCHA step-up planned if needed
- [ ] Adversarial review via `rate-limit-bypass-testing` when in scope
- [ ] `code-quality-standards` applied for implementation, tests, logging

## Scope And Authorization

- Design and implement on systems you **own** or are contracted to change.
- Do not flood third-party inboxes, shared providers, or production users.
  Validate in lab/staging with owned addresses and synthetic traffic.
- Adversarial keying/cooldown bypass → `rate-limit-bypass-testing` only under
  explicit authorization and attempt budgets.
- Redact email addresses, OTPs, session ids, and provider API keys in reports.
- Do not copy SMS budgets blindly onto email (cost/regulatory differ). Live ATO
  against non-owned accounts is out of scope.

---
name: sms-otp-risk-controls
description: >
  Design and harden SMS one-time password (OTP) risk controls: send/resend
  budgets, verify attempt limits, code entropy and TTL, purpose binding, and
  abuse-resistant UX. Use when login, signup, step-up, or recovery relies on
  SMS OTP and you need send-flood, brute-force, enumeration, and binding
  controls for owned applications or authorized remediation.
---

# SMS OTP Risk Controls

Engineering controls for **SMS-delivered OTPs**: when to send, how often, how
codes are generated and bound, how verification fails safely, and how residual
carrier/SIM risk is documented. Prefer stronger factors (WebAuthn, TOTP) where
product allows; when SMS is required, make it hard to flood, guess, or reuse.

## Scope And Authorization

- Design/implement on systems you **own** or are contracted to change.
- Authorized assessment only: dual test accounts you control; never trigger SMS
  or complete OTP for third parties; cap volume (cost and lockout risk).
- Do not perform SIM-swap, SS7, or carrier fraud research against real users.
- Redact phone numbers (partial mask), full OTPs, and session tokens in reports.
- Adversarial rate-limit expansion → `rate-limit-bypass-testing`. MFA skip /
  client-trust flaws → `mfa-bypass-methodology`. Soft API quotas →
  `api-rate-limit-design`. Hard lockout thresholds → `account-lockout-design`.

## When To Use

- Login, signup, password reset, step-up, device confirm, or phone-change uses
  SMS (or voice) OTP as a factor or sole proof
- SMS bombing / resend abuse, verify brute-force, or code reuse is in scope
- Choosing code length, TTL, single-use, purpose binding, and cooldown policy
- Mentions: SMS OTP, text verification code, 短信验证码, OTP flood, resend
  limit, phone verify, 2FA SMS, voice OTP fallback

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authenticator-app TOTP (RFC 6238) | `totp-mfa-implementation` |
| MFA skip, remember-device, step-up gaps | `mfa-bypass-methodology` |
| Soft HTTP quotas / `429` product design | `api-rate-limit-design` |
| Hard account lock after N fails | `account-lockout-design` |
| Multi-vector ATO chaining | `account-takeover-methodology` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

1. **Classify the SMS surface.**

   | Flow | Risk if weak | Control focus |
   | --- | --- | --- |
   | Login / step-up MFA | Online code guess, session elevate | Verify budget, binding, elev only after success |
   | Signup / phone verify | Enumerate phones, SMS cost bomb | Send budget, generic UX |
   | Reset / recover | ATO if code weak or unbound | Tighter TTL, purpose bind, notify |
   | Phone change | Swap to attacker MSISDN | Step-up + old-channel confirm |
   | Resend / voice fallback | Cost amplification | Cooldown + shared send budget |

2. **Normalize and bind identity.** Store phones in **E.164**. Bind each challenge
   to `user_id` (or pending signup id), **normalized MSISDN**, **purpose**
   (`login` \| `signup` \| `reset` \| `step_up` \| `phone_change`), and short
   **TTL**. Reject codes for wrong purpose or expired challenges. Prefer opaque
   `challenge_id` over accepting raw phone+code alone on privileged paths.

3. **Generate codes securely.**

   | Property | Recommended default |
   | --- | --- |
   | Entropy | CSPRNG; ≥6 digits (prefer 6–8); avoid sequential/predictable |
   | Storage | Hash at rest (or encrypt); never log plaintext OTP |
   | Lifetime | Short TTL (e.g. 5–10 min); one active challenge per purpose |
   | Use | Single-use; invalidate on success **and** on superseding resend |
   | Compare | Constant-time; fixed failure shape |

4. **Send / resend budgets (cost and harassment).** Dual-key: per destination
   MSISDN **and** per account/session **and** trusted IP ceiling. Cooldown
   between sends (e.g. 30–60s); daily/hourly caps per MSISDN and per initiator.
   Resend and voice share the same budget class. Provider webhooks: verify
   signatures; do not expose full OTP in callbacks or admin UIs.

5. **Verify budgets (online guessing).** Short codes need **strict** attempt
   limits (e.g. 3–5) then invalidate challenge and require resend; progressive
   delay; dual key account + IP. Atomic counters. Align hard lockout with
   `account-lockout-design`; soft volume with `api-rate-limit-design`.

6. **UX and enumeration.** Prefer generic “If eligible, a code was sent” and
   stable timing for known vs unknown phones where product allows. Do not return
   remaining attempts or “code was X digits.” Support paths must not reveal OTP.

7. **Session and elevation.** Issue or upgrade session **only** after server-side
   success; rotate session id at factor-2. Never trust client flags
   (`otp_ok`, `sms_verified`). Step-up again for phone change, disable MFA, and
   high-risk actions. Residual SIM-swap / SMS intercept: document; prefer TOTP /
   WebAuthn for high-value accounts.

8. **Tests and ops (`code-quality-standards`).** Unit/integration: expiry, reuse,
   wrong purpose, attempt lockout, resend invalidates old code, E.164 bucketing,
   no OTP in logs/metrics. Alerts: send spike per route, verify fail spike,
   provider error rate. Fail-closed or CAPTCHA when counter store is down on
   auth paths.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SMS/voice OTP send, verify, bind, TTL, flood controls | **This skill** | — |
| Authenticator TOTP enroll/verify | `totp-mfa-implementation` | this if SMS fallback exists |
| MFA skip / remember-device / client flag trust | `mfa-bypass-methodology` | this for OTP budgets |
| Soft API 429 / quota design | `api-rate-limit-design` | this for SMS cost keys |
| Hard lockout thresholds / unlock | `account-lockout-design` | this for OTP-specific N |
| Authorized limit key-split testing | `rate-limit-bypass-testing` | this for intended policy |
| CAPTCHA after send/verify abuse | `captcha-bypass-research` | this for when to step up |
| ATO multi-vector | `account-takeover-methodology` | this if SMS OTP is one gap |
| Implement services, tests, redaction | `code-quality-standards` | **always** on code |

- **`totp-mfa-implementation`:** app-based codes; keep this skill for SMS channel
  risk and provider/cost controls.
- **`mfa-bypass-methodology`:** switch when the bug is skippable second factor,
  not merely missing send caps.
- **`code-quality-standards`:** hashed/encrypted codes, atomic counters, no
  secrets in logs, tests for TTL/reuse/purpose/concurrency.

## Output Checklist

- [ ] SMS/voice surfaces and purposes inventoried (login, signup, reset, step-up)
- [ ] E.164 normalization; challenge bound to user + purpose + TTL
- [ ] Code entropy, hash-at-rest, single-use, resend invalidation documented
- [ ] Send/resend/voice budgets: MSISDN + account/session + trusted IP; cooldowns
- [ ] Verify attempt limits, progressive delay, atomic counters, invalidate-on-N
- [ ] Generic UX / enumeration trade-off; no OTP or remaining-attempt oracles
- [ ] Session elevate only after server verify; SID rotation at factor-2
- [ ] Residual SIM/SMS intercept risk noted; stronger factor recommended where needed
- [ ] Provider callback auth; redaction in logs, metrics, support tools
- [ ] Tests + alerts; store-outage behavior; `code-quality-standards` on code
- [ ] Neighbors routed: TOTP / MFA bypass / rate-limit / lockout as applicable

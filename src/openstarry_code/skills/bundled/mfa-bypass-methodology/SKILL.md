---
name: mfa-bypass-methodology
description: >-
  Authorized methodology for testing multi-factor authentication weaknesses:
  backup codes, remember-device, race on attempt counters, step-up gaps, and
  high-level response/status manipulation. Use when login, step-up, or recovery
  flows claim MFA is enforced but second-factor checks may be skippable, reusable,
  or weakly bound to the session.
---

# MFA Bypass Methodology (Authorized)

## Scope And Authorization

- Authorized apps, labs, CTFs, and program-scoped accounts **only**. Dual test users you control; never complete MFA for third parties or phish real OTP.
- Cap OTP brute; avoid lockouts on shared prod accounts. SMS/voice cost only with explicit approval.
- Redact OTP, backup codes, recovery secrets, and session cookies in public notes; store raw captures offline.
- **Response manipulation** = client-visible JSON/status/UI that the **server** fails to re-enforce — not carrier fraud or offline TOTP crypto breaks.

## When To Use

- Login, password change, transfer, or admin action requires TOTP, SMS, email OTP, push, WebAuthn, or backup codes.
- “Remember device”, trust cookies, or `mfa_verified` flags appear after factor-1.
- Recovery / backup-code / resend flows may be weaker than primary MFA.
- Keywords: “MFA bypass”, “2FA skip”, “OTP brute”, “backup code reuse”, “step-up missing”, “MFA race”.
- Primary when the gap is **second-factor enforcement**, not pure JWT forgery or password spray.

## Workflow

1. **Map MFA surfaces**  
   From proxy/UI record: enroll/disable; login step-2 path and fields (`otp`, `code`, `token`); resend behavior; backup-code format; remember-device cookie name/TTL/binding; which actions step-up; recovery (“lost phone”, email link). Use `api-recon-and-docs` if SPA/mobile differs. Reset links that mint sessions → `password-reset-poisoning` / `session-fixation-management`.

2. **Baseline honest MFA**  
   Clean browser, user A: complete password/SSO → capture pending session; submit valid OTP → capture privileged session. Note SID rotation at factor-1 vs factor-2. Record success/fail status and body shapes as oracles. Sequential wrong OTP should increment counters.

3. **Skip / incomplete-flow**  
   After factor-1 **without** OTP, call privileged APIs and deep links:

   ```http
   GET /api/me HTTP/1.1
   Host: target.example
   Cookie: session=<post_password_only>
   ```

   Also: `/app/home`, `/api/session/upgrade`, OAuth callback then API before MFA page, mobile paths omitting `mfa_token`. **Confirmed** if canary PII or state-changing success returns.

4. **High-level response / client-trust manipulation**  
   Intercept verify-OTP (and MFA status polls). Do not invent crypto. Flip client-visible signals and continue:

   | Probe | Action |
   | --- | --- |
   | Status | `401`→`200` / `false`→`true` on verify response |
   | Body flags | `mfa_passed` / `verified` / `success` |
   | Drop challenge | Remove `mfa_required` from login JSON; hit home API |
   | Token reuse | Replay old `mfa_ok` / step-up token on new login |

   **Bypass** only if later privileged requests succeed **without** a valid server post-MFA credential. SPA unlock + API 403 = defense-in-depth note, not full MFA bypass.

5. **Backup codes and recovery**  
   On **your** account: sample entropy/format (no mass guess); redeem once then reuse; try A’s code on B’s pending MFA; re-download codes without step-up; compare “disable MFA” email link strength to primary OTP; if in scope, whether factor-1 alone removes MFA. Weak email disable may chain `password-reset-poisoning`.

6. **OTP limits, race, rate limit**  
   Sequential wrong codes → lockout after N, key (IP/account/session), code validity after resend. Non-atomic counter or double-accept of one code → `race-condition`. Header/IP budget expand → `rate-limit-bypass-testing` helper; prove impact (session/OTP accept) here. Lab sinks only for SMS.

7. **Remember-device and binding**  
   Capture trust token `D`. Copy to second browser; use on user B; change IP/UA only; logout/password-change should revoke. JWT `amr`/`acr` client-asserted MFA level → `api-auth-and-jwt-abuse`.

8. **Step-up and lifecycle**  
   Fully MFA’d session: password change, disable MFA, add payee, export, OAuth grant **without** fresh MFA — server must re-challenge. Disable-MFA demands current factor. After reset, re-enroll/re-MFA per policy.

9. **Remediation** (implement with `code-quality-standards`)  
   Enforce MFA server-side on every privileged route; bind OTP/backup to `user_id`+challenge+purpose+TTL; single-use; constant-time compare; atomic attempt counters (account+IP); elevate session only after factor-2; hash backup codes; revocable remember-device tokens; step-up on privilege change; notify on disable/new device.

## Routing

| Need | Skill |
| --- | --- |
| JWT `amr`/`acr`, Bearer step-up, API auth | `api-auth-and-jwt-abuse` |
| Reset/magic-link Host or token poisoning | `password-reset-poisoning` |
| Parallel OTP accept / attempt-counter TOCTOU | `race-condition` |
| Expanding HTTP rate limits (headers, IP) | `rate-limit-bypass-testing` |
| SID not rotated after full login/MFA | `session-fixation-management` |
| OAuth MFA / IdP `acr_values` | `oauth-oidc-misconfiguration` |
| Secure MFA/session implementation | `code-quality-standards` |

## Output Checklist

- [ ] MFA types (TOTP/SMS/email/push/WebAuthn/backup) and enroll path
- [ ] Factor-1-only access results (endpoint, status, canary)
- [ ] Client response manipulation vs true server enforcement
- [ ] Backup/recovery: reuse, binding, disable-without-factor
- [ ] Attempt limits, race/parallel, lockout keying
- [ ] Remember-device portability/binding; step-up coverage
- [ ] Impact with dual test accounts only; remediation list

## Rules

- Authorized dual-account tests only; no third-party OTP interception or SIM abuse.
- Client flag flips count only when the **server** grants privilege without factor-2.
- Cap OTP guessing; prefer logic flaws over brute as the primary narrative.
- Do not relabel password spray, session theft, or pure JWT forgery as MFA bypass.
- One clean privileged canary after skip beats long theoretical OTP-space notes.
- Redact codes/sessions; authorized assessment only.

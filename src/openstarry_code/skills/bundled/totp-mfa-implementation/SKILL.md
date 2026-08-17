---
name: totp-mfa-implementation
description: >-
  Implement and harden RFC 6238 TOTP multi-factor authentication: secret
  generation, otpauth enrollment, verify windows, attempt limits, backup codes,
  and session elevation. Use when building or reviewing authenticator-app 2FA
  (enroll QR, verify code, disable/replace factor) for owned apps or authorized
  remediation work.
---

# TOTP MFA Implementation

Server-side **TOTP (RFC 6238)** second factor: CSPRNG secrets, confirmed enrollment,
time-window verify, rate limits, backup codes, and privileged-session elevation only
after a valid code. Pair implementation with `code-quality-standards`.

## When To Use

| Situation | Direction |
| --- | --- |
| Add or fix authenticator-app TOTP (Google/Authy/etc.) | **This skill** (primary) |
| Design enroll QR / `otpauth://`, verify, disable, recovery codes | **This skill** |
| Review secret storage, window, replay, constant-time compare | **This skill** |
| Test incomplete enroll / optional MFA / disable without step-up | `mfa-enrollment-flaws` |
| Test login skip, backup reuse, remember-device, step-up gaps | `mfa-bypass-methodology` |
| SMS/email OTP only (no TOTP secret) | Other channel skill; reuse limits/binding ideas |
| Live attacks on third-party accounts | **Do not** — authorized/owned only |

Keywords: TOTP, RFC 6238, otpauth, QR enroll, authenticator MFA, HOTP counter, backup codes, step-up.

## Workflow

### 1. Parameters and crypto baseline

| Parameter | Recommended default |
| --- | --- |
| Algorithm | HMAC-SHA1 (interop) or SHA-256; pin one server-side |
| Digits | 6 (or 8 for high-assurance) |
| Period | 30 seconds |
| Secret | ≥160 bits; base32 for `otpauth`; CSPRNG only |
| Verify window | ±1 step max (±30–60s); never large “skew forgive” |

Use a maintained library (e.g. `otplib`, `pyotp`, `otp` crates) — do not hand-roll HMAC truncation.

### 2. Enrollment (pending → confirmed)

1. Authenticated user starts enroll → generate secret; store **pending** (encrypted/KMS or app-key AEAD), not yet `mfa_enabled`.
2. Return `otpauth://totp/{issuer}:{account}?secret=...&issuer=...&algorithm=...&digits=6&period=30` (or QR of that URI). Never log full secret/URI.
3. Require **two consecutive valid codes** (or one code + proof of possession policy) before marking factor active.
4. Issue **hashed** backup codes only after confirm; show once; notify on enroll.
5. Incomplete enroll must not elevate session or set client-trusted `mfa_enrolled=true`. Enrollment policy gaps → `mfa-enrollment-flaws`.

### 3. Verify and elevate

```text
code_ok = constant_time_eq(submitted, totp(secret, t-1|t|t+1))
// reject if code matches last accepted step for this user (replay)
// then: attempts++, lockout/backoff; on success: clear pending MFA, elevate session
```

- Bind challenge to `user_id`, purpose (`login` | `step_up` | `disable`), and short TTL.
- Elevate **server** session/token only after success; rotate session id at factor-2.
- Do not trust body flags (`mfa_passed`) or client JWT `amr` alone for privilege.
- Step-up again for disable MFA, add factor, password change, high-risk actions.

### 4. Limits, recovery, storage

| Control | Secure behavior |
| --- | --- |
| Attempts | Per account (+ IP); lock or exponential backoff; atomic counter |
| Backup codes | High entropy; hash at rest (like passwords); single-use; regenerate invalidates old |
| Remember device | Opaque revocable token; bind user+device; short absolute TTL; not a forever MFA skip |
| Secrets at rest | Encrypt; least-privilege access; never in logs/metrics/URLs |
| Disable/replace | Current TOTP or backup + re-auth; notify email |

Login/recovery logic flaws and attempt races → assess with `mfa-bypass-methodology` / `race-condition`.

### 5. Tests (`code-quality-standards`)

- Valid code within window accepts; outside rejects.
- Replay same step rejected; wrong user secret rejected.
- Pending enroll without confirm → privileged API denied.
- N wrong codes → lockout; backup single-use; disable requires factor.
- Constant-time path on compare; no secret in error messages.

## Good / Bad

| Topic | Good | Bad |
| --- | --- | --- |
| Secret | CSPRNG ≥160-bit; encrypt at rest | `uuid`, timestamp, or predictable seed |
| Enroll | Pending until verify; then enable | Enable on QR display; skip forever |
| Window | ±1 step | ±10 steps “for UX” |
| Compare | Constant-time | Early `==` / string equals that leaks |
| Replay | Track last successful timestep | Accept any code in window forever |
| Backup | Hashed, one-time | Plaintext list; reusable forever |
| Session | Server elevates after factor-2 | Client sets `mfa: true` in localStorage |
| Disable | Step-up with current factor | Password-only DELETE factor |
| Logs | Redact secret, code, otpauth | Log full QR payload or OTP |
| Library | Maintained TOTP + tests | Custom HMAC “almost RFC” |

## Routing

| Need | Skill |
| --- | --- |
| Build/harden TOTP enroll–verify–disable | **This skill** |
| Enrollment skip, optional MFA, bind/disable flaws | `mfa-enrollment-flaws` |
| Login skip, backup reuse, remember-device, step-up | `mfa-bypass-methodology` |
| Reliability, secrets hygiene, tests, secure coding | `code-quality-standards` |
| JWT `amr`/`acr` or Bearer claim trust | `api-auth-and-jwt-abuse` |
| Attempt budget / HTTP rate-limit design | `api-rate-limit-design` / `rate-limit-bypass-testing` |

**Selection:** implementing authenticator TOTP → **this skill** + `code-quality-standards`.
Assessing live MFA gaps → `mfa-enrollment-flaws` or `mfa-bypass-methodology` primary.

## Output Checklist

- [ ] Algorithm, digits, period, window, secret length documented
- [ ] Enroll: pending secret, otpauth/QR, confirm-before-enable
- [ ] Verify: window, constant-time, replay (last step), attempt lockout
- [ ] Session elevation only server-side after factor-2; SID rotation noted
- [ ] Backup codes hashed + single-use; regenerate policy
- [ ] Disable/replace/step-up require current factor; user notify
- [ ] Secrets encrypted; redacted in logs; library choice recorded
- [ ] Automated tests listed; residual enrollment/login gaps routed to MFA skills

## Rules

- Implement only for systems you own or are authorized to change; never enroll or brute third-party factors.
- Prefer library correctness + tests over novel crypto. Secrets and codes are credentials — redact always.
- Do not treat client UI unlock or response-flag flips as server MFA; enforce on every privileged route.
- Hand assessment of skip/enrollment flaws to `mfa-enrollment-flaws` / `mfa-bypass-methodology`; keep this skill implementation-first.

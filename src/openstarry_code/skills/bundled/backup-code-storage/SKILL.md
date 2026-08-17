---
name: backup-code-storage
description: >-
  Design and implement MFA backup/recovery code generation, storage, display,
  redemption, and regeneration. Use when building or reviewing one-time backup
  codes, recovery codes, or offline second-factor fallbacks: entropy, hashing,
  single-use, rate limits, step-up for re-issue, and safe user presentation.
---

# MFA Backup Code Generation And Storage

Own the **lifecycle of MFA backup (recovery) codes**: generate, show once, store
safely, redeem, revoke, and re-issue. Defensive design and implementation for
systems you own or are authorized to harden.

## When To Use

| Situation | Direction |
| --- | --- |
| Generate / store / redeem / regenerate MFA backup codes | **This skill** |
| Hash-at-rest, single-use, attempt budgets, re-issue step-up | **This skill** |
| One-time reveal, download, remaining-count without leaking values | **This skill** |
| Attack testing: reuse, cross-user redeem, MFA skip via backup | `mfa-bypass-methodology` |
| Vault, pepper keys, secret scanning, server-secret rotation | `secrets-management-hygiene` |
| Secure coding, tests, constant-time compare, error paths | `code-quality-standards` |
| Enrollment skip / optional MFA / disable without factor | `mfa-enrollment-flaws` |

Keywords: backup codes, recovery codes, MFA offline codes, `recovery_codes`,
backup code hash, regenerate recovery codes. **Not primary:** live bypass
testing, general vault hygiene without codes, or TOTP enroll alone.

## Core Model

```
Generate N CSPRNG codes → show plaintext once → store hashes only
Redeem on MFA step-2 → normalize → constant-time verify → atomic mark used
Regenerate → step-up → invalidate all old → issue new set
```

| Property | Requirement |
| --- | --- |
| Entropy | ≥ 64 bits effective per code (prefer 80+); avoid short numeric-only |
| Count | Fixed set (e.g. 8–10); depleting set forces re-issue |
| Storage | Never plaintext at rest; salted/peppered hash per code |
| Use | Single-use; atomic consume; no cross-user redeem |
| Compare | Constant-time; strip hyphens/spaces; case-fold only if allowed |
| Audit | Log issue/redeem/regenerate **without** code values |
| Server secrets | Pepper/HMAC key in vault/KMS → `secrets-management-hygiene` |

Treat backup codes as **high-tier second-factor credentials**, not support master passwords.

## Workflow

### 1. Inventory surfaces and policy

Map generate, one-time reveal, download/print, redeem (login + step-up),
regenerate, remaining-count API, admin overrides. Record alphabet, length,
count, TTL, and behavior on password reset / MFA disable.

### 2. Generation

1. CSPRNG only — never weak PRNG. Unambiguous alphabet; optional `XXXX-XXXX`
   groups; strip separators before hash/verify.
2. Full set server-side in one transaction; bind `user_id` + purpose `mfa_backup`.
3. Authenticated (policy-appropriate enroll) context; rate-limit re-issue.
4. Apply `code-quality-standards` for types, errors, and RNG/format tests.

### 3. Storage and hashing

1. Store `hash`, `user_id`, `created_at`, `used_at=null`, optional pepper `kid`.
2. Prefer HMAC-with-server-pepper or slow hash per org standards — not bare
   MD5/SHA1 of the code alone.
3. Plaintext only on the generate response path; never DB, logs, analytics, or
   support tools. Pepper keys: `secrets-management-hygiene`.

### 4. Display and client handling

1. Full set shown **once** after generate/regenerate; optional explicit ack.
2. No API returns plaintext later; list may expose **count remaining** only.
3. Downloads: `Cache-Control: no-store`; avoid emailing codes by default.
4. SPA: do not park codes in `localStorage` or URLs.

### 5. Redemption

1. Accept only on MFA challenge for the **same** user/purpose; bind pending
   challenge/session when used.
2. Normalize input; constant-time verify; atomic mark used (`used_at IS NULL`);
   reject reuse and cross-user.
3. Attempt budget per account (+ IP); race/limit abuse → `mfa-bypass-methodology`.
4. Elevate session server-side only; never trust client `mfa_passed` flags.

### 6. Regeneration, disable, incidents

1. Regenerate requires step-up; invalidate **all** prior unused codes then insert.
2. Define MFA-disable and password-reset behavior (prefer invalidate).
3. Suspected leak: force regenerate, notify, review redeem audit; rotate pepper
   via `kid` dual-running if needed (`secrets-management-hygiene`).
4. Support tools must not display or bulk-export plaintext codes.

### 7. Verify implementation

With `code-quality-standards`: tests for single-use, cross-user reject,
regenerate invalidation, no plaintext in logs; synthetic fixtures only
(`secrets-management-hygiene`).

## Routing

| Need | Skill |
| --- | --- |
| Backup code generate, hash store, redeem, re-issue | **This skill** |
| Authorized MFA bypass (reuse, binding, skip, remember-device) | `mfa-bypass-methodology` |
| Pepper/vault, no secrets in git/logs, rotation | `secrets-management-hygiene` |
| Implementation quality, tests, safe errors | `code-quality-standards` |
| Enrollment skip / factor bind / disable without proof | `mfa-enrollment-flaws` |
| SID not rotated after MFA / JWT `amr`/`acr` claims | matching session or JWT skill |

### Required helpers

- **`secrets-management-hygiene`:** pepper/HMAC keys, redaction, leak response.
- **`mfa-bypass-methodology`:** authorized **assessment** of backup-code paths.
- **`code-quality-standards`:** always when implementing generate/hash/verify paths.

## Output Checklist

- [ ] Policy: count, alphabet/length, entropy, TTL, reset/disable behavior
- [ ] CSPRNG generation; unambiguous encoding; server-side only
- [ ] Plaintext once; no re-fetch API; no-store downloads
- [ ] Hashes only at rest; pepper via secret store; nothing in logs
- [ ] Redeem: same-user, constant-time, atomic single-use, attempt budget
- [ ] Regenerate: step-up; old set fully invalidated
- [ ] Audit issue/redeem/regenerate without code values
- [ ] Tests: reuse, cross-user, regenerate; synthetic fixtures
- [ ] Helpers: secrets hygiene + CQS; bypass work → MFA skill

## Rules

- Hash, single-use, step-up to re-issue; no shared support master codes.
- Never log or ticket live codes; redact examples.
- Build/review here; authorized attack proofs → `mfa-bypass-methodology`.
- Fail-closed redeem/regenerate; validate only on owned or authorized systems.

---
name: step-up-auth-patterns
description: >-
  Design and authorized assessment of step-up (re-authentication) patterns:
  sensitive-action challenges, short-lived elevation claims, binding to purpose
  and session, and server-side enforcement. Use when password change, payments,
  MFA disable, OAuth grants, export, or admin actions require a fresh factor after
  login, or when elevation tokens, acr/amr, or "recently authenticated" flags
  may be missing, reusable, or client-trusted.
---

# Step-Up Authentication Patterns

Secure **step-up** (transactional re-auth): after an existing session, high-risk
actions require a fresh factor or short-lived elevated credential, enforced on
the **server**. For **authorized** apps, labs, CTFs, and engagement-scoped
accounts only.

## Scope And Authorization

- Dual test accounts you control. Do not challenge or complete factors for third parties.
- Cap OTP/password attempt rates; avoid lockouts on shared prod identities.
- Redact passwords, OTP, elevation tokens, and session cookies; store raw captures offline.
- Prefer non-destructive proofs (read canaries, dry-run exports). State-changing demos need approval.

## When To Use

- Sensitive operations claim “confirm password”, MFA, WebAuthn, email OTP, or push **after** login.
- APIs accept `X-Step-Up`, `mfa_token`, `acr`, `amr`, `auth_time`, or `sudo`/`elevated` cookies/JWTs.
- UI gates password/MFA but the same action succeeds via API/mobile without a fresh challenge.
- Keywords: step-up, re-auth, transactional MFA, sudo mode, elevated session, recent authentication, `acr_values`, privilege change without re-challenge.
- Primary when the issue is **missing or weak elevation for a privileged action**, not full login MFA skip (that is `mfa-bypass-methodology`) or pure JWT alg/kid forgery (`api-auth-and-jwt-abuse`).

## Core Model

```
Authenticated session S (normal ACR)
  → User invokes high-risk action A
  → Server issues challenge C bound to user + purpose + TTL
  → Valid factor → short-lived elevation E (claim/token/session flag)
  → Action A accepted only with valid E; E expires or is single-use
```

| Pattern | Mechanism | Secure expectation |
| --- | --- | --- |
| **Re-enter password** | POST password then act | Server verifies hash; not UI-only |
| **Fresh MFA / WebAuthn** | OTP/assertion for purpose | Bound to challenge id + action class |
| **Elevated session window** | “sudo” flag N minutes | Server TTL; not client clock alone |
| **One-shot action token** | `step_up_token` on request | Single-use, purpose-scoped, short TTL |
| **Claim elevation** | JWT `acr`/`amr`/`auth_time` | Server-issued only; reject client assert |

**Good proof:** High-risk API succeeds with normal session and **no** valid recent elevation.  
**Bad proof:** UI blocked only; or full MFA-less login (route MFA skill); or forged access JWT without step-up context (JWT skill).

## Workflow

1. **Inventory step-up surfaces**  
   Map actions that should require re-auth: password/email change, MFA enroll/disable, payee/payout, large transfer, data export, OAuth consent/scopes, role elevation, API key mint, account delete. For each, note UI path, API method/path, challenge type, and response that grants elevation. Use `api-recon-and-docs` if SPA and API diverge.

2. **Baseline honest elevation**  
   Fully logged-in user A: trigger action → capture challenge request/response → complete factor → capture elevation artifact (cookie, body token, new JWT claims) → complete action. Record TTL, whether SID rotates, and success/fail body shapes as oracles.

   ```http
   POST /api/account/password HTTP/1.1
   Host: target.example
   Cookie: session=<S_normal>
   Content-Type: application/json

   {"current_password":"...","new_password":"..."}
   ```

3. **Skip / incomplete step-up**  
   With `S_normal` only (no challenge completed), call the same privileged APIs and deep links (mobile/API versions, GraphQL mutations, admin BFF). Drop step-up headers/body fields; omit `mfa_token` / `step_up_token`. **Confirmed** if state changes or sensitive canary returns without server challenge.

4. **Client-trust and flag manipulation**  
   Intercept challenge/verify responses. Flip only client-visible signals (`step_up_ok`, `elevated`, `sudo: true`, `acr: "2"`) and retry the action. Count as bypass **only** if the server accepts the privileged request without a valid server-minted elevation. SPA unlock + API 403 = partial control, not full step-up bypass.

5. **Binding, reuse, and TTL**  
   | Probe | Action | Secure behavior |
   | --- | --- | --- |
   | Purpose bind | Elevation from password-change used on export/pay | Reject wrong purpose |
   | Cross-user | A’s step-up token on B’s session | Reject |
   | Replay | Reuse one-shot token / old `auth_time` | Reject after use or TTL |
   | Cross-session | Copy elevated cookie to new browser/session | Fail if bound to SID |
   | Clock / stale | Wait past advertised window | Privilege drops server-side |

6. **Coverage gaps on lifecycle**  
   After normal MFA login, attempt disable MFA, add recovery email, mint personal access token, widen OAuth scopes, or admin impersonate **without** fresh step-up. Password reset completion and role switch should re-challenge or regenerate elevation policy consistently. SID not rotated on privilege change → note and hand fix to `session-fixation-management` if fixation-shaped.

7. **JWT / API claim elevation**  
   If elevation is a Bearer claim (`acr`, `amr`, `auth_time`, custom `sudo`): verify the **resource server** enforces min ACR for the route; try unsigned/`none`/alg swap only under JWT skill rules; client-supplied `acr` in body without signature is a step-up design flaw documented here, crypto confusion → `api-auth-and-jwt-abuse`.

8. **Remediation** (implement with `code-quality-standards`)  
   - Classify actions; default high-risk to require step-up server-side on every route/mutation.  
   - Challenges bound to `user_id` + `purpose` + nonce + short TTL; single-use where possible.  
   - Elevation is server-minted (opaque token or signed claims); never trust client booleans.  
   - Prefer purpose-scoped one-shot tokens over long global sudo windows; cap sudo TTL (minutes).  
   - Re-check authorization **and** elevation on the final state-changing request (no TOCTOU).  
   - Audit log step-up success/fail; notify on sensitive elevation (MFA disable, payee add).  
   - Tests: skip-fails, wrong-purpose rejects, replay rejects, TTL expiry, dual-account binding.

## Routing

| Need | Skill |
| --- | --- |
| Login/2FA skip, backup codes, remember-device, OTP race | `mfa-bypass-methodology` |
| JWT alg/kid/jku, Bearer forgery, claim confusion | `api-auth-and-jwt-abuse` |
| Secure implementation, tests, logging hygiene | `code-quality-standards` |
| SID not regenerated on privilege change | `session-fixation-management` |
| OAuth `acr_values` / IdP step-up | `oauth-oidc-misconfiguration` |
| Parallel accept of one elevation token | `race-condition` |

**Selection:** missing/weak re-auth on sensitive actions → **this skill**. Factor-2 never enforced at login → `mfa-bypass-methodology`. Token crypto → `api-auth-and-jwt-abuse`. Building the control → `code-quality-standards`.

## Output Checklist

- [ ] High-risk actions inventory and expected step-up type per action
- [ ] Baseline: challenge → elevation artifact → successful action
- [ ] Skip/incomplete-flow results (endpoint, status, canary)
- [ ] Client flag manipulation vs true server enforcement
- [ ] Purpose binding, cross-user, replay, TTL, cross-session outcomes
- [ ] Lifecycle gaps (MFA disable, export, OAuth grant, admin)
- [ ] JWT/claim elevation notes or hand-off to JWT skill
- [ ] Impact with dual test accounts only; remediation list; evidence redacted

## Rules

- Authorized dual-account tests only; no third-party OTP or password interception.
- Client UI or JSON flag flips count only when the **server** performs the privileged action without valid elevation.
- Do not relabel full login MFA bypass or pure JWT forgery as step-up gaps—route correctly.
- Prefer one clean privileged canary without step-up over long theoretical ACR matrices.
- Redact secrets and sessions; rotate test elevation tokens after demos when accounts are shared.

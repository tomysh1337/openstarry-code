---
name: mfa-enrollment-flaws
description: >-
  Authorized methodology for MFA enrollment and setup-skip flaws: force MFA
  incomplete, bind attacker factors, disable without step-up, and treat
  enrollment as optional. Use when register/enroll/setup-2FA, skip setup, or
  optional MFA paths may leave accounts without a server-enforced second factor.
---

# MFA Enrollment Flaws (Authorized)

Focus on **enrollment, setup, and binding** of second factors — not full login
OTP brute or generic step-up skip (`mfa-bypass-methodology`). Prove server-side
gaps with accounts you control.

## Use When

| Situation | Direction |
| --- | --- |
| Enroll TOTP/WebAuthn/SMS, “set up later”, optional MFA, disable MFA | **This skill** |
| Post-password/SSO reach app **without finishing MFA setup** | **This skill** |
| Attacker factor bound to victim, or factor removed without proof | **This skill** |
| Login skip, backup codes, remember-device, response-flag bypass | `mfa-bypass-methodology` |
| JWT `amr`/`acr` or Bearer step-up claims | `api-auth-and-jwt-abuse` |
| SAML assertion issues (not enroll UI) | `saml-sso-basics` |

Keywords: MFA enrollment, 2FA setup skip, optional MFA, enroll TOTP, WebAuthn
register, disable MFA, factor binding, mfa_enrolled=false.

## Scope And Authorization

- Authorized apps, labs, CTFs, program accounts **only**. Dual test users you
  control; never enroll/disable/rebind MFA on third parties.
- Prefer staging. Cap SMS/voice/email OTP; avoid shared-prod lockouts. Redact
  TOTP secrets, otpauth URIs, backup codes, WebAuthn IDs, session cookies.
- Logic/authorization focus — not SIM swap or offline TOTP breaks. Mass
  disable/re-enroll needs approval; default dual-account proofs.

## Workflow

### 1. Map enrollment surfaces

| Surface | Capture |
| --- | --- |
| Start enroll | `/mfa/setup`, `POST .../factors` |
| Confirm enroll | OTP verify, WebAuthn create finish |
| Skip / later | “Skip”, `?skip=1`, dismiss modal |
| Policy | Optional / grace N days / hard required |
| Disable / replace / flags | Delete factor; `mfa_enrolled` / JWT claims |

Use `api-recon-and-docs` if SPA/mobile differs.

### 2. Baseline honest enrollment

User A: register/login → complete enroll → logout → login with factor-2; record
privileged oracle and enroll-start vs confirm shapes.

### 3. Skip and incomplete-setup

After password/SSO **without** finishing enroll:

```http
GET /api/me HTTP/1.1
Host: target.example
Cookie: session=<post_auth_pre_enroll>
```

Also: home and state-changing APIs; mobile omitting setup; `POST` skip; abandon
after secret shown; grace `enroll_by` never enforced; invite/reset into app with
`mfa_required=false`.

**Confirmed** if privileged canary works while factor list empty or policy
requires MFA. UI-only unlock + API 403 = partial control, not full skip.

### 4. Bind and replace (owned accounts)

| Risk | Test |
| --- | --- |
| No re-auth to enroll | Add factor with factor-1-only session |
| Cross-user confirm | A’s enroll OTP on B’s pending enroll |
| Replace without proof | New TOTP then remove old without current OTP |
| Disable without factor | `DELETE /mfa/factors/{id}` password session only |
| Recovery at enroll | Codes before confirm; regenerate reuse |

WebAuthn: `user.id` / rpId must match server user; client cannot register for
another account. CSRF on enroll/disable → `csrf-cross-site-request-forgery`.

### 5. Policy and token edges

- Org require-MFA: member active past grace with no factors.
- API sets `mfa_enabled=true` without real factors (status-only).
- JIT/SAML users skip enroll password users get — assertion bugs →
  `saml-sso-basics`; missing enroll gate after good SSO stays here.
- Claims `amr=["mfa"]` / `mfa_enrolled=true` at enroll-start without confirm →
  whether APIs trust them → `api-auth-and-jwt-abuse`.
- SID rotation at enroll/skip → `session-fixation-management`; remember-device
  after disable → `mfa-bypass-methodology`.

### 6. Remediation

With `code-quality-standards`:

- Server-enforce enroll: privileged routes need registered factor + challenge
  when policy mandates MFA; no eternal skip.
- Bind factors to `user_id`; set enrolled only after confirm; step-up to
  add/replace/disable; notify on change.
- Protect TOTP secrets; hash backup codes; single-use recovery.
- Derive state from factor store, not client JWT/UI flags.
- WebAuthn: validate origin/rpId/user handle on registration finish.

## Routing

| Need | Skill |
| --- | --- |
| Enrollment / setup skip / disable-without-factor | **This skill** |
| Login OTP skip, backup reuse, remember-device, step-up | `mfa-bypass-methodology` |
| JWT `amr`/`acr`, Bearer, API auth claims | `api-auth-and-jwt-abuse` |
| SAML SSO signature/audience/ACS | `saml-sso-basics` |
| SAML XSW awareness | `saml-signature-wrapping-awareness` |
| CSRF / session / ATO / secure code | matching CSRF, fixation, ATO, CQS skills |

## Checklist

- [ ] Enroll/skip/disable/replace mapped; policy type noted
- [ ] Incomplete setup: privileged API with pre-enroll session
- [ ] Cross-user confirm / factor-binding; disable without factor
- [ ] `mfa_enrolled` claims vs factor store (JWT → auth skill)
- [ ] SSO/JIT enroll gate; session invalidation on enroll/disable
- [ ] Impact with owned accounts; remediation; secrets redacted

## Rules

- Owned dual accounts only; no third-party MFA rebind/disable.
- Require **server** privilege without required factor — not SPA-only unlock.
- Login bypass → `mfa-bypass-methodology`; JWT → `api-auth-and-jwt-abuse`;
  SAML XML → `saml-sso-basics`. Cap OTP; one clean canary; authorized only.

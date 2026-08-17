---
name: webauthn-attestation-review
description: >-
  Review WebAuthn/passkey attestation conveyance, statement formats, trust
  anchors, and AAGUID policy for registration. Use when choosing or auditing
  attestationPreference (none/indirect/direct/enterprise), MDS/trust-store
  verification, enterprise device allowlists, or privacy risks of storing
  full attestation objects on consumer vs high-assurance RPs.
---

# WebAuthn Attestation Review

Deep review of **attestation conveyance and verification** at registration—not
full ceremony design. Hand ceremony/assert to `passkeys-webauthn-basics`; hand
OTP second factors to `totp-mfa-implementation`.

## When To Use

- Setting or reviewing `attestation` / `attestationPreference` on create options.
- RP enforces **hardware/device class** via packed/tpm/android-key/apple statements,
  FIDO MDS, or enterprise vendor certs.
- Need **AAGUID** allow/deny, trust-store pinning, or enterprise attestation (EA).
- Privacy/compliance: storing attestation certs, serials, or batch keys.
- Keywords: none/indirect/direct/enterprise, `attStmt`, AAGUID, MDS, trust anchor,
  conveyance, self attestation, none fmt.

**Not primary:** full passkey register/assert → `passkeys-webauthn-basics`; TOTP →
`totp-mfa-implementation`; MFA skip testing → `mfa-bypass-methodology`.

## Scope And Authorization

- Owned apps, labs, CTFs, or **written** engagement scope only.
- Do not harvest production attestation certs, serials, or EA material from
  third-party users without authorization.
- Prefer staging authenticators and test MDS/trust packs; keep originals immutable;
  treat device-identifying attestation as sensitive in logs and reports.

## Workflow

### 1. Inventory conveyance and policy intent

| Field | Capture |
| --- | --- |
| Requested conveyance | `none` / `indirect` / `direct` / `enterprise` |
| RP assurance goal | Phishing-resistant login only vs device-class gate |
| Server verify path | Library options; custom CBOR/`attStmt` parsing |
| Trust material | MDS cache, vendor roots, enterprise CA, pin set |
| AAGUID policy | Allowlist, denylist, log-only, unused |
| Storage | Full `attestationObject` vs stripped after verify |
| Failure mode | Reject enroll vs soft-fail to `none` |

```text
create() options.attestation → authenticator may return attStmt
  → RP verifies fmt + trust path + AAGUID policy
  → store credential public key (+ optional metadata)
```

### 2. Conveyance types (risks and fit)

| Preference | Typical result | When appropriate | Main risks |
| --- | --- | --- | --- |
| **none** | `fmt=none` / empty trust path | Consumer passkeys; privacy-first | No device proof; do not claim hardware assurance |
| **indirect** | Anonymized/batch or proxy attestation | Some signal without unique device ID | Still needs correct verify; proxy quality varies |
| **direct** | Full statement + chain when supported | High-assurance / regulated device binding | Privacy; broken verify = false confidence |
| **enterprise** | Platform EA when RP is enterprise-approved | Managed fleet, MDM-aligned RPs | Mis-issued EA; logging blobs; non-EA clients fail |

Requesting `direct`/`enterprise` without a **working trust store and reject path**
is worse than `none` (false hardware claims). Authenticators may **downgrade**
despite `direct`—define accept vs reject for missing/untrusted statements.

### 3. Statement verification (when not `none`)

1. Parse `attestationObject` (`authData` + `fmt` + `attStmt`) via maintained lib.
2. Bind ceremony: challenge, origin, `rpIdHash`, AT flag, credential public key
   (same create checks as `passkeys-webauthn-basics`).
3. Per-`fmt` (packed, tpm, android-key, apple, fido-u2f, none, …): signature over
   expected bytes; cert chain when present.
4. **Trust store:** pin roots / current MDS; reject unknown roots and
   expired/revoked paths; never trust “any chain in attStmt.”
5. **Self / `none`:** no hardware proof—only if policy is explicitly none-equivalent.
6. Persist COSE key, credential id, `signCount`, AAGUID/transports as needed;
   drop or encrypt raw certs unless retention is required.

### 4. AAGUID and metadata policy

| Control | Secure behavior |
| --- | --- |
| Extract AAGUID | From authenticator data (16 bytes); stable policy key |
| Allowlist | High-assurance RPs: only approved models/vendors |
| Denylist | Known-bad or retired authenticators |
| MDS fields | Status (revoked, update available)—not sole trust |
| Missing AAGUID | Define reject vs accept (platform passkeys vary) |

Document enforced vs telemetry-only. Do not equate AAGUID marketing names with
security without a verified trust path.

### 5. Conveyance and storage risks

- **False assurance:** accept enroll when verify fails or is skipped.
- **Privacy:** long-lived unique certs/serials enable tracking; prefer summary
  (AAGUID, type, verify result).
- **Supply chain:** stale MDS / unpinned vendor CA accepts untrusted authenticators.
- **Enterprise EA:** only for EA-registered RPs and managed populations; BYOD
  fallback must not silently lower the bar without UX.
- **Logging:** redact `attStmt`, cert PEMs, and challenges.

### 6. Implementation quality

Apply `code-quality-standards`: typed options; accept/reject matrix unit tests;
virtual-authenticator integration tests; prefer library attestation + MDS support
over hand-rolled CBOR/crypto.

## Routing

| Need | Skill |
| --- | --- |
| Attestation conveyance, trust store, AAGUID policy | **This skill** |
| Full passkey register/assert, RP ID, origin, UV, counter | `passkeys-webauthn-basics` |
| Authenticator-app TOTP (not WebAuthn) | `totp-mfa-implementation` |
| MFA skip, backup codes, step-up gaps | `mfa-bypass-methodology` |
| Session/JWT `amr`/`acr` after assert | `api-auth-and-jwt-abuse` |
| Secure coding, tests, review baseline | `code-quality-standards` |

**Selection:** attestation policy/verify/trust → **this skill**. Ceremony lifecycle →
`passkeys-webauthn-basics`. OTP MFA → `totp-mfa-implementation`. Fixes →
`code-quality-standards`.

## Output Checklist

- [ ] Requested conveyance and RP assurance goal documented
- [ ] Server verifies or explicitly ignores attestation (no silent skip)
- [ ] Trust anchors / MDS / enterprise CA source, refresh, pin strategy
- [ ] Per-fmt accept/reject; self/`none` policy explicit
- [ ] AAGUID allow/deny or log-only; missing-AAGUID rule
- [ ] Downgrade (omitted statement): reject vs allow
- [ ] Storage minimized; certs redacted; EA/BYOD fallback documented
- [ ] Tests: good chain, bad root, wrong AAGUID, none fmt, verify-fail reject
- [ ] Handoffs: ceremony → `passkeys-webauthn-basics`; TOTP → `totp-mfa-implementation`

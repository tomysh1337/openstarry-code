---
name: fido2-enterprise-attestation
description: >-
  Design and authorized review of FIDO2/WebAuthn enterprise attestation (EA):
  conveyance preference enterprise, vendor/platform EA enrollment of the RP,
  unique device-identifying attStmt chains, MDM-aligned allowlists, and privacy-
  safe storage. Use when managed fleets, corporate RPs, or high-assurance device
  binding require enterprise attestation rather than consumer none/indirect/direct.
---

# FIDO2 Enterprise Attestation

Deep focus on **enterprise attestation (EA)** for FIDO2/WebAuthn registration on
**managed or high-assurance** RPs. Ceremony design → `passkeys-webauthn-basics`.
Generic none/indirect/direct, MDS, and AAGUID policy → `webauthn-attestation-review`.

## When To Use

- RP sets `attestation` / `attestationPreference` to **`enterprise`** (or vendor
  APIs expose “enterprise attestation”).
- Need **unique device identity** or enterprise cert path—not batch/anonymized
  keys under `direct`.
- Platform/vendor docs mention **enterprise RP registration**, EA enablement, or
  MDM/device-compliance coupling.
- Policy: only corporate-managed authenticators may enroll; BYOD fails closed or
  uses a separate lower-assurance path.
- Keywords: enterprise attestation, EA, `enterprise` conveyance, enterprise CA,
  device serial in attStmt, managed passkey, FIDO2 fleet policy, platform EA.

**Not primary:** consumer `none`/`indirect` → `passkeys-webauthn-basics` +
`webauthn-attestation-review`; TOTP → `totp-mfa-implementation`; MFA skip tests →
`mfa-bypass-methodology`.

## Workflow

### 1. Confirm EA is required

| Goal | Prefer |
| --- | --- |
| Phishing-resistant login only | `none` / passkeys; no EA |
| Model-class gate without unique device ID | `direct` + MDS/AAGUID allowlist |
| Unique device / enterprise cert on managed fleet | **`enterprise` (this skill)** |

Document who needs EA (workforce SSO, regulated device bind) vs privacy-preserving
passkeys. Never enable EA “for completeness” on public consumer RPs.

### 2. Platform and RP prerequisites

1. **RP identity:** origin / RP ID registered with platform or authenticator vendor
   as an **enterprise-approved** RP (process varies by OS/vendor).
2. **Create options:** `attestation: "enterprise"`; keep challenge, `rp.id`, user,
   `pubKeyCredParams`, UV/RK correct (`passkeys-webauthn-basics`).
3. **Support/downgrade:** only some platform authenticators return EA; CTAP/browser
   may return none or non-EA—define reject vs alternate path (never silent “EA proven”).
4. **Trust material:** pin enterprise vendor/platform CA roots; refresh deliberately;
   never trust “any cert in attStmt.”

```text
MDM / vendor EA registration of RP
  → create(attestation=enterprise)
  → attStmt with enterprise chain (when eligible)
  → RP verifies chain + ceremony bind + device policy
  → store credential + minimal device metadata
```

### 3. Verify enterprise statements (server)

1. Parse `attestationObject` via a maintained library (CBOR/`fmt`/`attStmt`).
2. Bind ceremony: challenge, origin, `rpIdHash`, AT flag, credential public key.
3. Validate **enterprise trust path** against pinned roots; reject self-attestation,
   empty/`none` fmt, or consumer batch chains when EA is required.
4. Extract stable policy keys (AAGUID, vendor-documented EA cert attributes); map to
   **asset/MDM inventory** only when authorized and required.
5. On verify failure or non-EA response: **reject enroll** or an explicit fallback
   tier—never soft-fail into “hardware assured.”

### 4. Fleet policy and BYOD

| Control | Secure behavior |
| --- | --- |
| EA-required population | Workforce managed devices only |
| BYOD / personal passkeys | Separate policy or deny; no silent downgrade |
| AAGUID / model allowlist | Optional extra gate after EA trust path |
| MDM correlation | Inventory APIs only; authorized scopes |
| Revocation | Retire CA packs; force re-enroll on compromise |

EA proves the enterprise path at **registration**, not continuous posture. Pair
ongoing compliance with MDM/endpoint controls, not `attStmt` alone.

### 5. Privacy, storage, logging, quality

- EA material can be **device-identifying**. Minimize retention (verify result,
  AAGUID, coarse class, enroll time)—not full PEM dumps unless mandated.
- Encrypt retained certs; restrict access; define TTL and legal basis.
- Redact `attStmt`, PEMs, challenges, user handles in logs and tickets.
- Apply `code-quality-standards`: typed options; accept/reject matrix; tests for
  good EA, bad root, missing EA, `none` fmt, downgrade; prefer library EA support.

## Routing

| Need | Skill |
| --- | --- |
| Enterprise attestation, EA trust, fleet enroll | **This skill** |
| General none/indirect/direct, MDS, AAGUID | `webauthn-attestation-review` |
| Full passkey register/assert, RP ID, origin, UV | `passkeys-webauthn-basics` |
| Authenticator-app TOTP | `totp-mfa-implementation` |
| MFA skip / backup-code / step-up gaps | `mfa-bypass-methodology` |
| Session/JWT `amr`/`acr` after assert | `api-auth-and-jwt-abuse` |
| Soft device_id tokens without FIDO proof | `device-binding-tokens` |
| Secure coding, tests, review baseline | `code-quality-standards` |

**Selection:** managed-fleet **enterprise** attestation → **this skill**. Broader
conveyance matrix → `webauthn-attestation-review`. Ceremony →
`passkeys-webauthn-basics`. Implementation → pair `code-quality-standards`.

## Output Checklist

- [ ] Assurance goal documented (EA unique-device vs MDS/AAGUID vs none)
- [ ] `attestation: enterprise` only where population and RP registration justify it
- [ ] Vendor/platform enterprise RP enrollment steps and status recorded
- [ ] Server verifies EA trust path; no silent skip or soft-fail to “assured”
- [ ] Downgrade / non-EA response: reject or explicit alternate tier
- [ ] Trust anchors: source, pin, refresh, retirement process
- [ ] BYOD vs managed policy and UX failure modes documented
- [ ] Storage minimized; EA certs/serials redacted; retention justified
- [ ] Tests: good EA, bad root, none fmt, missing EA, ceremony bind failures
- [ ] Handoffs: `webauthn-attestation-review`, `passkeys-webauthn-basics`,
      `code-quality-standards`

## Scope And Authorization

- Owned apps, labs, CTFs, or **written** engagement scope only.
- Do not harvest production EA certs, serials, or blobs from third-party users
  or unmanaged devices without authorization.
- Prefer staging RPs, test enterprise registration, and non-production authenticators.
- Keep originals immutable; treat device-identifying attestation as sensitive in
  reports. Active enroll mutation or trust-store weakening only when authorized.

---
name: passkeys-webauthn-basics
description: >-
  Implement and review Passkeys / WebAuthn (W3C Web Authentication) registration
  and assertion flows: RP ID, origin, challenge binding, credential store,
  user verification, and safe fallbacks. Use when adding or hardening
  passwordless/passkey login, WebAuthn MFA step-up, or credential-management APIs
  for first-party web or hybrid clients.
---

# Passkeys / WebAuthn Basics (Implementers)

Server- and client-side basics for **WebAuthn Level 2+** and **passkeys**
(discoverable multi-device credentials). Focus: correct ceremony binding and
lifecycle—not CTAP firmware reverse engineering or unauthorized auth bypass.

## When To Use

- Building or reviewing **passkey** enroll, login, or step-up MFA.
- Code or traffic shows `navigator.credentials.create` / `get`, `PublicKeyCredential`,
  WebAuthn options, or libs (`@simplewebauthn/*`, `fido2-lib`, Duo WebAuthn).
- Need a checklist for RP ID, origin, challenge TTL, counter, and UV policy.
- Keywords: passkey, WebAuthn, FIDO2, resident key, discoverable credential,
  attestation, assertion, `rpId`, user verification, conditional UI.
- **Not primary** for pure JWT crypto, classic OTP MFA skip tests, or OAuth redirects—
  see Routing.

## Core Model

```text
Register: challenge → create() → store credentialId + public key (+ signCount)
Authenticate: challenge → get() → verify assertion sig → elevate session
```

| Concept | Implementer rule |
| --- | --- |
| **RP ID** | Effective domain per WebAuthn rules; match deployment host policy |
| **Origin** | Exact scheme+host+port; verify from `clientDataJSON`, allowlist per env |
| **Challenge** | CSPRNG, single-use, short TTL, bound to user/session/purpose |
| **Credential** | Store `credentialId`, COSE public key, `signCount`, transports, user handle |
| **UV / RK** | `userVerification` per risk; discoverable keys for passwordless |
| **Attestation** | Optional for consumer passkeys; require only under device policy |

## Workflow

### 1. Map the surface

Record ceremonies (register, login, step-up, revoke); client type (web/WebView/native);
options (`rp.id`, UV, resident key, attestation); credential store shape; how success
elevates session/tokens; fallbacks (password, OTP, recovery).

### 2. Registration (create)

1. Strongly authenticate (or bootstrap enrollment) **before** bind.
2. Mint challenge; return `PublicKeyCredentialCreationOptions` (exclude known IDs).
3. Client: `navigator.credentials.create({ publicKey })`.
4. Server verify: `clientDataJSON` (`type=webauthn.create`, challenge, **origin**);
   `rpIdHash`; flags (AT; UV if required); extract COSE key; attestation only if policy needs it.
5. Persist credential bound to **server** user id—never trust client-chosen account id alone.

```http
POST /webauthn/register/options  → { challenge, rp, user, pubKeyCredParams, ... }
POST /webauthn/register/verify   → { id, rawId, response.clientDataJSON, attestationObject }
```

### 3. Authentication (get)

1. Identify user (username, conditional UI, or session for step-up).
2. Mint challenge; non-discoverable: set `allowCredentials` for that user.
3. Client: `navigator.credentials.get({ publicKey })` (optional conditional mediation).
4. Server: lookup credential → user; verify `type=webauthn.get`, challenge, origin,
   `rpIdHash`, UP/UV flags; signature over `authData || hash(clientDataJSON)`;
   if previous and new `signCount` are non-zero and new ≤ old → clone-risk policy
   (reject, alert, and/or force step-up).
5. Elevate session / mint tokens **only after** verify; regenerate session id.

### 4. Hardening (common failures)

| Pitfall | Secure behavior |
| --- | --- |
| Challenge multi-use | One-time; consume on success/fail |
| Origin/RP ID wrong env | Per-env allowlist; no wildcard origins |
| SPA “success” flag | Server crypto verify is authoritative |
| Cross-account bind | Global credential id uniqueness; enroll to current user only |
| Weak fallback | Password/OTP must not skip required assurance (`mfa-bypass-methodology`) |
| Post-assert tokens | Set `amr`/`acr`/session server-side (`api-auth-and-jwt-abuse`) |
| Last-factor delete | Require re-auth; designed recovery path |
| Hand-rolled CBOR | Prefer maintained libs; explicit alg allowlist (e.g. ES256) |

HTTPS (or localhost) required in browsers. Prefer short-lived challenges; never log
private keys (client-only) or long-lived raw challenges.

### 5. Policy and quality

- **Passwordless:** discoverable + UV preferred; document recovery.
- **Second factor / step-up:** fresh assertion for sensitive actions; multi-credential list/revoke.
- Conditional UI needs correct `get()` options and form `autocomplete` wiring.
- Ship with `code-quality-standards`: typed builders, safe errors, unit tests for
  origin/challenge/counter, integration tests via virtual authenticator
  (Chrome DevTools / Playwright WebAuthn).

## Routing

| Need | Skill |
| --- | --- |
| Passkey/WebAuthn ceremony design and verify | **This skill** |
| MFA skip, backup codes, remember-device, step-up gaps | `mfa-bypass-methodology` |
| Session/JWT after login; `amr`/`acr`; Bearer misuse | `api-auth-and-jwt-abuse` |
| Secure coding, tests, review baseline | `code-quality-standards` |

**Selection:** implement/review WebAuthn bind and assert → **this skill**. Authorized
MFA *enforcement* testing → `mfa-bypass-methodology`. Token/session issues after
assert → `api-auth-and-jwt-abuse`. Implementation work → always pair
`code-quality-standards`.

## Output Checklist

- [ ] RP ID, origin allowlist, environments documented
- [ ] Register and authenticate options + verify endpoints mapped
- [ ] Challenge: CSPRNG, TTL, single-use, purpose binding
- [ ] Server verifies origin, type, rpIdHash, signature, UV policy
- [ ] Credential store: id, public key, signCount, user link, revoke
- [ ] signCount / clone policy decided and tested
- [ ] Session elevation only post-verify; session regenerate / claims safe
- [ ] Fallback and recovery preserve required assurance level
- [ ] Attestation policy explicit (none vs enterprise)
- [ ] Tests: happy path + bad origin/challenge/counter; secrets redacted in logs

## Rules

- Server cryptographic verification is mandatory; UI success is not authentication.
- Origin and challenge binding are non-negotiable; env misconfig is a common outage/vuln.
- Store public keys and metadata only—never authenticator private keys.
- Passkeys reduce phishing risk only when origin/RP ID checks hold end-to-end.
- Bypass testing of MFA *around* passkeys → `mfa-bypass-methodology`; this skill is the implementer reference for the WebAuthn surface.
- Prefer standard libraries over hand-rolled CBOR/COSE unless justified.

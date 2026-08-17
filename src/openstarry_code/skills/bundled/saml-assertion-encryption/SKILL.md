---
name: saml-assertion-encryption
description: >-
  Authorized review of SAML 2.0 assertion encryption: EncryptedAssertion,
  key transport, SP encryption-certificate management, and decrypt-before-
  signature-verify order pitfalls. Use when EncryptedAssertion, EncryptedKey,
  WantAssertionsEncrypted, or SP decryption of SAML assertions is in scope.
---

# SAML Assertion Encryption (Authorized)

Assess **`saml:EncryptedAssertion`** (and related encrypted nodes) so
confidentiality does not break signature trust or audience/ACS validation.
Map signing, Audience, and ACS with `saml-sso-basics`. Metadata and encryption
certs → `saml-metadata-hygiene`.

## When To Use

| Situation | Direction |
| --- | --- |
| **EncryptedAssertion** / **EncryptedKey** in traffic or metadata | **This skill** |
| SP: `WantAssertionsEncrypted`, encryption cert, key transport | **This skill** |
| Suspect SP **decrypts then skips** signature / Audience / ACS | **This skill** |
| Plain signing, Audience, ACS only (no encrypt focus) | `saml-sso-basics` |
| Metadata import, EntityID pin, cert rollover, KeyDescriptor | `saml-metadata-hygiene` |
| XSW / verify≠parse after decrypt | `saml-signature-wrapping-awareness` |
| Third-party IdP production outside written scope | **Out of scope** |

Keywords: EncryptedAssertion, EncryptedKey, key transport, RSA-OAEP, AES-GCM,
SP encryption certificate, decrypt-before-verify, WantAssertionsEncrypted.

## Scope And Authorization

- **Authorized only:** owned SP/IdP apps, labs, CTFs, or written scope naming
  the SP and any IdP/tenant exercised. Prefer staging / test IdP.
- Do **not** attack commercial IdP production beyond SP mistakes and IdP apps
  **explicitly** in scope. Dual test identities only.
- Treat ciphertext, SP private decryption keys, and raw `SAMLResponse` as
  secrets: redact; store offline; never publish live blobs or private keys.
- Re-encrypt/re-sign only with keys **you control** in lab. Cap ACS spam.
- Assessment and hardening — not mass SSO disruption or key theft.

## Workflow

### 1. Inventory encryption surface

| Field | Capture |
| --- | --- |
| Encrypted nodes | Assertion, ID, Attribute (Response rare) |
| Key transport | RSA-OAEP, RSA-v1.5, ECDH-ES, static key |
| Data encryption | AES-GCM preferred; note CBC/legacy |
| SP encryption cert | Metadata `KeyDescriptor use="encryption"` |
| Private key custody | SP HSM/vault — never in metadata |
| What is signed | Response, inner Assertion, both, neither |
| Library | Stack/version (decrypt + verify path) |

Decode ACS copies **offline**. Note whether encryption is required or optional.

### 2. Certificate and key transport

1. IdP must encrypt to SP encryption cert(s) from **trusted** metadata — not an
   attacker-only `KeyInfo`. Public trust plane → `saml-metadata-hygiene`.
2. Flag encryption vs **signing** cert mix-ups, expired encryption certs still
   trusted, private keys in git/tickets → `secrets-management-hygiene`.
3. Prefer RSA-OAEP + AES-GCM; document RSA-1.5 / AES-CBC as residual risk.
4. Dual-cert rollover: SP decrypts with matching keys and **still** enforces
   signature + conditions on the plaintext assertion.

### 3. Decrypt-before-signature-verify order

```text
Secure: decrypt → verify required signature node → Audience/ACS/time/one-time ID
        → session only from verified subject
Weak:   decrypt → trust NameID/attrs (signature or conditions skipped)
```

| Probe (authorized lab) | Secure behavior |
| --- | --- |
| Ciphertext OK; signature stripped/broken after decrypt | Reject |
| Valid decrypt; wrong Audience / ACS inside | Reject |
| Outer Response signed only; inner assertion not integrity-bound | Reject if policy needs assertion integrity |
| Decrypt succeeds; verify never runs | **Critical** — encryption ≠ authentication |
| Unencrypted assertion accepted when encryption required | Reject (or documented exception) |

**Good proof:** SP session reflects identity that failed post-decrypt signature
or condition checks (or checks never ran).  
**Bad proof:** “Assertion is encrypted” with no weak-acceptance evidence.

Pitfalls: (1) encrypt-then-forget-sig; (2) verify envelope only, not inner
Assertion; (3) parse ≠ verified node after decrypt → XSW skill; (4) fail-open
on unknown `EncryptedKey`/alg (accept plaintext sibling).

### 4. Controlled checks and remediation

1. Baseline encrypted SSO as V; record session canary.
2. Reject path: bad tag/MAC, wrong transport key, expired conditions.
3. If encryption optional: unencrypted unsigned/forged acceptance = policy bypass.
4. Re-run Audience, Destination/Recipient, replay, cert-pin via `saml-sso-basics`
   — encryption must not short-circuit them.
5. Remediate with `code-quality-standards`: pin encryption certs; require
   verify + conditions **after** decrypt; OAEP+AEAD; vault/HSM private keys;
   XXE-safe parse; dual-cert staged retire. Metadata bags → `saml-metadata-hygiene`.

## Routing table

| Need | Skill |
| --- | --- |
| EncryptedAssertion, key transport, decrypt vs verify order | **This skill** |
| Signature, Audience, ACS, strip-sig, replay | `saml-sso-basics` |
| Metadata certs, EntityID, encryption KeyDescriptor, rollover | `saml-metadata-hygiene` |
| XSW / verify≠parse on decrypted XML | `saml-signature-wrapping-awareness` |
| Private key vault / rotation | `secrets-management-hygiene` |
| Session fixation at ACS | `session-fixation-management` |
| XXE via SAML XML | `xxe-xml-external-entity` |
| SP implementation / tests | `code-quality-standards` |
| ATO chaining including SAML | `account-takeover-methodology` |

## Output Checklist

- [ ] Auth covers SP and any IdP/tenant; staging preferred
- [ ] Encrypted nodes, transport/data algs, SP encryption cert recorded
- [ ] Signing policy vs ciphertext (Response / inner Assertion / both)
- [ ] Decrypt-then-verify order tested; auth-on-decrypt-only ruled out
- [ ] Optional-encryption plaintext bypass checked if applicable
- [ ] Post-decrypt Audience/ACS/time/replay (`saml-sso-basics`)
- [ ] Metadata cert hygiene (`saml-metadata-hygiene`); keys redacted
- [ ] Impact or secure reject baseline; OAEP+AEAD + never auth-on-decrypt remediation
- [ ] No third-party IdP abuse; no published private keys or live SAMLResponse

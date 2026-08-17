---
name: jwt-jwe-encryption-basics
description: >-
  Authorized design and assessment of JOSE JWE token encryption: compact
  five-part structure, key encryption (alg) vs content encryption (enc), CEK
  handling, nested JWT (JWS inside JWE), and decryption/key-management checks.
  Use when APIs or clients issue or consume encrypted tokens (eyJ... five segments),
  JWE protected payloads, or confidentiality is required beyond signed JWT alone.
---

# JWT / JWE Encryption Basics

Basics of **JSON Web Encryption (JWE)** for confidential tokens: structure,
algorithms, key management, and authorized review. Complements JWS/JWT abuse
work; encryption is not authentication by itself.

## When To Use

| Situation | Direction |
| --- | --- |
| Token has **five** base64url segments (not three) | **This skill** (primary) |
| Header shows `enc`, `alg` key wrap, `zip`, or `cty: JWT` | **This skill** |
| Design: encrypt access/ID/session payloads at rest or in transit layers | **This skill** |
| Nested JWT: JWE wrapping a signed JWS | **This skill** for outer encrypt |
| Three-part signed JWT only (`alg` none, confusion, kid) | `api-auth-and-jwt-abuse` |
| `iss`/`aud` claim policy on plaintext after decrypt | `jwt-audience-issuer-checks` |
| Refresh lifecycle / storage | `jwt-refresh-token-patterns` |
| No authorization for live decrypt/key work | **Do not use** actively |

Keywords: JWE, RFC 7516, compact serialization, CEK, `alg`/`enc`, A256GCM,
RSA-OAEP, ECDH-ES, dir, nested JWT, encrypted token, JOSE.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only.
- Treat CEKs, private keys, shared secrets, and full JWE strings as credentials:
  redact; store offline; rotate after production demos.
- Prefer non-destructive analysis: structure decode, library config review, decrypt
  only with **keys you control** or keys in-scope for the engagement.
- Do not attempt offline brute-force of production RSA/EC private keys or high-entropy
  CEKs beyond agreed wordlists and rate limits.
- Implementation pairs with `code-quality-standards` (secrets, logging, tests).

## Workflow

### 1. Distinguish JWS vs JWE

| Form | Segments | Role |
| --- | --- | --- |
| **JWS** (signed JWT) | 3: header.payload.signature | Integrity / authenticity |
| **JWE** (encrypted) | 5: header.encrypted_key.iv.ciphertext.tag | Confidentiality (+ integrity of ciphertext) |

```text
JWE compact: BASE64URL(ProtectedHeader) . BASE64URL(EncryptedKey) .
             BASE64URL(IV) . BASE64URL(Ciphertext) . BASE64URL(AuthTag)
```

Decode **only** the protected header (no trust): record `alg`, `enc`, `kid`, `zip`,
`cty`, `typ`, ephemeral keys (`epk` for ECDH-ES). Payload is ciphertext until decrypt.

### 2. Map `alg` (key management) vs `enc` (content encryption)

| Layer | Purpose | Common values |
| --- | --- | --- |
| **`alg`** | How the Content Encryption Key (CEK) is protected | `RSA-OAEP`, `RSA-OAEP-256`, `ECDH-ES`, `ECDH-ES+A256KW`, `A256KW`, `A128GCMKW`, `dir`, `PBES2-HS256+A128KW` |
| **`enc`** | How plaintext is encrypted with the CEK | `A128GCM`, `A192GCM`, `A256GCM`, `A128CBC-HS256`, … |

Rules of thumb:

- Prefer **AEAD** content encryption (`*GCM`) over legacy CBC+HMAC when designing.
- Prefer **asymmetric** or HSM-backed key wrap for multi-recipient / server-held private keys; avoid long-lived shared `dir` secrets in browsers.
- `dir` means the shared key **is** the CEK — key compromise decrypts all tokens.

### 3. Inventory keys and recipients

| Item | Capture |
| --- | --- |
| Who encrypts | AS, BFF, API, mobile client |
| Who decrypts | Resource server, gateway, single service |
| Key source | JWKS (`enc` use keys), KMS/HSM, static PEM, shared secret |
| `kid` policy | Pinned allow-list vs free header choice |
| Nested? | After decrypt, is plaintext a JWS (three parts)? |

For design: encrypt with recipient **public** key (`use: enc` in JWKS); never ship
decrypt private keys to untrusted clients.

### 4. Authorized assessment probes

Use only in-scope tokens and keys:

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Present JWE without decrypt capability on RS that must read claims | Fail closed or use opaque handle + server-side session |
| 2 | Strip/truncate segments; flip ciphertext bits | Reject (auth tag / parse fail) |
| 3 | Wrong `kid` or attacker-controlled key id for decrypt path | Reject; no file/URL fetch from header |
| 4 | Algorithm downgrade in header if library trusts JWE `alg`/`enc` alone | Server-pinned allow-list; reject unexpected pairs |
| 5 | Nested: decrypt succeeds but inner JWS not verified | Always verify inner JWS with pinned algs/keys |
| 6 | Shared `dir`/KW secret guessable (lab wordlist only) | Rotate; move to RSA-OAEP / ECDH-ES / KMS |
| 7 | Logs, URLs, or analytics store full five-part JWE | Treat as secret leak; `Cache-Control: no-store` |

**Critical:** ciphertext integrity fails open, or plaintext claims trusted after
decrypt **without** inner signature / binding when the threat model requires both.

### 5. Design and remediation themes

Apply `code-quality-standards` when implementing:

- Confidentiality need → JWE (or TLS + server-side storage); integrity of claims →
  **sign then encrypt** (JWS nested in JWE) or encrypt then sign only with a clear profile.
- Pin allowed (`alg`, `enc`) pairs server-side; never trust header alone.
- Separate **enc** keys from **sig** keys in JWKS; rotate with `kid`.
- Short token TTL; bind audience/issuer on **plaintext** claims after successful decrypt.
- Never log CEKs, private keys, or full JWE; redact to `kid` + length/hash.
- Tests: wrong-key decrypt fail, bit-flip reject, nested verify required, allow-list reject.

## Routing

| Need | Skill |
| --- | --- |
| Signed JWT alg/none/confusion/kid/jku/claim forge | `api-auth-and-jwt-abuse` |
| `iss` / `aud` / `azp` after plaintext available | `jwt-audience-issuer-checks` |
| Refresh rotation, reuse, storage | `jwt-refresh-token-patterns` |
| Device / DPoP / mTLS sender constraint | `device-binding-tokens` |
| Key/secret storage and rotation hygiene | `secrets-management-hygiene` |
| Secure implementation and tests | `code-quality-standards` |

**Selection:** **encrypt/decrypt structure, alg/enc, CEK, nested JWE** → **this skill**.
Signature-only JWT → `api-auth-and-jwt-abuse`. Claim party checks →
`jwt-audience-issuer-checks`. Code changes → `code-quality-standards`.

## Output Checklist

- [ ] Token form classified (3-part JWS vs 5-part JWE vs nested)
- [ ] Protected header: `alg`, `enc`, `kid`, `zip`, `cty`/`typ`, `epk` if any
- [ ] Encrypt/decrypt parties and key sources documented (`use: enc` vs `sig`)
- [ ] CEK path understood (wrap, ECDH, `dir`, KMS)
- [ ] Integrity behavior: tag failure, bit-flip, truncated segments
- [ ] Nested path: decrypt + mandatory inner JWS verify (or documented exception)
- [ ] Header-trust / kid / algorithm allow-list findings
- [ ] Logging/leak and storage risks noted; secrets redacted
- [ ] Remediation: pinned alg/enc, key separation, sign-then-encrypt profile, tests

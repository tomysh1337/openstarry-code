---
name: device-binding-tokens
description: >-
  High-level design and authorized assessment of device-bound and proof-of-possession
  tokens (DPoP-style, mTLS/cnf, sender-constrained access tokens). Use when APIs,
  mobile apps, or SPAs claim tokens are bound to a key, device, or TLS client cert,
  or when stolen Bearer tokens must not be replayable from another client.
---

# Device Binding Tokens (DPoP-Style)

High-level methodology for **sender-constrained** / **device-bound** access (and
sometimes refresh) tokens: DPoP-style proofs, certificate thumbprint binding
(`cnf.x5t#S256`), and related possession checks. Complements JWT crypto review and
refresh lifecycle; does not replace them.

Authorized apps, labs, CTFs, and named engagement targets only.

## When To Use

| Situation | Direction |
| --- | --- |
| `DPoP` header, `token_type=DPoP`, or `cnf.jkt` / `cnf.x5t#S256` claims | **This skill** (primary) |
| mTLS-bound access tokens, mutual-TLS client cert at RS | **This skill** |
| Design: prevent replay of stolen Bearer from another device/browser | **This skill** |
| Assess whether “device binding” is real PoP vs soft device-id claim | **This skill** |
| Access JWT alg/kid/jku/claim forgery only | `api-auth-and-jwt-abuse` |
| Refresh rotation, reuse detection, storage | `jwt-refresh-token-patterns` |
| Soft `device_id` claim with no key material (no PoP) | Document as **weak binding**; still map here, then JWT/session skills |
| No authorization for live auth APIs | **Do not use** actively |

Keywords: DPoP, RFC 9449, proof-of-possession, sender-constrained, `cnf`, `jkt`,
mTLS token binding, device-bound token, `htm`/`htu`/`ath`/`jti`/`nonce`.

## Scope And Authorization

- Owned apps, labs, or **named** engagement targets only. No third-party keys/certs.
- Treat private keys, client certs, DPoP proofs, and tokens as credentials: redact;
  store offline; rotate after demos if production was involved.
- Prefer non-destructive proofs. Implementation pairs with `code-quality-standards`.

## Workflow

### 1. Classify the binding mechanism

| Mechanism | Signals | What must be proven |
| --- | --- | --- |
| **DPoP** | `DPoP` JWT header; AS/RS docs; `cnf.jkt` | Possession of DPoP private key per request |
| **mTLS / cert-bound** | Client cert required; `cnf.x5t#S256` | Same cert as at token issue (or bound thumbprint) |
| **Hybrid** | DPoP + refresh cookie / BFF | Document both layers |
| **Soft device claim** | `device_id`, `did` in JWT only | Usually **not** PoP — replayable if JWT leaks |

Capture: token location (header/cookie), binding type, where the key lives
(hardware, OS keystore, browser, software), and which endpoints enforce binding.

### 2. Map issuance and use

1. Login / token endpoint → access (+ optional refresh); note `token_type`, `cnf`.
2. Resource request with proof (DPoP JWT or mTLS) → success baseline.
3. List who verifies: AS only, RS only, gateway, or BFF.

```http
GET /resource HTTP/1.1
Host: api.example
Authorization: DPoP <access_token>
DPoP: <dpop_proof_jwt>
```

Record DPoP JWT claims when present: `htm`, `htu`, `iat`, `jti`, `ath`, `nonce`.

### 3. Core binding probes (authorized, dual-client)

One accept/reject pair per row with **keys/tokens you control**:

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Access token without any proof / client cert | Reject (or document intentional Bearer fallback) |
| 2 | Valid token + proof signed by **other** key | Reject |
| 3 | Proof for wrong HTTP method/URL (`htm`/`htu`) | Reject |
| 4 | Replay same DPoP `jti` (or same proof) | Reject or single-use within window |
| 5 | Stale `iat` / missing required `nonce` when AS sends nonce | Reject |
| 6 | `ath` missing or not hash of access token (when required) | Reject |
| 7 | Token with `cnf.jkt` A used under key B | Reject |
| 8 | mTLS: token issued under cert A presented on cert B | Reject |
| 9 | Refresh without same binding policy as access | Document; escalate lifecycle gaps |

**High severity:** stolen access token usable from a second client with **no**
matching private key or cert.

### 4. Soft binding and bypass surfaces

- `device_id` / install-id headers that the server trusts **without** crypto PoP.
- Binding enforced only on some routes (`/payments` yes, `/export` no).
- Gateway strips client cert or DPoP; RS sees plain Bearer.
- Clock skew windows that accept ancient DPoP `iat`.
- Public clients storing DPoP keys in XSS-reachable JS memory — binding weakens
  under XSS (note residual risk; not a substitute for output encoding).

### 5. Remediation themes (`code-quality-standards`)

- Prefer real PoP: **DPoP** (RFC 9449-style) or **mTLS cert-bound** access tokens.
- Embed and **enforce** `cnf` (jkt or x5t#S256) at every protected RS path.
- Validate proof signature, `htm`/`htu`, freshness, `jti` uniqueness, `ath`, nonce.
- Short access TTL; pair refresh with same binding class via
  `jwt-refresh-token-patterns` (opaque refresh + rotation + family revoke).
- Never log private keys, full proofs, or raw tokens; `Cache-Control: no-store`.
- Tests: wrong-key reject, missing-proof reject, htm/htu mismatch, jti replay.

## Routing

| Need | Skill |
| --- | --- |
| Access JWT alg/kid/jku/claim forgery, weak HMAC | `api-auth-and-jwt-abuse` |
| Refresh rotation, reuse detection, storage, logout | `jwt-refresh-token-patterns` |
| Secure implementation, secrets, logging, tests | `code-quality-standards` |
| OAuth AS refresh / PKCE / redirect (if AS-centric) | `oauth-oidc-misconfiguration` / `oauth-pkce-checklist` |
| Cookie CSRF when hybrid cookie + PoP | `csrf-cross-site-request-forgery` |

**Selection:** device/key/cert **binding and PoP enforcement** → **this skill**.
Token crypto alone → `api-auth-and-jwt-abuse`. Refresh lifecycle alone →
`jwt-refresh-token-patterns`. Code changes → always apply `code-quality-standards`.

## Output Checklist

- [ ] Binding type classified (DPoP / mTLS / hybrid / soft claim only)
- [ ] Issuance path, `cnf` claims, `token_type`, verifying party documented
- [ ] Baseline success with correct key/cert recorded
- [ ] Missing proof, wrong key, wrong htm/htu, jti/nonce/`ath` results captured
- [ ] Soft device-id or partial-route enforcement gaps noted
- [ ] Residual XSS/key-exfil risk stated without overclaiming PoP strength
- [ ] JWT crypto issues handed to `api-auth-and-jwt-abuse` when in scope
- [ ] Refresh/device-list lifecycle handed to `jwt-refresh-token-patterns`
- [ ] Remediation + tests sketched under `code-quality-standards`; evidence redacted

## Rules

- Authorized dual-client tests only; never exfiltrate or replay third-party keys.
- Do not call a `device_id` string claim “device-bound” without PoP evidence.
- One clean wrong-key reject/accept proof beats bulk spraying; redact tokens/proofs.
- High-level skill: cite AS/library docs for wire formats; do not invent schemes.

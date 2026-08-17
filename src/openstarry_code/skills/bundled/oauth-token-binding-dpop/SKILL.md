---
name: oauth-token-binding-dpop
description: >-
  Authorized design and assessment of OAuth Demonstrating Proof of Possession
  (DPoP) and sender-constrained access tokens in the RFC 9449 style: DPoP proofs,
  htm/htu binding, nonce challenges, cnf.jkt key thumbprints, and Bearer vs DPoP
  enforcement. Use when AS/RS traffic shows DPoP headers, token_type=DPoP,
  cnf.jkt, or when stolen Bearer tokens must not replay from another client.
---

# OAuth Token Binding (DPoP / RFC 9449)

Focused methodology for **OAuth DPoP** and **sender-constrained** access tokens
(RFC 9449-style): proof JWTs, `htm`/`htu` binding, server nonces, and key
confirmation at AS and RS. Complements device PoP and JWT crypto; not a substitute
for OAuth redirect/PKCE review.

## Scope And Authorization

- **Authorized / lab / owned only.** Named engagement targets, CTFs, apps you own.
  Do not attack third-party IdPs or production clients outside written scope.
- Treat DPoP private keys, proofs, tokens, and nonces as credentials: redact,
  store offline, rotate after production demos.
- Prefer dual-client **accept/reject** evidence with keys **you control**. No
  unauthorized exploit PoCs, bulk third-party token replay, or out-of-scope key theft.
- Implementation work pairs with `code-quality-standards`.

## When To Use

| Situation | Direction |
| --- | --- |
| `DPoP` header, `Authorization: DPoP …`, `token_type: DPoP` | **This skill** (primary) |
| Access token has `cnf.jkt`, or AS advertises DPoP | **This skill** |
| Design: block replay of stolen access tokens from another client | **This skill** |
| “Bound token” may be soft `device_id` (no crypto PoP) | Label weak; then JWT/session skills |
| mTLS / general device PoP without OAuth DPoP focus | `device-binding-tokens` |
| JWT alg/kid/jku forgery or claim tampering alone | `api-auth-and-jwt-abuse` |
| redirect_uri, PKCE, state, OIDC mix-up, code interception | `oauth-oidc-misconfiguration` |
| No authorization for live token/resource endpoints | **Do not use** actively |

Keywords: RFC 9449, DPoP, sender-constrained, PoP, `htm`/`htu`/`ath`/`jti`/`nonce`, `cnf.jkt`, `DPoP-Nonce`, Bearer vs DPoP.

## Workflow

1. **Confirm role split and baseline**  
   Record AS token endpoint, RS APIs, client type (public vs confidential), and
   whether DPoP is required or optional. Capture one successful issuance and one
   successful RS call with a lab-controlled proof key.

   ```http
   POST /token HTTP/1.1
   Host: as.example
   DPoP: <proof_jwt>
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&code=...&code_verifier=...
   ```

   ```http
   GET /resource HTTP/1.1
   Host: api.example
   Authorization: DPoP <access_token>
   DPoP: <proof_jwt>
   ```

2. **Decode the DPoP proof JWT**  
   Header: `typ: dpop+jwt`, asymmetric `alg` (ES256/RS256…), embedded public `jwk`.
   Payload: `htm` (method), `htu` (URI without fragment), `iat`, `jti`, optional
   `ath` (hash of access token at RS), optional `nonce` (when `DPoP-Nonce` issued).

   **Good:** ES256; `jwk` matches token `cnf.jkt`; `htm`/`htu` match the wire
   request; fresh `iat`; unique `jti`; `ath` present at RS.  
   **Bad:** HS256 “proof”; missing `jwk`; wrong/loose `htu`; forever-reusable
   `jti`; no `ath` while claiming RFC 9449 RS mode.

3. **Key binding vs Bearer (dual-client probes)**  
   With two clients and keys you control:

   | # | Probe | Secure outcome |
   | --- | --- | --- |
   | 1 | Token as `Authorization: Bearer` (no DPoP) | Reject if DPoP-only; else document **Bearer fallback** |
   | 2 | Valid token + proof signed by **other** key | Reject (`cnf.jkt` mismatch) |
   | 3 | Wrong `htm` (GET proof on POST) | Reject |
   | 4 | Wrong `htu` (host/path/query or http vs https) | Reject |
   | 5 | Replay same proof / `jti` within window | Reject or single-use |
   | 6 | Stale `iat` outside skew policy | Reject |
   | 7 | Missing or wrong-token `ath` (RS) | Reject when `ath` required |
   | 8 | Token without `cnf.jkt` under DPoP scheme | Document incomplete binding |
   | 9 | Token endpoint skips proof when DPoP mandated | Document AS gap |

   **High severity:** stolen access token works from a second client with **no**
   matching DPoP private key (classic Bearer replay).

4. **Nonce challenge path**  
   If AS/RS returns `DPoP-Nonce`: bare proof fails; proof with matching `nonce`
   claim succeeds. **Good:** short-lived/single-use. **Bad:** ignored, static, or
   not tied to the proof key.

5. **Issuance binding and coverage**  
   Confirm access token `cnf.jkt` matches the DPoP key used at the token endpoint;
   note `token_type` (`DPoP` vs `Bearer`) and whether refresh shares PoP policy.
   Partial route enforcement (e.g. only `/payments`) is a binding gap. Hand refresh
   rotation/reuse to `jwt-refresh-token-patterns` when lifecycle dominates.

6. **Soft claims and handoffs**  
   `device_id` without crypto PoP is not DPoP—stolen JWT still replays. JWT crypto
   → `api-auth-and-jwt-abuse`; OAuth redirect/code → `oauth-oidc-misconfiguration`;
   mTLS/device umbrella → `device-binding-tokens`.

7. **Remediation themes**  
   Require DPoP at AS and RS; reject unbound Bearer under sender-constrained policy.
   Enforce signature, `htm`/`htu`, `iat`, `jti`, `ath`, nonce, and `cnf.jkt`. Short
   access TTL; bind refresh consistently. DPoP is not XSS defense. Tests: wrong-key,
   missing proof, htm/htu mismatch, jti replay, nonce fail.

## Routing

| Need | Skill |
| --- | --- |
| Broader device PoP, mTLS / `cnf.x5t#S256`, soft device umbrella | `device-binding-tokens` |
| Access JWT alg/kid/jku, weak HMAC, claim forgery | `api-auth-and-jwt-abuse` |
| OAuth redirect, PKCE, state, code leak, OIDC mix-up | `oauth-oidc-misconfiguration` |
| Refresh rotation, reuse detection, storage | `jwt-refresh-token-patterns` |
| Implementation quality / hybrid BFF cookie CSRF | `code-quality-standards` / `csrf-cross-site-request-forgery` |

**Selection:** OAuth DPoP proof chain (htm/htu/nonce/jkt/Bearer vs DPoP) → **this skill**.
Device/mTLS → `device-binding-tokens`; JWT crypto → `api-auth-and-jwt-abuse`;
AS redirect/PKCE → `oauth-oidc-misconfiguration`.

## Output Checklist

- [ ] AS/RS roles, client type, DPoP required vs optional documented
- [ ] Baseline success: token issuance + RS call with controlled key
- [ ] Proof claims reviewed: `htm`, `htu`, `iat`, `jti`, `ath`, `nonce`, `jwk`
- [ ] Access token `cnf.jkt` / `token_type` captured (or absence noted)
- [ ] Probes: Bearer fallback, wrong key, wrong htm/htu, jti replay, ath, nonce
- [ ] Soft device-id or partial-route enforcement gaps listed
- [ ] Residual XSS/key-exfil risk stated without overclaiming PoP strength
- [ ] Handoffs: `device-binding-tokens`, `api-auth-and-jwt-abuse`, `oauth-oidc-misconfiguration` as needed
- [ ] Remediation + tests sketched; tokens/proofs/keys redacted

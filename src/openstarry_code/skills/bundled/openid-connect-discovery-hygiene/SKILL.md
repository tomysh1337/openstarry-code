---
name: openid-connect-discovery-hygiene
description: >-
  Authorized review of OpenID Connect discovery document hygiene:
  /.well-known/openid-configuration (and OAuth AS metadata), issuer exact-match,
  HTTPS-only endpoints, JWKS URI trust, advertised algorithms/grants, and
  cross-document consistency with live IdP behavior. Use when OIDC discovery,
  openid-configuration, OP metadata, issuer mismatch, JWKS URI, or discovery
  document hardening is in scope for owned apps, labs, CTFs, or named engagements.
---

# OpenID Connect Discovery Hygiene

Hardening and authorized assessment of **OIDC Provider (OP) discovery** and related
**OAuth AS metadata**: advertised fields, client trust, live endpoint match — not full
OAuth redirect/PKCE or full ID-token claim validation.

## When To Use

- Reviewing or publishing `/.well-known/openid-configuration` (or AS metadata).
- Clients fail with issuer mismatch, wrong JWKS, or mixed HTTP/HTTPS metadata.
- Multi-tenant / multi-region IdPs where discovery `issuer` must equal token `iss`.
- Hardening advertised signing algs, grants, response types, or endpoint URLs.
- Keywords: OIDC discovery, openid-configuration, OP metadata, JWKS URI, issuer URL,
  authorization_endpoint, token_endpoint, userinfo_endpoint.

**Not primary for:** OAuth redirect/`state`/PKCE → `oauth-oidc-misconfiguration`; ID token
`nonce`/`at_hash` → `oidc-id-token-validation`; RS `iss`/`aud` → `jwt-audience-issuer-checks`;
JWT crypto → `api-auth-and-jwt-abuse`.

## Workflow

### 1. Fetch and pin the discovery document

| Step | Action |
| --- | --- |
| Location | `GET {issuer}/.well-known/openid-configuration` (issuer path/trailing-slash exact) |
| Transport | HTTPS only; valid cert; no cleartext redirect that rewrites issuer |
| Cache | Note `Cache-Control` / ETag; stale CDN copies pin old JWKS or endpoints |
| Alternate | Compare `/.well-known/oauth-authorization-server` if both exist |

Save a redacted copy: status, final URL after redirects, response headers.

### 2. Required fields and issuer hygiene

| Field | Hygiene rule |
| --- | --- |
| `issuer` | HTTPS URL; **exact** string used as token `iss` (scheme, host, port, path, slash) |
| `authorization_endpoint` | HTTPS; reachable; matches real authorize route |
| `token_endpoint` | HTTPS; not a debug/mock or wrong-environment host |
| `jwks_uri` | HTTPS; this OP’s keys only; not attacker-influenced host |
| `response_types_supported` | Only intended types (prefer `code`; drop unused `token`/hybrid) |
| `subject_types_supported` | Documented (`public` / `pairwise`) |
| `id_token_signing_alg_values_supported` | RS256/ES256/EdDSA preferred; **no** `none`; no weak unused algs |

**Critical:** ID/access token `iss` must **byte-for-byte equal** discovery `issuer`.

### 3. Endpoint and URL hygiene

| Check | Secure baseline |
| --- | --- |
| All URLs HTTPS | authorize, token, JWKS, userinfo, end_session, registration |
| Host consistency | Trusted OP hosts only; no undocumented third-party origins |
| Internal leakage | No staging-only, RFC1918, or admin paths in **production** discovery |
| `userinfo_endpoint` | HTTPS; auth required; scope-bounded attributes |
| `registration_endpoint` | Absent or strongly protected if DCR is not a product feature |
| PAR / mTLS aliases | If advertised, live behavior matches metadata |

Probe only **in-scope** hosts to confirm advertised paths behave as OIDC/OAuth.

### 4. Cryptography, grants, and JWKS

| Area | Hygiene |
| --- | --- |
| Signing / encryption algs | Advertise only what the OP uses and clients must accept |
| `token_endpoint_auth_methods_supported` | Prefer `private_key_jwt` / mTLS where fit; no weak-only public-client story |
| Grant types | Do not advertise `password` or implicit-style grants if disabled |
| PKCE | `code_challenge_methods_supported` includes `S256` |
| JWKS | TLS + JSON keys; every live signing `kid` present; controlled retirement |
| Multi-tenant | Per-issuer discovery; never serve tenant-B keys under tenant-A issuer |

Clients must not prefer token-header `jku`/`x5u` over pinned discovery JWKS
(`api-auth-and-jwt-abuse` for header attacks).

### 5. Consistency matrix and RP consumption

| Claim in discovery | Verify |
| --- | --- |
| `issuer` | Equals token `iss` and client configured issuer |
| `jwks_uri` keys | Validate a real ID/access token signature |
| authorize / token URLs | Test client happy-path hits these endpoints |
| response / grant types | Unsupported types rejected at runtime |

RP rules (pair `code-quality-standards`): discover from configured issuer; reject metadata
whose `issuer` ≠ config; bounded TTL cache; re-fetch unknown `kid` only from pinned
`jwks_uri`; avoid hardcoding stale authorize/token URLs.

### 6. Remediation themes

- One canonical HTTPS issuer; exact-match in docs, tokens, and clients.
- HTTPS-only endpoints; drop unused grants, hybrid/implicit, and weak algs from ads **and** policy.
- Protect/disable DCR; lock down PAR if exposed; align CDN cache with key rotation.
- Separate discovery per environment (dev/stage/prod issuers).

## Routing

| Need | Skill |
| --- | --- |
| Discovery / OP metadata hygiene | **This skill** |
| OAuth redirect, `state`, PKCE, code flow | `oauth-oidc-misconfiguration` |
| ID token `nonce`, `at_hash`, `auth_time`, skew | `oidc-id-token-validation` |
| RS JWT `iss` / `aud` / `azp` | `jwt-audience-issuer-checks` |
| `alg` none, `kid`/`jku`, weak HMAC | `api-auth-and-jwt-abuse` |
| Refresh token lifecycle | `jwt-refresh-token-patterns` |
| SAML metadata (not OIDC) | `saml-sso-basics` |
| Implementation quality and tests | `code-quality-standards` |

**Selection:** primary for the **discovery document** / OP-AS metadata artifact. Token claim
checks and OAuth browser flows are helpers, not replacements.

## Output Checklist

- [ ] Discovery URL(s), redirects, TLS, cache headers recorded
- [ ] `issuer` exact value; match to token `iss` and client config
- [ ] Required OIDC fields present; HTTPS on all security-sensitive endpoints
- [ ] `jwks_uri` TLS, key set, `kid` coverage vs live tokens
- [ ] Advertised algs, grants, response types, auth methods vs actual policy
- [ ] No prod leakage of internal/staging hosts; DCR/registration posture noted
- [ ] Metadata vs live consistency; client pin/cache guidance
- [ ] Remediation: canonical issuer, HTTPS-only, least-advertised surface, rotation cache
- [ ] Secrets/tokens redacted; scope limits respected

## Scope And Authorization

- Owned apps, labs, CTFs, or **written** scope naming the OP/issuer and clients; prefer staging.
- Do not brute-force, flood, or reconfigure third-party SaaS IdP production beyond **your**
  app registration and any IdP project **explicitly** in scope.
- Fetch discovery/JWKS only for in-scope issuers; redact secrets, private keys, and PII.
- Non-destructive first: compare documents; validate with **test clients you control**; production IdP config changes need change control.
- Authorized hygiene only — not phishing, code theft, or cross-tenant abuse.

---
name: oauth-client-authentication
description: >-
  Authorized design and assessment of OAuth 2.0 / OIDC client authentication at
  the token and related client-auth endpoints: none, client_secret_basic/post,
  client_secret_jwt, private_key_jwt, and mTLS (tls_client_auth /
  self_signed_tls_client_auth). Use when registering clients, reviewing AS
  token_endpoint_auth_methods, hardening confidential clients, or testing
  client-credential and assertion authentication under explicit scope.
---

# OAuth Client Authentication Methods

How the **client** proves identity to the authorization server (AS)—not end-user
login and not resource-server JWT crypto alone. Focus: `token_endpoint_auth_method`
and equivalent binding on token, revoke, introspect, and PAR.

## When To Use

| Situation | Direction |
| --- | --- |
| Token / introspection / revocation / PAR needs **client auth** | **This skill** |
| Registered or discovered `token_endpoint_auth_method(s)` | **This skill** |
| `client_secret_*`, `*_jwt`, or mTLS client auth in scope | **This skill** |
| Public client claims `none` but ships a “secret” | **This skill** |
| Client-credentials (M2M) hardening | **This skill** |
| Redirect / state / code leak / mix-up | `oauth-oidc-misconfiguration` |
| PKCE challenge/verifier only | `oauth-pkce-checklist` |
| Access JWT alg/kid on RS | `api-auth-and-jwt-abuse` |
| DPoP / cert-bound access tokens | `device-binding-tokens` / `oauth-token-binding-dpop` |

Keywords: client authentication, `client_secret`, `client_assertion`,
`private_key_jwt`, `client_secret_jwt`, mTLS, `tls_client_auth`, confidential vs
public client, RFC 6749 / 7523 / 8705.

## Workflow

### 1. Classify client and registered method

| Field | Capture |
| --- | --- |
| Client type | public (SPA/native) vs confidential (server/BFF/M2M) |
| Registered method | admin UI, dynamic registration, or metadata |
| Discovery | `token_endpoint_auth_methods_supported` |
| Credentials | secret, JWKS/`jwks_uri`, client cert DN/SAN |
| Auth-required endpoints | token, revoke, introspect, device, PAR |

**Rule:** public → `none` (+ PKCE for auth code). Confidential → secret, JWT
assertion, or mTLS. Never treat SPA/mobile-embedded strings as confidential secrets.

### 2. Method map

| Method | Client proof | Prefer when |
| --- | --- | --- |
| `none` | `client_id` only | Public clients + PKCE |
| `client_secret_basic` | HTTP Basic `id:secret` | Confidential; encoding care |
| `client_secret_post` | Body id + secret | Confidential; no body logs |
| `client_secret_jwt` | HMAC JWT `client_assertion` | Confidential; short TTL |
| `private_key_jwt` | Asymmetric JWT assertion | Strong M2M / multi-instance |
| `tls_client_auth` | mTLS; AS maps cert → client | High-assurance gateways |
| `self_signed_tls_client_auth` | mTLS self-signed via JWKS | Dynamic software clients |

```http
POST /token HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<ID>
&client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
&client_assertion=<JWT>
```

Assertion claims (typical): `iss`/`sub` = `client_id`; `aud` = token endpoint (or
issuer per profile); fresh `exp`/`jti`; alg pinned (HS* for secret JWT; RS/ES/EdDSA
for private_key_jwt).

### 3. Assessment probes (clients you control)

| # | Probe | Secure behavior |
| --- | --- | --- |
| 1 | Wrong/empty secret or missing Basic | `invalid_client` |
| 2 | Confidential accepts `none` / omitted secret | Reject (finding if accepted) |
| 3 | Public binary “secret” used as confidential | Reclassify public; policy finding |
| 4 | Wrong registered method only (basic vs post) | Reject if single method set |
| 5 | JWT: bad `aud`, expired, reused `jti`, alg none | Reject |
| 6 | `private_key_jwt` with unregistered key / bad `kid` | Reject |
| 7 | mTLS: no/wrong cert or other client’s cert | Reject |
| 8 | Token requires auth; revoke/introspect does not | Document; align all endpoints |

**High severity:** tokens for a confidential client without valid client auth.

### 4. Hygiene and remediation

With `code-quality-standards`: one primary method per client; hash/encrypt secrets;
rotate with dual-valid window; prefer `private_key_jwt` or mTLS over long-lived
shared secrets; pin assertion `aud`; require `jti` + short `exp`; never log secrets
or full assertions; lock down dynamic registration of methods/JWKS/certs.

- Public: `none` + PKCE (`oauth-pkce-checklist`); no embedded client_secret.
- Confidential web: BFF holds secret/key; browser never sees it.
- M2M: least-privilege scopes; short access TTL; rotate and revoke on compromise.

## Routing

| Need | Skill |
| --- | --- |
| Redirect, state, nonce, code leak, mix-up | `oauth-oidc-misconfiguration` |
| PKCE S256 / verifier binding | `oauth-pkce-checklist` |
| ID token RP validation | `oidc-id-token-validation` |
| RS JWT alg/kid/jku/claims | `api-auth-and-jwt-abuse` |
| `iss`/`aud` wrong-party acceptance | `jwt-audience-issuer-checks` |
| DPoP / cert-bound access tokens | `device-binding-tokens` / `oauth-token-binding-dpop` |
| Refresh rotation and storage | `jwt-refresh-token-patterns` |
| Multi-vector ATO including OAuth | `account-takeover-methodology` |
| Secure implementation and tests | `code-quality-standards` |

**Selection:** how the **client authenticates to the AS** → **this skill**. Browser
flow abuse → `oauth-oidc-misconfiguration`. Token PoP at RS → DPoP/device skills.

## Output Checklist

- [ ] Client type, `client_id`, registered method(s), discovery support
- [ ] Endpoints requiring client auth mapped
- [ ] Baseline success with correct method
- [ ] Wrong/missing secret, method confusion, public-as-confidential results
- [ ] JWT assertion or mTLS probes as applicable
- [ ] Secret exposure surface (repo, mobile, logs) noted
- [ ] Remediation: single method, rotation, key/cert pin, no public secrets
- [ ] Evidence redacted; residual risks routed to related skills

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only. Prefer test
  `client_id`s and credentials **you control** on in-scope authorization servers.
- Do not brute-force production client secrets beyond agreed limits; do not attack
  third-party IdP client registries outside written scope.
- Treat client secrets, private keys, mTLS material, assertions, and tokens as
  credentials: redact; store offline; rotate after production demos.
- Non-destructive first: accept/reject pairs with dual clients you own. Pair code
  fixes with `code-quality-standards`.

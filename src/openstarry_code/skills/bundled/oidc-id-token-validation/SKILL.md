---
name: oidc-id-token-validation
description: >-
  Authorized validation and assessment of OpenID Connect ID tokens: iss, aud,
  exp/nbf, nonce, signature via JWKS, and azp/at_hash checks. Use when an RP
  or API accepts id_token JWTs after OIDC login, hybrid flow, or token exchange
  and you must verify claim binding or prove missing validation.
---

# OIDC ID Token Validation

Focused methodology for **OpenID Connect `id_token`** acceptance: issuer, audience,
lifetime, nonce binding, and signature trust. Complements full OAuth flow testing
and generic JWT crypto abuse.

## When To Use

| Situation | Direction |
| --- | --- |
| RP/client validates (or should validate) an OIDC **`id_token`** | **This skill** |
| Claims under review: `iss`, `aud`, `exp`, `nbf`, `iat`, `nonce`, `azp`, `at_hash` | **This skill** |
| Hybrid / residual implicit / code + `id_token` response types | **This skill** (token checks) |
| Full OAuth: `redirect_uri`, `state`, PKCE, code leak, mix-up | `oauth-oidc-misconfiguration` |
| Resource-server access JWT: alg none, kid/jku, HS confusion | `api-auth-and-jwt-abuse` |
| Access + refresh lifecycle / rotation / reuse | `jwt-refresh-token-patterns` |
| SAML assertions (not OIDC JWT) | `saml-sso-basics` |
| No authorization for live auth surfaces | **Do not test actively** |

Keywords: `id_token`, OIDC Core, JWKS, `nonce`, audience, issuer, clock skew, `azp`.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only. Prefer staging IdPs and **test users**.
- Do **not** attack third-party IdP production beyond the **client/RP** integration and any IdP/tenant the program names.
- Treat `id_token`, access/refresh tokens, and codes as **credentials**: redact; store offline; rotate after production demos.
- Prefer non-destructive accept/reject evidence pairs. No mass login or lockout of real users.
- Assessment methodology only — not a guide to weaponize production IdPs at scale.

## Workflow

### 1. Map who validates what

| Field | Capture |
| --- | --- |
| Roles | IdP/AS, RP (client), optional resource server |
| Where checked | SPA library, BFF, mobile SDK, API gateway |
| Discovery | `/.well-known/openid-configuration` → `issuer`, `jwks_uri`, algs |
| Expected `aud` | Registered `client_id`(s) |
| Flow | auth code (+ PKCE), hybrid, legacy implicit |
| Nonce storage | Server session, cookie, SPA memory |

Decode payload **offline** only on tokens you may capture; do not publish live signatures.

### 2. Signature and key trust (baseline)

Confirm the verifier: (1) keys from **trusted** `jwks_uri` or pinned material—not attacker `jku`/`jwk` alone; (2) server-side alg allowlist (e.g. RS256/ES256), reject `none`; (3) `kid` maps to pinned JWKS. Deep alg/kid/jku forgery → `api-auth-and-jwt-abuse`. Stay here for **OIDC claim semantics**.

### 3. `iss` (issuer)

| Probe | Expected secure behavior |
| --- | --- |
| Omit `iss` | Reject |
| Wrong issuer (other IdP, http/https, trailing slash) | Reject |
| Exact discovery `issuer` | Accept only configured value(s) |
| Multi-tenant templates | Only registered tenants; no open suffix you control |

Accepting a foreign issuer → mix-up / cross-IdP risk (pair with `oauth-oidc-misconfiguration`).

### 4. `aud` (audience) and `azp`

| Probe | Expected secure behavior |
| --- | --- |
| Missing `aud` | Reject |
| Other client_id / API resource | Reject for this RP |
| Array with foreign client | Still require **this** `client_id` |
| Multi-aud without `azp` | Prefer require `azp` = this client |

**Baseline:** `aud` must include this RP’s `client_id` exactly—not a loose parent-string match.

### 5. `exp`, `nbf`, `iat` (lifetime)

| Probe | Secure behavior |
| --- | --- |
| After `exp` (or lab-signed expired) | Reject outside small skew |
| Future `nbf` | Reject until valid |
| Missing / unbounded `exp` | Require `exp`; cap max lifetime |
| Skew | Document ±1–5 min typical; avoid unbounded |

Replay a prior `id_token` after logout/`exp` when possible; one accept/reject pair is enough.

### 6. `nonce` (session binding)

When authorize included `nonce` (required for browser implicit/hybrid `id_token`; recommended for code flow at RP):

| Probe | Expected secure behavior |
| --- | --- |
| Omit / empty / wrong `nonce` | Reject if nonce was sent |
| Replay token from flow A into session B | Reject |
| Client never sent `nonce` but accepts any | Document residual CSRF/replay risk |

RP must compare `id_token.nonce` to the value **it generated and stored** for that session.

### 7. Related claims and remediation

- **`at_hash` / `c_hash`:** verify when access token or code is returned with `id_token`.
- **`auth_time` / `max_age`:** enforce re-auth freshness if requested.
- **`acr` / `amr`:** not client-asserted MFA proof without IdP policy.
- **Remediation:** pin JWKS + alg allowlist; require exact `iss` and `aud` (this `client_id`); enforce `exp`/`nbf` + skew; bind `nonce` to login session; prefer auth code + PKCE; validate `azp` on multi-aud; do not treat raw `id_token` as long-lived API session → `jwt-refresh-token-patterns`; implement per `code-quality-standards` (never log full tokens).

## Routing

| Need | Skill |
| --- | --- |
| `id_token` iss/aud/exp/nonce validation | **This skill** |
| OAuth flow: redirect_uri, state, PKCE, code, mix-up | `oauth-oidc-misconfiguration` |
| JWT alg/kid/jku/none forgery | `api-auth-and-jwt-abuse` |
| Access + refresh rotation, reuse, storage | `jwt-refresh-token-patterns` |
| PKCE public-client checklist | `oauth-pkce-checklist` |
| Multi-vector ATO including OIDC | `account-takeover-methodology` |
| Secure RP implementation | `code-quality-standards` |

**Selection:** OIDC **`id_token` claim acceptance** → this skill. Wire protocol → `oauth-oidc-misconfiguration`. Crypto/alg → `api-auth-and-jwt-abuse`. Refresh lifecycle → `jwt-refresh-token-patterns`.

## Output Checklist

- [ ] Authorization covers RP and any IdP/tenant exercised
- [ ] Discovery issuer, `jwks_uri`, client_id, verification location documented
- [ ] Signature/JWKS trust path recorded (or failure → JWT skill evidence)
- [ ] `iss`: exact match vs wrong/omit results
- [ ] `aud` / `azp`: this client_id required; foreign audience rejected
- [ ] `exp` / `nbf` / skew: expired and future-nbf rejected
- [ ] `nonce`: omit/swap/cross-session replay recorded
- [ ] `at_hash`/`c_hash`/`auth_time` noted if in flow
- [ ] Impact: unintended principal **or** secure reject baseline
- [ ] Remediation: pin keys/alg; enforce iss/aud/exp/nonce; prefer code+PKCE
- [ ] Tokens redacted; no third-party IdP abuse outside scope

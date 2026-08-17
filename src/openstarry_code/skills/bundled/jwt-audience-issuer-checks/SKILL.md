---
name: jwt-audience-issuer-checks
description: >-
  Authorized assessment and hardening of JWT issuer, audience, and authorized-party
  claims: missing, weak, multi-value, and cross-service acceptance of iss/aud/azp.
  Use when resource servers, API gateways, or OIDC relying parties verify Bearer or
  ID tokens and audience confusion, issuer mix-up, or azp handling is in scope.
---

# JWT Audience And Issuer Checks

Deep validation of **`iss`**, **`aud`**, and **`azp`** so a token minted for one
party is not accepted by another. Complements signature/`alg` work; not a full crypto skill.

## When To Use

- APIs or gateways accept JWTs where `iss` / `aud` are omitted, wildcarded, or only
  logged, not enforced.
- Multi-service IdP or shared JWKS: token for client/API **A** works on API **B**.
- OIDC / multi-audience access tokens; `azp` present or expected when `aud` is an array.
- Reviewing middleware: “verify signature only”, custom claim maps, or decode without
  audience options.
- Keywords: audience confusion, issuer not checked, token mix-up, wrong `client_id`,
  cross-tenant JWT.

**Not primary for:** pure `alg`/`kid`/`jku` forgery → `api-auth-and-jwt-abuse`; full
OIDC ID token stack (`nonce`, `at_hash`, clock skew) → `oidc-id-token-validation`;
OAuth redirect/`state`/PKCE → `oauth-oidc-misconfiguration`.

## Scope And Authorization

- Owned apps, labs, CTFs, or **named** engagement targets only. Prefer **test clients
  and users you control** on in-scope IdPs and resource servers.
- Do not mint or replay tokens against third-party IdPs or APIs outside written scope.
- Treat JWTs as credentials: redact PII; store captures offline; rotate after production
  demos if tokens could remain valid.
- Non-destructive first: prove accept/reject with claim swaps on **your** tokens.

## Workflow

### 1. Inventory expected parties

| Field | Capture |
| --- | --- |
| Token type | Access JWT, ID token, custom session JWT |
| Expected `iss` | Exact issuer URI(s) from discovery / config |
| Expected `aud` | API identifier, `client_id`, or resource indicator |
| `azp` policy | Required when multi-aud? Must equal trusted client? |
| Verifier | Library + options (`audience=`, `issuer=`, custom code) |
| Key source | JWKS URL, static PEM, multi-tenant key set |

Decode payload only (no trust): record `iss`, `aud` (string vs array), `azp`,
`client_id`, tenant ids, `exp`.

### 2. Issuer (`iss`) enforcement

| Probe | Secure behavior |
| --- | --- |
| Omit `iss` | Reject |
| Wrong issuer (other IdP / host / `http` vs `https`) | Reject |
| Trailing slash / case / port if config is exact-match | Reject unless documented |
| Issuer influenced by Host / `X-Forwarded-Host` | Reject attacker-controlled iss |
| Token from IdP B accepted by RP for IdP A | Reject (mix-up) |

Evidence: same verify path; only `iss` differs — or a second in-scope issuer token.

### 3. Audience (`aud`) enforcement

| Probe | Secure behavior |
| --- | --- |
| Omit `aud` | Reject |
| `aud` = other API or other `client_id` | Reject |
| Multi-value `aud` missing this API’s identifier | Reject |
| Empty string / `*` / prefix match | Reject (no wildcards) |
| ID token used as access token (or reverse) | Reject via `aud` + type separation |

**Critical:** RS-B accepts a token whose only legitimate audience is RS-A or client-A
while signature and expiry still validate.

```text
aud: "api://service-a"  → call Service-B     (expect 401)
aud: ["client-x"]       → call unrelated API (expect 401)
aud omitted             → expect 401
```

### 4. Authorized party (`azp`)

When `aud` is multi-value, OIDC expects `azp` to name the authorized client. Some
access-token profiles use `azp` or `client_id` similarly.

| Probe | Secure behavior |
| --- | --- |
| Multi-`aud` without `azp` where policy requires it | Reject |
| `azp` ≠ trusted/presenting client | Reject |
| `azp` ignored if any `aud` member matches | Weak if client binding required |

State the deployment’s profile rule first; do not invent `azp` requirements.

### 5. Cross-service matrix

1. Obtain token for A (honest flow you control).
2. Present unchanged to B’s middleware.
3. Repeat with legitimately issued A vs B tokens (or authorized re-sign only in lab).
4. Record status and whether `sub` is accepted.

Tenant claims (`tid`, org) are **not** substitutes for `aud` unless documented
combined policy — both should hold.

### 6. Implementation and remediation

Apply `code-quality-standards` when fixing:

- Library allow-lists for exact `issuer` and `audience`; never decode-only.
- Do not select keys from unpinned token `iss` alone.
- Multi-tenant: map `iss`/`aud` to tenant before authz.
- Log claim failures without full JWTs; table tests for omit/wrong/multi-aud/bad `azp`.
- Pin `iss`; require this resource in `aud`; enforce `azp` for multi-aud per profile;
  keep alg/key pinning via `api-auth-and-jwt-abuse` remediation.

## Routing

| Need | Skill |
| --- | --- |
| `alg` none, confusion, `kid`/`jku`, weak HMAC, generic forge | `api-auth-and-jwt-abuse` |
| Full OIDC ID token (`nonce`, `at_hash`, `auth_time`, clock) | `oidc-id-token-validation` |
| OAuth redirect, `state`, PKCE, code flow | `oauth-oidc-misconfiguration` |
| Refresh lifecycle / rotation | `jwt-refresh-token-patterns` |
| Secure verifier implementation and tests | `code-quality-standards` |

**Selection:** primary for **wrong-party acceptance** via `iss`/`aud`/`azp`. Crypto →
`api-auth-and-jwt-abuse`. Full ID token RP checklist → `oidc-id-token-validation`.
Fixes → `code-quality-standards`.

## Output Checklist

- [ ] Token types, expected `iss`/`aud`/`azp` policy, verifier library/options
- [ ] Actual claims: `iss`, `aud` shape, `azp`, tenant/client identifiers
- [ ] Issuer probes: omit, wrong, mix-up across in-scope IdPs
- [ ] Audience probes: omit, cross-API, multi-value, wildcard/prefix
- [ ] `azp` / client-binding probes where multi-aud or profile requires it
- [ ] Cross-service matrix (token-for-A on B); impact; redacted evidence; allow-list remediation + tests

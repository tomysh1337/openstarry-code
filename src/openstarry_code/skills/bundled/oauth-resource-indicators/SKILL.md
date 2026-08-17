---
name: oauth-resource-indicators
description: >-
  Authorized design and assessment of OAuth 2.0 Resource Indicators (RFC 8707):
  the resource request parameter, absolute resource URIs, multi-resource grants,
  and audience-restricted access tokens for the indicated protected resource(s).
  Use when clients or authorization servers send or require resource= at authorize
  or token endpoints, when APIs accept tokens without resource-aligned aud, or when
  downscoping tokens to a specific API URI is in scope for owned/lab systems.
---

# OAuth Resource Indicators (RFC 8707)

Focused methodology for **RFC 8707 Resource Indicators**: clients name the target
protected resource; the AS binds tokens; the RS enforces audience. Complements
OAuth/OIDC and JWT `aud` work; not a full redirect/PKCE or DPoP skill.

## When To Use

| Situation | Direction |
| --- | --- |
| `resource=` on authorize and/or token requests | **This skill** (primary) |
| Multi-API AS: token for API A works on API B | **This skill** + `jwt-audience-issuer-checks` |
| Design: downscope access tokens to a specific API URI | **This skill** |
| Docs/discovery mention resource indicators / RFC 8707 | **This skill** |
| Only JWT `iss`/`aud` options, no OAuth `resource` | `jwt-audience-issuer-checks` |
| redirect_uri, PKCE, state, code interception | `oauth-oidc-misconfiguration` |
| DPoP / sender-constrained tokens | `oauth-token-binding-dpop` |
| No authorization for live AS/RS endpoints | **Do not use** actively |

Keywords: RFC 8707, resource indicator, `resource` parameter, resource URI,
audience-restricted access token, multi-resource, token downscoping, AS/RS split.

## Workflow

### 1. Map parties and expected resources

Record AS authorize/token URLs, client type, each RS canonical absolute URI, and
whether `resource` is required, optional, or ignored.

| Field | Capture |
| --- | --- |
| Client | public/confidential; which APIs it should reach |
| Resource URIs | absolute URIs (no fragment) the AS accepts |
| Where `resource` appears | authorize, token, both, or refresh |
| Token shape | opaque vs JWT; `aud` / resource claims |
| RS verifier | matching audience/resource or Bearer-any |

### 2. Validate resource URI form (RFC 8707)

Each `resource` value is an **absolute URI**; **fragments are not allowed**.
Multiple `resource` parameters may request multiple resources when supported.

```http
GET /authorize?...&resource=https%3A%2F%2Fapi.example%2F&...
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=...&resource=https%3A%2F%2Fapi.example%2F
```

| Check | Secure behavior |
| --- | --- |
| Relative path, bare host, opaque string | Prefer reject |
| URI with `#fragment` | Reject |
| `http` vs `https`, slash, port, case | Exact-match per AS docs |
| Unknown / unregistered resource | Reject (no silent global token) |

### 3. Authorization and token endpoint behavior

1. **Authorize with `resource`**: grant must be scoped to indicated resource(s).
2. **Token with `resource`**: access token audience must not exceed the grant;
   refresh may **downscope**, not expand beyond the original grant.
3. **Omit `resource`**: document default (broad, registered default, or error)—
   broad multi-API defaults are high risk.
4. **Multi-`resource`**: token audiences must not unlock non-listed APIs.

### 4. Audience binding probes (authorized dual-API)

With two in-scope resources (RS-A, RS-B) and a client you control:

| # | Probe | Secure outcome |
| --- | --- | --- |
| 1 | Token for A, call B | Reject at B |
| 2 | No `resource` / broad aud on A and B | Reject if required; else gap |
| 3 | Token for A+B, call A only | OK if multi-resource granted |
| 4 | Refresh `resource=B` after grant only A | Reject expansion |
| 5 | Refresh with subset of granted resources | Downscope only |
| 6 | Lookalike host/path as `resource` | Reject if unregistered |

**High severity:** token for one resource URI accepted by another unrelated RS.

### 5. JWT / opaque alignment and remediation

- JWT: `aud` (or profile resource claim) must match indicated resource(s); deep
  `iss`/`aud`/`azp` matrix → `jwt-audience-issuer-checks`.
- Opaque: introspection/gateway must resolve audience server-side.
- **Scope strings alone** are not a substitute for resource indicators across
  separate API security domains.

Apply `code-quality-standards` when implementing: AS allowlist absolute resource
URIs; bind grants and tokens; refuse expansion on refresh; RS enforce this
resource’s audience; clients send correct `resource` per API. Tests: wrong-resource
call, omit-resource policy, multi-resource downscope, fragment/relative reject,
refresh expansion deny.

## Routing

| Need | Skill |
| --- | --- |
| JWT `iss` / `aud` / `azp` matrix | `jwt-audience-issuer-checks` |
| OAuth redirect, PKCE, state, code leak, OIDC mix-up | `oauth-oidc-misconfiguration` |
| DPoP / sender-constrained tokens | `oauth-token-binding-dpop` |
| JWT crypto (`alg`/`kid`/`jku`) | `api-auth-and-jwt-abuse` |
| Refresh rotation / reuse detection | `jwt-refresh-token-patterns` |
| Secure AS/RS/client implementation | `code-quality-standards` |

**Selection:** primary when **`resource`** or RFC 8707 resource→audience binding
is the focus. JWT wrong-party without OAuth `resource` → `jwt-audience-issuer-checks`.
Classic OAuth client threats → `oauth-oidc-misconfiguration`. PoP → `oauth-token-binding-dpop`.

## Output Checklist

- [ ] AS/RS/client map; resource URI allowlist; where `resource` is sent
- [ ] URI validation: absolute, no fragment; unknown/lookalike rejected
- [ ] Authorize + token (+ refresh) with/without `resource` documented
- [ ] Multi-resource and downscope-vs-expand rules evidenced
- [ ] Cross-API probes: token-for-A on B; broad/default audience risk noted
- [ ] Token binding form: JWT `aud` / introspection / gap
- [ ] Remediation + tests; tokens and secrets redacted
- [ ] Handoffs: `jwt-audience-issuer-checks`, `oauth-oidc-misconfiguration`, `oauth-token-binding-dpop` as needed

## Scope And Authorization

- **Authorized / lab / owned only.** Named targets, CTFs, or systems you own. Do
  not exercise third-party AS/RS outside written scope.
- Prefer **test clients and resources you control**. Dual-API accept/reject
  evidence; no production token theft or cross-tenant abuse.
- Treat tokens, codes, and client secrets as credentials: redact, store offline,
  rotate after production demos. Non-destructive first under your accounts.
- Implementation and hardening pairs with `code-quality-standards`.

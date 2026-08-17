---
name: api-gateway-authz-patterns
description: >
  Design and review API gateway authorization: JWT/OIDC validation, API keys,
  mTLS, claims- and scope-based route guards, identity header injection to
  backends, deny-by-default routing, and trust-boundary hardening. Use when
  configuring or assessing Kong, Envoy, AWS API Gateway, Azure APIM, Apigee,
  NGINX, or similar edge gateways for authn/authz — not for pure mesh
  AuthorizationPolicy, object-level BOLA, or unauthorized third-party probes.
---

# API Gateway Authorization Patterns

Edge and product **API gateway** controls that authenticate callers, authorize
routes/methods/scopes, and safely forward identity to backends. Complements
app-layer authz; does not replace object-level checks.

## When To Use

| Situation | Direction |
| --- | --- |
| Gateway JWT/OIDC validate, issuer/aud/JWKS, claim maps | **This skill** |
| API key, usage plan, consumer credential at the edge | **This skill** |
| Client mTLS or mutual TLS termination at gateway | **This skill** |
| Route/method/path guards; scope or role required per route | **This skill** |
| Inject / strip identity headers (`X-User-Id`, JWT claims) to upstream | **This skill** |
| Deny-by-default listener; public vs private route split | **This skill** |
| App JWT forge / alg confusion without gateway config focus | `api-auth-and-jwt-abuse` |
| Object-level access after identity is solid (BOLA) | `idor-broken-object-authorization` |
| Istio mesh `AuthorizationPolicy` / PeerAuthentication | `istio-authz-basics` |
| Rate limits and quotas at the edge | `api-rate-limit-design` |

## Workflow

### 1. Map trust boundary and routes

1. Inventory gateways, stages/environments, listeners, and route tables.
2. Classify each route: public anonymous, authenticated, privileged/admin,
   internal-only (should not be on public listeners).
3. Note where TLS terminates and whether backends are private (VPC/mesh) or
   reachable if the gateway is bypassed.
4. Record auth plugins/filters in order (key auth → JWT → ACL → transform).

### 2. Authentication at the edge

| Mechanism | Secure direction | Common failure |
| --- | --- | --- |
| JWT / OIDC | Validate sig, `iss`, `aud`, `exp`/`nbf`; pin algorithms; JWKS HTTPS | Trust client `alg`; skip aud; stale JWKS |
| API key | Server-side lookup; key not in URL/query logs; rotate | Key in query string; shared global key |
| mTLS | Require client cert; map SAN/SPIFFE to consumer | Optional mTLS; accept any CA |
| Opaque token | Introspect or session store; short TTL | Cache forever; no revocation path |

Prefer **gateway validates**, backend **re-validates or trusts only signed
internal tokens** — never raw spoofable headers from the public internet.

### 3. Authorization patterns

1. **Deny-by-default:** unmatched routes 404/403; no open admin under `/*`.
2. **Route × method × scope:** e.g. `POST /admin/**` needs `admin` role or
   `write:admin` scope; split read vs mutate.
3. **Consumer ACL / plan:** bind consumers to groups; avoid one key for all APIs.
4. **Claim mapping:** map `sub`, tenant, roles into **internal** headers only
   after successful auth; strip those headers on ingress if present from client.
5. **Service-to-service:** separate credentials from end-user tokens; prefer
   mTLS or short-lived client credentials for upstream calls.
6. **Bypass paths:** health/metrics/docs — lock to internal networks or strip
   sensitive data; never leave debug proxies on public stages.

### 4. Identity propagation and strip rules

| Rule | Rationale |
| --- | --- |
| Strip `X-User-*`, `X-Role`, `X-Forwarded-User` from client | Prevent header spoofing past gateway |
| Inject identity only from validated token/cert | Backend must not treat client headers as truth |
| Prefer signed internal JWT or mesh identity over plain headers | Limits lateral spoof if network is flat |
| Do not log full tokens or API keys | Secret hygiene |

### 5. Validate and remediate

1. **Positive:** valid token/key/cert + allowed scope reaches backend as expected.
2. **Negative:** missing/expired/wrong-aud token; stripped vs injected header
   spoof; method mismatch; path normalization tricks (`/admin`, `/admin/`,
   encoded segments) if gateway normalizes differently from backend.
3. **Bypass:** direct-to-origin if DNS/LB still exposes upstream; alternate
   stage/version host; HTTP method override headers if gateway honors them.
4. Document residual risk: gateway authz ≠ object-level authz. Apply
   `code-quality-standards` to policy-as-code and gateway config reviews.

## Routing

| Need | Skill |
| --- | --- |
| Gateway JWT/OIDC, API key, mTLS, route/scope guards, header trust | **This skill** |
| JWT attack classes (alg none, confusion, kid/jku) | `api-auth-and-jwt-abuse` |
| iss/aud/exp claim validation depth | `jwt-audience-issuer-checks` |
| Object-level BOLA after identity works | `idor-broken-object-authorization` |
| API surface and OpenAPI recon | `api-recon-and-docs` |
| Mesh-level Istio authz | `istio-authz-basics` |
| Edge rate limit / quota design | `api-rate-limit-design` |
| Secrets, keys, JWKS material handling | `secrets-management-hygiene` |
| Config and policy code quality | `code-quality-standards` |

## Output Checklist

- [ ] Gateway product, stage/env, listeners, and route inventory
- [ ] Auth mechanisms per route (JWT/OIDC, key, mTLS, none)
- [ ] Deny-by-default and public vs privileged route split documented
- [ ] Scope/role/method guards mapped; overbroad `*` paths flagged
- [ ] Ingress strip + post-auth identity injection rules verified
- [ ] Positive and negative tests (401/403/bypass) evidenced
- [ ] Direct-origin / stage bypass risk noted
- [ ] Residual: object-level authz still required on backends
- [ ] Secrets/tokens redacted; rotation notes if keys exposed in tests
- [ ] Owners and follow-ups for residual gaps

## Scope And Authorization

- **In scope:** owned gateways, lab/CTF stacks, or written engagements that name
  the gateway accounts, stages, and routes you may configure or test.
- **Out of scope:** third-party APIs; production credential stuffing; disabling
  edge auth without change window and rollback; mass scanning unrelated hosts.
- Prefer read-only config export and staging canaries before production denies.
- Redact API keys, JWTs, client certs, and consumer secrets in reports
  (`secrets-management-hygiene`). Gateway success does not prove BOLA-safe
  backends — hand object access to `idor-broken-object-authorization`.
- Only exercise bypass and negative tests against assets you own or are
  explicitly authorized to assess.

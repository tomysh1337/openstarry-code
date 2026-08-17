---
name: envoy-ext-authz-basics
description: >
  Design, review, and troubleshoot Envoy external authorization (ext_authz):
  HTTP/network filter placement, gRPC vs HTTP auth services, CheckRequest/
  CheckResponse, failure_mode_allow, header mutation, and route-level
  overrides. Use when hardening or assessing owned Envoy/Istio edges with
  ext_authz, drafting authz filter YAML, debugging 403/denied-by-ext_authz,
  or validating fail-closed behavior — not for unauthorized third-party proxy
  attacks or pure app-layer JWT forgery without the Envoy hop.
---

# Envoy External Authorization (ext_authz) Basics

Hardening and authorized assessment of **Envoy `ext_authz`**: call an external
auth service before upstream, enforce allow/deny, mutate headers, and avoid
fail-open or bypass misconfig. Covers standalone Envoy and mesh edges that
surface the same filter (Istio CUSTOM / EnvoyFilter).

## When To Use

| Situation | Direction |
| --- | --- |
| Configure/review `envoy.filters.http.ext_authz` or network ext_authz | **This skill** |
| gRPC (`Check`) vs HTTP auth service contract and timeouts | **This skill** |
| `failure_mode_allow`, denied body, status mapping | **This skill** |
| Header allow/deny lists, auth response → upstream headers | **This skill** |
| Per-route disable/override, path skips, filter order | **This skill** |
| Debug 403 / denied-by-ext_authz / auth service 5xx | **This skill** |
| Istio ALLOW/DENY/mTLS without CUSTOM ext_authz | `istio-authz-basics` |
| App JWT alg/claims abuse (no Envoy filter focus) | `api-auth-and-jwt-abuse` |
| Object-level API authz (BOLA/IDOR) behind the proxy | `idor-broken-object-authorization` |

## Scope And Authorization

- **In scope:** org-owned Envoy/Istio/gateway configs, staging/lab clusters,
  CTF/lab proxies, written engagements naming listeners and auth services.
- **Out of scope:** third-party edges; flipping prod to `failure_mode_allow:
  true` or disabling ext_authz without change window and rollback; mass probing
  unrelated auth endpoints.
- Prefer **config inventory + staged canary** before cluster-wide deny or new
  auth hops. Treat auth tokens, mTLS client keys, and identity headers as
  secrets (`secrets-management-hygiene`). ext_authz is edge policy, not app
  object-level authz.

## Workflow

### 1. Inventory filter surface

1. Locate HTTP (or network) filter chains: bootstrap, CDS/LDS, Gateway API /
   Istio `EnvoyFilter` / `AuthorizationPolicy` CUSTOM.
2. Note **filter order**: ext_authz must run before routes that must be
   protected; after decode of needed headers/body if the auth service requires
   them.
3. Record auth cluster: address, TLS/mTLS to auth service, timeout, retry.
4. List path/method exclusions and per-route `ExtAuthzPerRoute` overrides.

### 2. Auth service protocol and contract

| Mode | Expect | Failure mode |
| --- | --- | --- |
| gRPC | `envoy.service.auth.v3.Authorization/Check` | Wrong API version; unary only |
| HTTP | Path + method; status 200 allow, non-200 deny | Treating 5xx as allow |
| Timeout | Explicit, short; match auth SLO | Hung requests; cascade |
| Identity to auth | Peer cert, JWT, cookies, metadata | Trusting client-spoofable headers |

Auth service should receive enough context (path, method, headers, optional
body) and return clear allow/deny. Prefer **fail closed** on auth errors.

### 3. Allow, deny, and header mutation

1. **Deny:** non-OK Check / non-2xx HTTP → Envoy rejects (configurable status /
   body). Confirm clients cannot force allow via crafted headers alone.
2. **Allow + headers:** only **auth-service-issued** identity headers
   (`x-user-id`, roles) should reach upstream; **strip client-supplied** copies
   of those names before or via `allowed_client_headers` / server header rules.
3. **Request body:** enable buffer only when auth needs body; cap size; note
   streaming/large-upload paths may skip or fail.
4. **Response headers from auth:** use for audit correlation; do not leak
   internal policy detail to untrusted clients.

### 4. failure_mode_allow and bypass risks

| Setting / pattern | Risk if wrong |
| --- | --- |
| `failure_mode_allow: true` | Auth down ⇒ **open** proxy |
| Per-route `disabled: true` | Shadow APIs / admin paths unprotected |
| Filter only on some listeners | Direct pod/port bypass of edge |
| Inclusive path skip (`/`) | Accidental global skip |
| Trust of `X-Forwarded-*` / spoofed identity | Confused deputy to upstream |
| Auth cluster cleartext on shared net | Token/header interception |

Production sensitive edges: **`failure_mode_allow: false`** unless a documented
break-glass with monitoring and time-box. Pair with network policy so workloads
are not reachable without the ext_authz hop when architecture requires it.

### 5. Validate and remediate

1. **Positive:** valid session/JWT/mTLS → 200 upstream; identity headers only
   from the auth path.
2. **Negative:** missing/invalid credentials → deny; forged identity headers
   stripped; auth down/timeout fail-closed; skips truly public only.
3. **Flag:** fail-open; wide disables; client headers as identity; no mTLS to
   auth on shared nets; filter after forward; missing deny/5xx alerts.
4. Ship config-as-code with rollback; `code-quality-standards` on YAML/Helm;
   JWT crypto flaws → `api-auth-and-jwt-abuse`.

## Routing

| Need | Skill |
| --- | --- |
| Envoy ext_authz, Check API, fail-open/header trust | **This skill** |
| Istio AuthorizationPolicy / PeerAuthentication | `istio-authz-basics` |
| App JWT attacks / token misuse | `api-auth-and-jwt-abuse` |
| Object-level API authz | `idor-broken-object-authorization` |
| Auth secrets, client keys, tokens | `secrets-management-hygiene` |
| Policy/filter YAML quality | `code-quality-standards` |
| Unknown gRPC auth wire/schema | `protobuf-grpc-reverse-engineering` |

## Output Checklist

- [ ] Scope: listeners, clusters, auth service, environments recorded
- [ ] Filter type (HTTP/network), order, per-route overrides listed
- [ ] Protocol (gRPC v3 vs HTTP), timeout, TLS/mTLS to auth service
- [ ] `failure_mode_allow` value; break-glass justification if true
- [ ] Client identity headers stripped; only auth-issued headers upstream
- [ ] Path/method public skips explicit and minimal
- [ ] Positive allow and negative deny/timeout tests evidenced
- [ ] Direct-to-upstream bypass considered (NetworkPolicy / mesh)
- [ ] Metrics/alerts on deny, auth 5xx, and fail-open paths
- [ ] Secrets per `secrets-management-hygiene`; evidence redacted
- [ ] Residual gaps with owner/expiry; rollback noted

## Rules

- **Owned or explicitly authorized proxies and auth services only.**
- Prefer fail-closed; treat `failure_mode_allow: true` as exceptional.
- Never trust client-supplied identity headers the auth service also sets.
- ext_authz is edge policy — apps still need object-level authz.
- Do not disable ext_authz or open fail-mode in prod without rollback.

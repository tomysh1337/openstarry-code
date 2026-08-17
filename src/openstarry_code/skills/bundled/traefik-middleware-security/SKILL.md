---
name: traefik-middleware-security
description: >
  Design and review Traefik security middlewares: Headers (HSTS/CSP/XFO),
  IPAllowList, BasicAuth/DigestAuth/ForwardAuth, RateLimit, InFlightReq,
  RedirectScheme, CORS, and middleware chains on routers/services. Use when
  hardening Traefik static/dynamic config or CRDs, fixing missing edge headers
  or open dashboards, reviewing auth/rate-limit middleware order, or assessing
  org-owned Traefik ingress — not for attacking third-party edges without permission.
---

# Traefik Middleware Security

Hardening and authorized assessment of **Traefik** edge middlewares: security
headers, IP allowlists, authn front-doors, rate and concurrency limits, HTTPS
redirects, CORS, and correct **chain** attachment on routers. Focus is the
proxy control plane you own — not application business logic behind it.

## When To Use

| Situation | Direction |
| --- | --- |
| Headers middleware (HSTS, CSP, XFO, nosniff, Referrer-Policy) | **This skill** |
| IPAllowList / deny public admin or metrics entrypoints | **This skill** |
| BasicAuth, DigestAuth, ForwardAuth (auth gate at edge) | **This skill** |
| RateLimit, InFlightReq, CircuitBreaker abuse controls | **This skill** |
| RedirectScheme HTTP→HTTPS; middleware chains on routers | **This skill** |
| CORS middleware allowlist; plugin/custom middleware risk | **This skill** |
| nginx / ingress-nginx header and TLS edge only | `nginx-security-headers` |
| Express/app middleware stacks | `express-middleware-security` |
| Mesh Istio AuthorizationPolicy / mTLS | `istio-authz-basics` |
| JWT token abuse beyond ForwardAuth plumbing | `api-auth-and-jwt-abuse` |
| Rate-limit bypass research (authorized) | `rate-limit-bypass-testing` |

Triggers: Traefik middleware, traefik.yml, dynamic config, IngressRoute,
Middleware CRD, entryPoints, insecure API/dashboard, ForwardAuth, rateLimit.

## Workflow

### 1. Inventory edge and middleware surface

1. Identify Traefik version and providers (file, Docker labels, Kubernetes CRD).
2. Map **entryPoints** (web, websecure, traefik, metrics), TLS hop, public vs internal routers.
3. List Middleware objects and which routers **reference** them
   (`middlewares:` / `traefik.http.routers.*.middlewares`). Unattached middleware is not a control.
4. Note API/dashboard exposure (`api.insecure`, `api.dashboard`, entrypoint bind).

```bash
# Owned/lab only
kubectl get middleware,ingressroute,ingressroutetcp -A
# File provider: review static + dynamic YAML; docker labels on owned compose
```

### 2. Security headers baseline

Use `headers` middleware (`stsSeconds`, `customResponseHeaders`, CSP). Stage strict CSP.

| Control | Hardened direction | Failure mode |
| --- | --- | --- |
| STS | `stsSeconds` ≥ 15552000; subdomains when ready | Missing on HTTPS; set before stable TLS |
| Frame / CSP | `frameDeny` or CSP `frame-ancestors` | Clickjackable admin UI |
| nosniff / Referrer | `contentTypeNosniff`; strict Referrer-Policy | MIME sniff / Referer leaks |
| browserXSSFilter | Prefer CSP over legacy XSS filter alone | False sense of safety |
| custom headers | Force security headers; avoid banner leaks | Conflict with app/CDN |

Verify on 200, 3xx, and error paths for each critical router host.

### 3. Authn and IP gates

1. **IPAllowList** — admin, metrics, dashboard, internal tools; derive source IP only via trusted LB hops.
2. **BasicAuth / DigestAuth** — users file out of git; HTTPS only. Prefer ForwardAuth/IdP for multi-app SSO.
3. **ForwardAuth** — internal auth URL; trust only defined response headers; fail closed on auth outage; never pass unvalidated client identity headers to backends.
4. Chain order: **IP allow → rate limit → auth → headers/CORS** (document exceptions if auth needs body).

### 4. Abuse limits and HTTPS redirect

| Middleware | Check |
| --- | --- |
| RateLimit | `average`/`burst`/`period` on login and costly routes; source strategy |
| InFlightReq | Cap concurrent requests per source |
| CircuitBreaker | Expression not so loose it never trips; not a substitute for auth |
| RedirectScheme | permanent https redirect on `web` entrypoint |
| CORS | Explicit origins; no `*` with credentials; methods/headers allowlisted |
| path strip/replace | Prefix strip bugs → unexpected backend paths |

Plugins: pin versions; treat third-party plugins as supply-chain risk.

### 5. Validate and remediate

1. **Positive:** allowed IP + valid auth + HTTPS headers present.
2. **Negative:** blocked IP 403; missing auth 401; HTTP redirects; over-limit 429; foreign CORS; public dashboard closed.
3. **Flag:** routers without chain; open `api.insecure`; client `X-Forwarded-*` trusted from Internet; BasicAuth over cleartext; CORS `*`.
4. Stage changes; keep rollback; `code-quality-standards` on config-as-code; secrets → `secrets-management-hygiene`.

## Routing

| Need | Skill |
| --- | --- |
| Traefik security middlewares, chains, entrypoint gates | **This skill** |
| nginx security headers / TLS edge | `nginx-security-headers` |
| Express middleware order | `express-middleware-security` |
| Istio mesh authz / mTLS | `istio-authz-basics` |
| JWT/Bearer abuse testing | `api-auth-and-jwt-abuse` |
| Authorized rate-limit bypass | `rate-limit-bypass-testing` |
| TLS keys, htpasswd, ForwardAuth secrets | `secrets-management-hygiene` |
| Config/CI quality baseline | `code-quality-standards` |
| WebSocket auth/origin | `websocket-security` |

## Output Checklist

- [ ] Scope: Traefik version, providers, entrypoints, in-scope hosts recorded
- [ ] Middleware inventory vs routers that actually attach them
- [ ] Headers: HSTS/CSP/frame/nosniff verified on critical hosts and status codes
- [ ] IPAllowList on admin/dashboard/metrics; public surface minimized
- [ ] Auth middleware: Basic/Digest/ForwardAuth fail-closed; no cleartext secrets
- [ ] RateLimit / InFlightReq on abuse-sensitive routes
- [ ] RedirectScheme (or equivalent) HTTP→HTTPS; TLS termination noted
- [ ] CORS allowlist explicit; credentials policy correct
- [ ] API/dashboard not `insecure` on public binds
- [ ] Positive/negative checks evidenced; residual gaps with owner/expiry
- [ ] Secrets and config quality via helpers; evidence redacted

## Scope And Authorization

- **In scope:** org-owned Traefik static/dynamic config, Docker labels, Helm values,
  Kubernetes CRDs, staging/prod under written engagement, labs/CTF.
- **Out of scope:** third-party Traefik edges without permission; mass Internet
  scanning; production load floods without approval; disabling auth/TLS without
  change window and rollback.
- Prefer **config review + controlled request checks** over aggressive fuzzing.
- Treat htpasswd, ForwardAuth secrets, ACME material, and TLS keys as secrets —
  redact (`secrets-management-hygiene`). Edge middleware is **not** object-level
  API authz (IDOR → `idor-broken-object-authorization`; JWT forgery →
  `api-auth-and-jwt-abuse`).

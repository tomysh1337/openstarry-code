---
name: spring-actuator-hardening
description: >
  Authorized Spring Boot Actuator hardening: endpoint exposure, separate management
  port, Spring Security on /actuator, health details, and high-risk endpoints
  (env, heapdump, threaddump, loggers, shutdown, jolokia). Use when reviewing
  application.yml/properties, Spring Boot Actuator exposure, management.endpoints,
  or lab/prod apps you own — not for unauthorized scanning of third-party Actuators.
---

# Spring Boot Actuator Hardening

Assess and harden **Spring Boot Actuator** for apps you own or are authorized to
test. Focus on exposure, auth, listen address/port, and data leaks — not abusing
third-party management APIs.

## Scope And Authorization

- **In scope:** org-owned Spring Boot apps, staging/prod under engagement, labs/CTFs,
  config/IaC review without live abuse of out-of-scope hosts.
- **Out of scope:** mass scanning `/actuator`; heap/env dumps from foreign systems;
  destructive `shutdown`/logger changes without change control.
- Prefer config review + non-destructive probes (`health`, 401/403). Gate `heapdump`,
  full `env`, and write endpoints behind approval. Redact secrets/PII/heap contents.
- Public unauth sensitive endpoints: isolate, rotate exposed secrets, audit logs.
- Defense only: prove reachability/auth gaps; K8s probes do not justify public
  `env`/`heapdump` — split ports and exposure.

## When To Use

- Reviewing `management.*` in `application.yml`/`.properties`, Spring Cloud, or K8s probes
- `/actuator` beyond internal mesh; `exposure.include=*`; sensitive endpoints without auth
- Full health details public; management shares the public app port
- Boot 2.x/3.x hardening; post-incident “was Actuator open?”

Do **not** use as primary for: API JWT (`api-auth-and-jwt-abuse`), password vault
(`secrets-management-hygiene`), code baseline (`code-quality-standards`), edge TLS
(`nginx-security-headers`), SSRF to Actuator (`ssrf-server-side-request-forgery`),
K8s network/pod (`kubernetes-network-policy`, `kubernetes-pod-security`).

## Workflow

### 1. Inventory

Boot version; base-path (default `/actuator`); `exposure.include`/`exclude` and
per-endpoint `enabled`; same app port vs `management.server.port` (+ `address`);
Spring Security matchers/roles; K8s probes, Service/Ingress, LB, gateway routes;
optional Jolokia, Cloud Gateway actuators, custom endpoints.

### 2. Authorized exposure checks

```bash
curl -sS -o /dev/null -w "%{http_code}\n" "https://app.example/actuator"
curl -sS "https://app.example/actuator/health"
curl -sS -o /dev/null -w "%{http_code}\n" "https://app.example/actuator/env"
curl -sS -o /dev/null -w "%{http_code}\n" "https://app.example/actuator/heapdump"
```

| Signal | Risk |
| --- | --- |
| Unauth `env` / `configprops` / `beans` / `mappings` | Config and secret leak |
| Unauth `heapdump` / `threaddump` | Memory/credential leak — critical |
| Unauth write `loggers` / `shutdown` | Integrity / availability |
| Public Jolokia | Historical MBean/RCE class — disable or lock down |
| Full health details + DB URLs | Info leak; tighten `show-details` |
| Private `health`/`info` only | Often acceptable with minimal `info` |

### 3. Hardening baseline

```yaml
management:
  server:
    port: 8081
    address: 127.0.0.1
  endpoints:
    web:
      exposure:
        include: health,info    # never "*" on public apps
        exclude: env,heapdump,threaddump,logfile,shutdown,jolokia
  endpoint:
    health:
      show-details: when_authorized
      probes:
        enabled: true
    env:
      enabled: false
    shutdown:
      enabled: false
```

1. Expose only probe/ops needs; keep `metrics`/`prometheus` private.
2. Disable high-risk: `env`, `configprops`, `beans`, `mappings`, `heapdump`,
   `threaddump`, `logfile`, write `loggers`, `shutdown`, unused Jolokia.
3. Separate management port/address; block at SG/mesh from the Internet.
4. Authenticate non-public endpoints (e.g. role `ACTUATOR`); no shared password in git.
5. Health: `never` or `when_authorized`; no open Actuator CORS for browsers.

### 4. Security, deploy, verify

```java
// Boot 3 sketch — align with app SecurityFilterChain
http.securityMatcher("/actuator/**")
    .authorizeHttpRequests(auth -> auth
        .requestMatchers("/actuator/health", "/actuator/health/**").permitAll()
        .requestMatchers("/actuator/**").hasRole("ACTUATOR"))
    .httpBasic(Customizer.withDefaults());
```

Avoid `permitAll` on `/actuator/**`. Prefer private management port + allowlists.
Do not publish `/actuator` on public Ingress unless org accepts authenticated ops.
Reduce exposure; enforce Security; rotate secrets if `env`/heap was open; re-test
external vs internal; document exceptions; apply `code-quality-standards` and
`secrets-management-hygiene`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Actuator exposure, mgmt port, auth, health details | **This skill** | — |
| Management passwords / vault | `secrets-management-hygiene` | this skill |
| SecurityFilterChain / YAML changes | `code-quality-standards` | this skill |
| Edge TLS/headers blocking Actuator | `nginx-security-headers` | this skill |
| JWT/session on management login | `api-auth-and-jwt-abuse` | this skill |
| SSRF to internal Actuator | `ssrf-server-side-request-forgery` | this skill |
| K8s Service/probe placement | `kubernetes-network-policy` | this skill |

- **`code-quality-standards`:** Security config, YAML, tests for Actuator auth.
- **`secrets-management-hygiene`:** ops credentials; no secrets in repo or `/info`.

## Output Checklist

- [ ] Scope recorded; only in-scope hosts exercised
- [ ] Boot version, base-path, exposure, management port inventoried
- [ ] No anonymous sensitive endpoints from untrusted networks
- [ ] No public `include=*`; high-risk endpoints off or private+auth
- [ ] Health details limited; probes work; management port isolated
- [ ] Ingress does not publish Actuator publicly without authenticated ops
- [ ] Spring Security on non-public endpoints; no open Actuator CORS
- [ ] Secrets via `secrets-management-hygiene`; code via `code-quality-standards`
- [ ] Residual exceptions, owners, expiry documented

---
name: haproxy-acl-security
description: >
  Authorized HAProxy ACL and routing-control review: path/host/header matchers,
  use_backend / http-request deny allowlists, src and X-Forwarded-For trust,
  stats and admin plane protection, TLS client-cert ACLs, and bypass-prone
  patterns (normalization, case, method override). Use when reviewing haproxy.cfg
  / maps, frontend ACLs that gate auth or admin routes, or hardening org-owned
  load balancers — not for attacking third-party edges without permission.
---

# HAProxy ACL Security

Assess and harden **HAProxy access-control lists** and the actions that consume
them (`use_backend`, `http-request deny/allow/redirect`, `tcp-request`, stick
tables) on systems you own or are explicitly authorized to test. Evidence =
effective config + controlled requests that prove match/miss behavior.

## When To Use

| Situation | Direction |
| --- | --- |
| Review `haproxy.cfg`, includes, maps, `acl` / `http-request` / `use_backend` | **This skill** |
| Admin, internal, or auth-gated routes protected only by HAProxy ACLs | **This skill** |
| Path/host/header ACL bypasses (normalization, case, spoofed headers) | **This skill** |
| Stats socket/page, monitor URI, or management plane exposure | **This skill** |
| Src IP allowlists and `X-Forwarded-For` / PROXY protocol trust | **This skill** |
| nginx headers / TLS edge (not HAProxy ACL semantics) | `nginx-security-headers` |
| HTTP request smuggling at proxy boundaries | `request-smuggling`, `http2-specific-attacks` |
| Host-header / cache poison chains | `http-host-header-attacks` |
| App authz (IDOR) behind the LB | `idor-broken-object-authorization` |
| Config-as-code quality | `code-quality-standards` |
| TLS keys, basic-auth files, map secrets | `secrets-management-hygiene` |

## Scope And Authorization

- **In scope:** org-owned HAProxy (bare metal, VMs, containers, cloud LBs that
  expose HAProxy config), staging under written engagement, local labs/CTF
  configs, map/ACL review without live traffic to out-of-scope hosts.
- **Out of scope:** unauthenticated mass scanning of Internet edges; DoS via
  connection floods or stick-table exhaustion on shared prod without approval;
  changing production routing “to test” without change control and rollback.
- Prefer **config review + low-volume authorized probes** over aggressive fuzz.
- Redact cookies, tokens, client cert DNs, internal hostnames, and stats creds.
- Do not disable TLS or open admin backends on production without a windowed plan.

## Workflow

### 1. Inventory frontends, ACLs, and actions

1. Collect effective config: `haproxy -c -f ...` and full dump of includes/maps.
2. List each `frontend` / `listen`: binds, TLS, mode (`http`/`tcp`), default backend.
3. Extract every `acl` name and the **fetch samples** it uses (`path`, `path_beg`,
   `urlp`, `hdr`, `req.hdr`, `src`, `ssl_c_used`, `method`, `req.fhdr`, maps).
4. Map ACL → action: `use_backend`, `use-server`, `http-request deny|allow|tarpit|redirect|set-header`,
   `tcp-request connection/content reject`, `http-response`.
5. Note evaluation order: first matching `use_backend` wins; deny rules vs `default_backend` fall-through.

### 2. Matcher hygiene (bypass-prone patterns)

| Pattern | Risk | Hardening direction |
| --- | --- | --- |
| `path_beg /admin` only | `/Admin`, `//admin`, `/./admin`, encoded variants may miss or hit wrong backend | Prefer explicit allowlist backends; normalize; test encodings |
| `path_reg` overly broad or unanchored | Unintended routes match or critical paths miss | Anchor regex; prefer `path` / `path_beg` + map files |
| Host ACL without port/case rules | `Host` variants, absolute-form URI | Match canonical host; reject unknown hosts |
| Header ACL on client-controlled `X-Role`, `X-Original-URL` | Privilege if trusted at edge | Never authorize solely on spoofable request headers |
| `src` allowlist without PROXY/XFF policy | Real client IP wrong behind another LB | Trust PROXY protocol / `X-Forwarded-For` only from known hops |
| Method-only gates | Override via tunnels or backend reinterpretation | Combine method + path + authn evidence |
| ACL silent fail (missing map/file) | Open or closed unexpectedly | Fail closed on missing map; monitor config reload |

Verify with authorized probes: alternate case, double slashes, `%2e`, trailing
slash, long paths, extra `Host`, injected `X-Forwarded-*` from untrusted clients.

### 3. Trust boundaries: IP, PROXY, and headers

1. Document who terminates TLS and who may send PROXY protocol v1/v2.
2. If using `src` or stick-tables on client IP, confirm the sample is the **true**
   client after `accept-proxy` / trusted `X-Forwarded-For` depth — not the previous hop alone when multi-tier.
3. Strip or overwrite internal auth headers on the frontend before backends see
   client copies (`http-request del-header` / set from trusted context only).
4. Stats page (`stats enable`) and runtime API/socket: bind localhost or VPN;
   strong auth; no public `stats uri` without TLS + credentials.

### 4. Sensitive route and backend isolation

1. Admin/debug/metrics backends must not be `default_backend` fall-through.
2. Prefer **default deny** then explicit `http-request allow` for known good ACLs,
   or dedicated frontends for admin with network + mTLS.
3. mTLS: `ssl_c_used`, verify required, ACL on verified CN/SAN maps — not only
   “cert presented”.
4. Rate limits / stick-table denylist: document thresholds; avoid locking out
   shared NAT without ops runbook.

### 5. Verify, remediate, document

1. Positive: intended clients reach intended backends.
2. Negative: foreign host, path variants, spoofed role headers, untrusted src →
   deny or safe backend only.
3. Reload-safe changes; `haproxy -c` in CI (`code-quality-standards`).
4. Secrets in maps/crt lists/stats auth → `secrets-management-hygiene`.
5. Residual risk: CDN dual-ACL, app still must enforce authz.

## Routing

| Need | Skill |
| --- | --- |
| HAProxy ACL matchers, deny/allow, backend selection, stats/PROXY trust | **This skill** |
| nginx security headers / server_tokens | `nginx-security-headers` |
| Request smuggling (H1/H2) at proxies | `request-smuggling`, `http2-specific-attacks` |
| Host header / cache issues | `http-host-header-attacks`, `http-cache-poisoning-basics` |
| App object authz behind LB | `idor-broken-object-authorization` |
| WebSocket upgrade auth/origin | `websocket-security` |
| Config/IaC quality | `code-quality-standards` |
| Certs, stats passwords, map secrets | `secrets-management-hygiene` |
| Edge PCAP / protocol evidence (owned) | `NetworkProtocolAnalysisSkill` |

**Helpers when applicable:** `code-quality-standards`; `secrets-management-hygiene`;
`NetworkProtocolAnalysisSkill` for authorized packet proof.

## Output Checklist

- [ ] Scope/authorization recorded; only in-scope hosts and configs exercised
- [ ] Frontends, ACLs, maps, and actions inventoried with evaluation order
- [ ] Sensitive routes not reachable via path/host/header bypass variants
- [ ] No authz solely on client-spoofable headers; internal headers stripped/overwritten
- [ ] `src` / XFF / PROXY trust matches real topology; untrusted hops cannot forge client IP
- [ ] Stats/runtime socket not public; credentials and TLS appropriate
- [ ] Admin backends isolated; default_backend is safe fall-through
- [ ] mTLS ACLs require verified client certs where claimed
- [ ] Negative tests documented; config validated (`haproxy -c`); secrets redacted
- [ ] App-layer authz residual risk noted; helpers applied where relevant
- [ ] Evidence: config quotes + minimal authorized probes; originals immutable; secrets redacted

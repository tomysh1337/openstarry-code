---
name: nginx-rate-limit-zones
description: >
  Configure and review nginx limit_req / limit_req_zone (and related limit_conn)
  rate-limit zones: keys, shared-memory sizing, rate and burst, nodelay, status
  codes, trusted client IP, and per-location attachment. Use when designing or
  auditing nginx rate limits, limit_req_zone keys, burst/nodelay, 503 vs 429 at
  the edge, X-Forwarded-For keying, or hardening org-owned reverse proxies —
  not for flooding third-party sites.
---

# Nginx Rate Limit Zones

Own **nginx request-rate zones**: `limit_req_zone` / `limit_req` (and optional
`limit_conn_zone` / `limit_conn`) on systems you operate. Product API quotas →
`api-rate-limit-design`. Adversarial key bypass → `rate-limit-bypass-testing`.
Edge headers/TLS → `nginx-security-headers`.

## When To Use

- Adding or reviewing `limit_req_zone` / `limit_req` in `nginx.conf`,
  `conf.d/*`, `sites-enabled/*`, ingress-nginx, or OpenResty
- Choosing zone **keys**, **rate**, **burst**, `nodelay`/delay, and
  `limit_req_status` (429 vs 503)
- Fixing weak keying (raw `$http_x_forwarded_for`), tiny zones, missing limits
  on login/API locations, or opaque edge rejects
- Concurrent caps via `limit_conn_zone` / `limit_conn` beside RPS
- Keywords: nginx rate limit, `limit_req`, `limit_req_zone`, burst, nodelay,
  shared zone, edge throttle, 限流 zone

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Product keys, plan tiers, `429` UX catalog | `api-rate-limit-design` |
| Authorized bypass / XFF trust testing | `rate-limit-bypass-testing` |
| Security headers / TLS / server_tokens | `nginx-security-headers` |
| WAF signature / CRS tuning | `waf-rule-tuning-basics` |
| CAPTCHA after burn | `captcha-bypass-research` |
| Implementation/IaC hygiene | `code-quality-standards` |

## Repo Config First

Repo nginx templates, Helm values, and gateway policies **outrank** defaults.

1. **Existing zones:** `nginx -T` for `limit_req_zone`, `limit_req`,
   `limit_conn_zone`, `limit_req_status`, `limit_req_dry_run`
2. **Trusted client IP:** LB hop via `real_ip` (`set_real_ip_from`,
   `real_ip_header`) — never sole key on raw client XFF
3. **Sensitive locations:** login, OTP, reset, export — stricter zones and/or
   app dual-key limits
4. **Ingress / CDN / mesh:** avoid contradictory dual throttles without one budget
5. **Observability:** `limit_req` error_log, exporters, 429/503 rates
6. **Config-as-code:** ConfigMaps/Helm via reviewable diffs

**Precedence:** Follow the repo. Flag public `$http_x_forwarded_for` sole keys,
unlimited auth paths, or burst so large the rate is moot.

## Workflow

1. **Inventory.** On owned hosts: `nginx -t` then dump/search for `limit_req`,
   `limit_conn`, `real_ip`. Map each zone: key, `rate=`, name/size, attached
   `server`/`location`, status, dry_run.

2. **Keys.** Prefer real_ip so `$remote_addr` is the client; key
   `$binary_remote_addr` (compact). Optional composites: mapped route class or
   verified API-key/JWT id via `map`/`auth_request` — not client-spoofable ids.
   Never sole public key on raw `$http_x_forwarded_for` (budget multiplies).
   Auth stuffing needs **account-level** app limits; nginx IP zones are coarse edge.

3. **Zone size and rate** (http context):

   ```nginx
   limit_req_zone $binary_remote_addr zone=perip_general:10m rate=10r/s;
   limit_req_zone $binary_remote_addr zone=perip_login:10m rate=1r/s;
   limit_conn_zone $binary_remote_addr zone=addr_conn:10m;
   ```

   ~16k states/MB for binary IPv4 keys (order-of-magnitude); undersized zones
   evict unevenly. Separate general API vs login/OTP vs expensive export rates.

4. **Attach burst policy:**

   ```nginx
   limit_req_status 429;   # default 503; 429 better for APIs
   # limit_req_dry_run on;
   location /api/ {
       limit_req zone=perip_general burst=20 nodelay;
       proxy_pass http://upstream;
   }
   location /login {
       limit_req zone=perip_login burst=5 nodelay;
       limit_conn addr_conn 10;
       proxy_pass http://upstream;
   }
   ```

   | Directive | Effect |
   | --- | --- |
   | `burst=N` | Excess above rate up to N |
   | `nodelay` | Admit burst immediately (still capped) |
   | `delay=` | Fine-tune delayed admit (newer nginx) |
   | `limit_req_status` | Prefer 429 for APIs |
   | `limit_req_dry_run` | Log/measure before enforce |

5. **Allowlists and multi-zone.** `map` empty key for health checks / trusted
   CIDRs (empty = not limited). Multiple `limit_req` in one location all apply.
   URI-keyed buckets split on path aliases unless normalized — prefer IP edge +
   app identity limits for auth.

6. **Verify.** Stage dry_run/canary; load-test from owned clients; check logs and
   NAT false positives; `nginx -t` before reload; rollback snapshot ready. Pair
   product quotas and bypass review with sibling skills; IaC →
   `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| nginx `limit_req` / `limit_conn` zones design or audit | **This skill** | — |
| Product quotas, plan tiers, rich 429 UX | `api-rate-limit-design` | this for nginx mechanics |
| Prove XFF/path/IP bypass | `rate-limit-bypass-testing` | this for intended zones |
| Headers, TLS, server_tokens | `nginx-security-headers` | this if co-located |
| CAPTCHA / bot step-up | `captcha-bypass-research` | this for edge RPS |
| Config templates, tests, safe reload | `code-quality-standards` | **always** on changes |

This skill owns zone syntax, keys, burst/nodelay, status, attachment.
`api-rate-limit-design` owns identity/plan budgets; `rate-limit-bypass-testing`
proves key expansion under authorization.

## Output Checklist

- [ ] Effective `limit_req_zone` / `limit_req` / `limit_conn` inventory
- [ ] real_ip / trusted hop documented; no sole public XFF key
- [ ] Keys, rates, zone sizes, location attachments recorded
- [ ] burst / nodelay (or delay) justified (general vs auth vs expensive)
- [ ] `limit_req_status` chosen; dry_run/canary if staged
- [ ] Health/trusted allowlist via map empty-key if needed — not open disable
- [ ] Auth routes not IP-only sole control; app dual-key noted
- [ ] Metrics/logs; zone memory not clearly undersized
- [ ] `nginx -t` + reload/rollback; `code-quality-standards` on templates
- [ ] Follow-ups: `api-rate-limit-design`, `rate-limit-bypass-testing` as needed

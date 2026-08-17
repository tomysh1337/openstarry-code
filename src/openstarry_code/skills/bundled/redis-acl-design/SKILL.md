---
name: redis-acl-design
description: >
  Design least-privilege Redis ACL users: command categories, key/channel
  patterns, AUTH secrets, and deny lists for dangerous commands. Use when
  defining users.acl, ACL SETUSER rules, app vs admin roles, key-prefix
  isolation, or replacing shared requirepass with Redis 6+ ACL — not for
  unauthorized access to third-party Redis.
---

# Redis ACL Design

Design **Redis Access Control Lists** so each client runs only the commands and
touches only the key/channel patterns it needs. Defensive work for **owned or
explicitly authorized** Redis (self-hosted or managed).

## When To Use

- Creating or reviewing `users.acl` / `ACL SETUSER` / `user` directives
- Splitting **admin**, **app**, **worker**, **analytics**, and **replica** roles
- Mapping **categories** (`+@read`, `+@write`, `-@dangerous`) and command denies
- Enforcing **key patterns** (`~app:*`) and **channels** (`&app:events:*`)
- Moving from shared `requirepass` to per-user **AUTH** with strong secrets
- Keywords: Redis ACL, ACL LIST, ACL CAT, key pattern, requirepass, FLUSHALL deny

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Bind, protected-mode, public 6379, TLS, exposure | `redis-security-misconfig` |
| Password storage, rotation, leak IR | `secrets-management-hygiene` |
| App clients, IaC, tests around Redis | `code-quality-standards` |
| Cache TTL / stampede product design | `caching-strategies` |
| RESP/TLS PCAP | `NetworkProtocolAnalysisSkill` |

## Scope And Authorization

- **In scope:** Redis **you own** or are contracted to harden; ACL files and
  managed auth tokens under change control; non-destructive checks (`ACL WHOAMI`,
  `ACL LIST`, expected `NOPERM`).
- **Out of scope:** Third-party Redis auth or scanning; impact demos via
  `FLUSHALL`, `MODULE LOAD`, `DEBUG`, or `REPLICAOF` on shared prod; pasting
  live ACL passwords into tickets or chat.
- Prefer staging for ACL rewrites; keep break-glass admin before disabling
  `default`. Redact secrets and tenant key samples.
- Network bind, protected-mode, TLS, and exposure stay under
  `redis-security-misconfig` — this skill shapes **who may do what** after
  connectivity and base auth are in scope.

## Workflow

### 1. Inventory roles and prefixes

List clients (app, workers, admin, metrics, replicas). For each role, capture
command families and key/channel prefixes. Note multi-tenant soft isolation vs
separate instances. Output: role → prefix → commands (no plaintext secrets).

### 2. Prefer ACL over one shared password

Redis 6+ **ACL users** beat a single global `requirepass` for least privilege.

```bash
# Authorized session only
redis-cli --user admin -a "$ADMIN_PASS" --no-auth-warning ACL LIST
redis-cli ... ACL CAT dangerous
redis-cli ... ACL WHOAMI
redis-cli ... ACL GETUSER app
```

Unique CSPRNG secrets per user (vault via `secrets-management-hygiene`).
`user default off` once app/admin work. Never ship **admin** in app env.

### 3. Categories, then ±commands

1. Start **deny-all**: `-@all`, then add only needed categories.
2. Add as required: `+@connection`, `+@read`, `+@write`, `+@transaction`,
   `+@pubsub`, `+@stream`, `+@scripting`.
3. Strip danger: `-@dangerous`, plus named denies:
   `-flushall -flushdb -config -module -shutdown -replicaof -slaveof -debug
   -save -bgsave -keys -migrate -restore`.
4. Prefer app-limited `SCAN` over `+keys`.
5. Verify: `NOPERM` on `CONFIG`/`FLUSHDB` for app; GET/SET only on own prefix.

### 4. Key and channel patterns

| Rule | Guidance |
| --- | --- |
| Keys | `~app:prod:*` (or tighter); avoid `~*` for app roles |
| Reset | `resetkeys` then apply intended patterns |
| Channels | `resetchannels` then `&app:events:*` (`allchannels` only if justified) |
| Tenants | Prefer one ACL user per service/tenant; prefix alone is soft isolation |

### 5. Dangerous commands and AUTH

Non-admin must not reach high-impact admin surface (denies above). Optional
global `rename-command` and network/TLS: hand to `redis-security-misconfig`.

```bash
redis-cli -h redis.internal --user app -a "$APP_PASS" --no-auth-warning PING
```

Rotate per-user secrets independently. Clients/IaC: `code-quality-standards`
(timeouts, no secrets in logs).

### 6. Example ACL sketch

```conf
user admin on >change-me-admin ~* &* +@all
user app on >change-me-app ~app:* resetchannels -@all +@read +@write +@connection +@transaction -@dangerous -flushall -flushdb -config -module -shutdown -replicaof -keys
user analytics on >change-me-analytics ~app:metrics:* resetchannels -@all +@read +@connection -keys +ping
user default off
```

Replace placeholders; never commit production secrets.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ACL users, categories, key/channel patterns, AUTH roles | **This skill** | — |
| Bind, protected-mode, public exposure, TLS, rename survey | `redis-security-misconfig` | this for ACL detail |
| Secret storage / rotation / leak of Redis passwords | `secrets-management-hygiene` | this for ACL identities |
| Client/IaC implementation and tests | `code-quality-standards` | this for intended rules |
| Cache product behavior (TTL, stampede) | `caching-strategies` | this for security boundary |

Keep **this skill primary** for ACL design. Hand **exposure and full Redis
misconfig assessment** to `redis-security-misconfig`.

## Output Checklist

- [ ] Authorization recorded; only owned/in-scope Redis
- [ ] Roles inventoried with command needs and key/channel prefixes
- [ ] Per-user ACL; `default` off or limited; admin separate from app
- [ ] Built from `-@all` + minimal `+@...`; `-@dangerous` + named admin denies
- [ ] App key patterns not `~*`; channels reset and scoped
- [ ] AUTH verified per role (`WHOAMI`, `NOPERM` evidence)
- [ ] Secrets via `secrets-management-hygiene`; no plaintext in git/tickets
- [ ] Network/TLS/bind residuals → `redis-security-misconfig`
- [ ] Clients/IaC meet `code-quality-standards`; exceptions documented

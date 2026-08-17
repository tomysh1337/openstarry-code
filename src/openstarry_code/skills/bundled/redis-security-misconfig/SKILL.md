---
name: redis-security-misconfig
description: >
  Authorized Redis security assessment and hardening: bind addresses,
  protected-mode, AUTH/ACL, dangerous command exposure (FLUSH*, CONFIG, MODULE,
  DEBUG, SLAVEOF/REPLICAOF), network exposure, TLS, and safe config examples.
  Use when reviewing redis.conf, cloud Redis, or lab instances you own — not for
  unauthorized Internet scanning or abusing exposed third-party Redis.
---

# Redis Security Misconfiguration

Assess and harden **Redis** (and Redis-compatible managed services) for systems
you own or are explicitly authorized to test. Focus on network exposure,
authentication, ACL least privilege, and disabling or renaming high-impact
commands — not on weaponizing open instances against third parties.

## Scope And Authorization

- **In scope:** org-owned Redis, staging/prod under written engagement, local
  Docker/lab CTF instances, config/IaC review without live exploit of out-of-scope hosts.
- **Out of scope:** mass scanning for open port 6379; crypto-mining or ransomware
  on foreign instances; using discovered Redis to pivot into networks outside
  the engagement; destructive commands on shared prod without change control.
- Prefer **read-only probes** first (`PING`, `INFO`, command listing) on approved
  endpoints. Gate `FLUSHALL`, `CONFIG SET`, module loads, and replica rewrites
  behind explicit approval and backups.
- Redact passwords, ACL secrets, cloud auth tokens, and dump contents containing
  PII from reports and tickets.
- On suspected **Internet-exposed production Redis with no auth:** treat as
  incident — isolate, rotate credentials, audit persistence and crontabs —
  follow org IR, not public brag writeups with live IPs.

## Use When

- Reviewing `redis.conf`, ElastiCache/Memorystore/Azure Cache settings, or
  Kubernetes Redis charts
- Redis reachable beyond localhost / expected VPC; missing `requirepass` / ACL
- Suspected dangerous command surface (`CONFIG`, `FLUSHALL`, `MODULE`, `DEBUG`,
  `SLAVEOF`/`REPLICAOF`, `MIGRATE`, `KEYS` abuse)
- Hardening checklist for new environments; post-incident “was Redis open?”
- Chinese/English teams: Redis 未授权, bind 配置, requirepass, ACL, 危险命令,
  protected-mode

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Application cache key design / stampede | `caching-strategies` |
| Secret storage of the Redis password itself | `secrets-management-hygiene` |
| General code reliability around Redis clients | `code-quality-standards` |
| PCAP of RESP traffic / custom protocol work | `NetworkProtocolAnalysisSkill`, `traffic-analysis-pcap` |
| Host privesc after Redis write to disk (lab) | `linux-privilege-escalation` (lab only) |
| Container breakout via host mounts | `container-escape-techniques` (lab only) |

## Threat Themes (defensive)

| Theme | Weak outcome | Hardening direction |
| --- | --- | --- |
| Network exposure | `0.0.0.0:6379` on public IP | Bind private interfaces; SG/NACL; no public 6379 |
| No auth | Anyone who connects runs commands | ACL users + strong secrets; TLS where supported |
| Protected-mode off + weak bind | Accidental open service | Keep protected-mode on unless bind+auth correctly set |
| Dangerous commands | Remote flush, config rewrite, module load, replica of attacker | `rename-command` / ACL command rules / disable |
| Unencrypted links | Password and data on the wire | TLS (Redis 6+) or mesh/VPN-only paths |
| Overprivileged app user | App ACL can `FLUSHALL` / `CONFIG` | Least-privilege ACL per app role |
| Persistence + weak FS perms | Dump/AOF readable by other users | File perms, encrypt at rest per platform |
| Admin interfaces | `redis-commander` / UI exposed | SSO, network policy, no public admin |

## Workflow

### 1. Inventory instances and trust boundaries

1. List instances: host/port, version, managed vs self-hosted, VPC/subnet, DNS names.
2. Map **clients**: apps, sidekiq/rq workers, Celery, debug tunnels, bastions.
3. Identify admin paths: SSH tunnel, cloud console, Kubernetes service type
   (ClusterIP vs LoadBalancer vs NodePort).
4. Note whether Redis is used as cache (flush impact) vs primary data store
   (durability and RPO matter more).

Output: inventory table with owners — no plaintext passwords.

### 2. Network exposure assessment (authorized)

From an **approved** vantage point (same VPC probe host, bastion, or lab):

```bash
# Only against in-scope targets
nc -vz redis.internal 6379
# or
redis-cli -h redis.internal -p 6379 PING
```

Checks:

| Check | Evidence |
| --- | --- |
| Listening address | `bind` in config; `ss -lntp | grep 6379` on host |
| Public SG/NACL | Cloud console: 0.0.0.0/0 or ::/0 on 6379/6380 |
| Protected-mode | `CONFIG GET protected-mode` if permitted; or conf file |
| Cross-env reachability | Can staging clients hit prod Redis? |

If the engagement allows packet capture on a **lab mirror**, use
`NetworkProtocolAnalysisSkill` / `traffic-analysis-pcap` for RESP plaintext
visibility — do not MITM production without approval.

### 3. Authentication and ACL

Redis 6+ **ACL** is preferred over single shared `requirepass` alone.

```bash
# Authorized session with provided credentials
redis-cli -h redis.internal --user default -a '$REDIS_PASSWORD' --no-auth-warning PING
redis-cli -h redis.internal --user default -a '$REDIS_PASSWORD' --no-auth-warning ACL LIST
redis-cli -h redis.internal --user default -a '$REDIS_PASSWORD' --no-auth-warning ACL WHOAMI
```

Assess:

1. **No auth:** `PING` → `PONG` without credentials on a network-reachable port →
   critical exposure finding (do not run destructive commands to “prove” it).
2. **Weak/shared password:** password in git, Compose files, or world-readable
   env → `secrets-management-hygiene`.
3. **Default user** has all commands and all key patterns.
4. **App users** can run admin commands or access other tenants’ key prefixes.
5. **Replica/admin** credentials reused with app users.

Managed Redis: confirm AUTH tokens, IAM auth (where offered), in-transit
encryption flags, and that “public endpoint” is off.

### 4. Dangerous command exposure

With authorization, list what the **current user** may run (safer than guessing):

```bash
redis-cli --user app -a '$APP_PASS' --no-auth-warning COMMAND
# or attempt high-impact commands expecting NOPERM / unknown command
redis-cli ... CONFIG GET '*'
redis-cli ... ACL CAT dangerous
```

High-impact commands to ensure are **disabled, renamed, or ACL-denied** for
non-admin roles:

| Command / group | Why restricted |
| --- | --- |
| `FLUSHALL` / `FLUSHDB` | Total data loss |
| `CONFIG` | Runtime reconfig, dir/dbfilename (disk write primitives) |
| `MODULE LOAD` | Native code load |
| `DEBUG` | Crash / dangerous introspection |
| `SLAVEOF` / `REPLICAOF` | Point replica at attacker-controlled master |
| `MIGRATE` / `RESTORE` | Data movement / shape of RCE chains in old research |
| `SHUTDOWN` | Availability |
| `KEYS` / unbounded `SCAN` patterns | DoS / intel (prefer controlled `SCAN` with limits in apps) |
| `SCRIPT` / `EVAL` | Heavy Lua — restrict if unused; still authenticate always |
| `MONITOR` / `SYNC` / `PSYNC` | Traffic/data exposure |

**Assessment rule:** prove **permission** (command allowed to overly broad role)
with non-destructive evidence (`COMMAND INFO`, `NOPERM` vs `OK` on `CONFIG GET`).
Do **not** demonstrate impact via `FLUSHALL` or module load on shared systems.

Historical “unauth Redis → write cron/authorized_keys” chains depend on
`CONFIG SET dir/dbfilename` + `SAVE` and host layout — for **lab reconstruction
only**. In production reports, describe the **config weakness** and recommend
fixes; do not leave persistence artifacts.

### 5. TLS, replication, and management plane

1. **TLS:** Redis 6+ `tls-port`, cert paths, `tls-auth-clients`; cloud “encryption
   in transit”.
2. **Replication:** require auth on replicas; do not expose replica ports publicly;
   verify `masterauth` / ACL.
3. **Cluster bus** ports similarly constrained to private networks.
4. **Dangerous management UIs** and Portainer-style tools that embed Redis creds.
5. **Unix socket:** if used, file permissions (`unixsocketperm`) and user isolation.

### 6. Config and runtime hardening review

Read `redis.conf` or equivalent:

- `bind`, `protected-mode`, `port` / `tls-port`
- `requirepass` / `aclfile` / `user` directives
- `rename-command` lines
- `supervised`, `dir`, `dbfilename`, AOF settings
- `timeout`, `tcp-keepalive`
- Dangerous modules

Prefer **immutable config + ACL file** over ad-hoc runtime `CONFIG SET` in prod.

### 7. Remediate and verify

1. Apply bind + SG/NACL changes; confirm external `PING` fails from outside path.
2. Introduce ACL users; rotate old shared passwords (`secrets-management-hygiene`).
3. Rename/disable dangerous commands for non-admin; keep break-glass admin on
   localhost or bastion-only with MFA to host.
4. Enable TLS where platform supports; update clients.
5. Re-test app functionality; monitor error rates.
6. Document residual risks (legacy clients without TLS, shared DB index multi-tenancy).

### 8. Client and application hygiene

When touching app code or IaC, apply `code-quality-standards`:

- No Redis passwords in source; inject from platform secrets.
- Connection URLs redacted in logs (`logging-message-style` if shaping logs).
- Timeouts, limited pooling, avoid `KEYS *` in hot paths.
- Treat Redis as **untrusted multi-tenant shared memory** unless ACLs isolate keys.

## Concrete Config Examples

### Hardened redis.conf sketch (self-hosted)

```conf
# /etc/redis/redis.conf — illustrative; tune memory/persistence for the workload

# Network: private interface only (example)
bind 10.0.1.20 127.0.0.1
port 6379
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 60

# Do not expose the process to the public Internet; enforce via SG as well:
# deny 6379/tcp from 0.0.0.0/0

# Persistence paths — dedicated dir, not world-writable
dir /var/lib/redis
dbfilename dump.rdb
appendonly yes
appendfilename "appendonly.aof"

# Admin secret — DO NOT commit real values; load from a secrets manager drop-in
# Prefer ACL file over a single shared requirepass when possible.
# requirepass use-a-long-random-secret

aclfile /etc/redis/users.acl

# Rename high-impact commands (empty string disables)
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG "CONFIG_9f3c2e1a7b"
rename-command SHUTDOWN "SHUTDOWN_9f3c2e1a7b"
rename-command MODULE ""
rename-command DEBUG ""
rename-command REPLICAOF ""
rename-command SLAVEOF ""
rename-command KEYS ""

# Example: leave admin renames known only to ops runbooks (secrets-management-hygiene)
```

### ACL file (least privilege)

```conf
# /etc/redis/users.acl
# Admin: local ops only — all commands, but still use network controls
user admin on >change-me-admin-long-random ~* &* +@all

# Application: key prefix app: , no dangerous admin commands
user app on >change-me-app-long-random ~app:* resetchannels -@all +@read +@write +@connection +@transaction +@scripting -@dangerous -flushall -flushdb -config -module -shutdown -replicaof -slaveof -debug -save -bgsave -keys

# Read-only analytics
user analytics on >change-me-analytics-long-random ~app:metrics:* resetchannels -@all +@read +@connection -keys +ping +info

# Disable default user if you do not need it (Redis 6+)
user default off
```

Generate secrets with a CSPRNG; store in vault — never paste prod passwords into
chat. See `secrets-management-hygiene`.

### TLS sketch (Redis 6+)

```conf
port 0
tls-port 6379
tls-cert-file /etc/redis/tls/redis.crt
tls-key-file /etc/redis/tls/redis.key
tls-ca-cert-file /etc/redis/tls/ca.crt
tls-auth-clients yes
```

```bash
redis-cli --tls --cacert /etc/redis/tls/ca.crt \
  --cert /etc/redis/tls/client.crt --key /etc/redis/tls/client.key \
  -h redis.internal -p 6379 --user app -a "$APP_PASS" --no-auth-warning PING
```

### Docker Compose anti-patterns

**Bad**

```yaml
services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"   # published on all host interfaces
    # no command args for requirepass / ACL; default unprotected in many labs
```

**Better**

```yaml
services:
  redis:
    image: redis:7
    restart: unless-stopped
    # No host publish; only attach to internal network
    networks: [backend]
    volumes:
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
      - redisdata:/data
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]
    # Password via secrets mount / env substitution from orchestrator — not plain in git
networks:
  backend:
    internal: true
volumes:
  redisdata:
```

If host access is required for local dev, bind `127.0.0.1:6379:6379` and use a
**dev-only** password; never reuse prod credentials.

### Managed Redis (cloud) checklist mapping

| Control | What to verify in console/IaC |
| --- | --- |
| Public endpoint | Disabled |
| Auth token / IAM | Enabled; rotated; not in git |
| In-transit encryption | Enabled; clients use rediss:// or TLS flags |
| At-rest encryption | Per org policy |
| SG / firewall | App subnets only |
| Version | Supported release; auto minor patches on |

### Safe verification commands (non-destructive)

```bash
redis-cli -h "$HOST" -p "$PORT" --user "$USER" -a "$PASS" --no-auth-warning PING
redis-cli ... INFO server
redis-cli ... CONFIG GET bind          # expect NOPERM for app users
redis-cli ... CONFIG GET protected-mode
redis-cli ... ACL WHOAMI
redis-cli ... ACL LIST                   # admin only
```

**Avoid on shared prod without approval:** `FLUSH*`, `DEBUG SEGFAULT`,
`MODULE LOAD`, `REPLICAOF`, `MIGRATE`, mass `KEYS *`, large `CONFIG SET` experiments.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Redis bind/AUTH/ACL/dangerous commands/exposure assessment | **This skill** | — |
| Storing/rotating Redis passwords and ACL secrets | `secrets-management-hygiene` | this skill for Redis-side ACL |
| App client code, IaC modules, error handling | `code-quality-standards` | this skill for server controls |
| RESP/TLS PCAP, dissectors, lab protocol fuzz | `NetworkProtocolAnalysisSkill` | `traffic-analysis-pcap` |
| Stream triage of captures that include Redis | `traffic-analysis-pcap` | this skill for misconfig interpretation |
| Cache product patterns (TTL, stampede) | `caching-strategies` | this skill for security boundary |
| Lab privesc involving Redis-written files | `linux-privilege-escalation` | this skill for Redis config root cause |
| K8s service exposure of Redis | `kubernetes-pentesting` | this skill for Redis ACL/commands |

### Required helpers (when applicable)

- **`code-quality-standards`:** implementation baseline for clients, health checks,
  config templates, and tests around Redis connectivity.
- **`secrets-management-hygiene`:** password/ACL secret lifecycle, no secrets in
  git/images, rotation after exposure.
- **`NetworkProtocolAnalysisSkill`:** when engagement needs PCAP, Wireshark, or
  scripted protocol analysis of RESP/TLS rather than `redis-cli` alone.

## Checklist

- [ ] Scope/authorization recorded; no out-of-scope 6379 scanning
- [ ] Inventory of instances, clients, admin paths, data criticality
- [ ] Not publicly reachable; SG/NACL/bind verified from outside path
- [ ] `protected-mode` appropriate; bind not accidentally all interfaces
- [ ] Auth required; default user disabled or tightly limited (Redis 6+)
- [ ] ACL least privilege per app; admin separated; no shared prod/dev passwords
- [ ] Dangerous commands disabled/renamed or denied to app users (evidence via NOPERM)
- [ ] TLS or equivalent private transport; replication auth configured
- [ ] Persistence dir permissions and backups considered; no secrets in dumps committed to VCS
- [ ] Compose/K8s not publishing Redis on `0.0.0.0` without auth
- [ ] Passwords/ACL files handled via `secrets-management-hygiene`
- [ ] Client/IaC changes follow `code-quality-standards`
- [ ] Packet-level work (if any) uses `NetworkProtocolAnalysisSkill` under auth
- [ ] Residual risks and break-glass admin path documented

## Rules

- **Defense and authorized assessment only** — do not exploit open third-party Redis.
- Prefer proving **exposure and permissions** over destructive impact demos.
- Rotate credentials before publishing detailed exposure reports when prod was open.
- Treat historical RCE-via-persistence techniques as **lab teaching** and config
  justification, not a playbook for unauthorized hosts.
- Multi-tenant key prefixes without ACL are soft isolation only — say so in findings.
- Keep evidence packs with redaction; store dumps separately from tickets when
  they may contain personal data.
---

# Note

This skill owns **Redis exposure and misconfiguration hardening**: bind,
protected-mode, AUTH/ACL, dangerous command surface, and safe verification.
Pair with `secrets-management-hygiene` for credential lifecycle,
`code-quality-standards` for clients/IaC, and `NetworkProtocolAnalysisSkill`
when RESP/TLS packet evidence is required.

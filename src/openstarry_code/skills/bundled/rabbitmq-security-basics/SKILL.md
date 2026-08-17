---
name: rabbitmq-security-basics
description: >
  Authorized RabbitMQ security assessment and hardening: users, vhosts,
  configure/write/read permissions, TLS for AMQP and management, default guest
  account, loopback_users, and management UI exposure. Use when reviewing
  rabbitmq.conf / advanced.config, definitions exports, Docker Compose brokers,
  or owned/lab RabbitMQ instances — not for unauthorized scanning or abusing
  third-party message brokers.
---

# RabbitMQ Security Basics

Assess and harden **RabbitMQ** for brokers you own or are explicitly authorized
to test. Focus on users, vhosts, permissions, TLS, management UI, and the
**guest / loopback_users** footguns — not weaponizing open third-party brokers.

## Scope And Authorization

- **In scope:** org-owned RabbitMQ, staging/prod under written engagement, local
  Docker/lab/CTF brokers, config/IaC and definitions JSON review.
- **Out of scope:** mass scanning 5672/15672; publishing to foreign queues;
  pivoting outside engagement; destructive purge/delete on shared prod without
  change control.
- Prefer **read-only probes** first (`rabbitmqctl` lists, management GET with
  provided creds). Gate user deletes, policy wipes, forced closes, and mass
  purge behind approval and backups.
- Redact passwords, Erlang cookie, connection strings, and sensitive payloads.
  Internet-exposed prod with guest/weak admin → **incident** (isolate, rotate,
  audit); follow org IR.

## When To Use

- Reviewing `rabbitmq.conf`, `advanced.config`, `definitions.json`, Helm/Compose
- Broker or management UI reachable beyond private network
- Default **guest** present; **loopback_users** weakened so guest works remotely
- Shared admin for all apps; missing vhost isolation; new-env hardening checklist
- Chinese/English: RabbitMQ 安全, guest, loopback_users, vhost 权限, management UI

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Password/cookie/definitions secret lifecycle | `secrets-management-hygiene` |
| App clients, retries, IaC reliability | `code-quality-standards`, `retry-backoff-patterns` |
| Redis or other data-store exposure | `redis-security-misconfig` |
| nginx edge in front of management | `nginx-security-headers` |
| AMQP/TLS PCAP or protocol deep-dive | `NetworkProtocolAnalysisSkill`, `traffic-analysis-pcap` |

## Workflow

### 1. Inventory brokers and trust boundaries

List nodes (AMQP 5672 / AMQPS 5671, management 15672 / 15671), version, clustering,
managed vs self-hosted. Map clients (apps, workers, shovel/federation, ops, CI)
and admin paths (`rabbitmqctl`, management UI/API, cloud console). Note queue
payload sensitivity. Output: inventory with owners — no plaintext secrets.

### 2. Network and listener exposure (authorized)

From an approved vantage only:

| Check | Evidence |
| --- | --- |
| Listeners | `rabbitmq-diagnostics listeners`; host `ss` |
| Public SG/NACL | 0.0.0.0/0 or ::/0 on 5672/5671/15672/15671 |
| Management bind | Private/localhost + tunnel; not public bare UI |
| Cross-env reach | Staging clients able to hit prod broker? |

### 3. Default guest and loopback_users

1. Is user `guest` present? Tags? Still default password?
2. Config: keep `loopback_users.guest = true` (default). Empty/`none` allowing
   **remote guest** is critical. Prefer delete/disable guest outside pure local dev.
3. Create named admin with strong secret; never reuse guest across environments.
4. Verify AMQP and management both reject remote guest after fix.

```bash
# Authorized host / provided admin credentials only
rabbitmqctl list_users
rabbitmqctl list_permissions -p /
# Review: loopback_users, default_user, default_pass under /etc/rabbitmq/
```

### 4. Users, vhosts, and permissions

Permissions are per **vhost**: configure, write, read (name regexes).

1. List users/tags (`administrator`, `monitoring`, `policymaker`, `management`;
   app clients should usually have no admin tags).
2. Isolate unrelated apps/tenants with separate vhosts when required — avoid one
   shared `/` for everything sensitive.
3. Avoid blanket `.*` configure/write/read for untrusted apps; use prefixes.
4. Federation/shovel get dedicated users and minimal perms.
5. Definitions in git: passwords hashed/redacted; treat exports as sensitive.

### 5. TLS and management UI

1. Prefer AMQPS (5671) and HTTPS management (15671) off-localhost; drop cleartext
   when clients allow. TLS 1.2+; valid chain/SAN; document peer-cert policy.
2. Enable management plugin only if needed; no public UI without VPN/SSO and
   strong admin. Separate **monitoring** from **administrator**.
3. Reverse-proxy edge → `nginx-security-headers`. Keys/cookie → not in VCS
   (`secrets-management-hygiene`). Audit unexpected definition downloads.

### 6. Remediate and verify

Remove/disable guest; enforce loopback for local-only accounts; rotate secrets
after exposure. Split admin vs app users; tighten vhost perms; restrict listeners;
enable TLS. Re-test publish/consume; document residual risks. Clients/IaC →
`code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Users/vhosts/perms, guest, loopback_users, UI, TLS | **This skill** | — |
| Broker password / cookie / export secrets | `secrets-management-hygiene` | this skill |
| Client code, Compose/Helm, tests | `code-quality-standards` | this skill |
| Management behind nginx TLS/headers | `nginx-security-headers` | this skill |
| AMQP/TLS PCAP or dissectors | `NetworkProtocolAnalysisSkill` | `traffic-analysis-pcap` |
| Redis misconfig (not AMQP) | `redis-security-misconfig` | — |

**Helpers when applicable:** `code-quality-standards` (clients/templates/tests);
`secrets-management-hygiene` (passwords, Erlang cookie, export rotation);
`NetworkProtocolAnalysisSkill` (authorized PCAP when CLI/UI is not enough).

## Output Checklist

- [ ] Scope/authorization recorded; no out-of-scope 5672/15672 scanning
- [ ] Inventory of nodes, ports, clients, admin paths, data sensitivity
- [ ] Listeners not public without compensating controls; SG/NACL verified
- [ ] Default **guest** removed or loopback-only; no remote guest/guest
- [ ] `loopback_users` reviewed; local-only accounts not reachable remotely
- [ ] Users least-privilege tagged; no shared prod/dev admin passwords
- [ ] Vhosts isolate apps/tenants where required; app perms not blanket `.*`
- [ ] TLS for AMQP/management where traffic leaves the trust zone
- [ ] Management UI/API not public; monitoring vs administrator separated
- [ ] Secrets/exports via `secrets-management-hygiene`; clients/IaC via CQS
- [ ] Residual risks and break-glass admin path documented

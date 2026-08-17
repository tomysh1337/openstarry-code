---
name: mongodb-auth-hardening
description: >
  Authorized MongoDB authentication and exposure hardening: SCRAM, bindIp,
  TLS, role-based access control, localhost exception, and free monitoring
  disablement. Use when reviewing mongod.conf, Atlas/self-hosted MongoDB,
  unauthorized access risk, or hardening org-owned databases — not for
  scanning or abusing third-party MongoDB instances.
---

# MongoDB Auth Hardening

Assess and harden **MongoDB** authentication, network binding, TLS, and
role-based access for systems you own or are explicitly authorized to review.
Focus on closing open listeners, enforcing SCRAM, least-privilege roles, and
safe bootstrap via the localhost exception.

## Scope And Authorization

- **In scope:** org-owned MongoDB (self-hosted, Docker, Kubernetes, Atlas or
  other managed), staging/prod under written engagement, local lab/CTF
  instances, config/IaC review without live abuse of out-of-scope hosts.
- **Out of scope:** mass scanning for open 27017; brute force or dump of
  third-party databases; destructive drops on shared prod without change
  control; pivoting outside the engagement.
- Prefer **read-only checks** first (`ping`, `connectionStatus`, role listings).
  Gate user creates, `bindIp` restarts, and TLS cutovers behind approval.
- Redact connection strings, passwords, client certs, and Atlas keys from reports.
- Suspected **Internet-exposed prod with no auth:** treat as incident — isolate,
  enable auth, rotate credentials, audit access; follow org IR.

## When To Use

- Reviewing `mongod.conf` / Compose/Helm, or Atlas network and database users
- MongoDB reachable beyond expected VPC; missing `security.authorization`
- SCRAM setup, overly broad roles (`root`, `dbOwner` on `admin`), hardening
  checklists, or post-incident “was Mongo open?”
- Localhost exception bootstrap; free monitoring / extra management surfaces
- Teams: MongoDB 未授权, bindIp, SCRAM, 角色权限, TLS, 本地异常

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| App NoSQL injection | `nosql-injection` |
| Password/URI secret lifecycle | `secrets-management-hygiene` |
| Clients, IaC, migrations | `code-quality-standards`, `database-migration-safety` |
| Wire PCAP / protocol work | `NetworkProtocolAnalysisSkill`, `traffic-analysis-pcap` |

## Workflow

### 1. Inventory

List instances (host/port, version, managed vs self-hosted, replica set),
clients (apps, workers, Compass/mongosh, bastions), and admin paths (SSH,
Atlas UI, K8s LoadBalancer/NodePort). Note data criticality. No plaintext secrets.

### 2. Network exposure (`bindIp`)

| Check | Evidence |
| --- | --- |
| Listen address | `net.bindIp` / `bindIpAll`; `ss -lntp` on 27017 |
| Public firewall / SG | `0.0.0.0/0` on 27017/27018 |
| Managed public access | Atlas network allowlists; public endpoint flags |

Bind private interfaces or localhost + app subnets; prefer private link/VPC.
Do not rely on non-default ports alone.

### 3. SCRAM and authorization

1. Require `security.authorization: enabled` (or managed auth-required).
2. Prefer **SCRAM-SHA-256**; avoid anonymous data access on reachable ports.
3. Prove unauth access only in scope with non-destructive `ping` / listDatabases
   — do not dump collections for impact theater.
4. Connection strings must set user, `authSource`, and TLS; no secrets in git.

### 4. Localhost exception (bootstrap only)

When authorization is on but no users exist, MongoDB allows first-user creation
from connections that appear local:

1. Use **only** for initial bootstrap or owned break-glass recovery.
2. Create a strong admin immediately, then app users; verify remote unauth fails.
3. Do not leave bootstrap windows with `mongod` on all interfaces.
4. Document the runbook; do not depend on the exception long-term.

### 5. Role-based access (RBAC)

- Separate cluster/admin from application users.
- Narrowest built-in roles (e.g. `readWrite` on `appdb`); avoid `root` for apps.
- Custom roles when built-ins are too broad; audit unused accounts and shared
  prod/dev passwords; rotate and revoke on offboarding.

### 6. TLS and free monitoring

1. `net.tls` mode `requireTLS` (or managed TLS / `mongodb+srv`); validate CA/SAN.
2. Replica/shard internal auth (keyfile or x.509); no public replica ports.
3. **Disable free monitoring** if unused or policy-disallowed; lock down agents
   and legacy HTTP surfaces; remove sample/test DBs from prod.

### 7. Remediate and verify

Apply bindIp + allowlists; enable auth and least-privilege users; enforce TLS;
re-test apps; document residual risks (legacy drivers, temporary allowlist IPs).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| MongoDB auth, SCRAM, bindIp, TLS, RBAC, localhost exception | **This skill** | — |
| Credential/URI storage and rotation | `secrets-management-hygiene` | this skill |
| App drivers / IaC changes | `code-quality-standards` | this skill |
| NoSQL injection in queries | `nosql-injection` | this skill for DB boundary |
| MongoDB wire/PCAP | `NetworkProtocolAnalysisSkill` | `traffic-analysis-pcap` |
| K8s Service exposure | `kubernetes-pentesting` | this skill |

Helpers when applicable: **`code-quality-standards`** (clients/templates),
**`secrets-management-hygiene`** (passwords, keyfiles, Atlas keys),
**`NetworkProtocolAnalysisSkill`** (authorized PCAP beyond mongosh).

## Output Checklist

- [ ] Scope recorded; no out-of-scope 27017 scanning
- [ ] Inventory of instances, clients, admin paths, data criticality
- [ ] Not public; `bindIp` / SG / Atlas allowlist verified
- [ ] Authorization enabled; SCRAM preferred; no anonymous network data access
- [ ] Localhost exception bootstrap-only; admin created promptly
- [ ] RBAC least privilege; admin ≠ app users; no shared prod/dev secrets
- [ ] TLS required (or documented private-network exception); replica auth set
- [ ] Free monitoring off if required; agents/HTTP surfaces locked down
- [ ] Secrets via `secrets-management-hygiene`; clients/IaC via `code-quality-standards`
- [ ] Residual risks and break-glass path documented

## Rules

- Defense and **authorized assessment only** — do not exploit third-party MongoDB.
- Prove exposure and privilege without mass dumps or drops on shared systems.
- Rotate credentials before publishing detailed prod exposure reports.
- Redact evidence; treat open Internet MongoDB as an incident, not a trophy.

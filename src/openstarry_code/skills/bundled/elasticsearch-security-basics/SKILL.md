---
name: elasticsearch-security-basics
description: >
  Authorized Elasticsearch security hardening: xpack.security, HTTP/transport TLS,
  anonymous access disabled, users/role mapping, no public 9200/9300, and least-privilege
  snapshot/restore. Use when reviewing elasticsearch.yml, Elastic Cloud / ECK / self-managed
  clusters, or lab instances you own — not for unauthorized scanning or abusing third-party ES.
---

# Elasticsearch Security Basics

Assess and harden **Elasticsearch** for clusters you own or are explicitly authorized
to test. Focus on security enablement, TLS, identity/roles, public API exposure, and
snapshot privileges — not weaponizing open Internet instances.

## Scope And Authorization

- **In scope:** org-owned clusters (self-managed, Elastic Cloud, ECK), staging/prod under
  written engagement, local Docker/lab/CTF instances, config/IaC review without live
  exploit of out-of-scope hosts.
- **Out of scope:** mass scanning 9200/9300; dumping third-party indices; destructive
  wipes on foreign clusters; using ES to pivot outside engagement scope.
- Prefer **read-only probes** first (`GET /`, `_cluster/health`, `_security/*` with
  provided creds). Gate destructive index ops, role changes, and restores behind approval.
- Redact passwords, API keys, service tokens, cloud IDs, and PII from reports.
- Suspected **Internet-exposed prod with security off or anonymous read:** treat as
  incident — isolate, enable security, rotate credentials, audit repos and access.

## When To Use

- Reviewing `elasticsearch.yml`, keystore, Elastic Cloud settings, Helm/ECK/Compose
  that publish 9200
- Cluster beyond private network; `xpack.security` off/missing; anonymous access on
- TLS missing on HTTP (9200) or transport (9300); weak shared `elastic` superuser
- Over-privileged role mapping, native users, or API keys
- Broad snapshot/restore privileges; hardening or “was ES open?” post-incident

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Secret storage of ES passwords/API keys | `secrets-management-hygiene` |
| Client/IaC reliability | `code-quality-standards` |
| nginx/Kibana edge TLS and headers | `nginx-security-headers` |
| PCAP of HTTP/TLS to ES | `NetworkProtocolAnalysisSkill`, `traffic-analysis-pcap` |
| Other data-store exposure (e.g. Redis) | `redis-security-misconfig` |

## Workflow

### 1. Inventory

List nodes (version, deploy type, ports, network), clients (apps, Beats/Agents,
Logstash, Kibana, CCS/CCR), admin paths, and snapshot repos (S3/GCS/Azure/FS).
Note data sensitivity. Output: inventory with owners — no secrets.

### 2. Network exposure (authorized)

| Check | Evidence |
| --- | --- |
| Public SG/NACL/LB | 0.0.0.0/0 or ::/0 on **9200/9300** |
| Bind / publish | `http.host` / `network.host`; Docker `9200:9200` |
| Transport isolation | 9300 private / inter-node only |

**Hard rule:** no public **9200** without strong auth, TLS, and org-approved exception.
Prefer private endpoints, VPN/PrivateLink, IP allowlists, controlled edge.

### 3. xpack security and anonymous

1. Confirm `xpack.security.enabled: true` (verify on custom images/upgrades).
2. **Anonymous disabled** — no unauthenticated index read via anonymous roles.
3. Bootstrap/reset `elastic` only via break-glass; prefer API keys/service accounts
   for apps (`secrets-management-hygiene`).

```bash
# Authorized only — expect 401 without creds when security is on
curl -sS -o /dev/null -w "%{http_code}\n" "https://es.internal:9200/"
curl -sS -u "$ES_USER:$ES_PASS" "https://es.internal:9200/_security/authenticate"
```

Unauthenticated `200` on a reachable port → **critical exposure** (do not mass-dump).

### 4. TLS (HTTP and transport)

1. HTTP TLS to clients (`xpack.security.http.ssl.*`).
2. Transport TLS between nodes (`xpack.security.transport.ssl.*`); verification on.
3. Keys in keystore/secrets manager — never git; document SANs and rotation.
4. Kibana/agents trust the correct CA.

### 5. Users, roles, role mapping

1. Least privilege: index-scoped privileges — not `superuser`/`all` for apps.
2. Explicit role mapping from IdP groups/DNs; remove wildcards that grant admin.
3. Separate human admin, automation, and ingest; no shared prod/dev passwords.
4. Review API keys: owner, role descriptors, expiry; invalidate after leak.

### 6. Snapshot privileges

1. Who has snapshot create/restore, `manage_slm`, or broad `manage`?
2. Writable repos + restore can overwrite indices or exfiltrate if roles/IAM are weak.
3. Lock repo config to admins; least-privilege cloud IAM on buckets; encrypt repos.

### 7. Remediate and verify

Close public ports; enable security + TLS; rotate exposed credentials; tighten
roles/API keys; restrict snapshot privileges; re-test externally; document residuals.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ES xpack, TLS, anonymous, roles, public 9200, snapshot privs | **This skill** | — |
| Password/API key/repo secret lifecycle | `secrets-management-hygiene` | this skill |
| Client/Helm/IaC changes | `code-quality-standards` | this skill |
| nginx edge in front of Kibana/ES | `nginx-security-headers` | this skill |
| PCAP / TLS capture | `NetworkProtocolAnalysisSkill` | `traffic-analysis-pcap` |

## Output Checklist

- [ ] Scope/authorization recorded; no out-of-scope 9200/9300 scanning
- [ ] Inventory of nodes, clients, admin paths, data sensitivity
- [ ] Not publicly reachable on 9200/9300 (external path verified)
- [ ] `xpack.security` on; anonymous disabled (401/auth evidence)
- [ ] HTTP + transport TLS; keys not in VCS
- [ ] Roles/role mapping least-privilege; no unnecessary superuser
- [ ] App API keys/service accounts with rotation plan
- [ ] Snapshot/SLM privileges and repo IAM restricted
- [ ] Secrets via `secrets-management-hygiene`; code/IaC via `code-quality-standards`
- [ ] Residual risks and break-glass admin path documented

## Rules

- **Defense and authorized assessment only** — do not exploit third-party ES.
- Prove exposure/privileges non-destructively; avoid mass dumps or deletes on shared systems.
- Rotate credentials before publishing when prod was open; redact PII/secrets in evidence.

# Note

Owns **Elasticsearch security baselines**: xpack security, TLS, anonymous disabled,
role mapping, no public 9200, snapshot privilege hygiene. Pair with
`secrets-management-hygiene` and `code-quality-standards` as needed.

---
name: kafka-acl-basics
description: >
  Kafka ACL and auth hardening for owned or authorized clusters: SASL/SSL,
  super.users, authorizer config, least-privilege topic and consumer-group
  ACLs, and ZooKeeper vs KRaft metadata-auth notes. Use when reviewing
  server.properties / kraft configs, kafka-acls.sh, allow.everyone.if.no.acl.found,
  missing producer/consumer grants, or multi-tenant topic isolation — not for
  unauthorized cluster probing or abusing third-party brokers.
---

# Kafka ACL Basics

Design, review, and remediate **Kafka authorization** (ACLs) and the authn stack
(SASL + TLS) on clusters you own or are explicitly authorized to assess.
Evidence-driven: configs, ACL listings, and controlled client tests outweigh guesses.

## When To Use

| Situation | Direction |
| --- | --- |
| ACL design/audit for topics, groups, transactional IDs, cluster ops | **This skill** |
| Authorizer, `super.users`, SASL/SSL listeners, kraft or server.properties | **This skill** |
| `allow.everyone.if.no.acl.found=true` or empty ACLs on shared brokers | **This skill** |
| Least-privilege produce/consume; ZooKeeper vs KRaft auth notes | **This skill** |
| SCRAM/keystore secrets in git | `secrets-management-hygiene` |
| Client/IaC quality | `code-quality-standards` |
| Kafka wire/PCAP (owned) | `NetworkProtocolAnalysisSkill` |

## Scope And Authorization

- **In scope:** org-owned Kafka (self-managed, MSK, Confluent, Strimzi), staging
  under written engagement, local Docker/lab clusters, config/IaC review.
- **Out of scope:** scanning Internet-exposed Kafka without permission; ACL or
  topic destruction on shared prod without change control; pivoting beyond the
  engagement with broker access.
- Prefer **read-only** first: configs, `kafka-acls --list`, describe-only admin.
  Gate ACL/topic deletes and `super.user` experiments behind approval.
- Redact SCRAM material, keystore passwords, JAAS, and sensitive principals.
- Do not enable `allow.everyone.if.no.acl.found=true` on production “to test”
  without rollback and network compensating controls.


## Workflow

### 1. Inventory listeners, identity, and metadata mode

1. Map listeners: `PLAINTEXT` / `SSL` / `SASL_PLAINTEXT` / `SASL_SSL`; internal vs external.
2. Note **ZooKeeper** (`zookeeper.connect`) vs **KRaft** (`process.roles`, controller quorum).
3. Record authorizer class and `super.users` (User: principal list).
4. List principals: SASL users, mTLS DNs, service accounts.

```text
Client ──SASL (+ TLS)──▶ Broker ──authorizer + ACLs──▶ Topic / Group / Cluster
Metadata: ZK (legacy)  or  KRaft (controller + broker-stored ACLs/SCRAM)
```

### 2. Authentication and transport baseline

| Check | Secure direction | Common failure |
| --- | --- | --- |
| Listener | `SASL_SSL` (or mesh mTLS) on untrusted nets | `PLAINTEXT` multi-tenant/public |
| SASL | SCRAM-SHA-256/512, GSSAPI, or OAUTHBEARER | `PLAIN` over cleartext; shared admin |
| TLS | Valid broker (+ client) certs; modern protocols | Expired trust; missing client auth |
| Inter-broker | Dedicated secure listener + credentials | Weak PLAINTEXT for clients and replicas |
| Secrets | Vault/file-injected JAAS and keystores | Passwords in Compose/Helm git |

**ZooKeeper:** secure ZK auth/ACLs if ZK remains; open ZK undoes broker hardening.
**KRaft:** isolate controller listeners; SCRAM/ACLs via broker APIs still need network restriction on controllers.

### 3. Authorization model (least privilege)

ACL tuple: principal, host, operation, resource (Topic, Group, Cluster,
TransactionalId, …), Allow/Deny.

| Role | Resources | Minimal ops |
| --- | --- | --- |
| Producer | Topic(s) | `Write`, often `Describe` |
| Consumer | Topic(s) + Group | Topic `Read`/`Describe`; Group `Read` |
| Streams / EOS | + TransactionalId | As above + transactional grants |
| Topic admin / CI | limited Cluster/Topic | `Create`/`Alter`/`Delete` only if required |

Prefer narrow **Allow** over broad Allow + Deny. Avoid `User:*` and app
principals with `All` on `Topic:*` / `Group:*` / `Cluster:kafka-cluster`.

### 4. Authorizer, super.users, and ACL evidence

1. Authorizer must be **enabled**; without it, ACLs are ignored.
2. Steady-state prod: `allow.everyone.if.no.acl.found=false` once ACLs exist (true only for bootstrap).
3. `super.users`: minimal operators (and inter-broker if required). Super users **bypass** ACLs — treat as root.
4. List ACLs; flag over-broad app grants and unrestricted Host where identity is weak.

```bash
# Owned/lab — adjust bootstrap and paths for your distro
kafka-acls.sh --bootstrap-server "$BOOTSTRAP" --command-config client.properties --list
kafka-acls.sh ... --add --allow-principal User:orders-producer \
  --operation Write --operation Describe --topic orders.events
kafka-acls.sh ... --add --allow-principal User:orders-consumer \
  --operation Read --operation Describe --topic orders.events \
  --group orders-cg --operation Read
```

### 5. Verify and remediate

1. Negative tests (authorized): app principal cannot create topics, alter configs,
   read foreign topics/groups, or use Cluster admin ops unless granted.
2. Rotate SCRAM/keystores after over-privilege (`secrets-management-hygiene`).
3. Clients: principal-per-service; fail closed (`code-quality-standards`).
4. Document residual risk: super.users, open listeners, reachable ZK, dual IAM+ACL.

## Routing

| Need | Skill |
| --- | --- |
| Kafka ACLs, SASL/SSL, super.users, ZK vs KRaft auth notes | **This skill** |
| SCRAM/JAAS/keystore lifecycle | `secrets-management-hygiene` |
| Producer/consumer clients, Helm/IaC, tests | `code-quality-standards` |
| Kafka wire/PCAP (owned) | `NetworkProtocolAnalysisSkill` |
| Generic mTLS identity outside Kafka | `mtls-client-auth-basics` |

**Helpers:** `secrets-management-hygiene`; `code-quality-standards`;
`NetworkProtocolAnalysisSkill` for protocol evidence.

## Output Checklist

- [ ] Scope recorded (cluster, listeners, principals); ZK vs KRaft notes
- [ ] Listeners use SASL/TLS as required; PLAINTEXT justified or removed
- [ ] Authorizer on; `allow.everyone.if.no.acl.found` false in steady state
- [ ] `super.users` minimal; per-app least privilege on topics/groups
- [ ] Negative checks: no cross-tenant produce/consume or admin ops
- [ ] Secrets redacted; rotation via `secrets-management-hygiene`
- [ ] Client/config changes meet `code-quality-standards`; residual risks documented

## Rules

- **Owned or authorized clusters only.** Defense and scoped assessment.
- Super users and open-if-no-ACL are root-equivalent — call them out.
- Principal-per-service over shared produce-all credentials.
- Prove gaps with list/describe and denied ops — not mass deletes on shared systems.
- Keep ACL exports as evidence; originals immutable; redact secrets.

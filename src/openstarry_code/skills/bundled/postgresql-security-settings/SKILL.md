---
name: postgresql-security-settings
description: >
  Authorized PostgreSQL hardening for owned databases: pg_hba.conf access
  rules, SSL/TLS, SCRAM-SHA-256 password auth, role least privilege, superuser
  avoidance, extension allowlists, and connection/auth logging. Use when
  reviewing postgresql.conf / pg_hba.conf, RDS/Cloud SQL Postgres, role grants,
  password_encryption, hostssl, or Postgres security settings on systems you own.
---

# PostgreSQL Security Settings

Harden **PostgreSQL** (self-hosted or managed) for databases you **own** or are
explicitly authorized to assess. Focus on **`pg_hba`**, **TLS**, **SCRAM**,
**roles**, **extensions**, and **logging** — not third-party abuse.

## Scope And Authorization

- **In scope:** org-owned clusters, engagement staging/prod, local Docker/lab/CTF
  Postgres you control, config and IaC review.
- **Out of scope:** mass scanning `5432`; brute-forcing foreign DBs; destructive
  DDL/DML on shared prod without change control; out-of-scope pivot.
- Prefer **config review + non-destructive SQL** (`SHOW`, `pg_hba_file_rules`,
  catalogs). Gate `ALTER SYSTEM`, role drops, and extension installs behind
  backups and approval.
- Redact connection strings, passwords, client certs, and PII from reports.
- Internet-exposed Postgres with `trust`/`md5` and weak passwords is an
  **incident**: isolate, rotate, audit — follow org IR.

## When To Use

- Reviewing `postgresql.conf`, `pg_hba.conf`, or managed parameter groups
- `5432` beyond expected VPC; auth is `trust`/`password`/`md5` not **SCRAM**
- App roles are superuser, over-granted, or share one DBA credential
- Extensions need allowlisting; connection/auth logging missing
- Mentions: Postgres hardening, `pg_hba`, `hostssl`, `scram-sha-256`,
  `password_encryption`, least-privilege roles

Do **not** use as primary for: SQLi (`sqli-sql-injection`), vault/rotation
(`secrets-management-hygiene`), migrations (`database-migration-safety`), client
code (`code-quality-standards`), cloud public-DB flags (`aws-rds-public-access`).

## Workflow

1. **Inventory** — version, managed vs self-hosted, primary/replicas, ports, VPC,
   clients (apps, migrations, BI, bastions, replication). Locate effective config
   (data dir, Helm/ConfigMap, parameter groups). Note TLS and secret paths.

2. **Network / `pg_hba`** — private `listen_addresses`; SG/firewall deny public
   `5432`; first-match HBA rules narrowed by user/DB/CIDR. No remote `trust`/
   `ident` in prod. Prefer `hostssl` + **`scram-sha-256`** over `host`/`md5`/
   `password`. Separate tight replication lines.

```sql
SELECT * FROM pg_hba_file_rules;
SHOW listen_addresses; SHOW ssl; SHOW password_encryption;
```

3. **SSL/TLS** — server SSL, valid certs, TLS 1.2+. Force encrypted remote via
   `hostssl`. Clients: `sslmode=verify-full` (min `require`/`verify-ca`); never
   `disable` for prod remote. Managed force-SSL on; same bar for replication.

4. **SCRAM-SHA-256** — `password_encryption = scram-sha-256`; **rotate** role
   passwords so verifiers are SCRAM not MD5; align `pg_hba` methods; retire remote
   `md5` when clients allow. Vault secrets (`secrets-management-hygiene`).

5. **Roles / avoid superuser** — never run apps as `postgres`/superuser. Split:
   owner (DDL), app (needed DML), readonly, replication, break-glass DBA.
   Object-level grants; audit `rolsuper`, `rolcreaterole`, `rolcreatedb`,
   `rolreplication`, `rolbypassrls`. Lock unused logins; document RLS if used.

```sql
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls
FROM pg_roles WHERE rolcanlogin;
```

6. **Extensions** — inventory `pg_extension`; allowlist only; controlled install.
   Untrusted languages, `file_fdw`, OS/network egress = high impact; restrict
   `CREATE EXTENSION`. Drop unused; keep current with minor upgrades.

7. **Logging** — `log_connections`/`log_disconnections`; useful `log_line_prefix`.
   Prefer `log_statement = ddl` or `log_min_duration_statement` over full SQL
   logs. SIEM + auth-fail alerts. Never log passwords; redact URIs in app logs.

8. **Remediate** — tighten SG+HBA; enforce SSL+SCRAM; split superuser; allowlist
   extensions; verify logs. `code-quality-standards` on IaC/clients; residual risks.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| `pg_hba`, SSL, SCRAM, roles, extensions, logging | **This skill** | — |
| DB password/vault lifecycle | `secrets-management-hygiene` | this skill |
| Client/ORM/IaC implementation | `code-quality-standards` | this skill |
| Application SQLi | `sqli-sql-injection` | this (blast radius) |
| Schema migrations | `database-migration-safety` | this (migration roles) |
| Cloud public DB / SG | `aws-rds-public-access` / cloud SG skills | this (params) |

Helpers when applicable: `code-quality-standards`, `secrets-management-hygiene`,
`database-migration-safety`.

## Output Checklist

- [ ] Scope/authorization recorded; no out-of-scope `5432` scanning
- [ ] Inventory: version, clients, topology, config source
- [ ] Not publicly open without strong HBA + TLS + auth; SG verified
- [ ] `pg_hba`: no remote `trust`; least-privilege methods/CIDRs; first-match OK
- [ ] SSL for remote; clients use adequate `sslmode`
- [ ] `password_encryption = scram-sha-256`; roles rehashed; remote `md5` retired when ready
- [ ] App not superuser; least-privilege logins; replication locked down
- [ ] Extensions inventoried/allowlisted; unused dropped
- [ ] Connection/auth logging on and retained (safe statement policy)
- [ ] Secrets via `secrets-management-hygiene`; no passwords in git
- [ ] IaC/client changes follow `code-quality-standards`
- [ ] Residual risks and break-glass DBA path documented

## Rules

- Defense and **authorized** hardening only — never abuse third-party Postgres.
- Prove exposure/privileges non-destructively; no destructive demos on shared prod.
- Superuser is break-glass/controlled migrations only — not application pools.
- Prefer SCRAM + `hostssl` + narrow CIDRs over perimeter-only trust.
- Rotate credentials after exposure; keep evidence redacted.

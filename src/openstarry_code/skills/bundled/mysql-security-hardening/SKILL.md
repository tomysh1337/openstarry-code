---
name: mysql-security-hardening
description: >
  Authorized MySQL/MariaDB security hardening: bind-address, local_infile,
  user@host accounts, SSL/TLS, remove test DB, FILE privilege, and
  validate_password. Use when reviewing my.cnf, cloud MySQL/MariaDB, or owned
  lab instances — not for scanning or abusing third-party databases.
---

# MySQL / MariaDB Security Hardening

Assess and harden **MySQL** and **MariaDB** for systems you own or are
explicitly authorized to test. Focus on bind, user@host, FILE I/O, SSL, and
password policy.

## Scope And Authorization

- **In scope:** org-owned MySQL/MariaDB, staging/prod under written engagement,
  local Docker/lab CTF, config/IaC review without exploiting out-of-scope hosts.
- **Out of scope:** mass 3306 scanning; brute-force/dump of foreign instances;
  destructive DDL on shared prod without change control and backups.
- Prefer **read-only probes** first (`SHOW VARIABLES`, grants, `mysql.user`).
  Gate `DROP`, privilege revoke, and `REQUIRE SSL` flips behind approval.
- Redact passwords, connection strings, certs, and PII. Internet-exposed prod
  with weak auth → **incident** (isolate, rotate, audit grants); no live IPs.

## When To Use

- Reviewing `my.cnf` / `mysqld.cnf`, Compose MySQL, or managed RDS/Cloud SQL
- Port 3306 beyond localhost/VPC; accounts with `Host='%'`
- Hardening: `bind-address`, `local_infile`, SSL, `test` DB, `FILE`,
  `validate_password`; post-incident exposure or grant audit

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Application SQLi | `sqli-sql-injection` / `injection-checking` |
| Schema/migration safety | `database-migration-safety` |
| DB password/cert lifecycle | `secrets-management-hygiene` |
| App client/IaC quality | `code-quality-standards` |
| MySQL wire PCAP | `NetworkProtocolAnalysisSkill` |

## Workflow

### 1. Inventory

List host/port, version, managed vs self-hosted, clients, TCP vs socket, and
SG/Compose publish. Inventory with owners — no plaintext secrets.

### 2. bind-address and network exposure

```bash
ss -lntp | grep -E '3306|33060'   # authorized host only
mysql -h "$HOST" -u "$USER" -p -e "SHOW VARIABLES WHERE Variable_name IN ('bind_address','skip_networking','port','local_infile','require_secure_transport','have_ssl');"
```

| Check | Hardening direction |
| --- | --- |
| `bind_address` | `127.0.0.1` or private app IP — not public `0.0.0.0` |
| SG / NACL | App subnets only; no `0.0.0.0/0` on 3306 |
| Compose/K8s | Do not publish 3306 on all host interfaces |

### 3. Users, hosts, and test database

```sql
SELECT user, host, plugin, ssl_type, File_priv, Super_priv
  FROM mysql.user ORDER BY user, host;
SHOW DATABASES;
SHOW GRANTS FOR 'app'@'10.0.0.%';
```

1. Remove **anonymous** and empty-password accounts.
2. Narrow **admin** — no `Host='%'` from untrusted nets.
3. Scope app users to client subnets (`'app'@'10.0.1.%'`), not `%`.
4. **Drop default `test` DB** and related `mysql.db` rows on non-dev.
5. Drop unused accounts; no shared prod/dev passwords.

```sql
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
```

### 4. local_infile and FILE privilege

| Control | If weak | Direction |
| --- | --- | --- |
| `local_infile` | `LOAD DATA LOCAL` client file read | `local_infile=0` unless approved ETL |
| `FILE` privilege | `INTO OUTFILE` / server FS R/W | No app role; admin only if required |
| `secure_file_priv` | Unrestricted path | Dedicated dir or platform lockdown |

```sql
SHOW VARIABLES LIKE 'local_infile';
SHOW VARIABLES LIKE 'secure_file_priv';
SELECT user, host FROM mysql.user WHERE File_priv='Y';
```

Prove **permission** (grants/variables), not impact — no prod `INTO OUTFILE`.

### 5. SSL/TLS and validate_password

Configure server certs (TLS 1.2+). Prefer `require_secure_transport=ON` when
clients allow. Privileged/remote users: `REQUIRE SSL` (or `X509`). Clients:
`ssl-mode=REQUIRED`. Verify `SHOW STATUS LIKE 'Ssl_cipher';` non-empty.

```sql
SHOW VARIABLES LIKE 'validate_password%';
```

Enable `validate_password` (MySQL 8 component / MariaDB equivalent / cloud
policy). Prefer MEDIUM/STRONG, length ≥ org baseline. Rotate weak secrets via
`secrets-management-hygiene`.

### 6. Verify

Confirm external connect fails; re-check grants and variables; re-test apps.
Document residual exceptions. Apply `code-quality-standards` to IaC and DSNs.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| MySQL bind, users@host, SSL, FILE, local_infile, test DB, validate_password | **This skill** | — |
| Application SQLi | `sqli-sql-injection` | this skill for server exposure |
| Password/TLS key lifecycle | `secrets-management-hygiene` | this skill for server policy |
| Client/IaC changes | `code-quality-standards` | `database-migration-safety` |
| Wire capture / AWS RDS public | `NetworkProtocolAnalysisSkill` / this skill | `traffic-analysis-pcap`, `aws-rds-public-access` |

## Output Checklist

- [ ] Authorization recorded; no out-of-scope 3306 scanning
- [ ] Inventory of instances, clients, data criticality
- [ ] `bind-address` + SG not public without compensating controls
- [ ] No anonymous/empty-password; admin not on untrusted `%`
- [ ] App users host-scoped; least-privilege grants; `test` DB removed on non-dev
- [ ] `local_infile` off unless approved; `FILE` limited; `secure_file_priv` set
- [ ] SSL required for remote roles; cipher verified
- [ ] `validate_password` (or platform policy) at org baseline
- [ ] Secrets via `secrets-management-hygiene`; code/IaC via `code-quality-standards`; residual risks documented

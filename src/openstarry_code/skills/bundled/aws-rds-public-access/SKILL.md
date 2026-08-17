---
name: aws-rds-public-access
description: >
  Assess and harden Amazon RDS / Aurora for org-owned AWS accounts:
  PubliclyAccessible, DB subnet groups, security groups open to 0.0.0.0/0 on
  3306/5432 (and engine ports), public snapshots, and encryption at rest.
  Use when reviewing publicly reachable databases, open DB security groups,
  unencrypted instances/snapshots, or shared snapshot risk — not for scanning
  or abusing third-party RDS endpoints.
---

# AWS RDS Public Access

Defensive review of **Amazon RDS and Aurora** so databases are not Internet-reachable
by accident, snapshots are not world-shared, and storage is encrypted at rest.
**Owned or explicitly authorized AWS accounts only.**

## When To Use

- Instances/clusters show `PubliclyAccessible = true` or public DNS endpoints
- DB security groups allow `0.0.0.0/0` or `::/0` on **3306**, **5432**, **1433**,
  **1521**, or other engine ports
- DB subnet groups place DBs in public subnets (IGW default route)
- Snapshots are public (`restore=all`) or shared to unknown accounts
- Missing storage encryption (`StorageEncrypted = false`) or unencrypted shares
- Config / Security Hub flags public RDS or open DB ports; pre-prod hardening

Do **not** use as primary for: IAM → `aws-iam-least-privilege`; S3 backups →
`aws-s3-bucket-hardening`; secrets → `secrets-management-hygiene`; Terraform RDS →
`terraform-security-basics`; generic SG review → `firewall-rule-review`; app SQLi →
`sqli-sql-injection`.

## Workflow

### 1. Inventory

Confirm account/region authorization (`aws sts get-caller-identity`). List instances
and clusters; note engine, env, Multi-AZ, data class, and consumers (app SGs, bastion).

```bash
aws rds describe-db-instances \
  --query 'DBInstances[].{Id:DBInstanceIdentifier,Pub:PubliclyAccessible,Enc:StorageEncrypted,Sub:DBSubnetGroup.DBSubnetGroupName,SG:VpcSecurityGroups[*].VpcSecurityGroupId,Eng:Engine}' \
  --output table
aws rds describe-db-clusters \
  --query 'DBClusters[].{Id:DBClusterIdentifier,Pub:PubliclyAccessible,Enc:StorageEncrypted}' \
  --output table
```

### 2. PubliclyAccessible and subnet groups

| Check | Hardened expectation |
| --- | --- |
| `PubliclyAccessible` | `false` unless rare, documented exception |
| Subnet group | **Private** subnets only (no `0.0.0.0/0` → IGW) |
| Endpoint | VPC-private; no public admin for prod data planes |

```bash
aws rds describe-db-subnet-groups --db-subnet-group-name SUBNET_GROUP
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-xxx
```

`PubliclyAccessible=false` alone is insufficient if SGs still allow world ingress
or subnets are public — fix **flag + subnets + SG** together.

### 3. Security groups (3306 / 5432 / engine ports)

Flag ingress from `0.0.0.0/0` or `::/0` on database ports. Prefer app security
groups, tight private CIDRs, or bastion/SSM admin — never open Internet for prod DBs.

```bash
aws ec2 describe-security-groups --group-ids sg-xxx \
  --query 'SecurityGroups[].IpPermissions'
```

### 4. Snapshots public / shared

```bash
aws rds describe-db-snapshot-attributes --db-snapshot-identifier SNAP_ID
aws rds describe-db-cluster-snapshot-attributes --db-cluster-snapshot-identifier CSNAP_ID
# restore=all → public snapshot (critical if data-bearing)
```

Remove `all` and unknown account IDs from restore attributes. Prefer encrypted
snapshots; share only to contracted account IDs.

### 5. Encryption at rest

| Asset | Expectation |
| --- | --- |
| Instance/cluster storage | `StorageEncrypted = true` (CMK if policy requires) |
| Snapshots / clones | Encrypted; no public unencrypted copies |
| Master password | Secrets Manager/SSM — `secrets-management-hygiene` |

Legacy unencrypted DBs need **snapshot → encrypted copy → restore** cutover; you
cannot flip encryption in place.

### 6. Remediation and verify

1. Set `PubliclyAccessible=false`; move subnet group to private subnets only.
2. Revoke world-open SG/NACL rules on 3306/5432/engine ports; allow app/bastion SGs or known CIDRs only.
3. Clear public snapshot attributes; unshare unknown accounts.
4. Encrypt new instances; migrate old stores via encrypted snapshot copy/restore.
5. Prefer private access (VPC apps, RDS Proxy private, SSM over public admin).
6. If exposed: rotate master/app DB passwords; audit CloudTrail/logs.
7. Codify in IaC (`terraform-security-basics`); re-describe until clean; from an
   approved out-of-VPC probe, confirm TCP fails. Do not brute-force or bulk-dump.
8. Document residual exceptions with owner, expiry, and compensating controls.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| RDS public flag, subnet group, open DB SG, public snapshots, encryption | **This skill** | — |
| Broader SG/NACL hygiene | `firewall-rule-review` | this skill for RDS ports/attrs |
| Who may `rds:*` / modify SGs | `aws-iam-least-privilege` | this skill for resource posture |
| Backup/export buckets | `aws-s3-bucket-hardening` | — |
| DB password lifecycle after exposure | `secrets-management-hygiene` | this skill (isolate first) |
| Terraform RDS / module quality | `terraform-security-basics` | `code-quality-standards` |

## Output Checklist

- [ ] Authorization and account/region scope recorded (owned AWS only)
- [ ] Instances/clusters inventoried with engine, env, classification
- [ ] `PubliclyAccessible` false (or time-bounded documented exception)
- [ ] Subnet groups private only (no IGW default route on member subnets)
- [ ] No SG/NACL `0.0.0.0/0` or `::/0` on 3306/5432/engine ports
- [ ] Ingress limited to app SGs / known private CIDRs / controlled admin
- [ ] No public snapshots; cross-account shares reviewed
- [ ] Storage encryption on; snapshot encryption matches policy
- [ ] Credentials rotated if exposed (`secrets-management-hygiene`)
- [ ] IaC updated; residual exceptions owned and time-bounded
- [ ] Report redacts endpoints, secrets, and customer samples

## Scope And Authorization

- **In scope:** RDS/Aurora instances, clusters, proxies, subnet groups, security
  groups, snapshots, and related KMS in accounts **you own** or are contracted to
  assess; prefer read-only `Describe*` first.
- **Out of scope:** Internet-wide open-DB hunting; connecting to or dumping
  third-party databases; unapproved destructive modifies on shared prod.
- Gate `ModifyDBInstance`, SG rewrites, snapshot share changes, and encryption
  migrations behind approval, backups, and rollback. Redact endpoints, secrets,
  and customer data. Public exposure of **your** DB: isolate, rotate, audit.

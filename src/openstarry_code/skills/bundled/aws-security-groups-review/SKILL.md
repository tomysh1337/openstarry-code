---
name: aws-security-groups-review
description: >
  Authorized AWS Security Group (SG) and related NACL review for owned accounts:
  inventory rules, flag 0.0.0.0/0 and ::/0, unused or stale rules, SG-to-SG
  references, least-privilege ports, and stateful SG vs stateless NACL semantics.
  Use when reviewing VPC security groups, inbound/outbound rules, console or CLI
  exports, or IaC-defined SGs — not for unauthorized Internet scanning or
  third-party account probing.
---

# AWS Security Groups Review

Review and harden **VPC Security Groups** (and complementary NACLs) so only
intended traffic is allowed. For **org-owned or explicitly authorized AWS
accounts** — not mass scanning or attacking foreign VPCs.

## Scope And Authorization

- **In scope:** SGs, ENI attachments, VPC NACLs, and flow logs in accounts **you
  own** or are contracted to harden; read-only `Describe*`; controlled rule
  changes with rollback.
- **Out of scope:** Unauthorized Internet scanning; opening prod without change
  control; abusing open ports on third-party systems; destructive prod lockouts.
- Prefer **CLI/console inventory + VPC Flow Logs** over probes. Controlled
  connectivity checks only from approved vantage points to in-scope targets.
- Redact private CIDRs, bastion IPs, and topology outside ops channels.
- Helpers: IaC → `terraform-security-basics` + `code-quality-standards`; who may
  change SGs → `aws-iam-least-privilege`; multi-platform firewalls →
  `firewall-rule-review`.

## When To Use

- Reviewing **security group** inbound/outbound rules (EC2, RDS, ELB, EKS nodes)
- **`0.0.0.0/0` or `::/0`** on admin, DB, cache, or other sensitive ports
- Cleaning **unused SGs**, orphan/stale rules, or forgotten temporary wide opens
- Preferring **SG-to-SG references** over broad CIDRs; least-privilege ports
- Clarifying **stateful SG vs stateless NACL** roles and default deny
- Post-incident “was SSH/DB open to the Internet?” VPC exposure reviews

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Generic/host/multi-cloud firewall review | `firewall-rule-review` |
| IAM who can change SGs | `aws-iam-least-privilege` |
| S3 public access | `aws-s3-bucket-hardening` |
| Terraform SG modules | `terraform-security-basics` (+ this for live audit) |
| In-cluster NetworkPolicy | `kubernetes-network-policy` |
| Secrets after an open path | `secrets-management-hygiene` |

## Workflow

### 1. Inventory (owned account)

1. Record account ID, region(s), VPC(s), env, and authorization.
2. List SGs (name, VPC, attachments/consumers); map zones: Internet → edge/ALB →
   app → data → bastion/mgmt.
3. **Console:** VPC → Security Groups (filter by VPC / inbound). **CLI:**

```bash
aws sts get-caller-identity
aws ec2 describe-security-groups --query 'SecurityGroups[].{ID:GroupId,Name:GroupName,Vpc:VpcId}' --output table
aws ec2 describe-network-acls --query 'NetworkAcls[].{ID:NetworkAclId,Vpc:VpcId,Default:IsDefault}' --output table
aws ec2 describe-security-groups --output json > sg-export.json
```

### 2. Flag world-open and over-broad rules

Inspect every inbound rule (and critical egress). Severity signals:

| Pattern | Signal |
| --- | --- |
| `0.0.0.0/0` / `::/0` → 22, 3389, 5985/5986 | Critical admin surface |
| World-open DB/cache (3306, 5432, 1433, 27017, 6379, 9200…) | Critical data plane |
| World-open all TCP/UDP or ports `1-65535` | Critical over-broad |
| World-open 80/443 on **edge/ALB only** | Often OK — verify intent |
| Whole VPC/`/8` into data tier; undated any-any | High lateral / stale hole |

Filter exports for `CidrIp`/`CidrIpv6` of `0.0.0.0/0` and `::/0`. Do **not**
prove exposure via unauthorized Internet scans.

### 3. SG references and least-privilege ports

1. Prefer **source = security group ID** (or managed prefix list) for tier paths:
   ALB-SG → app-SG → db-SG — not wide CIDRs.
2. Allow only required **ports/protocols**; avoid “all traffic” between tiers
   unless owned and justified.
3. Split kitchen-sink SGs by function; review **egress** on data tiers (not
   ingress-only reviews).

### 4. Unused SGs and rules

1. No ENI/instance/LB/RDS (and no Lambda/VPC-endpoint consumers) → delete candidate.
2. Zero hits over org window (Flow Logs / tickets) → remove candidate.
3. Broken references to deleted source SGs → fix or drop.
4. Keep immutable pre-change exports for rollback evidence.

### 5. NACLs vs security groups

| Layer | Behavior | Review focus |
| --- | --- | --- |
| **SG** | Stateful; allow-only; on ENIs | Primary app allow policy |
| **NACL** | Stateless; allow+deny; subnet; numbered | Ephemeral return ports; accidental deny; default allow-all |

A tight NACL does **not** replace SG least privilege. Custom NACLs that allow
inbound but omit ephemeral outbound break return traffic — change under control.

### 6. Remediate and verify

1. Narrow admin to bastion/VPN/`/32` or **SSM Session Manager** (prefer no
   inbound SSH when SSM is the access path).
2. Replace private-tier CIDR sources with SG references; remove unused rules/SGs.
3. Ticket residual exceptions with **owner + expiry**; fix IaC to stop drift.
4. Re-export rules; prove expected Internet deny via architecture (no public IP,
   route tables, SG rules) — **no unauthorized scanning**.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| AWS SG/NACL review, 0.0.0.0/0, SG refs, unused SGs | **This skill** | — |
| Generic/host firewall methodology | `firewall-rule-review` | this skill for AWS |
| IAM Authorize/RevokeSecurityGroup* | `aws-iam-least-privilege` | this skill for rules |
| Terraform `aws_security_group*` | `terraform-security-basics` | this skill for live audit |
| SG module/script quality | `code-quality-standards` | this skill for controls |
| Secrets at risk after open path | `secrets-management-hygiene` | this skill for network cause |
| K8s NetworkPolicy | `kubernetes-network-policy` | this skill for node/VPC SGs |

## Output Checklist

- [ ] Authorization, account, region(s), VPC(s) recorded
- [ ] SG inventory with consumers; export retained (CLI/console)
- [ ] All `0.0.0.0/0` and `::/0` rules listed with port/proto + justification
- [ ] Admin/data ports not world-open without explicit exception
- [ ] Tier traffic uses SG-to-SG (or prefix list) where practical
- [ ] Ports/protocols least privilege; no unjustified all-traffic rules
- [ ] Unused SGs and stale/zero-hit rules flagged or removed
- [ ] NACL vs SG roles stated; custom NACL ephemeral/deny pitfalls checked
- [ ] Egress on sensitive tiers reviewed; exceptions have owner + expiry
- [ ] No unauthorized scan evidence used; verify via config/flow logs
- [ ] IAM/IaC follow-ups routed; residual risk and bastion/SSM path documented

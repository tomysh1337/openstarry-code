---
name: gcp-firewall-rules
description: >
  Review and harden Google Cloud VPC firewall rules for owned projects: 0.0.0.0/0
  ingress, priority/order, target tags vs service accounts, hierarchical firewall
  policies, and shadow/redundant rules. Use when assessing GCP VPC allow/deny
  posture, open admin ports, over-broad CIDRs, or effective policy after org/folder
  policies — not for scanning or abusing third-party GCP networks.
---

# GCP Firewall Rules (Authorized Hardening)

Assess and harden **Google Cloud VPC firewall rules** and **hierarchical firewall
policies** for **org-owned or explicitly authorized GCP projects** only.

## Scope And Authorization

- **In scope:** VPC firewall rules, hierarchical firewall policies (org/folder),
  network tags, service-account targets, and VPC layout in projects you **own**
  or are contracted to harden; read-only exports; controlled changes with rollback.
- **Out of scope:** Off-scope scanning; opening prod management ports without
  change control; foreign orgs/tenants; abusing discovered open hosts.
- Prefer **config + VPC Flow Logs** over live probes. Gate broad deny/priority
  rewrites on shared prod behind a maintenance window and rollback plan.
- Redact internal CIDRs, bastion IPs, project numbers, and customer topology.
- GKE pod policy → `kubernetes-network-policy`. Who can edit rules →
  `gcp-iam-basics`. Cross-platform SG/ACL patterns → `firewall-rule-review`.

## When To Use

- Reviewing **VPC firewall rules** (Console, `gcloud`, Terraform
  `google_compute_firewall` / hierarchical policy resources)
- **0.0.0.0/0** or `::/0` ingress to SSH, RDP, DB, Redis, or admin APIs
- **Priority** surprises, implied allow/deny, or rules that never hit
- **Target tags** vs **service accounts** vs “all instances”
- Org/folder **hierarchical firewall** overriding or shadowing VPC rules
- Cleaning **shadow**, duplicate, stale temporary, or undocumented broad allows
- Mentions: GCP firewall, VPC allow, network tags, target SA, hierarchical
  firewall policy, effective firewall, open 22/3389 on 0.0.0.0/0

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Multi-platform SG/NSG/host firewall review | `firewall-rule-review` |
| GCP IAM / who can edit firewalls | `gcp-iam-basics` |
| GKE NetworkPolicy / CNI isolation | `kubernetes-network-policy` |
| Secrets after a network hole | `secrets-management-hygiene` |
| Terraform module quality / tests | `code-quality-standards`, `terraform-security-basics` |
| Estate inventory first | `recon-and-methodology` |

## Core Semantics (GCP-specific)

| Concept | Practice |
| --- | --- |
| Priority | Lower number = **higher** precedence (0–65535); first match wins per direction |
| Deny vs allow | Explicit **deny** can block lower-priority allows; document overrides |
| Targets | Prefer **service accounts**; tags are mutable/shared — avoid “all instances” on sensitive allows |
| Hierarchical | Org/folder policies + VPC rules → always model **effective** policy |
| Shadow rules | Higher-priority broader allow/deny can make later rules dead (false safety) |
| Sources | Prefer IAP, VPC, or known admin CIDR over `0.0.0.0/0` for management |

**Anti-patterns:** ingress `0.0.0.0/0` to 22/3389/3306/5432/6379/27017; full port
ranges to app tiers; tags reused across trust zones; temporary any/any without
owner/expiry; deny never reached because an earlier allow shadows it.

## Workflow

### 1. Scope and inventory

Confirm project/org IDs, ownership, and change-freeze. Map VPCs, subnets, Shared
VPC host/service projects, trust zones, and critical assets (bastion, DB, GKE
nodes, internal LBs). Incomplete estate map → `recon-and-methodology` first.

### 2. Export VPC and hierarchical rules

```bash
# Owned projects only
gcloud config set project "$PROJECT_ID"
gcloud compute firewall-rules list --format=json
gcloud compute firewall-rules list \
  --filter='direction=INGRESS AND sourceRanges:0.0.0.0/0' \
  --format='table(name,priority,allowed,targetTags,targetServiceAccounts,network)'
# If org/folder in scope: list network-firewall-policies and their rules
```

Capture name, network, direction, action, priority, ranges, ports/protocols,
target tags/SAs, disabled flag, and description.

### 3. Priority, targets, shadows, egress

1. Sort by network + priority; for critical 5-tuples (Internet→SSH, peer→DB),
   find the **first** matching rule.
2. Flag **shadowed** rules (dead after a higher-priority broader match).
3. Prefer **service-account** targets for prod; review tag sprawl across zones.
4. Reconcile hierarchical org/folder policy with VPC rules for effective path.
5. Review **egress** from data/app tiers — not ingress-only.

### 4. Remediate and verify

Narrow management paths (IAP TCP, bastion, VPN/CIDR); remove unjustified
`0.0.0.0/0` admin/data ports. Split over-broad rules; assign owner, ticket, and
expiry on exceptions. Delete disabled/stale/shadowed rules; encode via IaC
(`terraform-security-basics` + `code-quality-standards`). Re-export; use Flow
Logs or probes from **approved** sources only. Credential exposure →
`secrets-management-hygiene`. Rule mutators → `gcp-iam-basics`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GCP VPC / hierarchical firewall review | **This skill** | — |
| Generic multi-platform firewall methodology | `firewall-rule-review` | this skill (GCP semantics) |
| IAM on firewall/network admin | `gcp-iam-basics` | this skill (rule content) |
| GKE pod NetworkPolicy | `kubernetes-network-policy` | this skill (node VPC) |
| Secrets after open exposure | `secrets-management-hygiene` | this skill (close path) |
| Terraform `google_compute_firewall` | `terraform-security-basics` | this skill + CQS |
| Missing project/VPC inventory | `recon-and-methodology` | this skill (deep rules) |

## Output Checklist

- [ ] Authorization, project/org scope, rollback constraints recorded
- [ ] VPCs, Shared VPC relationships, trust zones documented
- [ ] VPC rules exported; hierarchical policies included when in scope
- [ ] All ingress `0.0.0.0/0` / `::/0` allows listed with ports and targets
- [ ] No unjustified Internet-facing admin or data ports
- [ ] Priority / first-match behavior explained for critical paths
- [ ] Targets reviewed (SAs preferred; tags not cross-zone)
- [ ] Shadowed, duplicate, disabled, and stale temporary rules listed
- [ ] Egress posture noted for sensitive tiers
- [ ] Effective policy reconciled (hierarchical + VPC)
- [ ] Remediation least-privilege and staged; IaC preferred
- [ ] Flow-log or approved-probe evidence for high findings
- [ ] IAM / secrets / GKE follow-ups routed; exceptions have owner + expiry

## Rules

- **Owned or authorized GCP only** — no foreign org/project assessment.
- Prove exposure with **exports + priority analysis + logs**, not disruptive
  Internet-wide scans.
- State evaluation order and hierarchical vs VPC layers in findings.
- Undated unowned temporary `0.0.0.0/0` is still a finding.
- Keep immutable exports; change only through approved process and IaC.

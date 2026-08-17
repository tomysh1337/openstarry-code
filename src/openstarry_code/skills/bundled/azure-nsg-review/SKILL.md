---
name: azure-nsg-review
description: >
  Authorized Azure Network Security Group (NSG) review for owned subscriptions:
  rule priority, Any/Any Allow, service tags, Application Security Groups (ASG),
  NSG flow logs, and effective security rules. Use when auditing Azure NSG
  inbound/outbound rules, shadow priorities, open management ports, missing flow
  logging, or NIC effective rules — not for attacking third-party Azure estates.
---

# Azure NSG Review

Assess and harden **Azure Network Security Groups** so subnet and NIC traffic
matches least privilege. Defensive work for **org-owned or explicitly authorized
Azure subscriptions** only.

## Scope And Authorization

- **In scope:** NSGs, ASGs, VNets/subnets/NICs, Network Watcher flow logs, and
  ARM/Bicep/Terraform defining those rules in owned or contracted subscriptions;
  read-first portal/CLI/API exports.
- **Out of scope:** foreign-tenant scanning; unapproved prod opens; bulk traffic
  generation; disabling flow logs to hide activity; shared-platform bypass of
  other customers.
- Prefer **config + effective rules + flow logs** over live probes. Probe only
  approved targets from approved vantage points with rollback ready.
- Redact subscription IDs, private IP maps, jump hosts, and customer CIDRs in
  external reports.
- Generic multi-cloud review → `firewall-rule-review`. Blob exposure →
  `azure-blob-misconfig`. Secrets after exposure → `secrets-management-hygiene`.
  IaC quality → `code-quality-standards`.

## When To Use

- Reviewing Azure **NSG** rules, priorities, or subnet/NIC associations
- Finding **Any / Any / Allow** or Internet-open admin/data ports
- Checking **service tags** and **ASG** membership correctness
- Explaining **priority** shadowing (lower number wins; first match)
- Validating **effective security rules** on a NIC or subnet
- Enabling or triaging **NSG flow logs** / Traffic Analytics gaps
- Mentions: Azure NSG, effective security rules, ASG, Network Watcher flow log

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Generic multi-platform firewall methodology | `firewall-rule-review` |
| Azure Blob public access / SAS | `azure-blob-misconfig` |
| K8s NetworkPolicy (not Azure NSG) | `kubernetes-network-policy` |
| Estate inventory / engagement plan | `recon-and-methodology` |
| Secrets rotation after open path | `secrets-management-hygiene` |
| Module/tests for rule-as-code | `code-quality-standards` |

## Workflow

### 1. Inventory associations and trust zones

Record subscription, RGs, env, freeze, and authorization. List NSGs; note subnet
vs NIC association (both apply — understand merge). Map zones: Internet edge,
app, data, management/bastion, private endpoints. Incomplete estate →
`recon-and-methodology` first.

```bash
# Owned subscription only
az network nsg list -o table
az network nsg show -g "$RG" -n "$NSG" -o json
```

### 2. Export rules and priority semantics

Export security rules. Azure evaluates **priority** ascending (100 before 200);
first match wins per direction. Default rules (65000+) always exist. Per rule:
name, direction, priority, access, protocol, source, destination, ports, owner.
Tag **expected**, **over-broad**, **stale**, **shadowed**, or **undocumented**.

### 3. High-signal anti-patterns

| Pattern | Why it fails |
| --- | --- |
| Inbound Allow from Internet/`*` to 22, 3389, DB ports | Internet admin/data surface |
| Any Any Allow (source/dest/port all open) | Lateral movement and noise |
| Broad Allow that shadows a later Deny | False sense of control |
| Temporary open left months without owner/expiry | Forgotten hole |
| Wrong service tag (Internet vs VNet-only intent) | Unintended exposure |
| Empty/wrong ASG membership | Policy hits wrong NICs |
| Only subnet or only NIC NSG reviewed | Incomplete effective path |
| Flow logs off on sensitive subnets | No forensics or hit evidence |

Prefer ASG, service tag, or narrow CIDR over `*`; specific ports over `*`.

### 4. Service tags, ASGs, and effective rules

Verify service tags match product intent (e.g. `AzureLoadBalancer` probes ≠ full
Internet). ASG rules should express role pairs (web→app→data), not VNet any-to-any;
re-check membership when scale sets change. For critical NICs, pull **effective
security rules** so subnet + NIC + defaults match platform enforcement:

```bash
az network nic list-effective-nsg -g "$RG" -n "$NIC" -o json
```

### 5. Flow logs, remediate, verify

Enable Network Watcher **NSG flow logs** (v2 preferred) to a locked storage
account; optional Traffic Analytics. Use hits to confirm shadow rules, unused
temporary allows, and unexpected Internet sources before inflating severity.
Narrow sources/ports; remove shadowed/duplicates; date exceptions with owner.
Ship via IaC with `code-quality-standards`; stage non-prod; re-export effective
rules and confirm flow logs healthy. Credential exposure risk →
`secrets-management-hygiene`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Azure NSG priority, Any/Any, ASG, service tags, flow logs, effective rules | **This skill** | — |
| Generic SG/iptables/multi-cloud rule hygiene | `firewall-rule-review` | this skill for Azure specifics |
| Azure Blob / storage network exposure | `azure-blob-misconfig` | this skill if NSG path involved |
| Missing asset map / test plan | `recon-and-methodology` | this skill for NSG deep-dive |
| Secrets at risk from open paths | `secrets-management-hygiene` | this skill for network root cause |
| Bicep/Terraform NSG modules and tests | `code-quality-standards` | this skill for policy intent |

## Output Checklist

- [ ] Authorization and subscription/RG scope recorded (owned Azure only)
- [ ] NSGs inventoried with subnet and NIC associations
- [ ] Trust zones and critical assets (bastion, DB, PE) documented
- [ ] Rules exported with priority, direction, access, ports, sources
- [ ] Any/Any Allow and Internet-to-admin/data ports flagged or justified
- [ ] Shadowed and stale temporary rules listed with evidence
- [ ] Service tags and ASG membership match role intent
- [ ] Effective security rules reviewed for critical NICs
- [ ] NSG flow logs enabled for sensitive paths; hits used as evidence
- [ ] Remediation least-privilege and staged; exceptions owned with review date
- [ ] Follow-ups routed (secrets, recon, IaC via `code-quality-standards`)
- [ ] No third-party tenant probing or unapproved prod lockouts

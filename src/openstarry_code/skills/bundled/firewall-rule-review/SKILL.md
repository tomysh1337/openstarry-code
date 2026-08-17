---
name: firewall-rule-review
description: >
  Authorized firewall and security-group rule review methodology: inventory,
  least privilege, shadow/redundant rules, egress control, change hygiene, and
  evidence-based findings. Use when reviewing iptables/nftables, cloud SGs/NSGs,
  host firewalls, or network allowlists you own — not for attacking third parties.
---

# Firewall Rule Review

Review and harden **network allow/deny policy** for systems you own or are
explicitly authorized to assess: host firewalls, cloud SGs/NSGs/NACLs, appliance
ACLs, and rule-as-code — least privilege, documentation, safe change.

## Scope And Authorization

- **In scope:** org-owned VPCs, hosts, labs, and firewall configs under written
  engagement or team ownership; IaC defining the same rules.
- **Out of scope:** off-scope scanning; DoS via rule floods; opening prod without
  change control/rollback; bypassing other tenants.
- Prefer **config and flow-log review** before probes; probe only approved targets
  from approved vantage points. Redact sensitive topology outside ops channels.
- Broad **deny-all** on production needs a maintenance window and rollback.

## Use When

- Reviewing **iptables/nftables/ufw**, `firewalld`, Windows Firewall, or appliance ACLs
- Cloud **security groups**, NACLs, Azure NSG, GCP firewall rules, or similar
- Cleaning **any/any**, broad CIDRs, stale temporary rules, or shadow rules
- Designing **egress** allowlists; post-incident unexpected Internet/cross-env paths
- Chinese/English: 防火墙规则, 安全组, 最小权限, 入站/出站, 影子规则

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Secret exposure after a network hole | `secrets-management-hygiene` |
| Host OS hardening beyond network policy | `linux-hardening-checklist` |
| Engagement planning / asset inventory first | `recon-and-methodology` |
| IaC module quality/tests for rule code | `code-quality-standards` |

## Review Principles

| Principle | Practice |
| --- | --- |
| Default deny | Explicit allows; terminal deny where supported |
| Least privilege | Narrow source, dest, proto, port per layer (edge/SG/host) |
| Documented intent | Owner + ticket; expiry on temporary holes |
| Defense in depth | Edge + SG + host agree — not one layer alone |
| Egress matters | Outbound any/any is exfil and C2 path |
| Evidence | Cite rule id/policy name and exposure path |

## Workflow

### 1. Scope, inventory, topology

1. Record authorization, environments, change-freeze status.
2. Inventory SGs/NSGs, firewall policies, host rule sets, IaC modules.
3. Draw trust zones: Internet, edge, app, data, management/bastion, CI.
4. List critical assets (DB, bastion, vault, K8s API); note which layer is SSOT.
5. Incomplete assets → `recon-and-methodology` first, then return.

### 2. Export and classify

```bash
# Owned systems only — store exports as evidence
sudo nft list ruleset
sudo iptables-save
sudo ufw status verbose
# Cloud: org CLI/API or console export
```

Capture direction, action, priority/order, counters. For every permit: source,
dest, port/proto, path, owner/ticket, last hit. Tag **expected**, **over-broad**,
**stale**, **shadowed**, **conflict**, or **undocumented**.

### 3. High-signal anti-patterns

| Pattern | Why it fails |
| --- | --- |
| Inbound `0.0.0.0/0` to admin/DB (22, 3389, 5432, 6379…) | Internet attack surface |
| All protocols / full port ranges to app subnets | Easy lateral movement |
| Temporary any/any left for months | Forgotten hole |
| Deny never reached (earlier allow shadows it) | False sense of safety |
| Over-trusted shared SG membership | One weak member opens many peers |
| Data-tier egress any; prod↔stage wide; mgmt beyond bastion | Exfil / cross-env / control-plane |

Pair SSH openings with `ssh-key-hygiene` and `linux-hardening-checklist`.

### 4. Egress, evidence, remediate

1. App/data tiers: explicit egress (mirrors, known APIs), not “all outbound”.
2. Prefer **flow logs / hit counts** over noisy scans; if probing, expected allow
   and expected deny from approved sources only.
3. Compare architecture intent vs effective rules; resolve drift.
4. Narrow sources (SG refs, /32, VPN) and ports; date temporary exceptions.
5. Remove shadowed/duplicates; implement via IaC with `code-quality-standards`
   (reviewable diffs; no silent `0.0.0.0/0`). Stage non-prod → canary → monitor.
6. Follow on: `secrets-management-hygiene` if credentials may be exposed;
   `linux-hardening-checklist` for host baselines.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Firewall / SG / ACL rule review | **This skill** | — |
| Credentials at risk from open paths | `secrets-management-hygiene` | this skill for network root cause |
| Host OS/sshd after network review | `linux-hardening-checklist` | this skill for perimeter/SG |
| Asset/exposure inventory first | `recon-and-methodology` | this skill for rule deep-dive |
| Terraform/Ansible firewall modules | `code-quality-standards` | this skill for policy content |

- **`secrets-management-hygiene`:** secret risk after exposure.
- **`linux-hardening-checklist`:** host firewall + broader OS controls.
- **`recon-and-methodology`:** scoping and surface discovery before policy work.
- **`code-quality-standards`:** baseline for rule-as-code changes.

## Checklist

- [ ] Authorization, env, and rollback constraints recorded
- [ ] Topology and SSOT layers (edge / SG / host) documented
- [ ] Effective rules exported as evidence
- [ ] Broad allows have owner/intent or are flagged
- [ ] No unjustified Internet-facing admin/data ports
- [ ] Egress reviewed for data/app tiers — not only ingress
- [ ] Shadowed, duplicate, and stale temporary rules listed
- [ ] Flow-log or controlled-probe evidence for critical findings
- [ ] Remediation least-privilege and staged; IaC preferred
- [ ] Secret/host follow-ups routed; estate gaps via `recon-and-methodology`
- [ ] Rule-as-code meets `code-quality-standards`

## Rules

- **Authorized defensive review only** — no off-scope scanning or recreational lockouts.
- Prefer proving **exposure paths** with config + logs over disruptive tests.
- Undated unowned temporary any/any is still a finding.
- State platform semantics (stateful SG vs stateless NACL) in reports.
- Keep immutable rule exports; change only through the approved process.

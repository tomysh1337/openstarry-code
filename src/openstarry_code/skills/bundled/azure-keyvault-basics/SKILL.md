---
name: azure-keyvault-basics
description: >
  Authorized assessment and hardening of Azure Key Vault: access policies vs
  Azure RBAC, network firewall and private endpoints, soft-delete and purge
  protection, managed identity data-plane access, and secret rotation. Use when
  reviewing org-owned Key Vaults, ARM/Bicep/Terraform, or written Azure
  engagements — not unauthorized third-party vault enumeration.
---

# Azure Key Vault Basics (Authorized Hardening)

Assess and harden **Azure Key Vault** so secrets, keys, and certificates are
reachable only by intended principals, recoverable from accidental delete, and
rotated under a defined process. Defensive and **owned Azure only**.

## Scope And Authorization

- **In scope:** org-owned vaults/subscriptions, staging/prod under written
  engagement, lab tenants you control, IaC review, read-only policy/network inventory.
- **Out of scope:** foreign vault discovery; abusing leaked secrets on third parties;
  purging prod items without change control; out-of-scope subscriptions.
- Prefer **metadata** first. Gate secret-value reads, purges, and network changes.
- Redact secret values, key material, client secrets, and identifying vault URIs.
- Public vault + sensitive secrets → IR: lock network/RBAC, rotate via
  `secrets-management-hygiene`, audit logs — never paste live values.

## When To Use

- Auditing **access policies** vs **Azure RBAC** permission model
- Firewall open to Internet; missing private endpoint / VNet rules
- Soft-delete or **purge protection** off on production vaults
- Apps using shared secrets instead of **managed identity**
- Secret/key/certificate **rotation** or post-leak vault-side disable
- Mentions: Key Vault RBAC, access policy, purge protection, soft-delete,
  Key Vault firewall, managed identity, secret rotation

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org secret inventory, git/.env, leak IR process | `secrets-management-hygiene` |
| Subscription/estate recon | `recon-and-methodology` |
| App/SDK/IaC implementation quality | `code-quality-standards` |
| Multi-cloud Terraform baseline | `terraform-security-basics` |
| Azure Blob public access / storage SAS | `azure-blob-misconfig` |

## Access Model: Policies Vs RBAC

| Model | Notes | Prefer when |
| --- | --- | --- |
| **Vault access policies** | Per-principal secret/key/cert perms on vault | Legacy; avoid mixing with RBAC data plane |
| **Azure RBAC** | Data-plane roles + control-plane assignments | New vaults; groups; least privilege |
| **Do not mix** | Dual models are easy to misread | One model per vault; document exceptions |

`Contributor` on the vault resource ≠ data-plane secret get. Prefer groups and
**managed identities** over long-lived app registration secrets.

## Workflow

### 1. Inventory

List vaults, RGs, subscriptions, env, owners, data class, consumers (App Service,
Functions, AKS, VMs, CI). Note permission model, soft-delete, purge protection,
network default. Incomplete estate → `recon-and-methodology`. No secret values.

### 2. Permission model and least privilege

```bash
az keyvault show -n "$VAULT" -g "$RG" \
  --query "{enableRbacAuthorization:properties.enableRbacAuthorization,enableSoftDelete:properties.enableSoftDelete,enablePurgeProtection:properties.enablePurgeProtection,networkAcls:properties.networkAcls}"
az keyvault show -n "$VAULT" -g "$RG" --query properties.accessPolicies
az role assignment list --scope "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.KeyVault/vaults/$VAULT" -o table
```

Flag broad `all` secret perms; permanent human get/list in prod; CI with purge;
missing deploy-vs-runtime split. Prefer MI + `Key Vault Secrets User` (or narrower).

### 3. Network firewall

Production: default **deny** public; allow selected VNets/IPs or **private endpoint**
only. Trusted Microsoft services only if justified. Permanent `0.0.0.0/0` for build
agents is a finding — use approved private paths and short-lived exceptions.

### 4. Soft-delete, purge protection, diagnostics

Soft-delete **on** (modern default). **Purge protection on** for production so
deleted objects cannot be immediately purged. Diagnostics → Log Analytics: secret
get/list failures, RBAC/policy changes, purge attempts; alert on anomalies.

### 5. Managed identity and rotation

Apps: system- or user-assigned MI when possible. Rotation: dual-version cutover
(new → flip consumers → disable old). On leak: disable/expire versions first, then
rotate dependents — hand org process/scanning to `secrets-management-hygiene`.
Implement IaC/app changes with `code-quality-standards`.

### 6. Report

Order by blast radius (open network + broad get/list first). Evidence: policy/RBAC
snapshots, network ACL, soft-delete/purge flags — never live secret values.
Exceptions: owner + review date.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Key Vault RBAC/policies, firewall, soft-delete/purge, MI | **This skill** | — |
| Secret leak IR, git/.env, org rotation playbooks | `secrets-management-hygiene` | this skill (vault disable/network) |
| Subscription/estate discovery | `recon-and-methodology` | this skill (vault deep dive) |
| App SDK, Bicep/TF modules, tests | `code-quality-standards` | this skill (control intent) |
| Blob/storage public access | `azure-blob-misconfig` | — |

### Routing notes

- **`secrets-management-hygiene`:** lifecycle, scanning, rotation IR — **hand off**
  for org process; this skill owns vault control/data-plane settings.
- **`code-quality-standards`:** apps/IaC that create vaults, wire MI, or secret URIs.
- **`recon-and-methodology`:** authorized subscription map first.

## Output Checklist

- [ ] Authorization recorded; owned Azure / written engagement only
- [ ] Vaults inventoried with owners, env, data class (no secret values)
- [ ] One permission model per vault; RBAC preferred for new; mix justified
- [ ] Runtime MI least privilege; no unjustified permanent human get in prod
- [ ] Network default deny or private endpoint; no permanent open Internet path
- [ ] Soft-delete on; purge protection on for production
- [ ] Diagnostics/alerts on access and config changes
- [ ] Managed identity preferred over client secrets for apps
- [ ] Rotation dual-version plan; leaks → disable then rotate (`secrets-management-hygiene`)
- [ ] Fixes follow `code-quality-standards`; exceptions owned with review date
- [ ] Evidence redacted; no live secret material in reports

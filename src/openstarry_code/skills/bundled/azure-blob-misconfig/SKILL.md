---
name: azure-blob-misconfig
description: >
  Authorized assessment and hardening of Azure Blob Storage public access
  misconfigurations: container public access, anonymous read, SAS/shared keys,
  account firewalls, soft-delete/logging. Use when assessing org-owned accounts or
  written engagements — not unauthorized enumeration of third-party blobs.
---

# Azure Blob Public Access Misconfiguration

Assess and harden **Azure Blob Storage** so containers and accounts do not expose
data anonymously or via over-broad shared access. Defensive methodology only.

## Scope And Authorization

- **In scope:** org-owned storage accounts, staging/prod under written scope, lab
  subscriptions, ARM/Bicep/Terraform review, read-only portal/CLI checks.
- **Out of scope:** mass scanning `*.blob.core.windows.net`; bulk download of
  out-of-scope data; abusing leaked SAS on foreign accounts; unapproved deletes.
- Prefer **metadata/policy** inspection before bulk download. Gate writes/deletes.
- Redact account keys, SAS tokens, connection strings, identifying object paths.
- Public prod containers with sensitive data → IR: disable public access, rotate
  keys/SAS, audit logs.

## Use When

- Azure Storage public access, anonymous blob/container read, or `$web` exposure
- Container level Blob/Container; account “Allow Blob public access” enabled
- Over-broad SAS (account SAS, long TTL, `sp=racwdl`, HTTP allowed)
- Open storage firewall; missing private endpoint; keys/SAS in git or IaC
- Mentions: Azure blob public, anonymous blob, container ACL, SAS leak

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Secret inventory / rotation / vault | `secrets-management-hygiene` |
| Engagement recon / asset inventory | `recon-and-methodology` |
| App/SDK/IaC implementation quality | `code-quality-standards` |
| Multi-cloud Terraform baseline | `terraform-security-basics` |

## Threat Themes

| Theme | Weak outcome | Hardening |
| --- | --- | --- |
| Account public access | Containers can be public | Disable allow-blob-public-access |
| Container ACL | Anonymous list/read | Private containers; auth for reads |
| SAS / keys | Leaked token = data access | Short TTL user-delegation SAS; vault keys |
| Network | Internet public endpoint | Firewall, private endpoints |
| Logging / soft delete off | No recovery or forensics | Soft delete, versioning, diagnostics |

## Workflow

### 1. Inventory

List accounts, RGs, subscriptions, owners, env, data class (static vs backups/PII),
consumers, auth mode (keys, Entra+RBAC, SAS, MI). Incomplete estate map →
`recon-and-methodology` first. No secret values in the inventory.

### 2. Account-level controls

Expect: allow-blob-public-access **off** (unless documented static exception);
Shared Key minimized when Entra works; TLS 1.2+ and HTTPS-only; network default
deny with VNet/IP allowlist or private endpoint.

```bash
az storage account show -n "$ACCOUNT" -g "$RG" \
  --query "{allowBlobPublicAccess:allowBlobPublicAccess,minimumTlsVersion:minimumTlsVersion,supportsHttpsTrafficOnly:supportsHttpsTrafficOnly,networkRuleSet:networkRuleSet}"
```

### 3. Container anonymity

Per container: Private vs Blob (anonymous object read if URL known) vs Container
(anonymous list+read). Public only for intentional static assets — never mixed
with exports/logs/backups/uploads. From an **approved** vantage: non-destructive
HEAD/GET on a canary and unauthenticated list; record status; no bulk exfil.
Review `$web` separately.

### 4. SAS, keys, identity

Via `secrets-management-hygiene`: scan for connection strings, `AccountKey=`,
`?sv=` SAS; prefer user-delegation SAS with minimal `sp`, short expiry, HTTPS-only;
revocable stored access policies; rotate account keys on leak; apps use managed
identity + data-plane RBAC (`Storage Blob Data Reader/Contributor`).

### 5. Network, durability, remediate

Tighten firewall/private endpoints; soft delete/versioning; diagnostics + alerts
on public-access enablement. Disable public access; isolate intentional public
assets; rotate secrets; fix IaC/apps with `code-quality-standards`; re-test
anonymous deny; document exceptions with owner + review date.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Azure blob/container public access, storage SAS/keys | **This skill** | — |
| Secret leak, rotation, connection strings | `secrets-management-hygiene` | this skill (blob revoke) |
| Estate discovery / test plan | `recon-and-methodology` | this skill (blob controls) |
| SDK clients, IaC modules, tests | `code-quality-standards` | this skill (control intent) |

### Routing notes

- **`secrets-management-hygiene`:** keys/SAS/connection-string lifecycle; rotate-first.
- **`code-quality-standards`:** when changing apps/IaC that create containers, mint
  SAS, or wire managed identity.
- **`recon-and-methodology`:** authorized account/blast-radius discovery first.

## Checklist

- [ ] Authorization recorded; no third-party blob hunting
- [ ] Accounts inventoried with sensitivity and owners
- [ ] Allow Blob public access disabled unless documented exception
- [ ] Containers Private by default; public only for intentional assets
- [ ] Anonymous probe fails for sensitive containers (approved vantage)
- [ ] Shared Key minimized; Entra + RBAC / MI preferred
- [ ] SAS least privilege, short TTL, HTTPS-only
- [ ] No keys/SAS/connection strings in git/CI (`secrets-management-hygiene`)
- [ ] Network rules / private endpoints fit prod data risk
- [ ] Soft delete/versioning/logging; alerts on public-access changes
- [ ] Fixes follow `code-quality-standards`; exceptions owned with review date

## Rules

- Authorized assessment/hardening only — no abuse of foreign storage accounts.
- Prove anonymous reachability and policy weakness; avoid bulk download of real data.
- Rotate keys/SAS before wide distribution of reports with live tokens.
- Public access must be explicit product intent, never a leftover ACL.
---

# Note

Owns **Azure Blob public access exposure**. Pair with `secrets-management-hygiene`,
`code-quality-standards`, and `recon-and-methodology`.

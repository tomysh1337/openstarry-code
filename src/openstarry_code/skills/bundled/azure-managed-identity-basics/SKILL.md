---
name: azure-managed-identity-basics
description: >
  Authorized Azure managed identity hardening for owned subscriptions: system-
  vs user-assigned identity, IMDS token acquisition, Azure RBAC on the identity
  principal, and removing secrets from App Settings. Use when enabling or
  reviewing managed identity on App Service, Functions, VMs, AKS, Container Apps,
  or Logic Apps; replacing client secrets; or auditing over-privileged MI RBAC â€?  not for abusing third-party Azure tenants.
---

# Azure Managed Identity Basics (Authorized)

Prefer **Azure managed identities** so workloads obtain Entra ID tokens without
storing client secrets. Defensive work for **org-owned or explicitly authorized
Azure subscriptions** only.

## Scope And Authorization

- **In scope:** system- or user-assigned MI on owned compute (App Service,
  Functions, VMs/VMSS, AKS workload identity, Container Apps, Logic Apps);
  IMDS/MSI tokens; **RBAC** on the identity object ID; clearing App Settings
  secrets; IaC that wires MI.
- **Out of scope:** foreign tenants; tokens for resources you do not own;
  unapproved Owner/Contributor elevation on production MI.
- Prefer read-first inventory (identity state, role assignments, App Setting
  *names*). Gate grants, deletes, and secret removal behind change control.
- Never paste live tokens, connection strings, or client secrets into reports.
- Key Vault â†?`azure-keyvault-basics`. Secret lifecycle / leak IR â†?  `secrets-management-hygiene`. Implementation â†?`code-quality-standards`.

## When To Use

- Choosing **system-assigned** vs **user-assigned** managed identity
- Apps still store **client secrets**, keys, or connection strings in App Settings
- Wiring MI to Key Vault, Storage, SQL, Service Bus, Event Hubs, ACR, etc.
- Reviewing **over-broad RBAC** on an MI principal; debugging **IMDS** / MSI tokens
- Mentions: managed identity, MSI, user-assigned identity, IMDS, DefaultAzureCredential

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Key Vault firewall, soft-delete, purge, access model | `azure-keyvault-basics` |
| Org secret scanning, rotation playbooks, leak IR | `secrets-management-hygiene` |
| Azure Blob public access / SAS | `azure-blob-misconfig` |
| NSG / path to private endpoints | `azure-nsg-review` |
| App/IaC module quality and tests | `code-quality-standards` |

## System Vs User-Assigned

| Type | Lifecycle | Best for |
| --- | --- | --- |
| **System-assigned** | Tied to resource; deleted with it | Single app; simple ownership |
| **User-assigned** | Standalone; attach to many hosts | Shared identity, blue/green, pre-RBAC |

Prefer user-assigned when multiple resources share one principal or identity must
outlive a swap; system-assigned for one-resource, smaller blast radius. Do not
attach unused identities.

## Workflow

### 1. Inventory compute and secret surfaces

Record subscription, RGs, env, authorization. List workloads that should use MI.
Flag App Settings named `*SECRET*`, `*KEY*`, `ConnectionString`,
`AZURE_CLIENT_SECRET` â€?**names only**. Incomplete estate â†?`recon-and-methodology`.

```bash
# Owned subscription only
az webapp identity show -g "$RG" -n "$APP"
az functionapp identity show -g "$RG" -n "$FUNC"
az vm identity show -g "$RG" -n "$VM"
az identity list -g "$RG" -o table
```

### 2. Enable the right identity type

Enable system-assigned **or** create/attach user-assigned. Capture **principalId**
for RBAC. AKS: prefer workload identity / federated credentials over long-lived
pod secrets.

```bash
az webapp identity assign -g "$RG" -n "$APP"
az identity create -g "$RG" -n "$UAI"
az webapp identity assign -g "$RG" -n "$APP" \
  --identities "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$UAI"
```

### 3. Assign least-privilege RBAC (not App Settings secrets)

Assign data-plane roles on the **target resource scope** to the MI principalId â€?e.g. `Key Vault Secrets User`, container-scoped `Storage Blob Data Contributor`,
`AcrPull` â€?not subscription Owner/Contributor for runtime. Vault model/network/
purge â†?**`azure-keyvault-basics`**.

```bash
az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" \
  --scope "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.KeyVault/vaults/$VAULT"
az role assignment list --assignee "$PRINCIPAL_ID" -o table
```

### 4. IMDS token path and SDK usage

Tokens via **IMDS** (`169.254.169.254`, `Metadata: true`) or App Service MSI
(`IDENTITY_ENDPOINT` / `IDENTITY_HEADER`). Use official SDKs
(`DefaultAzureCredential` / `ManagedIdentityCredential`). Prefer identity-based
clients over embedded keys. Untrusted code reaching IMDS â†?`cloud-metadata-ssrf-defenses`.

```bash
# Owned Azure VM â€?do not log the token
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net"
```

### 5. Remove secrets and verify

Confirm MI â†?Key Vault references/SDK or identity-backed Azure clients. Remove
client secrets and account keys from App Settings after cutover; rotate anything
previously exposed â†?**`secrets-management-hygiene`**. Re-test (401/403 = RBAC
vs network). Document residual third-party secrets with owner + review date.
Ship under `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| System/user MI, IMDS, MI RBAC, kill App Settings secrets | **This skill** | â€?|
| Key Vault network, soft-delete, purge, access model | `azure-keyvault-basics` | this skill for MI wiring |
| Secret leak IR, git/.env, org rotation | `secrets-management-hygiene` | this skill to drop standing secrets |
| Blob public / SAS; SSRF to IMDS | `azure-blob-misconfig` / `cloud-metadata-ssrf-defenses` | this skill |
| Bicep/TF modules, credential code | `code-quality-standards` | this skill for identity intent |

**Hand-offs:** `azure-keyvault-basics` (vault controls after MI is principal);
`secrets-management-hygiene` (inventory/rotate remaining secrets, leak IR);
`code-quality-standards` (apps/IaC that assign MI).

## Output Checklist

- [ ] Authorization and subscription/RG scope recorded (owned Azure only)
- [ ] Workloads inventoried; system- vs user-assigned choice justified; principalId captured
- [ ] RBAC least privilege on resource scopes (no unjustified Owner/Contributor)
- [ ] Key Vault consumers use MI; vault controls via `azure-keyvault-basics`
- [ ] App Settings free of secrets where MI applies; exposed secrets rotated via
      `secrets-management-hygiene`
- [ ] IMDS/SDK path documented; residual third-party secrets owned with review date
- [ ] IaC/app changes meet `code-quality-standards`; no live tokens in evidence
- [ ] No foreign-tenant probing or unapproved prod privilege elevation

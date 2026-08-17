---
name: external-secrets-operator
description: >
  External Secrets Operator (ESO) for Kubernetes: SecretStore and
  ClusterSecretStore design, ExternalSecret sync, and provider IAM for AWS
  Secrets Manager, HashiCorp Vault, and GCP Secret Manager. Use when wiring or
  reviewing ESO CRDs, refresh intervals, dataFrom/extract mappings, IRSA/Workload
  Identity, or Vault Kubernetes auth for cluster secret sync — not for Vault
  Agent Injector sidecars (hand off vault-agent-injection).
---

# External Secrets Operator (ESO)

Sync secrets from external providers into Kubernetes `Secret` objects via
**SecretStore** / **ClusterSecretStore** and **ExternalSecret**. Prefer ESO when
apps consume standard K8s Secrets and the source of truth is AWS SM, Vault,
GCPSM, or similar. Owned/authorized clusters only.

## Scope And Authorization

- **In scope:** org-owned or ROE clusters; GitOps manifests; staging/lab;
  read-only inventory of stores, ExternalSecrets, and provider roles.
- **Out of scope:** using synced values outside engagement; broadening prod
  store credentials to “debug”; unapproved provider dumps.
- Prefer static CR review and non-prod sync first; gate live provider reads;
  never paste live secret values into tickets or chat.
- Org leak IR → `secrets-management-hygiene`. Live secret abuse →
  `kubernetes-pentesting` (authorized). Vault inject → `vault-agent-injection`.

## When To Use

- Designing or reviewing **ESO** install, CRDs, and controller health
- **SecretStore** (namespaced) vs **ClusterSecretStore** (cluster-wide)
- **ExternalSecret** `data` / `dataFrom` / `extract` / `template` mappings
- Sync health: Ready/Synced, refresh interval, creationPolicy, deletionPolicy
- Provider IAM: **AWS SM** (IRSA), **Vault** (K8s auth), **GCPSM** (Workload Identity)
- Replacing committed Secret manifests or plain Helm values with remote refs
- Keywords: ESO, ExternalSecret, SecretStore, ClusterSecretStore,
  external-secrets.io, AWS SM sync, GCPSM Kubernetes, Vault provider ESO

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Vault Agent Injector / agent-inject annotations | `vault-agent-injection` |
| Org secret inventory, .env, leak IR, rotation process | `secrets-management-hygiene` |
| AWS IAM beyond ESO SM role | `aws-iam-least-privilege` |
| GCP IAM estate beyond SM + WI for ESO | `gcp-iam-basics` |
| Live cluster secret/RBAC assessment (lab) | `kubernetes-pentesting` |
| Helm values / `--set` packaging leaks | `helm-chart-security` |
| Manifests, controllers, tests quality | `code-quality-standards` |

**ESO vs Vault Agent:** ESO writes K8s Secrets (API/etcd visibility). Agent
injection renders files in-pod without necessarily creating Secret objects.
One delivery pattern per workload class — do not double-sync the same path.

## Workflow

### 1. Inventory and delivery model

1. List consumers (Deploy/STS/Job), env vs volume, namespaces, data class.
2. Map each secret to provider path/ARN/name, env, owner (no values).
3. Confirm ESO version, CRDs, webhook health; choose ESO vs CSI vs
   `vault-agent-injection` for this workload class.

### 2. SecretStore vs ClusterSecretStore

| Kind | Scope | Prefer when |
| --- | --- | --- |
| **SecretStore** | One namespace | App teams own auth; least blast radius |
| **ClusterSecretStore** | Cluster | Platform providers with strict who-may-reference RBAC |

Flag ClusterSecretStores usable by any namespace with over-broad provider IAM.
Prefer IRSA / Workload Identity / Vault K8s auth over static keys in the store.
Any store auth Secret must be RBAC-tight and never committed to Git.

### 3. ExternalSecret mapping and sync

1. `secretStoreRef` → correct kind/name; fail closed if missing.
2. Prefer explicit `data` key→remoteRef maps; use `dataFrom`/`extract` only when
   full JSON blobs are intentional.
3. Set `refreshInterval` for rotation SLAs without API thrash; dual-run keys
   during provider version cutover.
4. Align `creationPolicy` / `deletionPolicy` with GitOps ownership; avoid orphan
   prod Secrets or surprise deletes. Keep templates minimal (no live values).
5. Alert on prolonged non-Ready / non-Synced status.

```bash
# Owned/lab — metadata only
kubectl get secretstore,clustersecretstore,externalsecret -A
kubectl describe externalsecret <name> -n <ns>
kubectl get es <name> -n <ns> -o jsonpath='{.status.conditions}{"\n"}'
```

### 4. Provider IAM (least privilege)

| Provider | Auth preference | Permission sketch |
| --- | --- | --- |
| **AWS SM** | IRSA / EKS Pod Identity on ESO SA | `GetSecretValue` (+ `DescribeSecret`) on named ARNs |
| **GCPSM** | GKE Workload Identity | `secretmanager.versions.access` on specific secrets |
| **Vault** | Kubernetes auth bound to ESO SA/ns | Read specific paths; short TTL; no root |

No `Resource: "*"` on prod store roles; separate stage/prod paths. Deep IAM →
`aws-iam-least-privilege` / `gcp-iam-basics`. Vault inject → `vault-agent-injection`.

### 5. Hardening and handoff

- RBAC: who can create ExternalSecret / reference ClusterSecretStore.
- NetworkPolicy: controller → provider endpoints only.
- Drop plaintext Secret YAML / Helm `--set` once ESO owns keys
  (`helm-chart-security`, `secrets-management-hygiene`).
- On leak: rotate at **provider**, force refresh / roll pods; org IR via
  `secrets-management-hygiene`. Apply `code-quality-standards` to CRDs/charts.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ESO CRDs, stores, ExternalSecret sync, provider wiring | **This skill** | — |
| Vault Agent Injector / agent-inject | `vault-agent-injection` | this if comparing models |
| Org secret lifecycle, scanning, leak IR | `secrets-management-hygiene` | this for K8s sync path |
| AWS IAM wildcards / trust | `aws-iam-least-privilege` | this for SM ARNs used by ESO |
| GCP IAM beyond SM + WI | `gcp-iam-basics` | this for GCPSM mapping |
| Live cluster secret/RBAC assessment | `kubernetes-pentesting` | this for ESO root cause |
| Helm chart/values packaging | `helm-chart-security` | this for ExternalSecret templates |
| Controllers, charts, CI, tests | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for ESO; switch for Vault inject, org secret process, or cloud IAM estate review.

## Output Checklist

- [ ] Authorization recorded (owned/lab/ROE cluster + provider accounts)
- [ ] Workloads mapped to provider refs/owners/envs (no secret values)
- [ ] Delivery model: ESO vs CSI vs `vault-agent-injection` (no dual-sync)
- [ ] SecretStore vs ClusterSecretStore justified; cluster scope least privilege
- [ ] ExternalSecret maps explicit; refresh/deletion policies set; Ready/Synced
- [ ] Provider auth: IRSA / WI / Vault K8s auth preferred over static keys
- [ ] Provider IAM scoped to named secrets/paths; stage/prod separation
- [ ] Store auth Secrets not in Git; RBAC on who can create ExternalSecret
- [ ] Rotation dual-run then refresh; leak → rotate-first (`secrets-management-hygiene`)
- [ ] Evidence redacted; code/charts use `code-quality-standards`; exceptions owned
- [ ] Routed: inject → `vault-agent-injection`; IAM → AWS/GCP; live → `kubernetes-pentesting`

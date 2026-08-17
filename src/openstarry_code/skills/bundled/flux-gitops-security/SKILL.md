---
name: flux-gitops-security
description: >
  Flux GitOps security for owned/authorized clusters: source trust (Git/OCI),
  multi-tenant path and namespace isolation, controller and impersonation RBAC,
  secrets decryption (SOPS/age/ESO), image automation and admission pins, and
  notification webhook hygiene. Use when hardening or reviewing Flux v2 bootstrap,
  GitRepository/OCIRepository/HelmRepository, Kustomization/HelmRelease,
  flux-system ServiceAccounts, decrypt keys, ImagePolicy/ImageUpdateAutomation,
  or GitOps repo branch protection before or after continuous reconcile.
---

# Flux GitOps Security

Harden **Flux CD (v2)** so the cluster reconciles only trusted sources, with least
privilege controllers, no plaintext secrets in Git, and fail-closed path/tenant
boundaries. Defensive/authorized only. Runtime → `kubernetes-pentesting`; secrets →
`secrets-management-hygiene`; Helm → `helm-chart-security`; images → `container-image-signing`.

## When To Use

- Designing or reviewing **Flux bootstrap**, `flux-system`, multi-cluster tenants
- **GitRepository** / **OCIRepository** / **HelmRepository** URL, ref, auth, verify
- **Kustomization** / **HelmRelease** path allowlists, `serviceAccountName`, decrypt
- Secrets in GitOps: **SOPS**/age/KMS, SealedSecrets, or ESO-owned keys
- **ImageRepository** / **ImagePolicy** / **ImageUpdateAutomation** write-back risk
- **Provider** / **Alert** / **Receiver** webhooks and notification credentials
- Keywords: Flux security, GitOps reconcile, flux-system RBAC, Kustomization path,
  OCI source verify, SOPS decrypt, image automation, Flux multi-tenancy

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Live cluster RBAC, secret dump, etcd/kubelet (lab) | `kubernetes-pentesting` |
| Helm values/`--set` packaging only | `helm-chart-security` |
| ESO SecretStore / ExternalSecret wiring | `external-secrets-operator` |
| Cosign/Sigstore image sign + admission | `container-image-signing` |
| Org vault/rotation/leak IR | `secrets-management-hygiene` |
| Git branch protection / CODEOWNERS gates | `branch-protection-rules` |
| Manifest/controller/CI quality | `code-quality-standards` |

## Workflow

### 1. Inventory trust roots

List clusters/envs, bootstrap, controllers, GitOps repos; who can merge to watched
paths and who can create Flux CRs; sources, decrypt secrets, image write-back, and
Receivers. Prefer static CR review before live change.

### 2. Source trust (Git / OCI / Helm)

| Control | Expectation |
| --- | --- |
| Ref pin | Branch or immutable tag/SHA; avoid unbounded refs where policy forbids |
| Auth | Deploy key / app / OIDC **read-only** on app repos; separate write for automation |
| OCI/Helm | HTTPS or signed/mirrored registries; pin chart/image digests per policy |
| Verify | Prefer source-controller signature verify when org requires it |
| Public Git | No secrets in tree; treat as hostile supply chain |

Flag any-branch sources, unauthenticated OCI, or world-readable deploy keys.

### 3. Multi-tenancy and path isolation

Tenant namespaces with restricted impersonation SA (not shared cluster-admin).
Tight `spec.path` / chart roots; no `../` into other tenants; fixed
`spec.targetNamespace`. Git layout: `tenants/<name>/` + CODEOWNERS; pair with
`branch-protection-rules`.

### 4. Controller and impersonation RBAC

Audit `flux-system` and tenant SA bindings. Prefer **impersonation**
(`serviceAccountName` on Kustomization/HelmRelease) under a **namespace-scoped** SA.
Controllers: only verbs needed for CRDs + apply under impersonation. NetworkPolicy:
controllers → Git/OCI/providers only when isolation is required.

### 5. Secrets in GitOps

| Pattern | Prefer |
| --- | --- |
| Plain Secret YAML in Git | **Never** for live credentials |
| SOPS/age/KMS decryptRef | Flux decrypt; keys as K8s Secrets, RBAC-tight |
| SealedSecrets / ESO | Seal or ExternalSecret → `external-secrets-operator` |
| Helm values secrets | No committed plaintext → `helm-chart-security` |

On leak: rotate first (`secrets-management-hygiene`), purge history, re-encrypt.
Never paste decrypt keys or webhook tokens into tickets.

### 6. Image automation, notifications, operate

- ImageUpdateAutomation: least-privilege Git **write**; protected branch; PR when
  policy forbids direct prod commits.
- ImagePolicy + `container-image-signing` admission so unsigned digests never apply.
- Alert/Provider/Receiver: rotated secrets; authenticated webhooks; no secret
  payloads in notification bodies.
- Gate suspend / force-reconcile on prod with audit. Alert on not Ready and
  unexpected revision jumps. GitOps CI: secret scan, policy lint, dry-run build.
- Apply `code-quality-standards` to overlays, patches, and bootstrap scripts.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Flux sources, tenants, RBAC, decrypt, automation, webhooks | **This skill** | — |
| Live cluster RBAC/secrets attack surface | `kubernetes-pentesting` | this for GitOps root cause |
| Helm chart/values packaging | `helm-chart-security` | this for HelmRelease |
| ESO sync CRDs | `external-secrets-operator` | this for GitOps ownership |
| Image Cosign/admission | `container-image-signing` | this for Image* CRs |
| Vault/rotation/leak IR | `secrets-management-hygiene` | this for Git decrypt paths |
| Protected branch / CODEOWNERS | `branch-protection-rules` | this for watched paths |
| Controllers, overlays, CI scripts | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for Flux CD security; switch for live exploitation, org secret process, or pure Helm packaging.

## Output Checklist

- [ ] Authorization recorded (owned/lab/ROE cluster + GitOps repos)
- [ ] Controllers, sources, tenants, decrypt keys, automation, Receivers inventoried
- [ ] Sources authenticated, ref-constrained; OCI/Helm verify/pin per policy
- [ ] Paths/targetNamespace isolated; no cross-tenant escape
- [ ] Impersonation SA least privilege; no casual cluster-admin for app tenants
- [ ] No plaintext secrets in Git; SOPS/ESO/sealed; keys RBAC-tight
- [ ] Image automation write-back least privilege; signing/admission aligned
- [ ] Notification webhooks authenticated/rotated; no secret leakage in alerts
- [ ] GitOps branch protection + CODEOWNERS on watched paths
- [ ] Findings cite CR names/paths/revisions; residuals owned with expiry
- [ ] Routed: runtime → `kubernetes-pentesting`; Helm → `helm-chart-security`; ESO →
      `external-secrets-operator`; images → `container-image-signing`; secrets →
      `secrets-management-hygiene`; branches → `branch-protection-rules`; code → CQS

## Scope And Authorization

- **In scope:** Flux installs, GitOps repos, and CRs you own or are contracted to
  review; staging/lab; read-only `flux get` / `kubectl get` under ROE.
- **Out of scope:** Pointing prod Flux at untrusted forks “to test impact”; using
  found deploy keys or decrypt material outside scope; unapproved suspend/delete
  of prod reconciliations.
- Prefer **static manifests** and dry-run builds before live reconcile changes.
- Treat Git history, SOPS keys, deploy keys, and webhook secrets as **sensitive**;
  redact in reports. Do not infer authorization from a lab-like name alone.

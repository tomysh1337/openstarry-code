---
name: sealed-secrets-patterns
description: >
  Bitnami SealedSecrets and kubeseal for GitOps-friendly secrets on owned clusters:
  seal plaintext Secrets into SealedSecret CRs, choose scope (strict/namespace-wide/
  cluster-wide), manage controller keys and rotation, and avoid decrypt-side misuse.
  Use when committing encrypted secrets to git, reviewing sealed-secrets controller
  install, fixing unseal failures after rename/namespace move, or rotating sealing
  keys — not for raw K8s Secret RBAC/etcd hygiene (hand off kubernetes-secrets-handling).
---

# Sealed Secrets Patterns (Bitnami / kubeseal)

Produce and operate **SealedSecret** objects so credentials can live in Git as
**asymmetric ciphertext** that only the in-cluster controller decrypts into native
`Secret`s. Defensive GitOps for owned, staging, lab, or ROE clusters.

## Scope And Authorization

- **In scope:** org-owned clusters and GitOps repos; kubeseal/controller you
  administer; sealing CI on trusted runners; lab key-rotation drills.
- **Out of scope:** sealing for clusters you do not control; extracting private
  sealing keys from foreign clusters; abusing recovered plaintext outside scope.
- Keep **plaintext Secrets and private sealing keys** out of tickets, chat, and
  CI logs. Store private keys as break-glass (`secrets-management-hygiene`).
- Prefer dry-run apply and non-prod unseal checks before production key changes.
- Native Secret RBAC, etcd encryption, mount vs env → `kubernetes-secrets-handling`.

## When To Use

- Need **git-safe** secret manifests (Argo CD / Flux / kubectl apply from VCS)
- Installing or reviewing **Bitnami sealed-secrets** controller + `kubeseal`
- Choosing **scope**: strict vs namespace-wide vs cluster-wide
- Unseal failures after rename, namespace move, or wrong cluster public key
- **Key rotation**, backup/restore of sealing keys, multi-cluster key strategy
- Helm/GitOps paths that should seal instead of committing plaintext Secrets

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Base64 myth, etcd encrypt, Secret RBAC, mount vs env | `kubernetes-secrets-handling` |
| Org vault/SM rotation, .env, leak IR | `secrets-management-hygiene` |
| External Secrets Operator / cloud SM sync | `external-secrets-operator` |
| Helm packaging, `--set` leaks | `helm-chart-security` |
| Live cluster attack surface (lab/ROE) | `kubernetes-pentesting` |
| Controllers, CI scripts, admission tests | `code-quality-standards` |

## Workflow

### 1. Confirm controller and public key

1. Verify controller Deployment/CRDs on the target cluster.
2. Fetch the **sealing certificate** (public) for offline seal:
   `kubeseal --fetch-cert > pub-sealed-secrets.pem` (authorized only).
3. Map each GitOps env to its cert — seal for A does not unseal on B unless keys
   were deliberately shared.
4. Who can read the **private** sealing key Secret is tier-0 access.

### 2. Seal with explicit scope

Scope is bound into ciphertext. Wrong scope → unseal failure until re-seal.

| Scope | Binding | Use when |
| --- | --- | --- |
| **strict** (default) | name + namespace | Single named Secret; safest default |
| **namespace-wide** | namespace only | Same ns, rename allowed |
| **cluster-wide** | unbound | Rare bootstrap; highest blast radius |

```bash
kubectl create secret generic app-db --dry-run=client \
  --from-literal=password='REDACTED' -o yaml -n app > /tmp/secret.yaml
kubeseal --format yaml --cert pub-sealed-secrets.pem \
  --scope strict < /tmp/secret.yaml > sealed-app-db.yaml
# delete /tmp/secret.yaml after seal — never commit it
```

Prefer **strict**. Do not default to cluster-wide for convenience.

### 3. GitOps layout

1. Commit **only** `SealedSecret` YAML (samples use placeholders).
2. Generate plaintext out-of-band (local, vault, short-lived CI) — not beside sealed files in git.
3. For **strict**, name/namespace must match the intended Secret.
4. After apply, controller creates the native `Secret`; injection hygiene →
   `kubernetes-secrets-handling`.
5. Multi-env: re-seal per cluster cert; never copy sealed blobs across clusters blindly.

### 4. Key rotation and recovery

1. **Backup** controller private keys before upgrade/DR; vault/offline, not the app Git repo.
2. Rotation: new key → re-seal or dual-key window per controller docs → canary unseal → retire old.
3. Lost private key without backup ⇒ existing SealedSecrets unrecoverable; re-seal from source of truth.
4. Key exposure: rotate sealing key, re-seal all, rotate app secrets (`secrets-management-hygiene`), audit access.
5. Document owner, backup location, and re-seal RTO.

### 5. Failure triage and verify

| Symptom | Typical cause |
| --- | --- |
| Secret never appears | Controller down; CRD missing |
| SealedSecret error events | Scope mismatch; wrong cert; strict rename |
| Stage works, prod fails | Sealed with stage cert |

1. Apply in non-prod; confirm Secret **keys** exist (not values in reports).
2. Roll a consumer; confirm app starts with no plaintext in git.
3. Wrong name/ns under strict must fail; private key not in Git; tight RBAC on key Secret.
4. Chart/CI changes: `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SealedSecrets, kubeseal, scope, sealing-key rotation, GitOps sealed YAML | **This skill** | — |
| Native Secret RBAC, etcd encrypt, base64, mount vs env | `kubernetes-secrets-handling` | this skill when source is sealed |
| Org vault, app secret rotation, leak IR | `secrets-management-hygiene` | this skill for re-seal |
| ESO / external store sync | `external-secrets-operator` | hygiene + secrets-handling |
| Helm values / chart secret packaging | `helm-chart-security` | this skill for seal step |
| Authorized cluster pentest | `kubernetes-pentesting` | secrets-handling |
| Scripts, controllers, CI quality | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for seal/unseal and controller keys. Hand native API
Secret posture to `kubernetes-secrets-handling` once objects exist.

## Output Checklist

- [ ] Authorization recorded; plaintext and private keys redacted
- [ ] Controller + public cert source documented per target cluster
- [ ] Scope deliberate (prefer **strict**); cluster-wide justified if used
- [ ] Only SealedSecret ciphertext committed — no plaintext Secret YAML
- [ ] Per-cluster re-seal; no blind cross-cluster sealed blob copies
- [ ] Private key backup, owner, and rotation procedure documented
- [ ] Non-prod unseal verified; strict wrong-name/ns rejection checked
- [ ] Consumer injection → `kubernetes-secrets-handling`
- [ ] App secret rotation/leak IR → `secrets-management-hygiene`
- [ ] Code/CI/chart changes → `code-quality-standards`
- [ ] Residuals (shared keys, multi-cluster certs) have owner + expiry

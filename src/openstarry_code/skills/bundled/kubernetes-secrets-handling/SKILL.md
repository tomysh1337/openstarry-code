---
name: kubernetes-secrets-handling
description: >
  Harden Kubernetes Secrets handling on owned clusters: base64 is not encryption,
  etcd encryption at rest, RBAC least privilege, mount vs env injection, and
  safe inventory without dumping Secret data into pods or logs. Use when
  reviewing Secret objects, ServiceAccount get/list/watch on secrets,
  EncryptionConfiguration, volume mounts vs envFrom, GitOps plaintext Secret
  manifests, or hand-off to External Secrets / Sealed Secrets — owned, lab, or
  ROE clusters only.
---

# Kubernetes Secrets Handling

Secure how **Kubernetes Secrets** are stored, authorized, injected, and reviewed.
Native Secrets are **base64-encoded API objects**, not encryption. Owned, staging,
lab, or written-ROE clusters only.

## Scope And Authorization

- **In scope:** owned/lab/ROE clusters; GitOps/Helm review; RBAC and
  `EncryptionConfiguration`; authorized metadata inventory.
- **Out of scope:** unauthorized access; dumping third-party Secrets; stolen
  kubeconfigs; mass-exporting values into tickets or chat.
- Prefer **metadata-only** inventory before reading `.data`. Never paste live
  secret values into reports or prompts.
- On production exposure: contain → rotate → audit
  (`secrets-management-hygiene`) before broad writeups. Redact tokens and PII.

## When To Use

- Teams treat base64 `.data` / `kubectl create secret` as “encrypted”
- **etcd encryption at rest** status and KEK/KMS protection unclear
- RBAC grants broad `get`/`list`/`watch` on `secrets`
- Choosing **volume mount** vs **env** / `envFrom`; avoiding env/`printenv` dumps
- Plaintext Secret YAML in Git; SealedSecrets vs ExternalSecrets decision
- Chinese/English: K8s Secret 明文, base64 不是加密, etcd 加密, Secret 挂载

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Vault/rotation/.env hygiene | `secrets-management-hygiene` |
| Sealed Secrets controller / sealed YAML | `sealed-secrets-patterns` |
| External Secrets Operator / SecretStore | `external-secrets-operator` |
| Full cluster RBAC/API assessment (lab) | `kubernetes-pentesting` |
| PSS/PSA / securityContext | `kubernetes-pod-security` |
| NetworkPolicy | `kubernetes-network-policy` |
| Chart/controller implementation quality | `code-quality-standards` |

## Workflow

### 1. Inventory without leaking values

1. Record cluster, namespaces, GitOps paths, types (`Opaque`, TLS, dockerconfig, SA).
2. List name/type/age/consumers — **not** decoded data.
3. Map readers: Roles/bindings; `auth can-i`; SA token automount.

```bash
kubectl get secrets -n <ns> -o custom-columns=NAME:.metadata.name,TYPE:.type,AGE:.metadata.creationTimestamp
kubectl auth can-i get secrets --as=system:serviceaccount:<ns>:<sa> -n <ns>
```

### 2. Correct the base64 myth

| Fact | Implication |
| --- | --- |
| `.data` is **base64**, not encryption | API read access = plaintext |
| etcd stores Secret objects | No encrypt-at-rest → disk/backup readers see values |
| `stringData` is convenience only | Still base64 in etcd after apply |
| Secret YAML in Git | Treat as credential leak |

Flag docs/charts that call base64 “encrypted.”

### 3. etcd encryption at rest

1. Confirm `EncryptionConfiguration` (or managed equivalent) covers `secrets`.
2. Prefer **KMS** KEK over static aescbc keys on disk; plan re-encrypt after rotation.
3. Backups inherit posture; managed control planes still need API RBAC as boundary.

### 4. RBAC least privilege

1. Default-deny cluster-wide `secrets` get/list/watch for humans and apps.
2. Prefer CSI/projected injection so runtime SAs never need `get secrets`.
3. Split deploy bots (create/update) from runtime SAs; audit admin-like bindings.
4. Disable unnecessary SA automount; short-lived tokens where possible.

### 5. Mount vs env (avoid dumps)

| Pattern | Prefer | Risk |
| --- | --- | --- |
| **Volume / projected mount** | Default | File perms; no full env dump |
| **Single env var** | Only if required | `/proc`, `kubectl exec env`, crash logs |
| **`envFrom: secretRef`** | Rare | Imports **all** keys into env |
| **Image/env in manifest** | Never (prod) | Layers, git, pod YAML leak |

Prefer mount + read at startup. Never log env/mounts; avoid debug sidecars with
broad Secret mounts; do not `cat` secrets into shared terminals.

### 6. GitOps hand-off and verify

1. No plaintext Secrets in VCS; placeholders in samples only.
2. Sealed Secrets → `sealed-secrets-patterns`. ESO/vault sync →
   `external-secrets-operator`. Lifecycle/rotation/IR →
   `secrets-management-hygiene`.
3. After leak: rotate source of truth → roll pods → revoke old → fix RBAC/git.
4. Report RBAC overreach, missing etcd encryption, envFrom sprawl, git Secrets,
   base64-as-crypto claims, over-automount. Verify with metadata — not value dumps.

## Routing table

| Situation | Primary | Helper |
| --- | --- | --- |
| K8s Secrets, base64 myth, etcd encrypt, mount vs env, RBAC on secrets | **This skill** | — |
| Vault/SM lifecycle, rotation, .env, leak IR | `secrets-management-hygiene` | this skill (in-cluster) |
| Sealed Secrets / sealed YAML | `sealed-secrets-patterns` | this skill (RBAC/mount) |
| ESO / SecretStore / ExternalSecret | `external-secrets-operator` | this skill + hygiene |
| Broad cluster pentest (lab/ROE) | `kubernetes-pentesting` | this skill (Secret findings) |
| Pod privileged/hostPath/PSA | `kubernetes-pod-security` | — |
| NetworkPolicy | `kubernetes-network-policy` | — |
| Charts, admission tests, app loaders | `code-quality-standards` | this skill (intent) |

## Output Checklist

- [ ] Scope/authorization recorded (owned/lab/ROE only)
- [ ] Inventory by name/type/consumer — **no plaintext values in reports**
- [ ] Base64 ≠ encryption communicated to stakeholders
- [ ] etcd / control-plane encryption-at-rest status recorded
- [ ] RBAC least privilege on secrets; SA automount reviewed
- [ ] Prefer mounts; env/`envFrom` justified and dump-resistant
- [ ] No plaintext Secrets in git; samples use placeholders
- [ ] SealedSecrets → `sealed-secrets-patterns` when chosen
- [ ] ExternalSecrets → `external-secrets-operator` when chosen
- [ ] Rotation/leak response → `secrets-management-hygiene`
- [ ] Broader attack surface → `kubernetes-pentesting` if in scope
- [ ] Code/chart changes follow `code-quality-standards`
- [ ] Residual exceptions listed with owner and expiry

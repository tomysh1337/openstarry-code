---
name: kubernetes-etcd-encryption
description: >
  Kubernetes etcd encryption at rest for owned or authorized clusters: API server
  EncryptionConfiguration, resource selection (Secrets and more), aescbc/aesgcm/
  secretbox/kms providers, identity fallback, key rotation, and re-encrypt
  verification. Use when enabling or reviewing --encryption-provider-config,
  KMS v1/v2 plugins, plaintext etcd Secrets, provider order, or secret re-encryption
  after key change — not for live etcd dump abuse outside scope.
---

# Kubernetes etcd Encryption at Rest

Harden **Kubernetes API objects stored in etcd** so Secrets (and selected
resources) are ciphertext at rest via kube-apiserver
**EncryptionConfiguration**. Owned, lab, or explicitly authorized clusters only.
Encryption at rest does **not** replace RBAC, TLS, network isolation, or secret
lifecycle; it limits disk/backup exposure of etcd data.

## When To Use

- Enabling or auditing **encryption at rest** for Secrets (or other resources)
- Designing **EncryptionConfiguration**: providers, order, identity fallback
- Choosing **aescbc**, **aesgcm**, **secretbox**, or **kms** (KMS v1/v2)
- **Key rotation**: add new key/provider, re-encrypt, retire old material
- Verifying objects show `k8s:enc:` prefixes in etcd (authorized read path)
- Managed control planes (EKS/GKE/AKS) encryption API/console settings
- Mentions: `--encryption-provider-config`, EncryptionConfiguration, etcd
  encryption, KMS plugin, secretbox, identity provider, re-encrypt Secrets

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org secret inventory, rotation IR, .env leaks | `secrets-management-hygiene` |
| Live RBAC/secret dump/kubelet assessment (lab) | `kubernetes-pentesting` |
| ESO / external store sync into K8s Secrets | `external-secrets-operator` |
| Helm values / `--set` secret packaging | `helm-chart-security` |
| AWS CMK policy, ViaService, grants | `aws-kms-key-policy-basics` |
| Controllers, manifests, CI quality | `code-quality-standards` |

## Workflow

### 1. Scope, threat model, inventory

1. Record cluster, env, control-plane ownership (self-managed vs managed), ROE.
2. List resources for ciphertext: usually **`secrets`**; optionally others per policy.
3. Note etcd topology, backup location, who can read etcd data or snapshots.
4. Confirm apiserver `--encryption-provider-config` path. Prefer non-prod first.

### 2. Choose providers and write EncryptionConfiguration

| Provider | Role | Notes |
| --- | --- | --- |
| **kms** | Preferred at scale | External KMS; KMS v2 preferred where supported |
| **secretbox** | Strong local DEK | 32-byte key; good self-managed default |
| **aesgcm** / **aescbc** | Local AES | Prefer aesgcm over legacy aescbc when available |
| **identity** | Plaintext passthrough | Must be **last** if present; reads old plaintext |

Rules: **write** uses the first provider; **read** tries in order until decrypt
succeeds; keep prior keys until every object is re-encrypted; never leave only
`identity` for Secrets in prod.

```yaml
# Illustrative — paths and keys are environment-specific
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - kms:
          apiVersion: v2
          name: org-kms
          endpoint: unix:///var/run/kmsplugin/socket.sock
      - identity: {}
```

Store local key material outside etcd, file-permission tight
(`secrets-management-hygiene`). Cloud CMK policy → `aws-kms-key-policy-basics`.

### 3. Roll apiserver and re-encrypt

1. Deploy EncryptionConfiguration to all control-plane apiservers consistently.
2. Restart/reload apiservers; confirm healthy and config path accepted.
3. **Re-encrypt** existing objects (update/replace Secrets or approved rewrite)
   so they are written with the new first provider.
4. Untouched objects and old backups may still hold prior plaintext/ciphertext.

### 4. Verify and rotate

Authorized control-plane / etcd access only:

1. Sample Secret keys in etcd: expect `k8s:enc:kms:v2:`, `k8s:enc:secretbox:v1:`,
   etc. — **never paste secret values**.
2. Confirm API reads still work for apps and controllers.
3. **Rotation:** new provider/key at the **top** → re-encrypt all targets →
   remove retired keys only after verify and backup policy allows.
4. Protect config and KMS credentials; RBAC on Secrets remains mandatory.
5. Automation → `code-quality-standards`; app delivery →
   `external-secrets-operator` / `secrets-management-hygiene`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| etcd encryption at rest, EncryptionConfiguration, re-encrypt | **This skill** | — |
| Secret lifecycle, leak IR, rotation process | `secrets-management-hygiene` | this for at-rest CP |
| Live cluster RBAC / secret exposure assessment | `kubernetes-pentesting` | this for ciphertext posture |
| ESO sync / SecretStore design | `external-secrets-operator` | this after Secret exists |
| Helm values packaging secrets | `helm-chart-security` | this for storage layer |
| AWS KMS CMK policy for KMS plugin | `aws-kms-key-policy-basics` | this for EncryptionConfiguration |
| IaC / scripts / config quality | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for apiserver encryption-at-rest; hand off org secrets process, live pentest, ESO, and cloud KMS policy to the table above.

## Output Checklist

- [ ] Authorization and cluster/env recorded (owned/lab/ROE only)
- [ ] Target resources listed (typically secrets); backups in threat model
- [ ] EncryptionConfiguration on all apiservers; flag path confirmed
- [ ] Provider order: active write first; identity last if used
- [ ] KMS v2/local DEK documented; key material not in Git/etcd
- [ ] Existing objects re-encrypted after enable or key change
- [ ] etcd samples show expected `k8s:enc:…` prefixes (redacted metadata only)
- [ ] API read path validated; apps/controllers healthy post-roll
- [ ] Rotation plan: add key → re-encrypt → retire; backup retention considered
- [ ] RBAC/TLS/network not treated as replaced by encryption at rest
- [ ] Routed: secrets IR → `secrets-management-hygiene`; live → `kubernetes-pentesting`;
      ESO → `external-secrets-operator`; CMK → `aws-kms-key-policy-basics`; CQS on automation
- [ ] Exceptions owned with expiry; no live secret values in reports

## Scope And Authorization

- **In scope:** org-owned or contracted clusters; EncryptionConfiguration design;
  provider selection; controlled apiserver rolls; authorized re-encrypt; read-only
  etcd/API verification under ROE; managed-plane encryption settings you control.
- **Out of scope:** unapproved etcd extraction from third-party clusters; using
  recovered Secrets outside engagement; mass prod Secret rewrite without change
  control; weakening RBAC “because etcd is encrypted.”
- Prefer staging/lab. Gate etcd peer access, snapshots, and KMS admin. Redact
  Secret data, DEKs, KMS credentials, and kubeconfigs. Pair with least-privilege
  API access and secret hygiene for defense in depth.

---
name: helm-secrets-plugins
description: >
  Helm secrets plugins (helm-secrets + SOPS/vals backends) for encrypting chart
  values, decrypt-on-render install/upgrade, and CI-safe secret files. Use when
  installing or configuring helm-secrets, choosing SOPS vs vals, encrypting
  values.yaml, wiring age/PGP or cloud KMS keys, or stopping plaintext Helm
  values and --set secret leaks in GitOps pipelines.
---

# Helm Secrets Plugins

Use **helm-secrets** (and related Helm plugins) so chart values that hold
credentials stay **encrypted at rest in Git** and decrypt only on trusted
runners or local workstations during `template` / `install` / `upgrade`.
Defensive packaging for owned charts and authorized clusters—not a substitute
for in-cluster secret stores or live Secret RBAC.

## When To Use

- Installing or upgrading **helm-secrets** / related Helm plugins
- Encrypting `values*.yaml` (or secret fragments) with **SOPS** (age, PGP, KMS)
- Using **vals** (or similar) refs instead of embedding ciphertext in every file
- CI: decrypt-on-render without writing plaintext to artifacts or logs
- Migrating off committed plaintext values and `helm --set password=…`
- Diagnosing decrypt failures (wrong key, wrong backend, path filters)
- Keywords: helm-secrets, helm secrets plugin, SOPS values, vals helm,
  encrypted values.yaml, helm secrets decrypt, HELM_SECRETS_

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full chart SA/NetPol/privileged/provenance review | `helm-chart-security` |
| Bitnami SealedSecret / kubeseal GitOps CRs | `sealed-secrets-patterns` |
| External Secrets Operator / cloud SM sync | `external-secrets-operator` |
| Org vault rotation, leak IR, .env scanning | `secrets-management-hygiene` |
| Native Secret RBAC, etcd, mount vs env | `kubernetes-secrets-handling` |
| Live cluster secret/RBAC assessment (lab) | `kubernetes-pentesting` |
| Chart helpers, plugin wrappers, CI scripts quality | `code-quality-standards` |

**Plugin vs in-cluster:** helm-secrets protects **values before apply**. SealedSecrets
and ESO protect **cluster objects / remote sources**. One primary path per secret
class; do not encrypt the same key three ways without a clear owner.

## Workflow

### 1. Choose backend and install plugin

1. Confirm team model: **SOPS-encrypted files** vs **vals** remote refs at render.
2. Install from a **pinned** trusted release: `helm plugin install` / `update`.
3. Document backend (SOPS age/PGP/KMS rules or vals providers).
4. Private keys/KMS roles only on break-glass or CI—not in the chart repo.

### 2. Encrypt values layout

| Pattern | Prefer |
| --- | --- |
| Whole `values-secrets.yaml` encrypted | SOPS + helm-secrets on `-f` |
| Few keys in a larger values file | SOPS path/regex rules; keep non-secrets plain |
| Runtime fetch from Vault/SM | vals refs; least IAM on the runner |
| One-off local install | temp decrypt → install → wipe; never commit plain |

```bash
# Owned repo only — placeholders, no live secrets
helm secrets encrypt values-secrets.yaml
helm secrets edit values-secrets.yaml
helm secrets template rel ./chart -f values.yaml -f values-secrets.yaml
helm secrets upgrade -i rel ./chart -f values.yaml -f values-secrets.yaml
```

If live secrets were committed: **rotate first**, then purge
(`secrets-management-hygiene`).

### 3. CI and GitOps

1. Decrypt keys/KMS via runner identity (OIDC/IRSA over long-lived key files).
2. Prefer `helm secrets …` so decrypt stays in-process; avoid leftover plaintext.
3. Never log full values, `--debug` dumps, or decrypted YAML.
4. Argo/Flux: trusted render step **or** prefer ESO/SealedSecrets when the
   reconciler cannot open SOPS—do not invent opaque blobs it cannot decrypt.
5. Pin plugin + SOPS/vals versions in pipeline docs/locks.

### 4. Key lifecycle and triage

| Symptom | Typical cause |
| --- | --- |
| Decrypt fails on CI only | Missing age key / wrong KMS role / env |
| Works locally, fails teammate | Private key not in org secret store |
| Partial plaintext in git | SOPS rules missed nested keys |
| Upgrade applies empty secret | Wrong `-f` order or decrypt skipped |

Rotation: add recipient/KMS → re-encrypt → dual-run → retire old. Lost private
key without backup ⇒ re-encrypt from source of truth. Leak ⇒ rotate app secrets
and keys; scrub CI. Scripts/hooks → `code-quality-standards`.

### 5. Handoff

Chart SA/NetPol/provenance → `helm-chart-security`. Long-lived cluster sync
without runner decrypt → ESO/CSI or SealedSecrets. Consumer mounts/env →
`kubernetes-secrets-handling`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| helm-secrets, SOPS/vals values, decrypt-on-render CI | **This skill** | — |
| Chart templates, SA, NetPol, `--set` packaging | `helm-chart-security` | this for encrypted values |
| SealedSecret / kubeseal | `sealed-secrets-patterns` | this if comparing models |
| ESO SecretStore / ExternalSecret | `external-secrets-operator` | this for pre-apply encrypt |
| Org rotation, leak IR, scanning | `secrets-management-hygiene` | this for Helm file IR |
| Native Secret RBAC / etcd / mount vs env | `kubernetes-secrets-handling` | after apply |
| Live cluster secret assessment (authorized) | `kubernetes-pentesting` | this for plugin root cause |
| Scripts, charts, pipeline code | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for plugin encryption and decrypt-on-render; switch for chart posture, SealedSecrets/ESO, or org secret IR.

## Output Checklist

- [ ] Authorization clear; no foreign-cluster key extraction
- [ ] Backend (SOPS vs vals) and key/KMS ownership documented
- [ ] Plugin + SOPS/vals versions pinned; install source trusted
- [ ] Secret values encrypted or remote-ref’d; no plaintext in Git
- [ ] Encrypt rules cover nested secret keys
- [ ] CI decrypt via plugin; no decrypted artifacts/logs
- [ ] Key rotation, backup, re-encrypt RTO documented
- [ ] Leak: rotate-first then re-encrypt (`secrets-management-hygiene`)
- [ ] Chart residuals → `helm-chart-security`
- [ ] In-cluster path vs SealedSecrets/ESO justified
- [ ] Consumer hygiene → `kubernetes-secrets-handling`
- [ ] Code/CI → `code-quality-standards`; residuals owned with expiry

## Scope And Authorization

- **In scope:** charts, values, and pipelines you own or are contracted to
  harden; staging/lab; decrypt only on authorized workstations/runners.
- **Out of scope:** cracking encrypted values from foreign repos; abusing
  recovered plaintext outside ROE; unapproved prod upgrades with stolen keys.
- Prefer static `helm secrets template` / lint before live `upgrade`.
- Treat decrypted values, private keys, and KMS-capable CI roles as **tier-0**;
  redact from tickets, chat, and examples. Gate live provider dumps behind ROE.

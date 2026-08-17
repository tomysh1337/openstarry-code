---
name: pulumi-secrets-basics
description: >
  Pulumi secrets and encrypted config for owned/authorized stacks: pulumi config
  set --secret, secrets providers (passphrase vs cloud KMS), stack outputs, and
  Pulumi ESC. Use when Pulumi secrets, stack config encryption,
  PULUMI_CONFIG_PASSPHRASE, secretsprovider, sensitive outputs, ESC environments,
  or hardening org Pulumi CI.
---

# Pulumi Secrets Basics

Harden how **Pulumi** stores and injects secrets for stacks you own or are
authorized to review. Own **encrypted config, secrets providers, stack outputs,
and ESC wiring**. Org-wide vault/rotation/leak IR → `secrets-management-hygiene`.
Defensive and authorized only.

## When To Use

- Setting or reviewing secrets via `pulumi config set --secret` / `config.requireSecret`
- Choosing or migrating **passphrase** vs **cloud KMS** secrets providers
- Stack YAML lacks `secure:` blobs, shows plaintext secrets, or shares one passphrase
- **Stack outputs** may leak (`pulumi stack output`, CI logs, stack references)
- Adopting or reviewing **Pulumi ESC** environments, providers, and OIDC imports
- Mentions: Pulumi secrets, `secretsprovider`, `PULUMI_CONFIG_PASSPHRASE`, ESC,
  encrypted config, sensitive outputs

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org vault, .env, scanning, rotation, leak IR | `secrets-management-hygiene` |
| Terraform/OpenTofu state and tfvars | `terraform-security-basics` |
| CI structure beyond Pulumi secret steps | `ci-cd-pipeline-patterns` |
| Program/module code quality | `code-quality-standards` |
| Deep cloud KMS/IAM policy design | matching cloud IAM skill |

## Repo Config First

Repo and org Pulumi conventions **outrank** examples below.

1. **Backend:** Pulumi Cloud vs DIY (`s3://`, `azblob://`, `gs://`, local) and stack readers
2. **Secrets provider:** passphrase, `awskms://`, `azurekeyvault://`, `gcpkms://`, `hashivault://`
3. **Stack layout:** `Pulumi.yaml`, `Pulumi.<stack>.yaml`, project/stack naming, org
4. **ESC:** whether environments are SSOT; which stacks import via `environment:`
5. **Languages / CI:** config APIs in use; OIDC; where passphrase or provider creds live
6. **Policy:** secret scanning, required KMS on prod, output redaction rules

**Precedence:** Follow repo/org. Flag prod on shared passphrase, config without
`--secret`, or plaintext credential outputs.

## Workflow

### 1. Inventory stacks and providers

List projects/stacks, envs, backends, secrets providers, and who can `pulumi up` /
read config / export state. Scan `Pulumi.*.yaml` for unencrypted secret-shaped keys
(never paste live values). Map CI: passphrase, KMS, ESC auth, fork-PR isolation.

### 2. Write secrets only as encrypted config

| Action | Expectation |
| --- | --- |
| CLI | `pulumi config set --secret myapp:dbPassword` (avoid shell history when possible) |
| Code | `config.requireSecret` / `getSecret`; treat as secret `Output` |
| YAML | Ciphertext under `secure:`; no plaintext passwords in committed stack files |
| Batch | ESC or CI secret → `config set --secret`; not committed `.env` into config |

**Good:** `pulumi config set --secret --path 'data.apiKey' "$VALUE"` + secret API reads.

**Bad:** `pulumi config set dbPassword 'SuperSecret'` (plaintext); hard-coded keys in
program code; logging `config.get("dbPassword")`.

Plaintext commit or CI log leak → **rotate first** (`secrets-management-hygiene`).

### 3. Passphrase vs cloud KMS

| Provider | Use when | Risks / controls |
| --- | --- | --- |
| **Passphrase** | Solo labs, throwaway stacks | Shared team passphrase is one root secret; CI store only; never git |
| **AWS/Azure/GCP KMS** | Team/prod stacks | Prefer; least-privilege key IAM; separate keys per env when required |
| **Vault / other** | Org standardizes on Vault | Align paths/policies with `secrets-management-hygiene` |

Change provider only with documented re-encrypt / `pulumi stack change-secrets-provider`.
Prod: prefer **cloud KMS** (or org Vault) over long-lived shared passphrases. Protect
`PULUMI_CONFIG_PASSPHRASE` / `_FILE` like root secrets. DIY backends: encrypt state at
rest and restrict IAM — state may hold secret material.

### 4. Stack outputs and dependencies

Mark secret outputs (`pulumi.secret` / `Output.secret`). Never print them; avoid
`pulumi stack output --show-secrets` in CI. Stack references must keep secret typing.
Prefer cloud SM/Key Vault generation; export **ARNs/IDs**, not raw values. Redact
previews/tickets; treat stack export/backup as sensitive.

### 5. Pulumi ESC

Use ESC for shared secrets/config; import into stacks with least privilege. Prefer
OIDC/dynamic cloud logins over static keys. Separate environments per env/tenant
(no prod in dev). Audit editors; rotate credentials like vault entries
(`secrets-management-hygiene`). Avoid dual-sourcing the same secret in ESC and
ad-hoc stack config without an owner.

### 6. CI and verification

OIDC to Pulumi/cloud; mask secrets; no full-config debug dumps. Fail closed if
required secrets missing. Secret-scan repo and stack YAML; gate merges. Apply
`code-quality-standards` to programs that load config or create keys. After
provider/secret rotation, controlled preview/up in non-prod first.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Pulumi encrypted config, secrets provider, outputs, ESC | **This skill** | — |
| Org vault, rotation, git leak IR, scanning policy | `secrets-management-hygiene` | this for Pulumi paths |
| Terraform/tfstate secrets | `terraform-security-basics` | — |
| Pipeline stages, approvals, OIDC wiring | `ci-cd-pipeline-patterns` | this for Pulumi secret steps |
| Program structure, tests, error handling | `code-quality-standards` | **always** on code changes |

**Hand-off notes:** `secrets-management-hygiene` owns inventory, rotation, revocation,
and scanning; this skill owns Pulumi encryption/provider/ESC mechanics.
`ci-cd-pipeline-patterns` for job trust (no passphrase/KMS on fork PRs).
`code-quality-standards` for config loaders and outputs.
`terraform-security-basics` for sibling IaC only.

## Output Checklist

- [ ] Stacks, backends, secrets providers, apply identities inventoried (no values)
- [ ] Secrets via `--secret` / secret APIs; no plaintext secrets in stack YAML
- [ ] Prod prefers KMS/Vault; passphrase only with owned CI storage
- [ ] Provider change has re-encrypt plan; passphrase/KMS material never in git
- [ ] Secret outputs marked; no CI `--show-secrets` or logged plaintext
- [ ] Prefer ARNs/IDs over raw credentials; stack exports treated sensitive
- [ ] ESC env-separated; least-privilege editors; OIDC preferred over static keys
- [ ] DIY state backend encryption and IAM reviewed
- [ ] CI masks secrets; fork PRs cannot read prod config/passphrase
- [ ] Leaks: rotate-first via `secrets-management-hygiene`, then re-encrypt config
- [ ] Code changes use `code-quality-standards`; residuals owned with review date
- [ ] Reports redacted — no live secrets, passphrases, or full stack dumps

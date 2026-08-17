---
name: aws-kms-key-policy-basics
description: >
  AWS KMS customer managed key (CMK) hardening for owned accounts: key policies
  vs IAM, kms:ViaService, grants, key-admin least privilege, and encryption
  context. Use when reviewing CMK key policies, over-broad kms:*, missing
  ViaService conditions, grant sprawl, dual key administrators, or weak
  encryption-context enforcement — not for abusing third-party AWS accounts.
---

# AWS KMS Key Policy Basics

Harden **AWS KMS** CMKs so decrypt/encrypt and administration stay least-privilege.
**Org-owned or explicitly authorized AWS accounts only.** Prefer CMKs when you
need an explicit admin/usage split and conditions.

## Scope And Authorization

- **In scope:** Owned CMKs (incl. multi-Region); key policies, grants, aliases,
  rotation; CloudTrail KMS events; controlled policy/grant changes; related IAM.
- **Out of scope:** Foreign-account keys; third-party decrypt; disabling logging;
  mass `ScheduleKeyDeletion` on shared prod without approval.
- Prefer non-prod. Gate `PutKeyPolicy`, grant create/retire, key deletion. Redact
  ciphertext, grant tokens, sensitive principal maps.
- Secrets/rotation IR → `secrets-management-hygiene`. Lambda role KMS →
  `aws-lambda-least-privilege`. Account IAM → `aws-iam-least-privilege`.
  S3 SSE-KMS → pair `aws-s3-bucket-hardening`.

## When To Use

- Designing or reviewing **CMK key policies** (root enablement, admins, users)
- Confusion over **key policy vs IAM** (both layers; key policy is the gate)
- Service crypto (S3, EBS, Secrets Manager, SQS, SNS, RDS) without
  **`kms:ViaService`** / source conditions
- **Grant** sprawl or unconstrained `CreateGrant` on app roles
- Over-broad `kms:*` / `kms:Decrypt` on `*` in IAM or key policy
- Missing/inconsistent **encryption context** on Encrypt/Decrypt/GenerateDataKey
- Mentions: KMS key policy, CMK, `kms:ViaService`, grants, key administrators,
  encryption context, schedule key deletion

Do **not** use as primary for: secrets lifecycle → `secrets-management-hygiene`;
Lambda roles/env → `aws-lambda-least-privilege`; account IAM →
`aws-iam-least-privilege`; S3 BPA → `aws-s3-bucket-hardening`; Terraform →
`terraform-security-basics`; code quality → `code-quality-standards`.

## Workflow

### 1. Inventory and model (key policy vs IAM)

Record account, region(s), env, authorization. List CMKs, aliases, consumers.

| Layer | Role | Note |
| --- | --- | --- |
| **Key policy** | Ultimate allow on the key | Enable IAM via account-root **or** name principals |
| **IAM identity** | Further restricts IAM-path principals | Insufficient alone without key-policy allow |
| **Grants** | Delegated (often temporary) ops | Inventory/retire; grant-token service flows |

**Effective use** = key policy **and** (IAM path) IAM **and** grant/context
conditions. Denies win.

```bash
# Owned account only
aws sts get-caller-identity
aws kms list-aliases
aws kms describe-key --key-id alias/app-prod
aws kms get-key-policy --key-id KEY_ID --policy-name default --output text
aws kms list-grants --key-id KEY_ID
```

Output: alias, key id, admins, users, services — **no secret values**.

### 2. Split key admins from key users

| Role | Actions (typical) | Guardrails |
| --- | --- | --- |
| **Key admin** | `PutKeyPolicy`, `CreateGrant`, `ScheduleKeyDeletion`, enable/disable | Break-glass; SSO/MFA; never daily app role |
| **Key user** | `Encrypt`, `Decrypt`, `GenerateDataKey*`, `DescribeKey` | ARN-scoped; no policy mutation |
| **Audit** | `Describe*`, `GetKeyPolicy`, `List*` | No decrypt |

Flag app `kms:*`, permanent human decrypt on prod data keys, admin+data-plane on
one principal.

### 3. Shape the key policy

1. **Root enablement** so IAM can apply on this key.
2. **KeyAdmins** — named roles only; optional MFA/tag conditions.
3. **KeyUsers** — explicit roles; crypto actions only.
4. **Services** — service principal + **`kms:ViaService`** + `aws:SourceAccount`
   (resource ARNs when supported).
5. No `Principal:"*"` decrypt; no user-level `kms:*`.

```json
"Condition": {
  "StringEquals": {
    "kms:ViaService": "s3.eu-west-1.amazonaws.com",
    "aws:SourceAccount": "111122223333"
  }
}
```

### 4. Grants, encryption context, verify

Map grants (grantee, ops, constraints, retiring principal); retire unused.
Avoid `CreateGrant` on app roles unless required and constrained (e.g.
`kms:GrantIsForAWSResource`). Require stable **non-secret** context pairs
(resource ARN, app id, env) on encrypt and matching decrypt; condition with
`kms:EncryptionContext:`. Context is logged — never put secrets there.
Access Analyzer; CloudTrail `Decrypt`/`Encrypt`/`CreateGrant`/`PutKeyPolicy`;
canary non-prod. Exposed material → `secrets-management-hygiene`. Lambda
`kms:Decrypt`/env → `aws-lambda-least-privilege` for the role; **this skill**
for CMK policy/grants/context. IaC → `terraform-security-basics` +
`code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CMK key policy, ViaService, grants, encryption context, key-admin split | **This skill** | — |
| Secret lifecycle, vault, rotation, leak IR | `secrets-management-hygiene` | this skill (CMK wrapping secrets) |
| Lambda execution role / env / invoke policy | `aws-lambda-least-privilege` | this skill (function CMK) |
| Account IAM wildcards / PassRole | `aws-iam-least-privilege` | this skill (KMS resource side) |
| S3 default encryption / BPA | `aws-s3-bucket-hardening` | this skill (bucket CMK) |
| Terraform/CDK key resources | `terraform-security-basics` | this skill (control intent) |

**Required hand-offs:** secrets → `secrets-management-hygiene`; Lambda identity →
`aws-lambda-least-privilege`. This skill owns **key policy, grants, ViaService,
encryption context, and key-admin least privilege**.

## Output Checklist

- [ ] Authorization and account/region scope recorded (owned AWS only)
- [ ] CMKs inventoried: aliases, state, rotation, consumers (no secrets)
- [ ] Key policy vs IAM applied; root enablement + explicit admins/users
- [ ] Key admins separated from crypto users; no app `kms:*`
- [ ] Service use constrained with `kms:ViaService` / source account
- [ ] Grants inventoried; unused/over-broad grants retired
- [ ] Encryption context required/conditioned where supported
- [ ] No unintended cross-account decrypt; Access Analyzer reviewed
- [ ] Secrets → `secrets-management-hygiene`; Lambda → `aws-lambda-least-privilege`
- [ ] Verified non-prod; exceptions owned; IaC uses `terraform-security-basics` / CQS

## Rules

- **Owned or authorized AWS accounts only.** Key policy is the resource gate;
  IAM cannot bypass a missing key-policy allow. Prefer CMKs for auditable
  admin/use split. Never put secrets in encryption context or tickets. Prove
  excess rights with policies, grants, and CloudTrail — not bulk prod decrypt.
  A compromised app role must not equal key administrator or account-wide decrypt.

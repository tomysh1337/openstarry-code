---
name: aws-secrets-manager-rotation
description: >
  AWS Secrets Manager automatic and immediate rotation for owned accounts:
  rotation Lambda steps, AWSCURRENT/AWSPENDING labels, multi-user strategies,
  hosted RDS/Redshift/DocumentDB rotation, and post-leak cutover. Use when
  enabling or fixing Secrets Manager rotation, staging-label stuck rotations,
  custom rotation functions, or dual-credential cutover — not for third-party
  account abuse or generic git/.env secret scanning alone.
---

# AWS Secrets Manager Rotation

Design, enable, and troubleshoot **AWS Secrets Manager rotation** so credentials
change on a schedule (or immediately after compromise) without breaking
consumers. **Org-owned or explicitly authorized AWS accounts only.**

## When To Use

- Enabling **automatic rotation** (schedule + Lambda or hosted rotation)
- Stuck rotation: **AWSCURRENT** never flips; **AWSPENDING** left behind
- Choosing **single-user** vs **multi-user / alternating-user** strategies
- Hosted rotation for **RDS, Aurora, Redshift, DocumentDB** vs custom Lambda
- Immediate rotation after leak; dual-version cutover for long-lived clients
- Mentions: Secrets Manager rotation, AWSCURRENT, AWSPENDING, rotate-secret,
  RotationConfiguration, multi-user rotation, hosted rotation

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org secret inventory, git/.env, leak IR | `secrets-management-hygiene` |
| CMK key policy / ViaService / grants | `aws-kms-key-policy-basics` |
| Rotation role wildcards / PassRole | `aws-iam-least-privilege` |
| Terraform secret modules / state | `terraform-security-basics` |
| App/SDK/IaC implementation quality | `code-quality-standards` |
| SSM Parameter Store (non-SM) | `secrets-management-hygiene` |

## Workflow

### 1. Scope and inventory

Record account, region(s), env, authorization, secret ARNs. Note rotation
status, Lambda ARN, schedule, KMS key, consumers. **No secret StringValue in
reports.**

```bash
# Owned account only
aws sts get-caller-identity
aws secretsmanager list-secrets \
  --query 'SecretList[].{Name:Name,Rotated:RotationEnabled,Lambda:RotationLambdaARN}'
aws secretsmanager describe-secret --secret-id SECRET_ID_OR_ARN
aws secretsmanager list-secret-version-ids --secret-id SECRET_ID_OR_ARN
```

### 2. Labels and rotation steps

| Stage / step | Meaning |
| --- | --- |
| **AWSCURRENT** | Version consumers should use now |
| **AWSPENDING** | Candidate version under rotation |
| **AWSPREVIOUS** | Prior current (rollback / multi-user handoff) |
| **createSecret** | Generate new material; put as AWSPENDING |
| **setSecret** | Apply pending credential on the target |
| **testSecret** | Verify pending credential end-to-end |
| **finishSecret** | Promote AWSPENDING → AWSCURRENT; clean labels |

Steps must be **idempotent**. Partial failure leaves AWSPENDING without finish —
repair the step, then re-`rotate-secret` or finish under change control.

### 3. Strategy and hosting

| Strategy | When | Notes |
| --- | --- | --- |
| **Single-user** | One DB/user or API key | Replace in place; clients refresh promptly |
| **Multi-user / alternating** | Zero-downtime DB passwords | Rotate idle user; apps read AWSCURRENT |
| **Hosted rotation** | RDS/Aurora/Redshift/DocDB | Prefer AWS templates when engine matches |
| **Custom Lambda** | Non-DB APIs, proprietary stores | Own create/set/test/finish; VPC + IAM |

CMK wrapping → `aws-kms-key-policy-basics`. Prefer Secrets Manager for
credentials that must rotate over static env/SSM values.

### 4. Permissions, enable, operate

Rotation Lambda role (least privilege): `DescribeSecret`, `GetSecretValue`,
`PutSecretValue`, `UpdateSecretVersionStage` on **specific secret ARNs**;
scoped target updates; KMS on the secret’s CMK (`kms:ViaService`
secretsmanager); VPC/SG only for needed private targets. No `Resource:"*"` for
put/stage. Wildcards/PassRole → `aws-iam-least-privilege`. Code →
`code-quality-standards`.

1. Non-prod first; enable schedule; invoke once manually.
2. Confirm create → set → test → finish; consumers still work.
3. Clients fetch by secret ID/ARN; cache TTL shorter than rotation interval.
4. After leak: disable compromised target material if possible, rotate, bust
   caches, audit CloudTrail — IR via `secrets-management-hygiene`.
5. Alarm on Lambda errors, stuck AWSPENDING, failed testSecret.
6. IaC → `terraform-security-basics` + this skill for rotation semantics.

```bash
aws secretsmanager rotate-secret --secret-id SECRET_ID_OR_ARN
aws secretsmanager describe-secret --secret-id SECRET_ID_OR_ARN \
  --query '{RotationEnabled:RotationEnabled,LastRotated:LastRotatedDate,Versions:VersionIdsToStages}'
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SM rotation, labels, Lambda steps, hosted templates | **This skill** | — |
| Org leak IR, git/.env, vault process beyond SM | `secrets-management-hygiene` | this skill (rotate) |
| CMK wrapping the secret | `aws-kms-key-policy-basics` | this skill |
| Rotation role wildcards / PassRole | `aws-iam-least-privilege` | this skill |
| Terraform secret/rotation resources | `terraform-security-basics` | this skill |
| Lambda/app implementation quality | `code-quality-standards` | this skill |

**Ownership:** this skill owns **Secrets Manager rotation mechanics** (labels,
steps, hosted vs custom, dual-credential cutover). Org hygiene/scanning →
`secrets-management-hygiene`.

## Output Checklist

- [ ] Authorization and account/region scope recorded (owned AWS only)
- [ ] Secrets inventoried: name/ARN, rotation on/off, Lambda/hosted, consumers
- [ ] Strategy chosen (single-user vs multi-user); downtime justified
- [ ] create/set/test/finish idempotent; AWSCURRENT/AWSPENDING understood
- [ ] Rotation role least-privilege on secret ARNs + target + KMS; no `*` put/stage
- [ ] Private targets: VPC/SG path verified; non-prod rotation exercised
- [ ] Consumers fetch by ID/ARN (no hard-coded secrets); caches refresh in time
- [ ] Alarms on rotation failures / stuck AWSPENDING
- [ ] Post-leak: rotate + cache bust + `secrets-management-hygiene` IR
- [ ] CMK/IAM/IaC handed off; no live secret values in reports

## Scope And Authorization

- **In scope:** Secrets Manager secrets **you own** or are contracted to manage;
  describe/list rotation config; controlled `RotateSecret` and version-stage
  fixes; custom rotation Lambda review; hosted rotation for supported engines.
- **Out of scope:** Foreign-account secrets; third-party credential use;
  disabling CloudTrail; mass prod rotation without a change window.
- Prefer non-prod. Gate secret-value reads, prod finishSecret, and target
  password changes. Redact secret strings/tokens. Pair IAM →
  `aws-iam-least-privilege`; CMK → `aws-kms-key-policy-basics`; leak IR →
  `secrets-management-hygiene`.

---
name: aws-ecs-task-security
description: >
  Harden Amazon ECS task definitions and services for owned AWS accounts: task
  role vs execution role split, Secrets Manager/SSM injection, public tasks and
  assignPublicIp, security groups, Fargate vs EC2 launch type, and privileged
  containers. Use when reviewing ECS task IAM, plaintext env secrets, open
  service security groups, privileged/SYS_ADMIN Linux parameters, or public
  Fargate tasks — not for abusing third-party AWS accounts.
---

# AWS ECS Task Security

Assess and harden **Amazon ECS** so tasks use least IAM privilege, inject
secrets safely, expose network paths intentionally, and deny host-equivalent
power. **Org-owned or explicitly authorized AWS accounts only.**

## Scope And Authorization

- **In scope:** ECS clusters, services, task defs, task/execution roles, SGs,
  SM/SSM/KMS in owned/contracted accounts; read-only inventory; controlled changes with rollback.
- **Out of scope:** Foreign-account abuse; off-scope stolen task creds; hiding
  activity; privileged/host breakout demos on shared prod.
- Prefer non-prod for experimental revisions. Gate public IP, open SGs, and
  privileged Linux parameters behind approval. Redact secrets/env/STS. Do not
  infer authorization from “sandbox-like” appearance.

## When To Use

- **taskRoleArn** vs **executionRoleArn** merged or over-privileged
- Secrets in plain `environment` instead of `secrets` (SM/SSM)
- `assignPublicIp=ENABLED`, public subnets, or `0.0.0.0/0` task/service SGs
- `privileged`, `SYS_ADMIN`, host net/PID/IPC, docker.sock-style mounts
- Fargate vs EC2 isolation; mentions of ECS task/execution role, secrets
  injection, public Fargate, awsvpc SGs, privileged ECS container

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Account-wide IAM / PassRole redesign | `aws-iam-least-privilege` |
| Secret rotation / leak IR beyond inject | `secrets-management-hygiene` |
| Image build / lab container escape | `dockerfile-best-practices` / `container-escape-techniques` |
| S3 BPA / Terraform ECS / app code quality | `aws-s3-bucket-hardening` / `terraform-security-basics` / `code-quality-standards` |

## Control Baseline

| Control | Hardened default |
| --- | --- |
| Execution role | ECR pull, logs, **read inject secrets only** — no app data APIs |
| Task role | App runtime APIs only; no `iam:*`, no cluster-admin ECS, no `*` |
| Secrets | Task `secrets` → SM/SSM; never plaintext in task JSON |
| Network / SGs | Private subnets; public IP only if intentional; least ports via ALB SG |
| Privileged / host ns | Off; prefer Fargate when host access not required |

**Role split:** execution = platform (ECR, logs, secret fetch). Task = app
process. Merging into one admin-like role is high severity.

## Workflow

### 1. Scope and inventory

Record account, region, cluster, env, authorization. Inventory services,
task-def revisions, launch type, network mode; both role ARNs, subnets,
`assignPublicIp`, SGs.

```bash
# Owned account only
aws sts get-caller-identity
aws ecs describe-services --cluster CLUSTER --services SVC \
  --query 'services[].{td:taskDefinition,net:networkConfiguration,launch:launchType}'
aws ecs describe-task-definition --task-definition FAMILY:REV
```

### 2. Split and shrink IAM roles

1. Review both policies (deep IAM → `aws-iam-least-privilege`).
2. **Execution:** ECR auth + scoped pull; log stream/put; SM/SSM read
   (+ KMS decrypt) **only** for secrets referenced in the task def.
3. **Task:** app AWS calls only; no unconstrained `PassRole` or IAM/ECS admin.
4. Trust: `ecs-tasks.amazonaws.com` only; source-account conditions if required.

### 3. Secrets injection

Flag tokens in `environment`, args, or image. Use task-definition `secrets`
from Secrets Manager or SSM SecureString; scope execution-role read to those
ARNs. Prefer task role over long-lived AKIA. Rotation/leaks/old plaintext
revisions → `secrets-management-hygiene`.

### 4. Network and security groups

Prefer private subnets and `assignPublicIp=DISABLED`. Ingress: required ports
only; source = ALB/NLB SG or known CIDRs — not world-open admin/DB. Tighten
egress where feasible (VPC endpoints for ECR/Logs/Secrets). Document residual
risk if a public service lacks strong app/ALB auth.

### 5. Fargate vs EC2 and privileged containers

| Topic | Guidance |
| --- | --- |
| Fargate | No host/privileged; good default isolation |
| EC2 launch type | Review **instance profile** separately from task role |
| `privileged`, `SYS_ADMIN`, host net/PID | Deny on app tasks |
| docker.sock / sensitive host mounts (EC2) | Host-equivalent — remove from apps |
| Readonly root / drop caps / non-root | Prefer; images → `dockerfile-best-practices` |

Escape claims only via `container-escape-techniques` on **owned lab** hosts.

### 6. Remediate and verify

New task-def revision (split roles, secret refs, non-privileged) → update
service → healthy deploy. Re-check SG/public IP and role creep. IaC:
`terraform-security-basics` + `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ECS roles, secrets inject, public tasks, SGs, privileged | **This skill** | — |
| Deep IAM / PassRole / trust | `aws-iam-least-privilege` | this skill (ECS attach) |
| Secret rotation, VCS leaks | `secrets-management-hygiene` | this skill (inject) |
| Image / lab escape / Terraform / implementation | matching helper skill | this skill for ECS controls |

## Output Checklist

- [ ] Authorization and account/cluster scope recorded (owned AWS only)
- [ ] Services/task defs inventoried (launch type, network, revisions)
- [ ] **executionRole** ≠ **taskRole**; platform vs app duties separated
- [ ] Execution role limited to pull, logs, and listed secret ARNs
- [ ] Task role least privilege; no unjustified admin/IAM/ECS wildcards
- [ ] No plaintext secrets in `environment`; inject via SM/SSM
- [ ] Public IP/subnets justified or removed; SGs least port/source
- [ ] Privileged/host mounts absent; Fargate vs EC2 risks noted; residuals owned/redacted

## Rules

- **Owned or authorized AWS accounts only** — no third-party ECS abuse.
- Keep task and execution roles separate; never merge into Admin.
- Prove risk from task definition + IAM + SG evidence, not destructive demos on shared prod.
- Public tasks + open SGs + broad task roles = high blast radius after credential theft.

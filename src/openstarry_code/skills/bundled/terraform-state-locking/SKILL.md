---
name: terraform-state-locking
description: >
  Configure and review Terraform/OpenTofu remote state locking and encryption:
  S3 + DynamoDB (or native S3 lock), azurerm, and gcs backends; force-unlock
  risks; who may unlock; and least-privilege lock/state IAM. Use when state
  lock, DynamoDB lock table, force-unlock, concurrent apply corruption, remote
  state encryption, or backend lock ownership — hand broader tfstate/IAM/S3
  baselines to terraform-security-basics.
---

# Terraform State Locking

Own **remote state locking**, **unlock governance**, and **backend encryption**
so concurrent applies do not corrupt state. Org-owned/authorized Terraform/OpenTofu
only. Broader tfstate/IAM/public bucket → `terraform-security-basics`.

## When To Use

- Backends: **S3 + DynamoDB** (or S3 native lock), **azurerm** blob lease, **gcs** lock
- Stuck locks, crashed CI, racey applies, `Error acquiring the state lock`
- **`terraform force-unlock`** policy; who may delete locks / break leases / overwrite state
- Remote state encryption (`encrypt = true`, SSE/CMK/CMEK)
- Mentions: state lock, DynamoDB lock table, force-unlock, concurrent apply, 状态锁

Do **not** use as primary for: full TF security → `terraform-security-basics`; live
S3 BPA → `aws-s3-bucket-hardening`; leak IR → `secrets-management-hygiene`; module
quality → `code-quality-standards`; CI stages → `ci-cd-pipeline-patterns`.

## Repo Config First

Repo backends, platform standards, and runbooks **outrank** defaults below.

1. **Backend type/location:** `s3` / `azurerm` / `gcs` in roots or CI/Terragrunt partials
2. **Lock mechanism:** DynamoDB table, S3 native lock, Azure lease, GCS lock — match TF version docs
3. **Apply identities:** humans, TFC/TFE, OIDC CI — lock RW vs state RO
4. **Key layout:** one state key per env/stack; no shared prod/dev keys
5. **Unlock runbook:** force-unlock approval, audit, break-glass owners
6. **Encryption policy:** SSE-S3/SSE-KMS, Azure SSE/CMK, GCS default/CMEK
7. **Neighbors:** `terraform-security-basics` for BPA/versioning/public access

**Precedence:** Follow the repo. Flag missing locks, world-writable lock tables, or
unlogged force-unlock even if local solo apply “works.”

## Workflow

### 1. Inventory

List roots/workspaces: backend type, bucket/container, state key, region, lock
resource, plan vs apply principals. Flag local state in git/laptops. Output:
root → backend → lock resource → identity (no secrets).

### 2. Configure locking per backend

| Backend | Lock control | Hardened expectation |
| --- | --- | --- |
| **S3** | `dynamodb_table` and/or native S3 lock | Lock **on** for teams; dedicated table or documented native lock |
| **azurerm** | Blob lease on state blob | Private container; lease held during apply |
| **gcs** | Object-based lock / prefix | Bucket not public; lock objects not broadly deletable |

```hcl
terraform {
  backend "s3" {
    bucket         = "org-tfstate-prod"
    key            = "payments/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "org-tfstate-locks"
    encrypt        = true
    # kms_key_id  = "arn:aws:kms:..."  # when CMK required
  }
}
```

**Bad:** no lock on multi-operator prod; `encrypt = false`; lock table open to `*`.
**azurerm/gcs:** private storage + platform/CMK encryption; exact HCL from current
provider docs and in-repo examples.

### 3. Encryption and confidentiality

Require SSE (`encrypt = true` on S3; Azure/GCS on). CMK users = apply roles only.
Treat state as a **secret document** — least-privilege read; no public ACLs. Secrets
IR → `secrets-management-hygiene`; BPA → `terraform-security-basics` /
`aws-s3-bucket-hardening`.

### 4. Who can lock, unlock, and read state

| Capability | Prefer | Avoid |
| --- | --- | --- |
| Acquire/release lock | Apply role only | All developers on prod lock table |
| Delete lock / break lease | Break-glass + audit | Broad `dynamodb:DeleteItem` on `*` |
| Read state | Apply + limited plan/audit | Wide RO / public principals |
| Write/delete state object | Apply role only | Unscoped shared admin |

DynamoDB LockID is typically the full state path. Scope IAM to the lock table ARN and
needed actions (`GetItem`/`PutItem`/`DeleteItem`/`DescribeTable`) — not `dynamodb:*` on `*`.

### 5. Stuck locks and force-unlock risks

1. Confirm **no apply is running** (CI, colleague, TFC) before unlock.
2. Prefer natural unlock: stop the holder or platform UI release.
3. `terraform force-unlock LOCK_ID` does **not** verify the holder is gone — concurrent
   applies can **corrupt state**.
4. Require ticket/approval, recorded LOCK_ID, operator identity, post-unlock `plan`,
   audit log. **Never** auto force-unlock on every CI failure.
5. After crash: inspect lock metadata; fix timeouts, missing `-lock-timeout`, zombies.

### 6. Verify and hand off

Second identity must fail concurrent apply while locked. Unauthorized principals must
not delete locks or read state. Confirm encryption. Hand public bucket, broad IAM,
secrets-in-tfvars, plan/apply gates to **`terraform-security-basics`**.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| State locking, force-unlock, lock IAM, backend encrypt | **This skill** | — |
| Broader TF security, public state bucket, IAM modules, secrets in IaC | `terraform-security-basics` | **hand off** after lock/encrypt fixed |
| Live S3 BPA/policy for state bucket | `aws-s3-bucket-hardening` | this for lock/backend HCL |
| State/credential leak IR | `secrets-management-hygiene` | this to re-lock readers |
| Backend/module implementation | `code-quality-standards` | this for lock requirements |
| Pipeline stages / OIDC | `ci-cd-pipeline-patterns` | this for apply-role lock rights |

- **`terraform-security-basics`:** full baseline; this skill deepens **locking and unlock governance only**.
- **`code-quality-standards`:** backend modules, IAM fragments, tests.

## Output Checklist

- [ ] Backends inventoried: type, location, key, lock resource, apply identities
- [ ] Locking enabled for multi-operator / CI remote state
- [ ] S3 DynamoDB and/or native lock; azurerm/gcs lease/lock verified
- [ ] State store encryption on (`encrypt` / SSE / CMEK as required)
- [ ] IAM: apply lock+write; plan limited; unlock delete not world-wide
- [ ] Force-unlock only via break-glass runbook (approval + audit)
- [ ] No automated unconditional force-unlock in CI
- [ ] Concurrent-apply test: second apply fails to acquire lock
- [ ] Residual bucket/IAM/secrets → `terraform-security-basics`
- [ ] `code-quality-standards` on IaC changes; secrets redacted in reports

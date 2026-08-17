---
name: terraform-security-basics
description: >-
  Terraform security basics for authorized/org-owned infra: remote state and
  secrets hygiene, IAM least privilege, public S3 and open security groups,
  provider credential patterns, and safe plan/apply. Use when Terraform
  security, tfstate secrets, public bucket, overly broad IAM, terraform.tfvars
  credentials, or hardening Terraform modules and CI apply paths.
---

# Terraform Security Basics

Review and harden **Terraform** (and close cousins: OpenTofu) configuration and
workflows so infrastructure-as-code does not leak secrets, grant excessive IAM,
or expose data stores publicly. Defensive and authorized assessment only.

## Scope And Authorization

- **In scope:** Terraform/OpenTofu roots, modules, backends, and pipelines you
  own or are contracted to harden; read-only `plan` in non-prod; controlled
  `apply` with change windows and rollback.
- **Out of scope:** Using discovered cloud keys against accounts you do not own;
  destructive `apply`/`destroy` on production without approval; opening
  resources “to test impact” on shared accounts.
- Prefer **non-production** workspaces for risky experiments. Never commit real
  access keys into examples or tickets.
- Treat **state files** as sensitive artifacts (often contain plaintext secrets).
  Redact `terraform show` / plan JSON in reports.
- Pair secret lifecycle with `secrets-management-hygiene`; container build
  concerns with `dockerfile-best-practices` when TF builds/pushes images.

## Use When

- Authoring or reviewing `*.tf`, modules, terragrunt stacks, or Terraform Cloud/Enterprise workspaces
- `terraform.tfstate` / remote state may contain secrets or is stored insecurely
- IAM policies, roles, instance profiles look like `*` on actions/resources
- S3 (or compatible) buckets, security groups, or load balancers may be public
- CI runs `terraform apply` with long-lived cloud keys
- User mentions: Terraform security, tfstate, public S3, least privilege IAM,
  `terraform.tfvars` secrets, provider credentials, OpenTofu hardening

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General vault/rotation/.env hygiene | `secrets-management-hygiene` |
| Application code quality inside provisioned hosts | `code-quality-standards` |
| Dockerfile/image hardening only | `dockerfile-best-practices` |
| K8s RBAC deep dive (cluster already exists) | `kubernetes-pentesting` |
| CI structure beyond TF steps | `ci-cd-pipeline-patterns` |
| Zip/artifact path escape in provisioner scripts | `zip-slip-path-safety` |

## Threat Model (dense)

| Area | Risk | Impact |
| --- | --- | --- |
| State backend | World-readable state, no encryption, no lock | Secret dump, race corrupts state |
| Secrets in VCS | Keys in `.tf`, `tfvars`, plans committed | Credential theft, account takeover |
| Provider creds | Long-lived AKIA in CI/dev laptops | Lateral cloud abuse |
| IAM | `Action = "*"`, `Resource = "*"`, admin for every module | Blast radius on any compromise |
| Data stores | Public ACL/policy on S3, open RDS SG `0.0.0.0/0` | Data breach, ransomware surface |
| Network | `0.0.0.0/0` on SSH/RDP/DB ports | Direct attack surface |
| Remote-exec | Untrusted scripts, secrets in user_data logged | Host compromise, secret leak in TF state |
| Supply chain | Unpinned modules/providers from untrusted registry | Malicious infra code |
| Workspaces | Prod/dev same credentials and backend | Cross-env damage |

## Workflow

### 1. Inventory roots and trust boundaries

1. List Terraform roots/workspaces: env (dev/stage/prod), backend type, who can
   `plan`/`apply`, and cloud accounts/subscriptions.
2. Map **human** vs **automation** identities (local AWS profile, OIDC role, TFC
   run identity).
3. Flag shared state, shared “god” roles, and modules copied without review.
4. Note provisioners (`remote-exec`, `local-exec`), `user_data`, and template
   files that embed secrets.

Output: short inventory (no secret values) — roots, backends, apply identities.

### 2. State backend security

Remote state is mandatory for teams; configure it as a **secret store**.

| Control | Expectation |
| --- | --- |
| Location | Org-owned bucket/container; not public; not personal account |
| Encryption | Server-side encryption on; CMK when policy requires |
| Access | Least privilege: state RW for apply role only; RO for plan-only |
| Locking | DynamoDB / native locks enabled to prevent concurrent apply |
| Versioning | Object versioning on for recovery after bad apply |
| Public access | S3 Block Public Access **all four** on; no public policy |
| Cross-account | Explicit, documented; no anonymous `Principal = "*"` |

**Good — S3 backend sketch (AWS)**

```hcl
terraform {
  backend "s3" {
    bucket         = "org-tfstate-prod"
    key            = "payments/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "org-tfstate-locks"
    encrypt        = true
    # kms_key_id   = "arn:aws:kms:..."  # when required
  }
}
```

**Bad**

- Local `terraform.tfstate` committed to git
- Backend bucket with ACL `public-read` or policy `Principal:"*"` `s3:GetObject`
- `encrypt = false` or missing lock table
- One bucket key prefix for all envs with world-wide IAM `s3:*`

**State secrets awareness:** resource attributes (DB passwords, private keys,
access keys created by TF) often land in state. Prefer:

- Secrets Manager / Vault / SSM Parameter Store generation + **reference** by ARN
- `ignore_changes` only with clear reason; still treat state as sensitive
- Restricted `terraform output` — mark `sensitive = true`
- Never paste full state into tickets or chat

### 3. Secrets out of code and plans

Apply `secrets-management-hygiene` principles to Terraform:

1. **Scan** for `AKIA`, `-----BEGIN`, passwords in `*.tf`, `*.tfvars`, `*.tfstate*`,
   plan JSON, and module examples.
2. Use **variables** without defaults for secrets; inject via CI secret store,
   TFC sensitive vars, or ambient OIDC — not committed `terraform.tfvars`.
3. Provide `terraform.tfvars.example` with placeholders only.
4. `.gitignore`: `.terraform/`, `*.tfstate`, `*.tfstate.*`, `crash.log`,
   `*.tfvars` (if they hold secrets), override files with credentials.
5. Avoid `provider "aws" { access_key = "..." secret_key = "..." }` in code —
   use env, shared config, or OIDC assume-role.
6. For `user_data` / templates: pull secrets at **instance runtime** from IMDS +
   SM, not render plaintext into templates stored in state.

**Good**

```hcl
variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "app" {
  # ...
  password = var.db_password  # still lands in state — prefer managed secret
}
```

**Better (pattern)**

```hcl
resource "aws_secretsmanager_secret" "db" {
  name = "app/prod/db"
}

# Password generated/stored outside TF or via random+SM rotation;
# app/IAM reads secret by ARN; minimize password attribute in TF resources.
```

**Bad**

```hcl
provider "aws" {
  access_key = "AKIA..."
  secret_key = "wJal..."
}

resource "aws_db_instance" "app" {
  password = "SuperSecret123!"  # hardcoded
}
```

### 4. IAM least privilege

1. Inventory `aws_iam_policy`, `azurerm_role_assignment`, `google_project_iam_*`
   and inline policies in modules.
2. Flag:
   - `"Action": "*"` or service wildcards with `"Resource": "*"`
   - `AdministratorAccess` / Owner on human or CI roles used for everyday apply
   - Cross-service pass-role with broad trust policies
   - Public `Principal: "*"` without hard conditions
3. Split roles: **plan** (read-mostly) vs **apply** (narrow write on known types).
4. Scope by resource ARN prefix, tags/conditions (`aws:ResourceTag`), and
   account/region.
5. Prefer cloud **managed policies only when** they match need; otherwise
   custom least privilege.
6. CI: OIDC federated role with bound subject (repo + ref + environment), not
   long-lived access keys on all branches; deny secrets to fork PRs.

**Good — narrowed S3 policy fragment**

```hcl
data "aws_iam_policy_document" "app_s3" {
  statement {
    sid       = "ListOwnPrefix"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["app-data/*"]
    }
  }
  statement {
    sid       = "RWOwnObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.app.arn}/app-data/*"]
  }
}
```

**Bad**

```hcl
statement {
  actions   = ["*"]
  resources = ["*"]
}
```

### 5. Public S3 and data exposure

For each `aws_s3_bucket` (and Azure/GCP equivalents):

| Check | Secure default |
| --- | --- |
| Block Public Access | All four blocks `true` |
| ACL | Private; avoid `public-read` |
| Bucket policy | No `Principal:"*"` get/put unless intentional static site with review |
| Encryption | SSE-S3 or SSE-KMS required |
| Versioning / logging | On for sensitive data buckets |
| Website hosting | Only if product requires; separate from tfstate/logs |
| Cross-account | Explicit principals + conditions |

**Good**

```hcl
resource "aws_s3_bucket_public_access_block" "app" {
  bucket                  = aws_s3_bucket.app.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app" {
  bucket = aws_s3_bucket.app.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

**Bad**

```hcl
acl = "public-read"

# or policy:
# Principal = "*", Action = "s3:GetObject", Resource = "arn:aws:s3:::bucket/*"
# without Block Public Access
```

Static websites and public assets must be **explicit**, documented, and never
mixed with state, logs, or backups.

### 6. Network exposure (quick pass)

1. Security groups / NSGs / firewall rules: flag inbound `0.0.0.0/0` or `::/0`
   on admin (22, 3389), DB (5432, 3306, 1433), Redis, Elasticsearch, etc.
2. Prefer private subnets + bastion/SSM Session Manager; no SSH from internet.
3. Load balancers: HTTPS listeners, restricted security groups to LB only.
4. Default VPCs/open rules in example modules — do not copy into prod roots.

### 7. Modules, providers, and supply chain

1. Pin provider versions (`required_providers` constraints) and **module**
   versions/refs (tag or commit SHA — not floating `main`).
2. Prefer private module registry or mirrored modules for prod.
3. `terraform init` in CI with lockfile (` .terraform.lock.hcl`) committed.
4. Review `external` data sources and downloads of remote scripts.
5. Disable or gate `remote-exec` where config management should own hosts.

### 8. Plan / apply hygiene

1. `terraform fmt` + `validate` in CI; `tflint` / `tfsec` / `checkov` / `trivy
   config` as org standard (pick one primary, fail on high).
2. Require plan artifact review before apply on prod; protected environments.
3. Separate workspaces/state per env; separate cloud accounts when possible.
4. No `terraform apply -auto-approve` on prod from unprotected branches.
5. Break-glass admin role audited and not the daily apply role.
6. After apply, confirm public-access blocks and IAM with cloud console/CLI
   read-only checks — do not trust intent alone.

### 9. Authorized misconfiguration review (assessment mode)

When assessing customer/org TF (with authorization):

1. Static review of roots + `terraform plan` in **read-only** or sandbox account.
2. Grep/policy-as-code for public S3, open SGs, admin IAM, hardcoded secrets.
3. Check backend bucket ACLs/policies live (describe only).
4. Report with file paths, resource addresses, and severity; no live key abuse.
5. Hand app-layer issues on provisioned apps to web/API skills separately.

## Concrete Techniques Cheat Sheet

| Goal | Technique |
| --- | --- |
| Find secrets | gitleaks/trufflehog on repo; scan `tfvars`, state, plans |
| Find public S3 | Grep `public-read`, `Principal = "*"`, missing public_access_block |
| Find open SG | Grep `0.0.0.0/0` + sensitive ports in `aws_security_group` |
| Find admin IAM | Grep `"*"` actions; managed policy attachments Admin |
| State risk | Confirm encrypt, lock, block public, who has s3:GetObject |
| CI hardening | OIDC role + env protection; no AKIA in GitHub secrets for forks |
| Policy as code | checkov/tfsec/trivy on PR; block merge on HIGH |
| Sensitive outputs | `sensitive = true`; limit who can read state |
| Module pin | `source = "...//module?ref=v1.2.3"` or commit SHA |
| Implement fix | Smallest IAM/S3/SG change + `code-quality-standards` for modules |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Terraform/OpenTofu security, tfstate, IAM, public S3 | **This skill** | — |
| Secret inventory, vault, rotation, leak IR | `secrets-management-hygiene` | this skill for TF/state-specific paths |
| Module/code structure, tests, error handling | `code-quality-standards` | this skill for cloud control intent |
| Images built/pushed by pipelines TF triggers | `dockerfile-best-practices` | `ci-cd-pipeline-patterns` |
| CI workflow design around plan/apply | `ci-cd-pipeline-patterns` | this skill for cloud identity & state |
| Path traversal in packer/provisioner archives | `zip-slip-path-safety` / `path-traversal-lfi` | — |
| File access on provisioned app | `file-access-vuln` | — |
| K8s objects after cluster exists | `kubernetes-pentesting` | this skill for cluster IAM/network bootstrap |
| Design-time threats for platform | `threat-modeling-stride` | this skill for IaC mitigations |

### Routing notes (required helpers)

- **`secrets-management-hygiene`:** canonical secret lifecycle; TF state and
  `tfvars` are high-value secret containers — remediate with that skill’s
  rotate-first discipline.
- **`code-quality-standards`:** when writing/refactoring modules, variable
  validation, and tests for security controls.
- **`dockerfile-best-practices`:** when Terraform builds or deploys container
  images; keep secrets out of layers and run non-root.
- **`path-traversal-lfi` / `file-access-vuln` / `zip-slip-path-safety`:** when
  provisioners, object storage apps, or archive extract on hosts are in scope —
  IaC may open the bucket/SG; app path skills own the app bug class.
- **`ci-cd-pipeline-patterns`:** pipeline stages, approvals, and OIDC wiring detail.

## Checklist

- [ ] Roots/workspaces/backends/apply identities inventoried (no secret values)
- [ ] Remote state: encrypt, lock, versioning, non-public, least-privilege IAM
- [ ] No credentials in `*.tf` / committed `tfvars` / provider blocks
- [ ] Sensitive vars marked; outputs sensitive; state treated as confidential
- [ ] `.gitignore` covers state, crash logs, and secret var files
- [ ] IAM policies reviewed: no unnecessary `*` / admin on daily roles
- [ ] Plan vs apply roles separated where practical; OIDC over long-lived keys
- [ ] All S3 (and equivalents): Block Public Access; encryption; no accidental public policy
- [ ] Security groups: no admin/DB ports from `0.0.0.0/0` without exception record
- [ ] Providers/modules pinned; lockfile committed; policy-as-code in CI
- [ ] Prod apply gated; no unreviewed `-auto-approve` on default branch
- [ ] `secrets-management-hygiene` followed for any leaked key in history/state
- [ ] `code-quality-standards` applied when changing modules
- [ ] Residual risks documented (vendor constraints, temporary exceptions + expiry)

## Rules

- State is sensitive — share sparingly, encrypt at rest, restrict IAM.
- Prefer generating and storing secrets **outside** resource arguments when the
  provider supports references; still assume state may contain secrets.
- Least privilege is iterative: start narrow, widen with errors, never start at `*`.
- Public exposure must be explicit product intent, not a missing block.
- Authorized org/lab only — no offensive use of found cloud credentials.
- Destroy and apply can be highly destructive; require change control on prod.
---

# Note

This skill owns **Terraform/OpenTofu security baselines** (state, secrets in IaC,
IAM, public storage/network). Pair with `secrets-management-hygiene` for org-wide
secret process, `code-quality-standards` for module implementation quality, and
`dockerfile-best-practices` / `ci-cd-pipeline-patterns` for delivery pipelines.

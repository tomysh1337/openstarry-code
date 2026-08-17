---
name: github-actions-oidc-aws
description: >
  Configure and review GitHub Actions OIDC federation to AWS IAM roles so CI
  obtains short-lived credentials via sts:AssumeRoleWithWebIdentity without
  long-lived access keys. Use when designing or auditing GitHub OIDC providers,
  role trust policies (sub/aud conditions), aws-actions/configure-aws-credentials,
  id-token permissions, environment-scoped deploy roles, or retiring AKIA keys
  from workflows on owned or authorized AWS accounts and GitHub orgs.
---

# GitHub Actions OIDC to AWS

Replace **static AWS access keys in GitHub secrets** with **OIDC federation**:
GitHub Actions id-token → IAM OIDC provider → `sts:AssumeRoleWithWebIdentity` →
short-lived role credentials. For **org-owned or explicitly authorized** AWS
accounts and GitHub orgs only.

## When To Use

- Wiring **GitHub Actions → AWS** without `AWS_ACCESS_KEY_ID` /
  `AWS_SECRET_ACCESS_KEY` repository secrets
- Creating or reviewing the IAM **OIDC provider**
  (`token.actions.githubusercontent.com`) and **role trust** conditions
- Hardening `sub` / `aud` binds (repo, ref, environment, job_workflow_ref)
- Using `aws-actions/configure-aws-credentials` with `role-to-assume` and
  `permissions: id-token: write`
- Migrating deploy/plan jobs off long-lived AKIA; splitting prod vs PR roles
- Mentions: GHA OIDC AWS, AssumeRoleWithWebIdentity, GitHub OIDC provider,
  configure-aws-credentials, CI role trust, no access keys in Actions

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Broad IAM least privilege, PassRole, Access Analyzer | `aws-iam-least-privilege` |
| Pipeline stages, cache, artifacts, general CI shape | `ci-cd-pipeline-patterns` |
| CI secret masking, fork isolation, multi-cloud OIDC hygiene | `secrets-in-ci-pipelines` |
| AKIA leak IR / org rotation process | `secrets-management-hygiene` |
| GCP WIF / GitHub → GCP SA | `gcp-workload-identity-federation` |
| Terraform IAM modules / state backend identity | `terraform-security-basics` |
| Implementation quality of HCL/YAML generators | `code-quality-standards` |

## Repo Config First

Repo and org **identity and CI config outrank** examples below.

1. **Existing federation:** IAM OIDC providers already in account; org reusable
   workflows that assume shared roles
2. **Workflow files:** `.github/workflows/*` — job `permissions`, environments,
   jobs that need AWS (and any residual AKIA secrets)
3. **GitHub Environments:** protection rules and deployment branches — map to
   trust `sub` claims (`environment:production`, etc.)
4. **Branch protection:** required checks; deploy only from protected refs
5. **Org policy:** allowed OIDC subjects, SHA-pinned actions, fork PR secret rules
6. **AWS layout:** account-per-env; SCPs that may block OIDC STS
7. **IaC source of truth:** Terraform/CloudFormation for provider + roles vs
   console-only drift

**Precedence:** Follow repo/org. Flag org-wide trust without repo bind, prod
roles assumable from any branch/fork path, or dual AKIA+OIDC without a retire plan.

## Workflow

### 1. Scope and job-class design

1. Record AWS account IDs, regions, GitHub org/repo, env, ownership.
2. List AWS-calling workflows; **one IAM role per job class and environment**
   (prod deploy ≠ PR plan/read-only ≠ break-glass).
3. Inventory residual `AWS_ACCESS_KEY_*` secrets — delete after OIDC works.

### 2. IAM OIDC provider (once per account, usually)

1. Provider URL `https://token.actions.githubusercontent.com` with current
   **thumbprint(s)** per AWS/GitHub docs (re-check on cert rotation).
2. Audience typically `sts.amazonaws.com` (must match trust `aud`).
3. Prefer one account-level provider reused by many roles; document owner.

### 3. Trust policy — the real trust boundary

1. Principal: `Federated` → the account’s GitHub OIDC provider ARN.
2. Action: `sts:AssumeRoleWithWebIdentity` only.
3. **Required conditions:**
   - `token.actions.githubusercontent.com:aud` = `sts.amazonaws.com` (or your
     explicit audience)
   - `token.actions.githubusercontent.com:sub` bound to specific
     `repo:ORG/REPO:...` — never account/org-wide without review
4. Prefer **GitHub Environment** subjects for prod
   (`repo:ORG/REPO:environment:production`) plus environment protection.
5. Or bind `ref:refs/heads/main` / release tags; avoid bare
   `repo:ORG/REPO:*` on prod.
6. Reject missing `sub`, `StringLike` to `repo:ORG/*`, and any-ref trust on
   high-privilege roles. Fork PRs must not satisfy prod trust.

### 4. Role permissions and workflow wire-up

1. Least-privilege actions/resources only — not `AdministratorAccess`.
2. Constrain `iam:PassRole` if the job deploys compute (`aws-iam-least-privilege`).
3. Separate plan (read) vs apply (write) when using Terraform/CDK.
4. Job needs `permissions: { contents: read, id-token: write }`.
5. Use `aws-actions/configure-aws-credentials` with `role-to-assume` and
   `aws-region`; no static keys in `env:`.
6. Gate deploy with `environment:` and `if:` on trusted events/refs.
7. Prove exchange in **non-prod**; confirm caller identity is the role.
8. Confirm fork / untrusted `pull_request` cannot assume prod roles
   (`secrets-in-ci-pipelines`).
9. Remove AKIA secrets; rotate if exposed. Encode provider + roles in IaC
   (`terraform-security-basics`, `code-quality-standards`). Re-audit trust on
   repo renames and new deploy workflows.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GHA OIDC provider, role trust sub/aud, configure-aws-credentials | **This skill** | — |
| Role permission statements, PassRole, analyzer findings | `aws-iam-least-privilege` | this (trust/OIDC) |
| Pipeline stages, cache, artifacts, general GHA structure | `ci-cd-pipeline-patterns` | this for AWS identity |
| Fork PRs, secret masking, residual key hygiene in CI | `secrets-in-ci-pipelines` | this (AWS OIDC detail) |
| AKIA leak IR / rotation program | `secrets-management-hygiene` | this + IAM |
| GitHub OIDC → GCP | `gcp-workload-identity-federation` | — |
| Terraform defining OIDC provider/roles | `terraform-security-basics` | this + CQS |

- **`aws-iam-least-privilege`:** what the role can do after assume — not GHA claim binding.
- **`secrets-in-ci-pipelines`:** CI credential model/leaks; hand here for AWS trust and provider setup.
- **`ci-cd-pipeline-patterns`:** when/how jobs run; this skill owns the AWS federation path.

## Output Checklist

- [ ] Authorization and account/org/repo/env scope recorded (owned only)
- [ ] Job classes mapped to dedicated roles (prod ≠ PR/plan)
- [ ] IAM OIDC provider present; audience documented
- [ ] Trust: `aud` set; `sub` binds specific repo (+ environment or ref for prod)
- [ ] No org-wide / `repo:ORG/*` / unbound-ref trust on privileged deploy roles
- [ ] Role permissions least privilege — not admin by default
- [ ] Workflow has `id-token: write` and uses configure-aws-credentials (or STS equivalent)
- [ ] Deploy gated by GitHub environment and/or protected ref conditions
- [ ] Fork/untrusted PR cannot assume prod role or obtain prod secrets
- [ ] Residual AKIA secrets removed after OIDC proof; rotated if exposed
- [ ] Non-prod proof then prod window; tokens/ARNs redacted in logs
- [ ] Follow-ups: permissions → `aws-iam-least-privilege`; CI → `secrets-in-ci-pipelines`
- [ ] IaC + `code-quality-standards`; exceptions have owner + expiry

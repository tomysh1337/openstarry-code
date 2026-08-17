---
name: cloudformation-iam-guardrails
description: >
  CloudFormation IAM guardrails for owned AWS accounts: roles and policies in
  templates, CAPABILITY_IAM / CAPABILITY_NAMED_IAM deploy gates, permissions
  boundaries, CloudFormation service roles, stack policies, and least-privilege
  policies. Use when hardening or reviewing CloudFormation YAML/JSON that creates
  IAM, pipelines that pass capabilities, or stack-update protection for critical
  resources — not for abusing third-party AWS accounts.
---

# CloudFormation IAM Guardrails

Harden **CloudFormation** so templates mint only necessary IAM, deploy paths
cannot silently create privileged roles, service roles stay least-privilege, and
stack updates cannot replace critical identity resources without policy.
**Org-owned or explicitly authorized AWS accounts only.**

## Scope And Authorization

- **In scope:** Templates (YAML/JSON), nested stacks, change sets, stack policies,
  CloudFormation **service roles**, workload execution roles (Lambda, ECS, EC2
  profiles, CodeBuild, etc.), deploy pipeline identities, and `CAPABILITY_*` flags
  in **accounts you own** or are contracted to assess.
- **Out of scope:** Foreign-account apply/assume; found-key privilege creation;
  destructive deletes on shared prod without approval.
- Prefer non-prod stacks and change sets. Gate named IAM, admin policies, and
  stack-policy overrides behind change control. Redact secrets in reports.
- Account-wide IAM → `aws-iam-least-privilege`. Secrets → `secrets-management-hygiene`.
  Terraform → `terraform-security-basics`. Module quality → `code-quality-standards`.

## When To Use

- Templates declare `AWS::IAM::Role`, `Policy`, `ManagedPolicy`, `User`, instance
  profiles, or `PermissionsBoundary`
- Deploy needs **`CAPABILITY_IAM`** / **`CAPABILITY_NAMED_IAM`** (or CDK/SAM)
- CFN **service role** is admin / `*` / can pass any role; created roles lack
  boundaries; trust broad; `iam:PassRole` unconstrained
- Need **stack policies** to block accidental `Update:Replace` / `Delete` on IAM,
  KMS, logging, or data resources
- Mentions: CloudFormation IAM, CAPABILITY_IAM, stack policy, CFN service role,
  permissions boundary in template, least-privilege CFN roles

Do **not** use as primary for: general IAM → `aws-iam-least-privilege`; Terraform →
`terraform-security-basics`; Lambda-only → `aws-lambda-least-privilege`; secret
rotation → `secrets-management-hygiene`.

## Workflow
### 1. Inventory stacks and IAM in templates

Record account, region, env, stack names, authorization. Grep for `AWS::IAM::`,
`AssumeRolePolicyDocument`, `ManagedPolicyArns`, `PermissionsBoundary`, nested
stacks. Map **deploy principal** vs **CFN service role** vs **workload roles**.

```bash
# Owned account only
aws sts get-caller-identity
aws cloudformation get-template --stack-name STACK --query 'TemplateBody' --output text
aws cloudformation describe-stack-resources --stack-name STACK \
  --query "StackResources[?ResourceType=='AWS::IAM::Role']"
```

Output: inventory (stacks, IAM logical IDs, deploy identity) — **no secrets**.
### 2. Least-privilege roles in the template

| Check | Expectation |
| --- | --- |
| Trust | Specific service/account/OIDC — not `Principal:"*"`; source account/ARN conditions when available |
| Actions / resources | Enumerated actions; ARN-scoped; no daily `AdministratorAccess` |
| `iam:PassRole` | Intended role ARNs only + `iam:PassedToService` where applicable |
| Managed / scope | Minimal job-scoped policies; one role per workload family; prefer CFN-generated names |

Reject bare `"Action":"*"`, `"Resource":"*"` without ticket + expiry.
### 3. Permissions boundaries

When stacks **create** roles/users: set `PermissionsBoundary` on every minted
principal; boundary blocks boundary removal, unrestricted IAM mutate, and admin
attach; creator needs `iam:CreateRole` **conditioned** on `iam:PermissionsBoundary`
equaling the org boundary ARN; pass boundary ARN as a reviewed parameter.
### 4. CAPABILITY_IAM and CAPABILITY_NAMED_IAM

- **`CAPABILITY_IAM`**: IAM with generated names; **`CAPABILITY_NAMED_IAM`**: custom
  physical names. Flags are **acknowledgment**, not a security control — still
  review every IAM resource. CI passes capabilities only after change-set review of
  expected IAM diffs; fail pipelines that always inject both flags. Prefer
  `create-change-set` → review → `execute-change-set`. Audit CDK/SAM auto-capabilities.
### 5. Service role vs deploy principal vs workload

| Principal | Duty |
| --- | --- |
| Deploy (user/CI OIDC) | `cloudformation:*` on target stacks + `iam:PassRole` **only** to CFN service role |
| CFN service role | Mutate declared resource types only — **not** account admin |
| Workload roles | Runtime only; never used to deploy the stack |

Scope the service role to required services/ARNs; constrain `iam:PassRole` to
template execution roles. Never reuse the service role as app runtime.
### 6. Stack policies, retain, and verify

Deny `Update:Replace` / `Delete` on critical logical IDs (IAM, KMS, log buckets,
databases) unless break-glass. Use `DeletionPolicy` / `UpdateReplacePolicy: Retain`
where delete is catastrophic. Restrict stack-policy-during-update overrides; audit
in CloudTrail. Change set in non-prod; after apply check trust, policies, boundary;
Access Analyzer on new roles; exceptions (owner + expiry). Apply
`code-quality-standards` when editing templates.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CFN templates, CAPABILITY_*, service role, stack policy, IAM in stacks | **This skill** | — |
| Account-wide IAM / trust / PassRole / Analyzer | `aws-iam-least-privilege` | this skill for CFN delivery |
| Terraform IAM and state | `terraform-security-basics` | this skill if dual IaC with CFN |
| Secret parameters, AKIA, rotation | `secrets-management-hygiene` | this skill for NoEcho / dynamic refs |
| Lambda execution role depth | `aws-lambda-least-privilege` | this skill when CFN-minted |
| Template structure / tests / lint | `code-quality-standards` | this skill for IAM intent |

## Output Checklist

- [ ] Authorization and account/region/stack scope recorded (owned AWS only)
- [ ] Templates inventoried: IAM, nested stacks, PassRole, boundaries
- [ ] Trust specific; no unnecessary `*` / Admin on workload roles
- [ ] Permissions boundaries set/enforced when stack mints IAM
- [ ] CAPABILITY_IAM / CAPABILITY_NAMED_IAM only after change-set review
- [ ] CFN service role least-privilege; deploy PassRole limited to that role
- [ ] Workload roles separated from deploy/service roles
- [ ] Stack policy + Retain protect IAM/crypto/data resources
- [ ] No plaintext secrets in parameters; NoEcho / SSM / Secrets Manager refs
- [ ] Post-apply verify + Analyzer; exceptions have owner + expiry
- [ ] Handed off to related skills when applicable

## Rules

- **Owned or authorized AWS accounts only.** Capabilities acknowledge IAM creation —
  they do not make broad policies safe. Temporary admin needs ticket and expiry.
  Prefer change sets over blind deploy. Compromised CFN service role ≠ account admin.
  Redact secrets from reports.

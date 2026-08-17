---
name: aws-iam-least-privilege
description: >
  AWS IAM least-privilege review methodology for owned cloud accounts: inventory
  principals, shrink Action/Resource wildcards, fix trust policies and
  privilege-escalation paths, prefer roles/OIDC over long-lived keys. Use when
  reviewing IAM policies, roles, users, permission boundaries, Access Analyzer
  findings, or overly broad AdministratorAccess attachments — not for abusing
  third-party AWS accounts.
---

# AWS IAM Least Privilege

Review and harden **AWS IAM** so human users, service roles, and automation
principals hold only the permissions they need. Defensive methodology for
**org-owned or explicitly authorized AWS accounts** — not credential abuse or
lateral movement into accounts outside scope.

## Scope And Authorization

- **In scope:** AWS accounts, Organizations, and IAM resources **you own** or
  are contracted to assess; read-only inventory (`Get*`, `List*`, Access
  Analyzer); controlled policy changes with change windows and rollback.
- **Out of scope:** Using found access keys against accounts you do not own;
  creating backdoor users/roles in foreign accounts; disabling logging to hide
  activity; privilege escalation demos on shared prod without approval.
- Prefer **non-production accounts** or sandbox OU for experimental policy
  rewrites. Gate `Delete*`, broad `Put*`, and identity-provider changes behind
  explicit approval.
- Treat access keys, session tokens, assume-role outputs, and CloudTrail
  excerpts as sensitive — redact account IDs/ARNs per org policy when required;
  never paste live secrets into tickets or chat.
- Pair secret lifecycle (AKIA keys, OIDC, break-glass passwords) with
  `secrets-management-hygiene`. IaC-defined IAM → also use
  `terraform-security-basics`. Implementation quality on modules/scripts →
  `code-quality-standards`.

## Use When

- Reviewing IAM **users, groups, roles, instance/task profiles, permission
  boundaries**, or Organizations SCPs
- Policies contain `"Action": "*"` / `"Resource": "*"` or managed
  `AdministratorAccess` on daily human/CI principals
- Trust policies allow broad `sts:AssumeRole` (`Principal: "*"` without hard
  conditions, untrusted accounts, missing `ExternalId` / MFA / source ARN)
- Access Analyzer, IAM Access Advisor, or CloudTrail show unused or excessive
  permissions
- Migrating long-lived **access keys** to roles, SSO, or CI **OIDC** federation
- Hardening service roles for EC2, Lambda, ECS, CodeBuild, GitHub Actions, etc.
- User mentions: IAM least privilege, overly permissive policy, privilege
  escalation, passrole, trust policy, permission boundary, Access Analyzer

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| S3 Block Public Access, bucket encryption, public bucket policy | `aws-s3-bucket-hardening` |
| Secret storage, rotation, leaked AKIA in git | `secrets-management-hygiene` |
| Terraform/OpenTofu IAM modules, state, CI apply identity | `terraform-security-basics` |
| App code reliability around AWS SDK usage | `code-quality-standards` |
| Org-wide secret process beyond IAM keys | `secrets-management-hygiene` |
| Design workshop / STRIDE register | `threat-modeling-stride` |

## Threat Themes (defensive)

| Theme | Weak outcome | Hardening direction |
| --- | --- | --- |
| Wildcard actions | Any API in account/region | Enumerate needed actions; service prefixes only |
| Wildcard resources | Touch any bucket/queue/key | ARN prefixes, tags, conditions |
| Admin everywhere | Single compromise = full account | Job-function roles; break-glass separate |
| Broad trust | Anyone can assume role | Account/OIDC subject conditions; MFA |
| Long-lived keys | Laptop/CI leak becomes standing access | SSO/OIDC roles; rotate/delete keys |
| Privilege escalation | `iam:PassRole` + create services → admin | Constrain PassRole ARNs; boundaries |
| Missing boundaries | Dev role can attach Admin policy | Permission boundaries on creators |
| No monitoring | Silent policy creep | Access Analyzer, Access Advisor, CloudTrail |

## Workflow

### 1. Confirm scope and inventory principals

1. Record account ID(s), OU, environment (dev/stage/prod), and authorization.
2. List principals: IAM users, roles, groups, IdP/SSO permission sets, service-linked roles (note but rarely edit SLR definitions).
3. Map **who applies infra** (human console, SSO, CI OIDC role, Terraform apply role).
4. Flag shared “god” roles, unused users, and access keys older than org policy.

```bash
# Owned account only — read-only inventory sketches
aws sts get-caller-identity
aws iam list-users --output table
aws iam list-roles --query 'Roles[].RoleName' --output text
aws iam list-access-keys --user-name SOME_USER
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d > credential-report.csv
```

Output: inventory of principals and apply paths — **no secret values**.

### 2. Collect attached and effective policy

For each high-risk principal (humans with console, CI apply, break-glass, data
plane roles):

```bash
aws iam list-attached-user-policies --user-name SOME_USER
aws iam list-user-policies --user-name SOME_USER
aws iam list-attached-role-policies --role-name SOME_ROLE
aws iam list-role-policies --role-name SOME_ROLE
aws iam get-role --role-name SOME_ROLE   # includes AssumeRolePolicyDocument
aws iam get-policy-version \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --version-id v1
# Customer managed:
aws iam get-policy --policy-arn arn:aws:iam::ACCOUNT:policy/AppPolicy
aws iam get-policy-version --policy-arn arn:aws:iam::ACCOUNT:policy/AppPolicy --version-id vN
```

Build a matrix: principal → managed/inline policies → dangerous statements
(`*`, admin, `iam:*`, `sts:AssumeRole` on `*`, `iam:PassRole` on `*`).

### 3. Flag high-risk policy patterns

| Pattern | Why it matters |
| --- | --- |
| `"Action":"*"` + `"Resource":"*"` | Full account API access (subject to SCP) |
| Managed `AdministratorAccess` / `PowerUserAccess` on daily roles | Blast radius |
| `iam:*` or `iam:CreateUser`/`Attach*`/`Put*` without boundary | Self-escalation |
| `iam:PassRole` on `*` + `ec2:RunInstances` / `lambda:CreateFunction` / `ecs:RunTask` | Classic escalate-to-privileged-role |
| `sts:AssumeRole` resource `*` | Assume any role that trusts principal |
| Trust `Principal:"*"` without conditions | Public assume (critical if usable) |
| Trust foreign account without contract | Cross-account lateral path |
| Missing `aws:SourceAccount` / `aws:SourceArn` on service principals | Confused deputy |
| KMS `kms:*` on `*` | Decrypt/re-encrypt broadly |
| S3 `s3:*` on `*` | All buckets (pair with S3 skill for bucket side) |

**Privilege-escalation review (defensive):** for roles that can mutate IAM or
pass roles, verify they **cannot** attach admin policies to themselves or pass
a more privileged role than intended. Prefer **permission boundaries** on any
principal that creates roles/users.

### 4. Use AWS analysis helpers (owned account)

```bash
# Access Analyzer — external access findings
aws accessanalyzer list-analyzers
aws accessanalyzer list-findings --analyzer-arn arn:aws:access-analyzer:REGION:ACCOUNT:analyzer/NAME

# Last-used data (shrink unused permissions)
aws iam get-role --role-name SOME_ROLE --query 'Role.RoleLastUsed'
aws iam generate-service-last-accessed-details --arn arn:aws:iam::ACCOUNT:role/SOME_ROLE
# then poll get-service-last-accessed-details with returned JobId

# Simulate (optional, authorized)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/SOME_ROLE \
  --action-names s3:GetObject ec2:TerminateInstances \
  --resource-arns arn:aws:s3:::example-bucket/*
```

Prefer evidence from Access Advisor + CloudTrail over guesswork when trimming.

### 5. Redesign toward least privilege

1. **Split roles** by job: read-only, deploy, break-glass admin (MFA + short
   session + audited).
2. **Enumerate actions** from runtime needs and CloudTrail; start narrow, widen
   with AccessDenied — never start at `*`.
3. **Scope resources** to ARNs or patterns (`arn:aws:s3:::app-prod-*/*`).
4. Add **conditions**: `aws:RequestedRegion`, `aws:ResourceTag/`,
   `aws:PrincipalTag/`, `s3:prefix`, MFA (`aws:MultiFactorAuthPresent`),
   `sts:ExternalId`, OIDC `sub`/`aud`.
5. Constrain **`iam:PassRole`** to specific role ARNs and, where supported,
   `iam:PassedToService`.
6. Put **permission boundaries** on developer/CI creators.
7. Replace IAM **users + access keys** with **SSO permission sets** or
   **workload identity (OIDC)** for CI.

### 6. Trust policy hardening

Review every role trust document:

| Check | Expectation |
| --- | --- |
| Principal | Specific AWS account, service, or OIDC provider — not `*` |
| Service roles | `Service: lambda.amazonaws.com` etc., plus source ARN/account conditions when available |
| Cross-account | Explicit account IDs; `ExternalId` or org-id conditions as appropriate |
| OIDC (e.g. GitHub) | Bound `sub` (repo + ref/environment), correct `aud` |
| Humans | SSO / IdP; MFA conditions on sensitive roles |
| Session | Reasonable max session duration |

### 7. Keys, SSO, and secrets

1. Inventory access keys; delete unused; rotate compromised (`secrets-management-hygiene`).
2. Prefer IAM Identity Center (SSO) over long-lived IAM users.
3. CI: GitHub/GitLab OIDC → `sts:AssumeRoleWithWebIdentity` with subject claims;
   no static AKIA on all branches; deny secrets to fork PRs.
4. Never commit keys in Terraform/tfvars or app config — hand to
   `secrets-management-hygiene` + `terraform-security-basics` when IaC is the
   delivery path.

### 8. Implement, verify, document

1. Change policies in **dev** first; use policy simulator and canary deploys.
2. Confirm apps still work; watch CloudTrail `AccessDenied`.
3. Re-run Access Analyzer; confirm unused admin attachments removed.
4. Document residual exceptions with owner and expiry.
5. Module/script changes follow `code-quality-standards`.

## Concrete AWS Examples

### Bad — admin on a daily app/CI role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

Or attachment of `arn:aws:iam::aws:policy/AdministratorAccess` to
`github-actions-deploy` / `app-ec2-role`.

### Good — narrowed application role (S3 prefix + SSM + logs)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListOwnBucketPrefix",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::app-prod-data",
      "Condition": {
        "StringLike": { "s3:prefix": ["app-data/*"] }
      }
    },
    {
      "Sid": "RWOwnObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::app-prod-data/app-data/*"
    },
    {
      "Sid": "ReadAppSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:eu-west-1:111122223333:secret:app/prod/*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-west-1:111122223333:log-group:/aws/lambda/app-prod*"
    }
  ]
}
```

### Good — constrained PassRole (Lambda deploy role)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DeployLambda",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:eu-west-1:111122223333:function:app-prod-*"
    },
    {
      "Sid": "PassOnlyAppLambdaRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::111122223333:role/app-prod-lambda-exec",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
```

### Bad vs good — role trust (confused deputy / broad OIDC)

**Bad** — GitHub OIDC with no subject bind (any repo in the org may assume):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

**Good** — bind repo and environment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:my-org/my-app:environment:production",
            "repo:my-org/my-app:ref:refs/heads/main"
          ]
        }
      }
    }
  ]
}
```

### Good — service principal with source conditions (S3 → Lambda sketch)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "s3.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "111122223333"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:::app-prod-data"
        }
      }
    }
  ]
}
```

### Permission boundary sketch (developers may create roles only under boundary)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBoundedServices",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "logs:*",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyBoundaryEscape",
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePermissionsBoundary",
        "iam:PutRolePermissionsBoundary"
      ],
      "Resource": "*"
    }
  ]
}
```

(Boundary design is org-specific — adjust deny/allow sets carefully; test in
sandbox. Creators need `iam:CreateRole` with requirement that
`PermissionsBoundary` equals the boundary ARN — express that on the **creator**
policy with conditions.)

### CLI: replace access key with role usage (ops hygiene)

```bash
# List and delete unused keys for an IAM user (owned account; after SSO migration)
aws iam list-access-keys --user-name legacy-deploy
aws iam delete-access-key --user-name legacy-deploy --access-key-id AKIA...

# Assume a role interactively (example — do not log credentials)
aws sts assume-role \
  --role-arn arn:aws:iam::111122223333:role/break-glass-admin \
  --role-session-name $(whoami)-$(date +%Y%m%d) \
  --serial-number arn:aws:iam::111122223333:mfa/SOME_USER \
  --token-code 123456 \
  --duration-seconds 900
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| IAM least privilege, trust policies, PassRole, Access Analyzer | **This skill** | — |
| Public S3, encryption, bucket policies, BPA | `aws-s3-bucket-hardening` | this skill for principals that touch S3 |
| AKIA/OIDC secret lifecycle, rotation after leak | `secrets-management-hygiene` | this skill for IAM principal design |
| Terraform IAM modules, state backend roles, apply identity | `terraform-security-basics` | this skill for policy semantics |
| Implementing modules, policy generators, tests | `code-quality-standards` | this skill for control intent |
| Org secret inventory beyond IAM | `secrets-management-hygiene` | — |
| Design-time threat register | `threat-modeling-stride` | this skill for IAM mitigations |

### Required helpers (when applicable)

- **`secrets-management-hygiene`:** access keys, session material, break-glass
  passwords, OIDC client secrets — inventory, rotation, no VCS, leak IR.
- **`terraform-security-basics`:** when IAM is defined or applied via Terraform/
  OpenTofu (state, CI OIDC role, module wildcards).
- **`code-quality-standards`:** baseline when writing/refactoring policy JSON/HCL
  generators, validation, and automated tests for IAM changes.

## Checklist

- [ ] Authorization and account IDs recorded; only owned/in-scope accounts
- [ ] Principals inventoried (users, roles, SSO sets, CI/OIDC apply roles)
- [ ] Credential report reviewed; unused users/keys flagged
- [ ] Admin / `Action:*` / `Resource:*` on daily principals eliminated or justified
- [ ] Trust policies: no unbounded `*`; OIDC `sub`/`aud` bound; cross-account explicit
- [ ] `iam:PassRole` constrained to specific roles and services
- [ ] Privilege-escalation paths (IAM mutate + PassRole + create compute) reviewed
- [ ] Permission boundaries on role/user creators where org uses them
- [ ] Access Analyzer / Access Advisor / CloudTrail used to evidence unused rights
- [ ] Long-lived access keys minimized; SSO/OIDC preferred
- [ ] Secrets/keys handled via `secrets-management-hygiene` (rotate before wide leak writeups)
- [ ] IaC IAM paths reviewed with `terraform-security-basics` when applicable
- [ ] Policy/module changes meet `code-quality-standards`
- [ ] Residual exceptions documented with owner and review date
- [ ] Changes verified in non-prod then prod change window; AccessDenied monitored

## Rules

- **Owned or authorized AWS accounts only** — no third-party account abuse.
- Least privilege is iterative: measure with Access Advisor and logs; do not
  ship `*` “temporarily” without expiry and ticket.
- Prefer **roles and federation** over long-lived IAM user keys.
- Prove **permission excess** with policy documents and analyzer findings — not
  destructive actions on shared production.
- Break-glass admin must be **MFA-backed, short-lived, and audited** — not the
  default console role.
- Redact secrets and avoid committing live account credentials in examples.
---

# Note

This skill owns **AWS IAM least-privilege review and redesign**: principal
inventory, policy and trust hardening, PassRole/escalation review, and
federation over static keys. Pair with `aws-s3-bucket-hardening` for bucket
controls, `secrets-management-hygiene` for credential lifecycle,
`terraform-security-basics` for IaC delivery, and `code-quality-standards` for
safe implementation of policy-as-code.

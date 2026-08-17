---
name: aws-lambda-least-privilege
description: >
  AWS Lambda least-privilege hardening for owned accounts: execution-role IAM,
  function resource policies, env-var secrets, VPC ENI/SG posture, over-broad
  Action/Resource wildcards, and IAM Access Analyzer findings. Use when reviewing
  Lambda roles, lambda:InvokeFunction permissions, plaintext secrets in
  environment variables, or overly permissive AWSLambda* managed policies —
  not for abusing third-party AWS accounts.
---

# AWS Lambda Least Privilege
Harden **AWS Lambda** so each function uses the smallest useful identity, is
invokable only by intended principals, and does not keep long-lived secrets in
environment variables. **Org-owned or explicitly authorized AWS accounts only.**

## Scope And Authorization
- **In scope:** Functions, aliases/versions, execution roles, resource-based
  policies, event-source mappings, Function URLs, related VPC/SG/KMS you own;
  read-only inventory and Access Analyzer; controlled policy changes with rollback.
- **Out of scope:** Foreign-account invoke/modify; backdoor deploys with found
  keys; destructive mass deletes on shared prod without approval; public-invoke
  demos that process real PII.
- Prefer non-prod experiments. Gate role swaps, public resource-policy grants,
  and SG opens behind change control. Redact env values, tokens, and customer data.
- Secret **lifecycle** (rotation, vault, leak IR) → `secrets-management-hygiene`.
  Account-wide IAM → `aws-iam-least-privilege`. IaC → `terraform-security-basics`
  + `code-quality-standards`.

## When To Use
- Execution roles with `"Action":"*"` / `"Resource":"*"`, admin managed policies,
  or one shared “god” role across unrelated functions
- Resource policies allow `Principal:"*"`, unknown accounts, or service invoke
  without `aws:SourceAccount` / `aws:SourceArn`
- Passwords, API keys, or tokens in **environment variables** or deployment zips
- VPC-attached functions with open SGs or unnecessary public egress
- Access Analyzer, Access Advisor, or CloudTrail show unused/excessive rights
- Mentions: Lambda least privilege, execution role, resource policy,
  `lambda:InvokeFunction`, env secrets, Lambda VPC, over-broad `*`, Access Analyzer
Do **not** use as primary for: account-wide IAM → `aws-iam-least-privilege`;
secret rotation/vault → `secrets-management-hygiene`; Terraform/SAM/CDK →
`terraform-security-basics`; handler quality → `code-quality-standards`;
SSRF from code → `cloud-metadata-ssrf-defenses`; S3 store side →
`aws-s3-bucket-hardening`.

## Workflow
### 1. Inventory functions and trust boundaries
Record account, region(s), env, and authorization. List functions (runtime, VPC,
layers, aliases, triggers: API GW, S3, SQS, EventBridge, SNS, ALB, Step Functions,
cross-account). Map **execution role** vs **invoke principals** vs **deploy/CI**;
flag shared roles across unrelated workloads.
```bash
# Owned account only
aws sts get-caller-identity
aws lambda list-functions --query 'Functions[].FunctionName' --output text
aws lambda get-function-configuration --function-name FN
aws lambda get-policy --function-name FN
aws lambda get-function-url-config --function-name FN
```
Output: inventory (name, role ARN, triggers, VPC) — **no secret values**.
### 2. Execution-role least privilege
Trust should be `lambda.amazonaws.com` (document multi-service exceptions). Flag
`*`, `iam:*`, unbounded `s3:*`/`dynamodb:*`/`kms:*`/`secretsmanager:*`, and admin
managed policies. Scope actions and ARNs to own resources (log groups,
buckets/prefixes, tables, queues, specific secret ARNs and KMS keys). Prefer one
role per function (or tight family). Trim with Access Advisor and CloudTrail —
start narrow, widen on `AccessDenied`; never start at `*`.
```bash
aws iam get-role --role-name ROLE
aws iam list-attached-role-policies --role-name ROLE
aws iam list-role-policies --role-name ROLE
aws iam generate-service-last-accessed-details --arn arn:aws:iam::ACCOUNT:role/ROLE
```
### 3. Resource-based policy (who may invoke)
| Check | Expectation |
| --- | --- |
| Principal | Specific service/account/role — not anonymous `*` unless deliberate public API |
| Service invoke | `aws:SourceAccount` + `aws:SourceArn` (confused-deputy defense) |
| Cross-account / Function URL | Explicit accounts; URL auth not `NONE` unless product-public; CORS minimal |
| Qualifiers | Prefer alias ARNs for production grants |
### 4. Environment secrets
Scan env vars and packages for credentials. Move to Secrets Manager or SSM
SecureString; grant only `GetSecretValue`/`GetParameter` (+ scoped `kms:Decrypt`)
on those ARNs. Never log secret values. On exposure: **rotate first** via
`secrets-management-hygiene`, then strip plaintext from config.
### 5. VPC, PassRole, and side surfaces
Private subnets; SGs allow only required egress to known peers — no open sensitive
ports from `0.0.0.0/0`. Prefer VPC endpoints for private AWS API use. Review layers,
EFS mounts, and invoke fan-out for privilege chaining. Deploy identities:
`iam:PassRole` only to intended execution role ARNs with
`iam:PassedToService=lambda.amazonaws.com`.
### 6. Access Analyzer and verify
```bash
aws accessanalyzer list-findings --analyzer-arn ANALYZER_ARN \
  --filter '{"resourceType":{"eq":["AWS::Lambda::Function","AWS::IAM::Role"]}}'
```
Fix external-access findings; canary in non-prod; smoke-test triggers; document
exceptions (owner + expiry). Apply `code-quality-standards` when changing IaC.

## Routing
| Situation | Primary | Helper |
| --- | --- | --- |
| Lambda role, resource policy, env secrets, VPC for functions | **This skill** | — |
| Account-wide IAM / PassRole / SSO / CI OIDC | `aws-iam-least-privilege` | this skill for function surfaces |
| Secret storage, rotation, leak IR | `secrets-management-hygiene` | this skill for env/role wiring |
| Terraform/SAM/CDK delivery | `terraform-security-basics` | this skill for control intent |
| Handler/module code quality | `code-quality-standards` | this skill for IAM requirements |
| S3 trigger bucket / SSRF from code | `aws-s3-bucket-hardening` / `cloud-metadata-ssrf-defenses` | this skill for role blast radius |
**Required hand-off:** env/package secrets and rotation always through
`secrets-management-hygiene`. This skill removes plaintext config and grants
least-privilege **reads** on secret ARNs only.

## Output Checklist
- [ ] Authorization and account/region scope recorded (owned AWS only)
- [ ] Functions inventoried: role, triggers, VPC, URLs/aliases (no secrets)
- [ ] Execution role: no unnecessary `*`/admin; ARN-scoped; trust is `lambda.amazonaws.com`
- [ ] Resource policy: no unintended public/cross-account invoke; source conditions set
- [ ] Function URL auth/CORS reviewed if present
- [ ] No long-lived secrets in env/package; SM/SSM + scoped KMS decrypt
- [ ] Secret findings handed to `secrets-management-hygiene` (rotate if exposed)
- [ ] VPC SG/subnet minimized when VPC-enabled; deploy `PassRole` constrained
- [ ] Access Analyzer / Access Advisor / CloudTrail used as evidence
- [ ] Verified in non-prod; residual exceptions have owner + review date
- [ ] IaC/code paths use `terraform-security-basics` / `code-quality-standards` when applicable

## Rules
- **Owned or authorized AWS accounts only.** Least privilege is iterative;
  temporary `*` needs ticket and expiry. Prefer secrets managers over env vars;
  redact all examples. Prove excess rights with policies and analyzer findings —
  not destructive production invokes. A compromised Lambda role must not equal
  account admin.

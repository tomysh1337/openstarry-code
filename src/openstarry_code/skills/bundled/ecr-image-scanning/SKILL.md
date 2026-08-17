---
name: ecr-image-scanning
description: >
  Enable and operate Amazon ECR image vulnerability scanning for owned AWS
  accounts: basic vs enhanced (Inspector) scan, scan-on-push, registry and
  repository scan filters, finding triage, and CI/deploy gates on CRITICAL/HIGH.
  Use when reviewing ECR scan configuration, scanOnPush, Inspector enhanced
  scanning, describe-image-scan-findings, blocking deploys on CVE findings, or
  ECR registry scanning rules — not for abusing third-party registries.
---

# ECR Image Scanning

Configure and operate **Amazon ECR** vulnerability scanning so images are
scanned on push (or continuously under enhanced mode), findings are triaged by
severity, and **ship gates** fail closed. Prefer **enhanced scanning** (Amazon
Inspector). **Owned or explicitly authorized AWS accounts only.**

## When To Use

- Enable or audit **scan-on-push**, repo scan filters, or registry **enhanced
  scanning** (Inspector) for ECR
- Read/triage **image scan findings** (CVE, package, severity) via CLI/API
- Wire **CI/deploy gates** that wait for scan complete and block on severity
- Mentions: ECR scanning, `scanOnPush`, `BASIC` vs `ENHANCED`, Inspector ECR,
  `start-image-scan`, `describe-image-scan-findings`, image CVE policy in ECR

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage / non-root / secrets in layers | `dockerfile-best-practices` |
| Cosign / Sigstore image signing and admission | `container-image-signing` |
| SBOM generate/publish / fail-if-missing SBOM | `sbom-ci-enforcement` |
| Broad SCA / supply-chain program | `sbom-and-supply-chain` |
| ECS task roles / public tasks / privileged | `aws-ecs-task-security` |
| Account IAM redesign / PassRole | `aws-iam-least-privilege` |
| Secrets / pipeline OIDC / script quality | `secrets-management-hygiene` / `ci-cd-pipeline-patterns` / `code-quality-standards` |

## Workflow

### 1. Scope and inventory

Record account, region, registry, repos, env, and authorization. Note scan type
(`BASIC` / `ENHANCED`), scan-on-push, and digests that ship.

```bash
# Owned account only
aws sts get-caller-identity
aws ecr get-registry-scanning-configuration
aws ecr describe-repositories --query 'repositories[].{name:repositoryName,scan:imageScanningConfiguration}'
```

### 2. Choose scan mode and coverage

| Mode | Behavior | Prefer when |
| --- | --- | --- |
| **BASIC** | On-push or manual; package CVE results in ECR | Cost-sensitive / non-prod minimum |
| **ENHANCED** | Inspector continuous + registry filters | Prod and regulated paths |

Prefer **ENHANCED** for production. Enable **scan-on-push** (or enhanced filters)
for ship repos; scope filters (e.g. `prod/*`) to bound cost/noise. Evaluate
**immutable digests** that deploy — not floating tags alone.

### 3. IAM and least privilege

CI/scanners: `ecr:StartImageScan`, `ecr:DescribeImageScanFindings`,
`ecr:DescribeImages`, pull as needed — no broad admin. Registry config
(`PutRegistryScanningConfiguration`, repo update) stays separate from app task
roles. Deep IAM redesign → `aws-iam-least-privilege`.

### 4. Run and collect findings

Push by digest (or `start-image-scan` when basic/manual). Poll until
`scanStatus` is `COMPLETE` (or Inspector findings available). Export severity
counts, packages, CVE IDs, digest, fix versions. “No scan configured” ≠ “no CVEs.”

```bash
aws ecr describe-image-scan-findings \
  --repository-name REPO \
  --image-id imageDigest=sha256:DIGEST
```

### 5. Triage and remediate

| Finding class | Action |
| --- | --- |
| CRITICAL/HIGH in **runtime** packages | Patch base/deps, rebuild, re-push, re-scan |
| CVE only in **build** layers not shipped | Slim multi-stage (`dockerfile-best-practices`) |
| No fix available | Time-boxed exception: owner, expiry, compensations |
| Base image noise / false positive | Newer base digest; evidence-backed, time-boxed suppress |

Primary fix is rebuild, not permanent waive. Pair digests with
`container-image-signing`; SBOM gates with `sbom-ci-enforcement`.

### 6. Gate deploys and verify

CI: after push, **wait for scan** → fail on policy (e.g. any CRITICAL). Pipeline
topology → `ci-cd-pipeline-patterns`. Promote only digests that passed (+
signature/SBOM if required). Re-check config after drift; apply
`code-quality-standards` to automation. Enhanced: alert on new CVEs for running images.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ECR scan mode, scan-on-push, findings, CVE ship gates | **This skill** | — |
| Dockerfile / image contents hardening | `dockerfile-best-practices` | this post-push |
| Image sign/verify/admission | `container-image-signing` | this for CVE scan |
| SBOM CI presence gates | `sbom-ci-enforcement` | this for ECR CVE |
| ECS runtime IAM/network | `aws-ecs-task-security` | this for image CVEs |
| IAM policy depth | `aws-iam-least-privilege` | this for scan APIs |
| Secrets / pipeline OIDC / script quality | matching helper | this for scan config/gates |

## Output Checklist

- [ ] Authorization, account, region, registry/repos, and env recorded
- [ ] Scan mode known (`BASIC` vs `ENHANCED`); enhanced preferred for prod
- [ ] Scan-on-push or enhanced filters cover ship repos; digests identified
- [ ] Findings for deploy digests; severity counts and top CVEs listed
- [ ] CRITICAL/HIGH runtime issues: fix, rebuild, or time-boxed exception
- [ ] CI/deploy gate waits for scan and fails closed per policy
- [ ] IAM for scan/describe scoped; hand-offs (Dockerfile/signing/SBOM/ECS) noted
- [ ] Secrets redacted; residuals and owners documented

## Scope And Authorization

- **In scope:** ECR repos and registry scanning config, Inspector enhanced
  filters, image scan findings, and authorized CI gates in **owned or
  contracted** AWS accounts.
- **Out of scope:** Third-party registries without permission; using findings
  outside engagement scope; destructive mass re-tag/delete on shared prod
  without approval.
- Prefer non-prod for experimental config. Gate registry-wide enhanced scanning
  and fail-closed prod gates behind owner approval and rollback. Redact registry
  credentials. Do not infer authorization because a registry “looks like” a lab.
- Evidence: registry/repo config + **image digests** + finding payloads — not tags alone.


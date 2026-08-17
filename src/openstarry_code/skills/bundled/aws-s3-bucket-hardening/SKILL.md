---
name: aws-s3-bucket-hardening
description: >
  AWS S3 bucket hardening for owned cloud accounts: Block Public Access,
  encryption (SSE-S3/SSE-KMS), bucket policies and ACLs, versioning, logging,
  and TLS-only access. Use when reviewing public buckets, missing BPA,
  plaintext objects, overly broad Principal "*", or hardening app/logs/tfstate
  buckets — not for abusing third-party buckets.
---

# AWS S3 Bucket Hardening

Assess and harden **Amazon S3** buckets so data is not accidentally public,
is encrypted at rest, and is reachable only by intended principals over TLS.
Defensive methodology for **org-owned or explicitly authorized AWS accounts** —
not scanning or exploiting third-party buckets.

## Scope And Authorization

- **In scope:** S3 buckets and related KMS keys, CloudFront origins, and IAM
  principals in accounts **you own** or are contracted to harden; read-only
  `GetBucket*` / Access Analyzer; controlled config changes with rollback.
- **Out of scope:** Mass public-bucket hunting on the Internet; downloading or
  exfiltrating data from buckets you do not own; disabling logging to hide
  access; destructive mass deletes on shared prod without approval.
- Prefer **non-production** buckets for experimental policy rewrites. Gate
  public website exposure, ACL changes, and KMS key policy edits behind change
  control.
- Treat object contents, pre-signed URLs, access logs, and bucket policies that
  embed account structure as sensitive — redact in reports when policy requires.
- Never use discovered open buckets outside engagement scope. On accidental
  public exposure of **your** sensitive data: treat as incident — block public
  access, rotate exposed secrets (`secrets-management-hygiene`), audit
  CloudTrail/S3 access logs.
- IaC-defined buckets → pair with `terraform-security-basics`. Who can
  `s3:*` → pair with `aws-iam-least-privilege`. Implementation of modules →
  `code-quality-standards`.

## Use When

- Reviewing S3 **public access**, ACLs, or bucket policies (`Principal: "*"`)
- Missing or partial **S3 Block Public Access** (account or bucket)
- Encryption not enforced (no default SSE, clients can upload unencrypted)
- Hardening buckets for **app data, logs, backups, static sites, or tfstate**
- Access Analyzer or Trusted Advisor flags public/shared buckets
- Configuring **versioning, Object Lock, access logging, or TLS-only** policies
- User mentions: public S3, BPA, bucket policy, SSE-KMS, website hosting,
  presigned URL abuse surface, cross-account bucket access

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| IAM role/user least privilege (beyond S3 resource policy) | `aws-iam-least-privilege` |
| Secrets in objects or leaked keys in git | `secrets-management-hygiene` |
| Terraform S3 backend / `aws_s3_bucket*` modules | `terraform-security-basics` |
| App upload path / path traversal in keys | `path-traversal-lfi`, `upload-insecure-files` |
| Zip slip when extracting objects | `zip-slip-path-safety` |
| Code quality of apps writing to S3 | `code-quality-standards` |

## Control Baseline (what good looks like)

| Control | Hardened default | Notes |
| --- | --- | --- |
| Block Public Access | All **four** settings **true** (bucket + account) | Overrides accidental public ACL/policy |
| ACL | Private; prefer **Bucket owner enforced** (ACLs disabled) | Avoid `public-read` / `authenticated-read` |
| Bucket policy | Explicit principals only; no anonymous `*` unless intentional static site | Document exceptions |
| Encryption | Default SSE-S3 or SSE-KMS; deny unencrypted `PutObject` | CMK when org requires |
| TLS | Deny non-TLS (`aws:SecureTransport` = false) | Stops cleartext GETs/PUTs |
| Versioning | On for sensitive/state/backup buckets | Recovery after overwrite/delete |
| Logging / inventory | Access logging or CloudTrail data events for sensitive buckets | Forensics |
| Object ownership | Bucket owner enforced | Simplifies ACL foot-guns |
| Public website | Separate bucket/CloudFront; never mix with state/logs/PII | Explicit product intent only |

**Public by design** (marketing static assets) must be explicit, reviewed, and
never shared with tfstate, backups, or private app data.

## Workflow

### 1. Inventory buckets and data classification

1. Confirm account ID and authorization.
2. List buckets; note region, purpose (app, logs, state, public assets), owners.
3. Classify sensitivity: public OK / internal / confidential / regulated.
4. Map writers/readers: app roles, CI, CloudFront OAI/OAC, cross-account IDs.

```bash
# Owned account only
aws sts get-caller-identity
aws s3api list-buckets --query 'Buckets[].Name' --output text
aws s3api get-bucket-location --bucket EXAMPLE_BUCKET
```

Output: inventory table — bucket, purpose, sensitivity, owners — no object dumps.

### 2. Public access assessment

For each bucket:

```bash
BUCKET=example-app-prod-data

# Account-level BPA
aws s3control get-public-access-block --account-id 111122223333

# Bucket-level BPA
aws s3api get-public-access-block --bucket "$BUCKET"

# ACL and ownership
aws s3api get-bucket-acl --bucket "$BUCKET"
aws s3api get-bucket-ownership-controls --bucket "$BUCKET"

# Policy
aws s3api get-bucket-policy --bucket "$BUCKET" --query Policy --output text

# Effective public status helpers
aws s3api get-bucket-policy-status --bucket "$BUCKET"
aws s3api get-public-access-block --bucket "$BUCKET"
```

| Finding | Severity signal |
| --- | --- |
| Any BPA flag false + public policy/ACL | High/critical if sensitive data |
| `Principal:"*"` with `s3:GetObject` on private data | Critical exposure |
| Website hosting on data/state bucket | High mis-design |
| Public list (`s3:ListBucket` to `*`) | Enables object enumeration |
| Cross-account `*` or unknown accounts | Review immediately |

Access Analyzer:

```bash
aws accessanalyzer list-findings --analyzer-arn arn:aws:access-analyzer:REGION:ACCOUNT:analyzer/NAME \
  --filter '{"resourceType":{"eq":["AWS::S3::Bucket"]}}'
```

### 3. Encryption assessment

```bash
aws s3api get-bucket-encryption --bucket "$BUCKET"
# If error NoSuchBucketConfiguration → no default encryption configured
```

Checks:

1. Default encryption present (AES256 or `aws:kms`).
2. KMS key policy allows intended roles only; key not world-usable.
3. Bucket policy **denies** `PutObject` without `x-amz-server-side-encryption`
   (and KMS key ID when required).
4. Sensitive workloads prefer SSE-KMS + least-privilege key grants.

### 4. Policy, ACL, and TLS review

Read bucket policy for:

- Anonymous or `AuthenticatedUsers` group grants
- Over-broad actions (`s3:*`) for public or partner principals
- Missing TLS deny
- Confused-deputy gaps on service principals (missing `aws:SourceArn` /
  `aws:SourceAccount` where applicable)
- Cross-account grants still needed and documented

Prefer **IAM policies on roles** for same-account access and **bucket policy**
for cross-account or public-exception cases — keep both consistent.

### 5. Durability, logging, and lifecycle

```bash
aws s3api get-bucket-versioning --bucket "$BUCKET"
aws s3api get-bucket-logging --bucket "$BUCKET"
aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"
aws s3api get-object-lock-configuration --bucket "$BUCKET"  # if used
```

| Control | When to require |
| --- | --- |
| Versioning | tfstate, backups, sensitive mutable data |
| MFA delete / Object Lock | High-integrity / compliance retention |
| Access logging or CloudTrail data events | Security-relevant buckets |
| Lifecycle | Expire incomplete MPU; transition cold data; cost hygiene |
| Replication | DR design — review dest bucket hardening too |

### 6. Intentional public or CDN patterns

If product requires public reads:

1. Use a **dedicated** public assets bucket or CloudFront + OAC to private origin.
2. Keep BPA appropriately configured for the chosen pattern (CloudFront OAC often
   keeps origin private).
3. Never place secrets, PII exports, or Terraform state in public prefixes.
4. Document residual risk (hotlinking, data scraping).

### 7. Remediate and verify

1. Enable account-level BPA; fix bucket BPA to all four true unless exception.
2. Set ownership to **BucketOwnerEnforced**; clear public ACLs.
3. Apply default encryption + deny insecure transport + deny unencrypted puts.
4. Enable versioning/logging as required.
5. Tighten IAM principals with `aws-iam-least-privilege`.
6. Re-check `get-bucket-policy-status` and Access Analyzer.
7. For leaks of secrets that lived in objects: `secrets-management-hygiene`.
8. IaC updates: `terraform-security-basics` + `code-quality-standards`.

### 8. Safe verification only

```bash
# Expect failure from unauthorized/public path after hardening
curl -sI "https://example-app-prod-data.s3.amazonaws.com/app-data/object.txt"
# Authorized read as the app role (example)
aws s3 cp "s3://example-app-prod-data/app-data/object.txt" - --profile app-readonly
```

Do **not** bulk-download production objects “to prove impact” beyond minimal
evidence samples approved in scope.

## Concrete AWS Examples

### Enable Block Public Access (bucket)

```bash
aws s3api put-public-access-block --bucket example-app-prod-data --public-access-block-configuration \
  'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'
```

Account-level:

```bash
aws s3control put-public-access-block --account-id 111122223333 --public-access-block-configuration \
  'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'
```

### Default encryption (SSE-KMS)

```bash
aws s3api put-bucket-encryption --bucket example-app-prod-data --server-side-encryption-configuration '{
  "Rules": [{
    "ApplyServerSideEncryptionByDefault": {
      "SSEAlgorithm": "aws:kms",
      "KMSMasterKeyID": "arn:aws:kms:eu-west-1:111122223333:key/KEY-UUID"
    },
    "BucketKeyEnabled": true
  }]
}'
```

SSE-S3 variant: `"SSEAlgorithm": "AES256"` without KMS key fields.

### Hardened bucket policy (TLS + encryption + deny public residual)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::example-app-prod-data",
        "arn:aws:s3:::example-app-prod-data/*"
      ],
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    },
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::example-app-prod-data/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    },
    {
      "Sid": "AllowAppRoleRWPrefix",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111122223333:role/app-prod-task"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::example-app-prod-data/app-data/*"
    },
    {
      "Sid": "AllowAppRoleListPrefix",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111122223333:role/app-prod-task"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::example-app-prod-data",
      "Condition": {
        "StringLike": { "s3:prefix": ["app-data/*"] }
      }
    }
  ]
}
```

Apply:

```bash
aws s3api put-bucket-policy --bucket example-app-prod-data --policy file://bucket-policy.json
```

### Bad — anonymous read of all objects

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::example-app-prod-data/*"
    }
  ]
}
```

Acceptable only for a **dedicated public assets** bucket with non-sensitive
content, deliberate product review, and preferably CDN in front — never for
state, logs, backups, or PII.

### Bad — ACL public-read

```bash
# Do not use for private data
aws s3api put-bucket-acl --bucket example-app-prod-data --acl public-read
```

Prefer:

```bash
aws s3api put-bucket-ownership-controls --bucket example-app-prod-data --ownership-controls \
  'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
```

### Versioning + access logging

```bash
aws s3api put-bucket-versioning --bucket example-app-prod-data \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-logging --bucket example-app-prod-data --bucket-logging-status '{
  "LoggingEnabled": {
    "TargetBucket": "example-org-s3-access-logs",
    "TargetPrefix": "example-app-prod-data/"
  }
}'
```

Ensure the **log bucket** is private, encrypted, BPA-on, and has a policy that
allows only the logging service / intended readers.

### Terraform sketch (pair with terraform-security-basics)

```hcl
resource "aws_s3_bucket" "app" {
  bucket = "example-app-prod-data"
}

resource "aws_s3_bucket_public_access_block" "app" {
  bucket                  = aws_s3_bucket.app.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "app" {
  bucket = aws_s3_bucket.app.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app" {
  bucket = aws_s3_bucket.app.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "app" {
  bucket = aws_s3_bucket.app.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "app" {
  bucket = aws_s3_bucket.app.id
  policy = data.aws_iam_policy_document.app_bucket.json
}
```

### CloudFront OAC note (private origin)

Prefer **Origin Access Control** to a private bucket over legacy OAI + public
bucket. Bucket policy should allow only the CloudFront service principal with
conditions on distribution ARN — keep BPA enabled and objects non-public.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| S3 BPA, encryption, bucket policy, public access, logging | **This skill** | — |
| IAM principals with s3:* or PassRole into data plane | `aws-iam-least-privilege` | this skill for resource policies |
| Secrets stored in objects / leaked keys / rotation | `secrets-management-hygiene` | this skill for bucket exposure fix |
| Terraform bucket modules, tfstate backend bucket | `terraform-security-basics` | this skill for live S3 control checks |
| Implementing bucket modules, policy tests, apps using SDK | `code-quality-standards` | this skill for control requirements |
| Upload/path issues in application layer | `upload-insecure-files`, `path-traversal-lfi` | this skill for bucket config |
| Archive extract from S3 artifacts | `zip-slip-path-safety` | — |

### Required helpers (when applicable)

- **`secrets-management-hygiene`:** when objects or policies led to credential
  exposure; rotate secrets stored in S3; keep keys out of buckets and git.
- **`terraform-security-basics`:** when buckets/backends are managed as code;
  state bucket must meet this skill’s BPA/encryption/logging bar.
- **`code-quality-standards`:** when changing IaC modules, policy generators, or
  application code that configures or uses S3.
- **`aws-iam-least-privilege`:** identity-side companion for roles that list/get/
  put objects or manage bucket configuration.

## Checklist

- [ ] Authorization and account scope recorded; only owned buckets exercised
- [ ] Buckets inventoried with purpose and data classification
- [ ] Account-level Block Public Access: all four true (or documented exception)
- [ ] Per-bucket BPA: all four true unless deliberate public design
- [ ] No public ACL; Bucket owner enforced where possible
- [ ] Bucket policy: no unintended `Principal:"*"`; cross-account grants reviewed
- [ ] Default encryption enabled (SSE-S3 or SSE-KMS); unencrypted puts denied if required
- [ ] TLS-only deny (`aws:SecureTransport`) applied
- [ ] Versioning/logging/Object Lock set for sensitive or state buckets
- [ ] Public/static assets isolated from private data/state/logs
- [ ] Access Analyzer / policy status re-checked after changes
- [ ] IAM data-plane principals tightened (`aws-iam-least-privilege`)
- [ ] Exposed secrets rotated (`secrets-management-hygiene`)
- [ ] IaC paths use `terraform-security-basics`; code changes use `code-quality-standards`
- [ ] Residual public or cross-account exceptions documented with owner and expiry

## Rules

- **Owned or authorized AWS accounts only** — do not access third-party buckets.
- Public exposure must be **explicit product intent**, not a missing BPA flag.
- Prefer proving misconfiguration with **policy/ACL/BPA evidence** over bulk
  data download.
- Treat access logs and object samples as sensitive; minimize retention in tickets.
- Encrypt and privatize **tfstate, backups, and logs** first — highest blast radius.
- Coordinate CloudFront/CDN and origin policies so “private origin” stays private.
---

# Note

This skill owns **AWS S3 bucket hardening**: Block Public Access, encryption,
bucket policies/ACLs, TLS-only access, versioning, and logging. Pair with
`aws-iam-least-privilege` for identity permissions, `secrets-management-hygiene`
for credential/object secret lifecycle, `terraform-security-basics` for IaC and
state backends, and `code-quality-standards` for safe implementation changes.

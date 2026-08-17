---
name: gcp-storage-public-access
description: >
  Authorized assessment and hardening of Google Cloud Storage (GCS) public
  exposure: allUsers / allAuthenticatedUsers IAM, uniform bucket-level access,
  public access prevention, legacy ACLs vs IAM, and org-policy guardrails.
  Use when reviewing org-owned buckets or written engagements — not unauthorized
  enumeration of third-party GCS buckets.
---

# GCS Public Access (Authorized Hardening)

Assess and harden **Google Cloud Storage** so buckets and objects are not
anonymously readable or listable unless that is explicit product intent.
Defensive methodology for **owned or explicitly authorized GCP** only.

## Scope And Authorization

- **In scope:** buckets/projects you **own** or are contracted to assess;
  read-only IAM/metadata/org policy; controlled PAP/UBLA/IAM changes with approval.
- **Out of scope:** mass scanning foreign GCS; bulk download of out-of-scope
  objects; abusing leaked HMAC/SA keys on third-party projects.
- Prefer **policy/metadata** evidence over bulk download. Redact PII paths,
  signed URLs, HMAC/SA keys. Public sensitive data → IR: remove public
  principals, enforce PAP, rotate secrets (`secrets-management-hygiene`), audit logs.

## When To Use

- GCS **public buckets**, anonymous object URLs, or CDN origins on GCS
- IAM members `allUsers` / `allAuthenticatedUsers` on bucket or object
- Missing/weak **public access prevention** (bucket or org constraint)
- **Uniform bucket-level access** off; mixed legacy **ACLs** and IAM
- Mentions: GCS public, allUsers, UBLA, PAP, anonymous `storage.objects.get`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Project/org IAM, SA keys, actAs | `gcp-iam-basics` |
| AWS S3 BPA / policies / ACLs | `aws-s3-bucket-hardening` |
| Azure Blob anonymous / SAS | `azure-blob-misconfig` |
| Secrets, SA JSON, HMAC rotation | `secrets-management-hygiene` |
| Multi-cloud Terraform baseline | `terraform-security-basics` |
| Estate inventory / test plan | `recon-and-methodology` |
| App/IaC implementation quality | `code-quality-standards` |

## Control Themes

| Control | Weak outcome | Hardened default |
| --- | --- | --- |
| Public principals | Anyone reads/lists | No `allUsers` / `allAuthenticatedUsers` on private data |
| Public access prevention | Accidental public IAM | PAP **enforced** (bucket + org) |
| Uniform bucket-level access | Per-object ACL drift | **UBLA on**; IAM only |
| Legacy ACLs | AllUsers READER/OWNER | Clear public ACLs; migrate to IAM |
| Intentional public assets | Mixed with backups/PII | Dedicated public bucket only |
| Logging / versioning | Weak IR/recovery | Soft delete/versioning; access logs |

**Public by design** must be explicit — never mix with state, logs, or private uploads.

## Workflow

### 1. Inventory

Confirm authorization. List buckets with purpose, sensitivity, consumers.
Incomplete estate → `recon-and-methodology` first.

```bash
gcloud config get-value project
gcloud storage buckets list --format="table(name,location,uniform_bucket_level_access,public_access_prevention)"
```

### 2. Public principals and exposure

```bash
BUCKET=gs://example-app-prod-data
gcloud storage buckets describe "$BUCKET" --format=json
gcloud storage buckets get-iam-policy "$BUCKET" --format=json
# If UBLA off:
gcloud storage buckets describe "$BUCKET" --format="yaml(acl,defaultObjectAcl)"
```

| Finding | Signal |
| --- | --- |
| `allUsers` + objectViewer / legacyObjectReader | Anonymous object read |
| `allUsers` + list / legacyBucketReader | Anonymous enumeration |
| `allAuthenticatedUsers` on private data | Any Google account |
| PAP not enforced + public binding | Accidental public risk |
| UBLA off + AllUsers object ACLs | Hidden per-object public |

Approved vantage only: non-destructive canary HEAD/GET and unauthenticated list;
record status — no bulk exfil.

### 3. Harden and verify

1. Remove public IAM members; clear public ACLs if UBLA still off.
2. Enable **UBLA**; set **PAP enforced** (org constraint when in scope).
3. Isolate intentional static assets; document owner + review date.
4. Versioning/soft-delete + access logs for sensitive data; alert on public IAM.
5. Broader identity plane → `gcp-iam-basics`. Secrets → `secrets-management-hygiene`.
6. IaC/apps → `terraform-security-basics` + `code-quality-standards`.
7. Re-test anonymous deny; re-check IAM and `public_access_prevention`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GCS public, allUsers, UBLA, PAP, ACL vs IAM | **This skill** | — |
| Broader GCP IAM / SA keys | `gcp-iam-basics` | this skill (bucket public) |
| AWS S3 public access | `aws-s3-bucket-hardening` | — |
| Azure Blob public / SAS | `azure-blob-misconfig` | — |
| Secret/HMAC/SA key leak | `secrets-management-hygiene` | this skill (revoke public) |
| Terraform GCS / state hygiene | `terraform-security-basics` | this skill (live checks) |
| App/IaC code changes | `code-quality-standards` | this skill (control intent) |
| Project discovery plan | `recon-and-methodology` | this skill (bucket controls) |

Hand off other clouds to `aws-s3-bucket-hardening` / `azure-blob-misconfig`.
This skill owns **GCS data-plane public exposure**; `gcp-iam-basics` owns project/org IAM.

## Output Checklist

- [ ] Authorization recorded; only owned/authorized GCS exercised
- [ ] Buckets inventoried with purpose, sensitivity, owners
- [ ] No unintended `allUsers` / `allAuthenticatedUsers` on private data
- [ ] PAP **enforced**; UBLA on (or public ACLs cleared)
- [ ] Anonymous canary fails for sensitive prefixes (approved vantage)
- [ ] Intentional public assets isolated and documented
- [ ] Versioning/logging fit risk; alerts on public IAM changes
- [ ] Secrets rotated if exposed; IaC/code paths use companion skills
- [ ] Residual public exceptions have owner + review date

## Rules

- **Owned or authorized GCP only** — no third-party bucket hunting or exfil.
- Prove exposure with IAM/ACL/PAP metadata and minimal canary checks.
- Public access must be explicit product intent, not leftover ACL/IAM.
---

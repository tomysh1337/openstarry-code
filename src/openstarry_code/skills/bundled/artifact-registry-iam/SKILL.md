---
name: artifact-registry-iam
description: >
  Authorized assessment and hardening of Google Cloud Artifact Registry IAM:
  repository- vs project-level bindings, reader/writer/repoAdmin least privilege,
  public allUsers exposure, CI push identities, and cross-project consumers.
  Use when reviewing org-owned Artifact Registry repos, package/container pull
  and push roles, Terraform google_artifact_registry_*_iam_*, or accidental
  public packages — not unauthorized enumeration of third-party registries.
---

# Artifact Registry IAM (Authorized Hardening)

Review and harden **Google Cloud Artifact Registry** so humans, CI, and runtime
pullers receive only the repository permissions they need. Defensive methodology
for **owned or explicitly authorized GCP** — not third-party registry abuse.

## When To Use

- Artifact Registry **repository or project IAM** (Docker, Maven, npm, Python, Go, apt/yum)
- Over-broad roles (`owner`, `editor`, `artifactregistry.admin`) on daily humans, CI, or runtime SAs
- **Public** packages: `allUsers` / `allAuthenticatedUsers` on repo IAM
- Same SA for CI **push** and runtime **pull**; missing identity split
- Cross-project readers, remote/virtual repos, or `createOnPush*` writer patterns
- Mentions: Artifact Registry IAM, `artifactregistry.reader` / `writer` / `repoAdmin`,
  AR public repo, gcr.io migration IAM, AR least privilege

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Project/org IAM, SA keys, actAs, WIF design | `gcp-iam-basics` |
| Cosign/Sigstore sign, verify, admission | `container-image-signing` |
| GCS public buckets / PAP / UBLA | `gcp-storage-public-access` |
| Secret/SA JSON leak IR | `secrets-management-hygiene` |
| Terraform baseline / state hygiene | `terraform-security-basics` |
| Estate discovery plan | `recon-and-methodology` |
| App/IaC implementation quality | `code-quality-standards` |

## Workflow

### 1. Confirm scope and inventory repos

Record project ID(s), env (dev/stage/prod), authorization, and owners. List
repositories, formats, locations, and consumers (CI, GKE, Cloud Run, developers).
Incomplete estate → `recon-and-methodology` first.

```bash
gcloud artifacts repositories list --format="table(name,format,location,mode)"
```

### 2. Collect IAM (read-only)

```bash
REPO=my-docker-prod; LOC=us
gcloud artifacts repositories get-iam-policy "$REPO" --location="$LOC" --format=json
gcloud projects get-iam-policy "$PROJECT_ID" --flatten="bindings[].members" \
  --filter="bindings.role:artifactregistry" --format=json
```

Matrix: principal → role → repo (or project-wide). Project-level AR roles span
all repos unless constrained elsewhere.

### 3. Flag high-risk patterns

| Pattern | Why it matters |
| --- | --- |
| `allUsers` / `allAuthenticatedUsers` + reader/writer | Public pull or push |
| `admin` / `repoAdmin` on daily CI or humans | Delete repos, set IAM, blast radius |
| Same SA for push + runtime pull | Compromised workload can overwrite images |
| Project `editor`/`owner` instead of AR roles | Far more than package access |
| Writer on every repo for one job | Lateral overwrite across apps/envs |
| Unbounded cross-project SA member | Untrusted supply-chain pull path |
| One-off user bindings (no groups) | Sprawl; hard offboarding |

**Public-by-design** (open-source mirrors) must be isolated repos with owner +
review date — never mix with private app images.

### 4. Redesign and verify

| Identity | Prefer | Avoid |
| --- | --- | --- |
| Runtime pull | `artifactregistry.reader` on needed repos | writer, admin, editor |
| CI push | `writer` or `createOnPushWriter` on target repo(s) | admin, all repos, JSON keys |
| Developers | reader via **group**; break-glass repoAdmin separate | owner/editor daily |
| Scanners | reader (org-approved) | writer |

Prefer **repository-level** bindings; split **push** vs **pull** SAs via WIF/WI
(`gcp-iam-basics`, `gcp-workload-identity-federation`). Remove unintended public
principals. Encode in IaC (`terraform-security-basics` + `code-quality-standards`).
Re-read IAM after change; alert on AR `setIamPolicy`. Image integrity →
`container-image-signing` (IAM is not signing).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| AR repo/project IAM, public AR, push/pull split | **This skill** | — |
| Broader GCP IAM, keys, impersonation | `gcp-iam-basics` | this skill (AR bindings) |
| WIF for CI pull/push | `gcp-workload-identity-federation` | this skill (repo roles) |
| Cosign/Sigstore / admission | `container-image-signing` | this skill (who may push) |
| SA JSON / token leak | `secrets-management-hygiene` | this skill (revoke AR roles) |
| Terraform AR + IAM modules | `terraform-security-basics` | this skill (role intent) |
| Implementing modules/scripts | `code-quality-standards` | this skill (control intent) |

Owns **who can list/pull/push/admin** Artifact Registry. Signing →
`container-image-signing`; project-wide IAM footguns → `gcp-iam-basics`.

## Output Checklist

- [ ] Authorization and project/repo scope recorded; read-only inventory first
- [ ] Repos listed with format, location, purpose, sensitivity
- [ ] Repo + project AR IAM collected; principal × role matrix built
- [ ] No unintended `allUsers` / `allAuthenticatedUsers` on private repos
- [ ] No daily human/CI/runtime with unjustified admin/repoAdmin/editor/owner
- [ ] Push identity ≠ runtime pull; writers scoped to target repos
- [ ] Humans via groups; automation via WIF/WI/attached SA (not JSON keys)
- [ ] Cross-project members justified; public-by-design repos isolated + owned
- [ ] IAM via IaC where possible; CQS applied; exceptions documented with expiry
- [ ] Signing/admission needs handed to `container-image-signing` when in scope

## Scope And Authorization

- **In scope:** Artifact Registry repos and related IAM on projects **you own** or
  are contracted to assess; read-only `get-iam-policy` / list; controlled binding
  changes with change windows and rollback.
- **Out of scope:** Pulling/overwriting third-party packages; abusing leaked
  credentials against foreign repos; mass scraping public AR for exploitation.
- Prefer **policy evidence** over bulk layer download. Gate `set-iam-policy`,
  public grants, and mass deletes behind approval.
- Redact SA key JSON and pull tokens; rotate via `secrets-management-hygiene` on
  exposure. Prove excess with bindings and minimal authorized probes — do not
  corrupt shared production tags without approval.

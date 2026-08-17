---
name: gcp-workload-identity-federation
description: >
  Configure and review Google Cloud Workload Identity Federation (WIF) so CI
  and external IdPs (especially GitHub Actions OIDC) obtain short-lived tokens
  for a GCP service account without user-managed SA keys. Use when designing or
  auditing workload identity pools/providers, attribute mappings and conditions,
  principalSet IAM bindings, GitHub/GitLab OIDC to GCP SA, or retiring long-lived
  JSON keys for deploy jobs on owned or authorized GCP projects.
---

# GCP Workload Identity Federation (WIF)

Replace **long-lived service-account keys** with **OIDC federation**: external
IdP/CI → Workload Identity Pool/Provider → short-lived credentials for a dedicated
GCP service account (SA). Primary path: **GitHub Actions OIDC → GCP SA**. For
**org-owned or explicitly authorized GCP** only.

## Scope And Authorization

- **In scope:** Pools/providers, attribute maps/conditions, SA
  `roles/iam.workloadIdentityUser` bindings, and CI OIDC wiring in projects you
  **own** or are contracted to harden; read-only inventory; controlled changes.
- **Out of scope:** Foreign GCP orgs; loosening prod conditions “to debug”;
  minting/replaying tokens outside engagement.
- Prefer **non-prod** for first proof. Gate prod provider/IAM changes. Redact
  project numbers, pool IDs, SA emails, tokens.
- Broader IAM / SA key estate → `gcp-iam-basics`. CI secrets, fork-PR isolation,
  multi-cloud OIDC → `secrets-in-ci-pipelines`.

## When To Use

- Designing **WIF** so GitHub Actions / GitLab CI / OIDC issuers call GCP
- Reviewing **pools**, OIDC **providers**, **attribute mappings**, and **CEL
  attribute conditions** (repo/ref/environment limits)
- Binding `principalSet`/`principal` members to a deploy SA; retiring SA JSON keys
- Mentions: Workload Identity Federation, WIF, GitHub OIDC GCP,
  `google-github-actions/auth`, attribute condition, no SA key in CI

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Project/org IAM, basic roles, actAs, key estate | `gcp-iam-basics` |
| CI secrets, fork isolation, masking, generic OIDC | `secrets-in-ci-pipelines` |
| GKE pod → GSA (K8s WI, not external OIDC) | `gcp-iam-basics` |
| Org secret leak IR / rotation | `secrets-management-hygiene` |
| Pipeline stages / cache / artifacts | `ci-cd-pipeline-patterns` |
| Terraform WIF module quality | `terraform-security-basics`, CQS |

## Core Model

| Piece | Role |
| --- | --- |
| **External IdP** | Issues OIDC token (e.g. GitHub Actions) |
| **Pool + OIDC provider** | Trust issuer; map claims; **attribute condition** |
| **Service account** | Target identity; only roles the job needs |
| **IAM binding** | SA trusts pool `principalSet`/`principal` |
| **CI job** | OIDC id-token → STS/WIF → short-lived access |

**Rule:** WIF + least-privilege SA beats user-managed SA keys. Residual keys for
the same SA remain risk until disabled.

## Workflow

### 1. Scope and identity design

1. Record project IDs, env, ownership, change freeze.
2. List GCP-needing workflows; **one SA per job class and environment**
   (prod deploy ≠ PR plan/lint).
3. Inventory SA keys for those SAs — disable after WIF works
   (`gcp-iam-basics`, `secrets-in-ci-pipelines`).

### 2. Pool, provider, attribute conditions

1. Create workload identity **pool** (stable ID; document owner).
2. Add **OIDC provider** (issuer URL + allowed audiences per Google/GitHub docs).
3. Map JWT claims → attributes (`google.subject`, repository, ref, environment).
4. Strict **attribute condition** CEL — e.g. only
   `attribute.repository == 'ORG/REPO'`; prod only for
   `attribute.ref == 'refs/heads/main'` or a GitHub **environment** claim.
5. Reject org-wide/any-ref trust and missing `aud` checks. Fork PRs must not
   satisfy prod conditions.

### 3. SA binding and least privilege

1. Dedicated SA; grant only needed roles (not `editor`/`owner`).
2. Grant `roles/iam.workloadIdentityUser` for a tight `principalSet` (e.g. by
   `attribute.repository`), not pool-wide.
3. Deep role/impersonation review → `gcp-iam-basics`.

### 4. Wire CI, verify, retire keys

1. GitHub: `permissions: id-token: write` (minimal other perms).
2. Official auth action/STS with full `workload_identity_provider` +
   `service_account` resource names.
3. Prove exchange in **non-prod**; then prod protected env + matching condition.
4. Confirm access **without** a key file (`GOOGLE_APPLICATION_CREDENTIALS`).
5. Disable residual keys; rotate if exposed (`secrets-in-ci-pipelines`,
   `secrets-management-hygiene`). Encode via IaC + `code-quality-standards`.
   Re-audit conditions on repo/env renames; alert on SA key creation.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| WIF pool/provider, attribute conditions, GitHub OIDC → GCP SA | **This skill** | — |
| Broader GCP IAM, basic roles, actAs, key estate | `gcp-iam-basics` | this (federation) |
| CI secret hygiene, forks, masking, multi-cloud OIDC | `secrets-in-ci-pipelines` | this (WIF detail) |
| Key leak IR / org rotation | `secrets-management-hygiene` | this + `gcp-iam-basics` |
| Pipeline stages/cache/artifacts | `ci-cd-pipeline-patterns` | this for identity |
| Terraform `google_iam_workload_identity_*` | `terraform-security-basics` | this + CQS |

- **`gcp-iam-basics`:** SA roles and project policy — not WIF provider CEL.
- **`secrets-in-ci-pipelines`:** CI credential model/leaks; hand here for GCP
  pool/provider/attribute hardening.

## Output Checklist

- [ ] Authorization and project/env scope recorded (owned GCP only)
- [ ] Job classes mapped to dedicated SAs (prod ≠ PR)
- [ ] Pool + OIDC provider documented (issuer, audience)
- [ ] Attribute mappings cover claims used in conditions
- [ ] Attribute conditions bind repo (and ref/environment for prod)
- [ ] No org-wide/unrestricted principalSet on prod deploy SA
- [ ] SA roles least privilege — not `owner`/`editor`
- [ ] CI uses OIDC; no JSON key required for that path
- [ ] Residual user-managed SA keys disabled after federation works
- [ ] Fork/untrusted PR cannot satisfy prod WIF conditions
- [ ] Non-prod proof then prod window; tokens redacted in logs
- [ ] Follow-ups: IAM → `gcp-iam-basics`; CI → `secrets-in-ci-pipelines`
- [ ] IaC + `code-quality-standards`; exceptions have owner + expiry

## Rules

- **Owned or authorized GCP only** — no foreign-tenant federation abuse.
- Federated short-lived tokens beat long-lived SA keys; delete keys when WIF works.
- Attribute conditions are the trust boundary — loose CEL ≈ public assume. Separate
  plan vs apply SAs; never share prod deploy with all workflows. Redact secrets.

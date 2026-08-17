---
name: gcp-iam-basics
description: >
  GCP IAM principles for authorized assessment and hardening: least privilege,
  policy inheritance, service accounts, basic roles, key hygiene, and common
  privilege-escalation footguns. Use when reviewing org-owned projects or written
  engagements — not unauthorized enumeration of third-party GCP organizations.
---

# GCP IAM Basics (Authorized Assessment)

Review and harden **Google Cloud IAM** so humans and workloads receive only the
permissions they need. Defensive and authorized only.

## Scope And Authorization

- **In scope:** org/folder/project IAM you own or are contracted to assess;
  read-only `get-iam-policy` / Policy Analyzer / Recommender; controlled role
  changes with change windows.
- **Out of scope:** attacking GCP outside engagement; keys/persistence in foreign
  accounts; mass scraping public GCP for exploitation.
- Prefer **read-only inventory** first. Gate `set-iam-policy`, key creation, and
  org-policy changes behind approval. Redact SA key JSON and sensitive members.
- Leaked over-privileged SA key → disable key, revoke roles, audit Admin Activity;
  follow IR.

## Use When

- Project/folder/org IAM, Terraform `google_*_iam_*`, or Console role grants
- Basic roles (`roles/owner`, `editor`, `viewer`) on users or service accounts
- User-managed SA keys in git/CI; default compute SA over-privileged
- Mentions: GCP IAM least privilege, SA key, principalSet, impersonation,
  `serviceAccountUser`, domain-wide delegation, org policy
- Authorized review of IAM escalation paths (actAs, token creator, project IAM admin)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org-wide secret/key rotation process | `secrets-management-hygiene` |
| Engagement recon / cloud asset plan | `recon-and-methodology` |
| App code quality for ADC clients | `code-quality-standards` |
| Multi-cloud Terraform baseline | `terraform-security-basics` |
| In-cluster K8s RBAC on GKE | `kubernetes-pentesting` |

## IAM Principles

| Principle | Practice |
| --- | --- |
| Least privilege | Predefined/custom roles over basic `editor`/`owner` |
| Inheritance | Org → folder → project → resource; org policy for hard denies |
| Prefer identities | Groups/federation over SA keys; groups over one-off users |
| Workload identity | Attached SA / GKE WI / WIF — not downloaded JSON |
| Separation | Break-glass owner ≠ daily deployer ≠ runtime app SA |
| Audit | Admin Activity; alert on policy and key changes |

## Common Footguns

| Footgun | Why it matters |
| --- | --- |
| `owner` / `editor` on humans or CI | Near-full project control |
| Default Compute SA with editor | Workloads inherit project-wide write |
| `serviceAccountUser` / `TokenCreator` | actAs or mint tokens for privileged SAs |
| `resourcemanager.projectIamAdmin` | Can self-escalate bindings |
| User-managed SA keys | Exfiltrateable long-lived credentials |
| `allUsers` / `allAuthenticatedUsers` | Public or any-Google-account access |
| Cross-project admin SA | Lateral movement across environments |

## Workflow

### 1. Inventory

Map org → folders → projects (prod vs non-prod). List users, groups, domains,
SAs, principalSets; CI (WIF, Cloud Build), break-glass. Incomplete project list →
`recon-and-methodology` first.

### 2. Collect policies (read-only)

```bash
gcloud projects get-iam-policy "$PROJECT_ID" --format=json
gcloud organizations get-iam-policy "$ORG_ID" --format=json   # if in scope
```

Include resource-level IAM (buckets, KMS, BigQuery, Secret Manager). Use Policy
Analyzer / Recommender for unused bindings — right-size, do not blind-delete.

### 3. Analyze, keys, remediate, report

Who / role / resource / justification. Flag basic roles on non-break-glass
principals; public IAM members; impersonation edges to powerful SAs; split
runtime vs deploy SAs; prefer WIF over JSON keys. Via `secrets-management-hygiene`:
inventory SAs/keys; ban JSON in git/CI; prefer ADC/WIF/attached SA. Leak: disable
key → rotate → audit. Replace basic roles; humans via groups; per-workload SAs;
minimal impersonation; IaC with `code-quality-standards`. Report by blast radius
with redacted evidence and concrete role replacements — never use discovered keys
out of scope.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GCP IAM least privilege, SA keys, escalation paths | **This skill** | — |
| SA JSON / key leak, rotation IR | `secrets-management-hygiene` | this skill (IAM bind/disable) |
| Cloud estate discovery, scoping | `recon-and-methodology` | this skill (IAM deep review) |
| App/IaC that sets IAM or uses ADC | `code-quality-standards` | this skill (role design) |
| In-cluster K8s RBAC on GKE | `kubernetes-pentesting` | this skill (GCP SA / WI) |

### Routing notes

- **`secrets-management-hygiene`:** SA keys and CI secrets; rotate/disable first.
- **`code-quality-standards`:** when implementing IAM in code/IaC or app auth wiring.
- **`recon-and-methodology`:** authorized project/trust-boundary mapping first.

## Checklist

- [ ] Scope recorded; read-only first
- [ ] Hierarchy and principals inventoried
- [ ] Project + critical resource IAM collected
- [ ] No unjustified `owner`/`editor` on daily humans, CI, or runtime SAs
- [ ] Default compute SA not project editor; per-workload SAs used
- [ ] Impersonation edges reviewed and minimal
- [ ] User-managed SA keys minimized; none in git/CI plaintext
- [ ] WIF or attached SA preferred for automation
- [ ] No unintended public IAM members on sensitive resources
- [ ] Org policy guardrails reviewed where in scope
- [ ] Remediation via IaC; `code-quality-standards` applied
- [ ] Logging/alerting on IAM and key changes; exceptions owned

## Rules

- Authorized assessment/hardening only — no third-party org abuse.
- Prove excessive permissions and path existence; do not exploit them off-scope.
- Disable leaked keys before detailed exposure writeups; redact SA key material.
- Groups + predefined/custom roles beat basic roles and one-off user grants.
---

# Note

Owns **GCP IAM least-privilege hardening**. Pair with `secrets-management-hygiene`,
`code-quality-standards`, and `recon-and-methodology`.

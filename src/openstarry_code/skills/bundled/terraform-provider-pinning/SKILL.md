---
name: terraform-provider-pinning
description: >
  Pin Terraform/OpenTofu providers for reproducible init and plan: required_providers
  version constraints, .terraform.lock.hcl, terraform providers lock, registry source
  addresses, and CI lock-aware init. Use when provider versions float, lockfile is
  missing or uncommitted, required_providers lacks constraints, init picks unexpected
  provider builds, multi-platform checksums, or Terraform Cloud/Enterprise provider
  install policy is in scope — hand broad IaC security to terraform-security-basics
  and generic lock/bot strategy to dependency-pinning-strategies.
---

# Terraform Provider Pinning

Own **provider version and lockfile discipline** so `terraform init` / `tofu init`
resolves the same provider binaries across laptops, CI, and apply runners. Not module
pinning, state/IAM hardening, or multi-ecosystem bot strategy.

## When To Use

- Authoring or reviewing `required_providers` / `required_version` in `terraform {}`
- `.terraform.lock.hcl` missing, uncommitted, stale, or rewritten every machine
- Provider upgrades, major bumps, or “plan changed with no HCL edit”
- Multi-OS CI platform checksums; private/mirror registry install
- Keywords: provider pin, lock.hcl, `~>`, `terraform providers lock`, floating
  provider, hashicorp/aws version, OpenTofu provider lock, plugin cache

Do **not** use as primary for: tfstate/IAM/public S3/secrets → `terraform-security-basics`;
module `source`/`ref` or Renovate/Dependabot policy → `dependency-pinning-strategies`;
pipeline/OIDC → `ci-cd-pipeline-patterns`; HCL quality → `code-quality-standards`;
plugin CVE/SBOM → `sbom-and-supply-chain`.

## Repo Config First

Repo and org Terraform policy **outrank** defaults below.

1. **Roots:** each stack’s `terraform {}` (monorepo roots vs shared modules)
2. **Lockfiles:** `.terraform.lock.hcl` committed? gitignored by mistake?
3. **Version floors:** `required_version`, mandated Terraform/OpenTofu range
4. **Sources:** public registry vs private registry / network mirror
5. **CI init:** exact flags; unreviewed `init -upgrade` allowed?
6. **Neighbors:** Terragrunt, TFC/TFE install methods, Renovate TF presets

**Precedence:** Keep existing locks and org-approved majors. Flag unconstrained
`required_providers`, deleted locks, and CI that upgrades providers every run.

## Workflow

### 1. Inventory

For each root: list `required_providers` (**source**, **version**, aliases); align
`required_version` with the CI/dev binary; note `provider "X" {}` is config, not a
version pin; record whether the lockfile is in VCS.

### 2. Constrain `required_providers`

Declare **source + version** for every direct provider. Prefer `~>` for routine work;
exact `=` after incidents or freezes.

```hcl
terraform {
  required_version = ">= 1.5.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}
```

| Constraint | Meaning | Use |
| --- | --- | --- |
| `= 5.60.0` | Exact | Incident freeze |
| `~> 5.60` | Patch in 5.60.x | Common root + lock |
| `>= 5.0, < 6.0` | Minor room in major | Shared modules |
| Unset / `*` | Unbounded | **Reject** on prod roots |

Constraints allow a set; **`.terraform.lock.hcl` freezes** the chosen version and
install checksums.

### 3. Commit `.terraform.lock.hcl`

1. After a good resolve, commit the lock **next to the root** (do not gitignore it).
2. Do not hand-edit hashes; regenerate via CLI.
3. Multi-OS teams/CI — refresh needed platforms:

```bash
terraform providers lock \
  -platform=linux_amd64 -platform=linux_arm64 \
  -platform=darwin_amd64 -platform=darwin_arm64 \
  -platform=windows_amd64
```

4. Upgrade: bump constraint or deliberate `init -upgrade` → review lock diff →
   plan non-prod → merge HCL + lock together.

### 4. CI and init hygiene

1. Default CI: `terraform init -input=false` **without** `-upgrade`.
2. Treat unexpected lock mutation as failure.
3. Plugin caches (`TF_PLUGIN_CACHE_DIR`) must not override lock selection.
4. Document private `provider_installation` / network_mirror so sources match.
5. After major bumps: `validate` + plan; watch schema renames/deprecations.

### 5. Verify

Clean init on a fresh runner using only the committed lock; confirm provider list
matches; multi-platform lock installs without missing-checksum errors; document owner/cadence.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Provider constraints, lock.hcl, providers lock, init pin | **This skill** | — |
| State, IAM, public storage, secrets in TF | `terraform-security-basics` | this if unpinned |
| Generic lockfiles / Renovate / Dependabot | `dependency-pinning-strategies` | this for TF providers |
| Plan/apply pipeline, OIDC roles | `ci-cd-pipeline-patterns` | this for init flags |
| Module HCL quality and tests | `code-quality-standards` | **always** on edits |
| CVE/SBOM of installed plugins | `sbom-and-supply-chain` | this for freeze |

Keep **this skill primary** until every root has constraints + a committed lock.
Hand broader IaC security to `terraform-security-basics`; org pin/bot philosophy to
`dependency-pinning-strategies`.

## Output Checklist

- [ ] Roots inventoried; each provider has `source` + version constraint
- [ ] `required_version` matches CI/dev Terraform or OpenTofu binary
- [ ] `.terraform.lock.hcl` committed; not gitignored on deployable roots
- [ ] Multi-platform checksums when agents span OS/arch
- [ ] CI init lock-aware (no unreviewed `-upgrade` on protected branches)
- [ ] Upgrade path: constraint bump → lock refresh → plan review
- [ ] Private registry/mirror config matches provider source addresses
- [ ] Hand-off: `terraform-security-basics` / `dependency-pinning-strategies`; CQS on edits

## Rules

- **Repo config first.** Constraints allow; **lockfiles freeze.** Unconstrained
  providers are a defect on production roots. Never delete a lock to “fix” init
  without regenerating on the team’s TF/OpenTofu version. Provider **config**
  (region, assume_role) is separate from **version** pins.

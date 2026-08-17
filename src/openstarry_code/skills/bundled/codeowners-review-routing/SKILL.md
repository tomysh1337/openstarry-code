---
name: codeowners-review-routing
description: >
  Design and maintain CODEOWNERS path ownership, required review rules, and
  monorepo routing that avoids single-owner bottlenecks. Use when CODEOWNERS
  syntax, path owners, required reviewers, branch protection review counts,
  monorepo package ownership, review routing, or fixing slow PR queues caused by
  overly broad owner teams.
---

# CODEOWNERS Review Routing

Own **who must review which paths**: CODEOWNERS syntax, required vs optional
review, monorepo package maps, and load-balanced ownership so PRs merge without
one person or team as a permanent gate.

## When To Use

- Authoring or refactoring **CODEOWNERS** (GitHub/GitLab/Azure DevOps)
- Mapping **path → team/user**; **required reviews** / code-owner enforcement
- Monorepo package owners, shared libs, platform/infra paths
- Reducing **owner bottlenecks** (single individual, huge catch-all `*`)
- Keywords: CODEOWNERS, required reviewers, path ownership, review routing,
  monorepo owners, bottleneck, branch protection code owners

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| PR title/body Why/What/Test | `pr-description-writing` |
| Branch strategy / when to open PR | `git-workflow-conventions` |
| Review comment tone / severity | `code-review-comments-style` |
| Code correctness of the change | `code-quality-standards` |
| CI pipeline shape | `ci-cd-pipeline-patterns` |

## Repo Config First

Host and repo rules **outrank** defaults below.

1. **Owners files:** `.github/CODEOWNERS`, root/`docs` `CODEOWNERS`, GitLab
   `CODEOWNERS`, Azure path policies
2. **Branch protection / rulesets:** min approvers; require code-owner review;
   dismiss stale; last-push approval
3. **Team graph:** valid `@org/team` / users with write/approve rights
4. **Monorepo layout:** `apps/*`, `packages/*`, generators (Nx, Turborepo, custom)
5. **Overlays:** assignment bots, Gerrit OWNERS, Danger rules—reconcile dual maps
6. **Sensitive paths:** crypto, auth, billing, prod infra—tighter teams
7. **Neighbors:** match team names and last-match order conventions

**Precedence:** Follow host dialect and live protection. Edit the active owners
file; do not invent a parallel ownership map.

## Workflow

### 1. Inventory

| Capture | Why |
| --- | --- |
| Hot paths (auth, payments, infra, shared libs) | Need explicit owners, not only `*` |
| PR volume per path | Detect bottleneck teams |
| Broad globs / orphan paths | Mega-reviews or unowned churn |

### 2. CODEOWNERS syntax (portable core)

```text
# Last matching pattern wins on GitHub — confirm host dialect
*                         @org/default-reviewers
*.md                      @org/docs
/apps/web/                @org/web-team
/packages/ui/**           @org/design-system
/services/billing/        @org/billing @org/security
```

- Leading `/` = repo root (GitHub); bare patterns may match any segment.
- Owners: `@user`, `@org/team`, or email; teams need visibility + permission.
- CODEOWNERS only **suggests** until protection enables require-code-owners (or
  GitLab approval rules / ADO path policies). Separate tags from mandatory gates.

### 3. Required reviews (protection layer)

1. Global **min approvers** (often 1–2) on the default branch.
2. Enable **require code owners** only when path coverage is real.
3. Prefer **path-scoped** tighter rules (billing, IAM, Terraform) over raising
   global count for every file.
4. Admin-bypass for incidents only—not permanent single-human gates.

### 4. Monorepo patterns

| Pattern | Use |
| --- | --- |
| Per-app / per-package directory owners | Default product-team map |
| Dedicated owners for `packages/*` | Avoid any-app free-for-all on shared code |
| Platform team on `/infra`, `/.github` | CI and landing-zone changes |
| Separate docs owners; generated CODEOWNERS + CI | Large monorepos / `*.md` |

Root workspace files (`package.json`, lockfiles) → multi-member platform team, not one TL.

### 5. Avoid owner bottlenecks

1. Prefer **teams** over individuals; replace bootstrap individuals quickly.
2. Never leave sole `@person` on high-churn `*` or `/`.
3. Split mega-teams; secondary owners on critical paths; verify host **any-of vs all-of**.
4. Push specificity so most PRs hit one package team; rebalance slow-queue globs.
5. Require security/platform only on sensitive globs—not every PR.

### 6. Validate and ship

Dry-run PR on sample paths; host coverage UI if any; CI-check teams resolve;
update CONTRIBUTING “who owns what”; revisit quarterly for orphan packages.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CODEOWNERS, path owners, required code-owner reviews, monorepo routing, bottlenecks | **This skill** | — |
| Branch/PR process hygiene | `git-workflow-conventions` | this for owner rules |
| PR description | `pr-description-writing` | this if owners explained |
| Review comment wording | `code-review-comments-style` | — |
| CI enforcing owners validity | `ci-cd-pipeline-patterns` | this for patterns |
| Code quality under review | `code-quality-standards` | domain skill |

## Output Checklist

- [ ] Host dialect and live owners path confirmed (GitHub/GitLab/ADO)
- [ ] Protection: review count vs require-code-owners documented
- [ ] Sensitive paths (auth, billing, infra) have explicit teams
- [ ] Monorepo packages/apps mapped; shared libs and root config owned deliberately
- [ ] Last-match / section order verified for the host
- [ ] Teams (not lone individuals) on high-churn paths; no single-human `*`
- [ ] Multi-owner any-of vs all-of; optional vs required not conflated
- [ ] Validation: sample PR/coverage tool + invalid-team CI; CONTRIBUTING updated
- [ ] Routed: PR body → `pr-description-writing`; git process → `git-workflow-conventions`

## Rules

- **Repo/host first:** dialect and protection beat blog defaults.
- **Teams over heroes:** individuals on `*` or core packages create queue outages.
- **Specific before broad:** package paths over one global owner for all code.
- **Required ≠ mentioned:** enable code-owner requirements only after real coverage.
- **Sensitive tighter; rest lighter**—protect security without freezing delivery.

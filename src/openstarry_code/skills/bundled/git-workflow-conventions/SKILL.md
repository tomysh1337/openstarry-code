---
name: git-workflow-conventions
description: >
  Apply branch naming, trunk-based or Git Flow high-level strategy, and PR
  hygiene for healthy git history. Use when git branch, git workflow, 分支策略,
  branch naming, trunk-based development, Git Flow, feature branch, release
  branch, or how to open/update/merge a PR safely.
---

# Git Workflow Conventions

Keep branching, integration, and pull-request hygiene predictable so history
stays reviewable and automation (CI, protected branches, release bots) can do
its job. Prefer the **repository’s documented model** over generic blog
defaults; when the repo is silent, use the safe trunk-oriented defaults below.

## Use When

- Choosing or renaming a **branch** (`feature/…`, `fix/…`, `hotfix/…`)
- Deciding **trunk-based**, **GitHub Flow**, or **Git Flow**-style branching
- User mentions: git branch, git workflow, 分支策略, 分支命名, feature branch,
  release branch, long-lived branch, merge vs rebase policy
- Preparing a change for review: small PR scope, base branch, sync with main,
  when to open draft vs ready
- Cleaning up after merge (delete branch, avoid force-push on shared branches)

**Do not use as primary** for:

| Need | Skill instead |
| --- | --- |
| Commit subject/body text | `commit-message-conventions` |
| PR title/body Why/What/Test prose | `pr-description-writing` |
| Review comment tone / severity | `code-review-comments-style` |
| Code correctness of the change | `code-quality-standards` (+ domain skill) |
| CHANGELOG / release notes | `changelog-and-release-notes` |

## Repo Config First

Repository and platform rules **outrank** this skill’s defaults.

1. **Contrib docs:** `CONTRIBUTING.md`, `docs/contributing*`, internal wiki on
   branching, `AGENTS.md` process notes
2. **Templates and bots:** `.github/PULL_REQUEST_TEMPLATE*`, branch protection
   rules, required checks, Danger/reviewdog, merge queue, `CODEOWNERS`
3. **Default / protected branches:** `main` vs `master` vs `develop`; which
   branches accept direct push; required PR reviews and status checks
4. **Automation:** `release-please`, `semantic-release`, changesets, Git Flow
   plugins, monorepo tools that expect certain branch prefixes
5. **Existing names:** recent branches and PR titles — match prefix vocabulary
   (`feat/`, `feature/`, `fix/`, ticket IDs) and language (EN/ZH)
6. **Host defaults:** GitHub/GitLab/Azure DevOps merge method (merge commit /
   squash / rebase) and whether the team rewrites history on feature branches

**Precedence:** Follow documented branch protection and CONTRIBUTING. If none
exist, use **trunk-based / GitHub Flow** defaults (short-lived branches off
`main`, PR required) unless the team clearly runs multi-branch Git Flow.

## Workflow

### 1. Identify the integration model

| Model | When it fits | High-level shape |
| --- | --- | --- |
| **Trunk-based / GitHub Flow** | Continuous delivery, small PRs, feature flags | Branch from `main` → PR → merge to `main` → delete branch |
| **Git Flow (simplified)** | Versioned releases, long stabilization | `main` (or `master`) = production; `develop` = integration; `feature/*` → develop; `release/*` / `hotfix/*` → main + develop |
| **Release branches only** | Hotfixes and scheduled trains without full Git Flow | Short `release/x.y` cut from main; hotfixes branch from release or main per policy |

Do **not** invent a full Git Flow tree (develop + release + support) for a repo
that only has `main` and feature PRs.

### 2. Name the branch

Default pattern when the repo has no stricter rule:

```text
<type>/<short-slug>
<type>/<ticket-id>-<short-slug>
```

| Type | Use |
| --- | --- |
| `feat` / `feature` | New capability (pick **one** spelling the repo already uses) |
| `fix` | Bug fix |
| `hotfix` | Production-urgent fix (often from `main` or release branch) |
| `chore` | Tooling, deps, non-user maintenance |
| `docs` | Documentation-only |
| `refactor` | Internal restructure without intentional behavior change |
| `release` | Release train / version cut (if model uses it) |
| `test` / `ci` | Tests or CI-only when teams separate them |

Rules:

- **Lowercase**, hyphens for words: `feat/add-export-csv`, not `Feat/Add_Export_CSV`
- **Short slug** (~3–6 words); no full sentence
- Include **ticket id** when the team’s board requires it: `fix/PROJ-1234-null-token`
- Avoid personal-only names (`john/tmp`, `wip`) for work that will be reviewed
- Never put secrets or customer names in branch names

### 3. Keep the branch short-lived and focused

1. Branch from the correct base (`main`, `develop`, or `release/x.y` per model).
2. One **intent** per branch/PR when practical (one story, one fix cluster).
3. Rebase or merge **base** regularly so the PR does not rot (follow team
   preference: rebase-only feature branches vs merge-from-main).
4. Prefer **small, reviewable** diffs over multi-week mega-branches; use draft
   PRs early for visibility without requesting review.
5. Do not commit secrets, generated noise, or unrelated reformats.

### 4. PR hygiene (process, not prose)

Before marking ready for review:

| Check | Action |
| --- | --- |
| Base branch | Correct target; not an abandoned fork of an old release |
| Scope | Diff matches the branch intent; split or drop drive-bys |
| History | Commits readable enough for reviewers (or accept squash merge policy) |
| Sync | Up to date with base; conflicts resolved locally |
| CI | Local lint/test that match required checks when feasible |
| Draft vs ready | Draft until checklist-ready; then request reviewers / CODEOWNERS |
| Description | Hand off body writing to `pr-description-writing` |
| Commits | Hand off message text to `commit-message-conventions` |

After merge:

- Delete the remote branch if the platform does not auto-delete
- Do **not** force-push to `main` / `develop` / shared release branches
- Force-push to a **personal feature branch** only when rewriting is agreed
  (and never after others based work on it without coordination)

### 5. Merge method (follow repo, else these heuristics)

| Method | Prefer when |
| --- | --- |
| **Squash** | Noisy WIP commits on the branch; team wants one commit per PR on main |
| **Merge commit** | Team wants explicit PR nodes and non-linear but traceable history |
| **Rebase merge** | Team wants linear history and already enforces clean commits |

Do not fight protected-branch settings. If squash is required, still write a
good **PR title** (it often becomes the squash subject).

### 6. Hotfix and release trains (only if the model uses them)

- **Hotfix:** branch from production line (`main` or live release tag policy),
  fix minimally, PR with accelerated review, merge back to integration line so
  the fix is not lost.
- **Release branch:** freeze scope; only fixes and release meta; tag from the
  release branch per project versioning.
- Document upgrade or rollback only in release notes skill territory—not in
  branch names.

## Examples

### Good

```text
# Trunk / GitHub Flow
git switch main
git pull
git switch -c feat/PROJ-842-export-csv
# … small commits …
# open PR → main, pass CI, squash or merge per repo
```

```text
fix/auth-reject-expired-refresh
chore/upgrade-eslint-9
docs/contributing-branch-names
hotfix/1.4.2-null-pointer-login
```

```text
# Intentional Git Flow feature (when develop exists)
git switch develop && git pull
git switch -c feature/billing-proration
# PR → develop; release/* cut later by release owner
```

### Bad

```text
git switch -c Johns-Work-FINAL-v2
git switch -c fix
git switch -c asdf
git switch -c feature/rewrite-entire-backend-and-also-fix-css
```

*Why bad:* non-descriptive, unbounded scope, or unstable personal naming.

```text
# Long-lived branch with no PR for weeks, 400 files, mixed features
# Force-push to main to "clean history"
# Commit .env with production secrets on a "quick fix" branch
```

*Why bad:* unreviewable risk, protection bypass, secret leak.

```text
# Repo only has main + PRs, but agent creates develop + release + support
# trees "because Git Flow is best practice"
```

*Why bad:* invents process the team does not run; breaks automation and habits.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Branch naming, 分支策略, trunk vs Git Flow, PR process hygiene | **This skill** | — |
| Commit message text | `commit-message-conventions` | — |
| PR title/body (Why / What / Test) | `pr-description-writing` | this skill for base branch/scope |
| Review comment wording / approve vs request-changes | `code-review-comments-style` | `code-quality-standards` for judging the diff |
| Implement or review the code on the branch | `code-quality-standards` | domain skill |
| User-facing release notes from merged work | `changelog-and-release-notes` | — |
| CONTRIBUTING documents the workflow for humans | `readme-and-contributing-docs` | this skill for branch/PR rules content |

## Checklist

- [ ] Repo CONTRIBUTING, protected branches, and real branch name patterns read first
- [ ] Integration model matches the repo (not a cargo-culted full Git Flow)
- [ ] Branch name: type + short slug (+ ticket if required); no secrets
- [ ] Branched from the correct base; short-lived; one primary intent
- [ ] PR targets correct base; conflicts resolved; CI expectations known
- [ ] Scope is reviewable; draft until ready; CODEOWNERS/reviewers considered
- [ ] Commit messages handled via `commit-message-conventions` when writing them
- [ ] PR description handled via `pr-description-writing` when opening/updating PR
- [ ] Merge method respects platform settings; no force-push to shared trunks
- [ ] Remote feature branch deleted after merge when appropriate

## Rules

- **Repo config first:** protection rules and CONTRIBUTING beat generic “best practice.”
- **Short-lived branches:** prefer trunk-oriented flow unless the repo runs release trains.
- **One intent:** split mega-branches; do not hide refactors inside hotfixes.
- **Hygiene over heroics:** never force-push shared branches or commit secrets “just this once.”
- **Hand off prose:** branch/process here; commit text and PR body to their skills.
- **Evidence:** infer model from existing branches/PRs and CI, not from assumptions about CTF or sandbox repos.

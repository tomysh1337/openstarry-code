---
name: pr-description-writing
description: >
  Write clear pull/merge request titles and bodies using Why / What / Test
  structure, linked issues, and review-friendly scope. Use when PR description,
  写 PR, pull request body, MR description, PR title, GitHub/GitLab PR template,
  or summarizing a branch for reviewers.
---

# PR Description Writing

A PR description is the **review contract**: why the change exists, what landed,
how it was verified, and what risk remains. Optimize for a reviewer who has not
lived in the branch. Match the repository template; fill gaps with the Why /
What / Test structure below.

## Use When

- Drafting or rewriting a **PR/MR title and body** (English or 写 PR / PR 描述)
- User asks for PR description structure, summary for reviewers, or template fill
- Opening a draft or ready PR and needs scannable context, test plan, screenshots
- Tightening a vague description before request-review
- Squash-merge repos where the **PR title** becomes the main history subject

**Do not use as primary** for:

| Need | Skill instead |
| --- | --- |
| Branch naming / trunk vs Git Flow / when to open PR | `git-workflow-conventions` |
| Per-commit subject/body | `commit-message-conventions` |
| Writing review comments on someone else’s PR | `code-review-comments-style` |
| Implementing or judging code quality | `code-quality-standards` |
| Product release notes after merge | `changelog-and-release-notes` |

## Repo Config First

Repository templates and bots **outrank** this skill’s section names.

1. **PR templates:** `.github/PULL_REQUEST_TEMPLATE.md`,
   `.github/PULL_REQUEST_TEMPLATE/*`, `.gitlab/merge_request_templates/*`,
   Azure DevOps PR templates
2. **Contrib docs:** `CONTRIBUTING.md` “opening a PR” checklist, required
   sections (changelog, screenshots, migration)
3. **Title automation:** semantic PR title linters, Conventional Commits on PR
   titles (`feat:`, `fix:`), commitlint-for-PRs, `release-please` label rules
4. **Linked work:** issue/ticket keywords (`Fixes #123`, Jira smart commits),
   required labels, CODEOWNERS expectations
5. **Recent merged PRs:** tone, language (EN/ZH), length, whether checklists are
   real or cargo-culted
6. **Screenshots / recordings:** UI projects may require before/after; CLI/API
   projects may require sample output or curl

**Precedence:** Fill the project template completely. If the template is empty
or missing, use **Why / What / Test** (plus Risk / Rollback when non-trivial).
Never invent test results you did not run.

## Workflow

### 1. Ground in the actual change

```text
git log <base>..HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

- Confirm base branch (usually `main` / `develop`) via
  `git-workflow-conventions`.
- Note user-visible behavior, API/config breaks, migrations, and feature flags.
- Collect issue/ticket IDs and design doc links if any.
- Redact secrets, tokens, private customer data from description and screenshots.

### 2. Write the title

Goals: scannable in the PR list; accurate for squash-merge history.

**Defaults when the repo is silent:**

```text
<type>: <imperative outcome>
<type>(<scope>): <imperative outcome>
```

Examples: `fix(auth): reject expired refresh tokens`,  
`feat: export billing CSV from dashboard`.

Rules:

- **One primary intent** — same bar as a good commit subject
- Imperative, specific outcome — not “update code” / “WIP” / “misc”
- Match Conventional Commit types if the team lints PR titles
- Ticket id in title **only** if team policy requires it (else link in body)
- ~72 characters when practical; no trailing period

### 3. Structure the body (Why / What / Test)

Use the repo template headings when present. Otherwise:

```markdown
## Why
<!-- Problem, user impact, or constraint. Link issue if any. -->

## What
<!-- Behavior change, approach, and notable non-changes / out of scope. -->

## Test
<!-- Commands run, scenarios covered, what was *not* tested. -->

## Risk / rollout
<!-- Optional: feature flag, migration, rollback, monitoring. -->
```

| Section | Answer |
| --- | --- |
| **Why** | Motivation: bug symptom, user story, debt that blocks work, security constraint. Prefer impact over “I refactored.” |
| **What** | Observable change and key design choices. Call out **breaking** changes, migrations, flags, and deliberate non-goals. |
| **Test** | Exact commands and scenarios (`npm test -- auth`, manual UI path, API cases). Say if CI-only or if something needs reviewer help. |
| **Risk / rollout** | For non-trivial work: blast radius, flag name, rollback steps, metrics/logs to watch. |

Optional sections when useful:

- **Screenshots / recordings** (UI)
- **API / schema notes** (contract diffs, OpenAPI)
- **Checklist** (template items honestly checked)
- **Related PRs** (stacked PRs: “depends on #N”)

### 4. Link issues and trailers

```markdown
Fixes #123
Closes #456
Refs #789
```

- Use the keywords the host recognizes for auto-close.
- Prefer links over pasting long external ticket text.
- Do not claim `Fixes` if the PR only partially addresses the issue—use `Refs`
  and state remaining work.

### 5. Reviewer-oriented pass

- Diff size honest: if huge, explain why or split (see
  `git-workflow-conventions`).
- Point reviewers at the **riskiest files** or decisions (2–4 bullets max).
- Mark **draft** until Why/What/Test are truthful and CI is understood.
- Update the description when the implementation pivots; stale PR bodies burn trust.
- Language: match team PR language (EN or 中文); bilingual only if the team does.

### 6. Hand off

- Request review after description + CI hygiene; CODEOWNERS as configured.
- Implementation quality remains `code-quality-standards`.
- Expect feedback phrasing from `code-review-comments-style` (as reviewer), not
  this skill.

## Examples

### Good

**Title:** `fix(auth): reject expired refresh tokens`

```markdown
## Why
Refresh tokens with `exp` in the past were still accepted when skew compensation
ran after signature checks, allowing session minting outside the intended window.
Fixes #1842.

## What
- Validate `exp` before creating a server session
- Add clock-skew allowance only for near-future `nbf`, not for expired `exp`
- No public API change; log reason code `refresh_expired` on reject

## Test
- [x] `npm test -- --grep refresh`
- [x] Manual: expired fixture token → 401; valid token → 200
- [ ] Not tested: multi-region clock skew beyond 30s (follow-up)

## Risk / rollout
Low. Fail-closed on expiry. Rollback = revert this PR. Watch `refresh_expired` rate.
```

**Title:** `feat(billing): export invoices as CSV`

```markdown
## Why
Finance ops export invoices weekly by hand from SQL. They need a self-serve CSV
from the dashboard (PROJ-842).

## What
- Adds **Export CSV** on the invoices list (current filters applied)
- Cap 10k rows; over-cap returns 413 with guidance to narrow filters
- Out of scope: scheduled email export

## Test
- [x] Unit tests for CSV columns and filter passthrough
- [x] Staging: filter last 30 days → download opens in Sheets
- Screenshot: attached (before/after control placement)
```

**Chinese team body (when PR language is 中文):**

```markdown
## 为什么
列表接口在未传工作区头时会串租户数据，见 #902。

## 改动
- `GET /items` 强制要求 `X-Workspace-Id`
- 缺省返回 400；文档已更新

## 测试
- [x] `go test ./api/...`
- [x] 手工：缺头 400，正确头 200
```

### Bad

**Title:** `update` / `fix stuff` / `WIP` / `asdf`

```markdown
## Description
Changed some files. Please review.
```

*Why bad:* no motivation, no scope, no verification; reviewer must reverse-engineer the diff.

```markdown
## What
- Modified AuthService.java
- Modified TokenValidator.java
- Modified tests
```

*Why bad:* file list is the diff; missing why and user-visible outcome.

```markdown
## Test
- [x] Tested
```

*Why bad:* not reproducible; no command or scenario.

```markdown
## Why
As per discussion.
## What
Major rewrite of the platform.
## Test
Trust me.
```

*Why bad:* unbounded scope; no evidence; not reviewable.

```markdown
## Test
- [x] All tests pass
```
*(author never ran tests; CI red)*

*Why bad:* dishonest checklist destroys trust.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| PR/MR title and body, 写 PR, Why/What/Test | **This skill** | — |
| Branch name, base branch, draft vs ready, split PR | `git-workflow-conventions` | — |
| Individual commit messages on the branch | `commit-message-conventions` | — |
| How to phrase review feedback on this PR | `code-review-comments-style` | `code-quality-standards` for substance |
| Code quality of the implementation | `code-quality-standards` | domain skill |
| Post-merge user-facing release notes | `changelog-and-release-notes` | PR body as input evidence |
| CONTRIBUTING “how to open a PR” docs | `readme-and-contributing-docs` | this skill for example PR shape |

## Checklist

- [ ] Repo PR template, title linters, and recent PR style read first
- [ ] Title states one clear outcome (Conventional type if required)
- [ ] **Why** explains problem/impact; issue linked with correct keyword
- [ ] **What** describes behavior and explicit non-goals / breaking changes
- [ ] **Test** lists real commands/scenarios; unchecked items are honest
- [ ] Risk, flags, migrations, and rollback noted when non-trivial
- [ ] Screenshots or sample output attached when UI/API contract needs them
- [ ] No secrets, tokens, prod data, or private customer identifiers
- [ ] Description matches the final diff (updated after pivots)
- [ ] Stacked/dependent PRs called out; base branch correct
- [ ] Language matches team PR norms (EN / 中文)

## Rules

- **Truth over theater:** never check “tested” without evidence; never claim fixes the issue only partially addresses without saying so.
- **Reviewer time:** lead with why and risk; do not paste the entire diff as prose.
- **Repo template first:** section names and required checklists from the project win.
- **One intent:** if the description needs “also” five times, split the PR (`git-workflow-conventions`).
- **Redact:** credentials, session cookies, internal-only URLs, and PII stay out of PR text and images.
- **Hand off:** process/branching to `git-workflow-conventions`; commit text to `commit-message-conventions`; review replies to `code-review-comments-style`.

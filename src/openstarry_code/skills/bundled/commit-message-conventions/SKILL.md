---
name: commit-message-conventions
description: >
  Write clear git commit messages using Conventional Commits (type, optional scope,
  subject/body/footer), emphasizing why the change exists rather than restating the
  diff. Use when drafting or reviewing a commit message, Conventional Commits,
  提交信息, git commit -m, changelog-friendly subjects, or breaking-change footers.
---

# Commit Message Conventions

Produce commit messages that are scannable in history, compatible with automated
changelog tooling, and useful to future readers who lack the author's context.

## Use When

- Drafting or rewriting a `git commit` subject/body (English or 提交信息)
- User asks for Conventional Commits / `type(scope): subject` format
- Preparing a message that should feed Keep a Changelog or release automation
- Reviewing whether a proposed message explains **why**, not only **what**
- Splitting work into commits and needing consistent type/scope choices

**Do not use as primary** when the task is only implementing code with no commit
step — use `code-quality-standards` (and domain skills) first; switch here when
the user asks to commit or to phrase the message.

## Repo Config First

Repository-local rules **outrank** this skill's defaults. Before writing a message:

1. **Commit / contrib docs:** `CONTRIBUTING.md`, `COMMIT.md`, `.github/PULL_REQUEST_TEMPLATE*`, team wiki notes on commits.
2. **Commitlint / hooks:** `commitlint.config.*`, `.commitlintrc*`, `package.json` → `commitlint`, `.husky/*`, `lefthook.yml`, `.pre-commit-config.yaml` (gitlint, conventional-pre-commit).
3. **Existing history:** recent `git log --oneline` (last 15–30) for real type set, scope names, language (EN/ZH), and subject style (imperative, casing, period rules).
4. **Monorepo scopes:** package or app names used as scopes (`web`, `api`, `billing`) — match those strings exactly.
5. **Release tooling:** `semantic-release`, `release-please`, `changesets`, `cliff.toml`, `git-cliff`, `cocogitto` — they define which types bump versions and appear in notes.

If local config conflicts with generic Conventional Commits advice, **follow the
repo**. If config is missing, use the defaults in this skill and stay consistent
with recent history.

## Workflow

### 1. Inspect the change

```text
git status
git diff --staged   # prefer staged; if empty, unstaged only with user OK
git log -15 --oneline
```

- Group by intent: one logical change per commit when the user wants history quality.
- Note user-facing vs internal-only impact (affects type and later changelog).
- Never put secrets, tokens, or full env values in the message.

### 2. Choose type (default Conventional Commits)

| Type | Use for |
| --- | --- |
| `feat` | New user-visible capability or API |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting/whitespace; no behavior change |
| `refactor` | Internal restructure; no intended behavior change |
| `perf` | Performance improvement |
| `test` | Tests only |
| `build` | Build system, dependencies packaging |
| `ci` | CI config and scripts |
| `chore` | Maintenance that does not fit above |
| `revert` | Reverts a previous commit |

Use repo-defined types if commitlint allows extras (`improve`, `security`, …).

### 3. Optional scope

- Short noun from the repo's vocabulary: module, package, feature area.
- Omit scope when the change is broad or scope would be noise.
- Prefer existing scopes from history over inventing synonyms.

### 4. Subject line (why-oriented, imperative)

Format:

```text
type(scope): subject

# or without scope
type: subject
```

Rules:

- **Imperative mood:** "add", "fix", "reject" — not "added" / "adds" / "fixed".
- **Lowercase subject** after the colon unless starting with a proper noun or acronym (unless repo history uses a different casing rule).
- **No trailing period** on the subject.
- **~50 characters target**, hard wrap awareness at ~72 for the whole first line when possible.
- Describe **motivation or outcome**, not a file list: the diff already shows what changed.
- Breaking change: either `type(scope)!: subject` or a `BREAKING CHANGE:` footer (or both if the repo expects both).

### 5. Body (when needed)

Add a body when the subject cannot carry enough context:

- Blank line after subject.
- Explain **why** (problem, constraint, risk) and any non-obvious approach.
- Mention side effects, migration needs, follow-ups.
- Wrap near 72 columns when writing multi-line prose.
- Bullet lists are fine for multiple drivers or consequences.

Skip the body for tiny, obvious one-liners **if** the subject already states the reason.

### 6. Footers

```text
BREAKING CHANGE: description of incompatibility and migration hint

Fixes #123
Refs #456
Reviewed-by: Name
```

- Use issue/ticket trailers the project already uses (`Fixes`, `Closes`, `Refs`, `Related`).
- Put breaking-change detail in the footer when consumers must act.

### 7. Deliver the message

- Prefer a HEREDOC or editor multi-line commit over `git commit -m` twice (subject/body clarity).
- Do not amend or force-push unless the user explicitly wants that.
- If the user only asked for the text, output the final message in a fenced block ready to paste.

## Examples

### Good

```text
fix(auth): reject expired refresh tokens at validation

Tokens with past exp were accepted when clock skew compensation
ran after signature checks. Validate exp before issuing sessions
so replay after logout windows fails closed.
```

```text
feat(api)!: require workspace id on list endpoints

BREAKING CHANGE: GET /items without X-Workspace-Id now returns 400.
Clients must send the header or use /workspaces/{id}/items.
```

```text
docs: explain local skill routing in Agents.md
```

```text
perf(search): cache parsed query AST for repeated filters

Profiling showed 30% of CPU on identical filter strings per request
batch. Cache is request-scoped to avoid cross-tenant leaks.
```

### Bad

```text
fix: update files
```

*Why bad:* no intent; "update files" is pure what-noise.

```text
Fixed the bug in AuthManager.java and UserService.java and also cleaned imports.
```

*Why bad:* past tense; filename dump; no reason; not Conventional Commits.

```text
feat: stuff
WIP
asdf
```

*Why bad:* placeholder; unshippable history.

```text
feat: add new feature

- modified a.ts
- modified b.ts
- modified c.ts
```

*Why bad:* body restates the diff instead of motivation or risk.

```text
chore: bump everything and refactor api and fix login and add tests
```

*Why bad:* multiple intents; should be split or narrowed to the primary why.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Write/review commit message | **This skill** | — |
| Implement or review the code being committed | `code-quality-standards` | domain skill |
| User-facing CHANGELOG / release notes | `changelog-and-release-notes` | this skill for per-commit subjects |
| PR description (broader than one commit) | `pr-description-writing` | this skill for each commit |
| Security fix commit | **This skill** (`fix` / repo type) | do not put exploit detail or secrets in message |
| Only running git mechanics (rebase help) | user/process | this skill only for message text |

## Checklist

- [ ] Read repo commitlint/CONTRIBUTING and matched recent `git log` style
- [ ] Staged diff understood; message matches **this** commit only
- [ ] Correct `type` and optional `scope` from project vocabulary
- [ ] Subject: imperative, concise, **why/outcome**, no trailing period
- [ ] `!` or `BREAKING CHANGE:` present when compatibility breaks
- [ ] Body adds context when non-obvious; does not list files for their own sake
- [ ] Footers use project ticket conventions when applicable
- [ ] No secrets, credentials, or sensitive personal data in the message
- [ ] Message language consistent with repo history (EN/ZH/mixed policy)

## Rules

- **Why over what:** the subject answers "why does this commit exist?"
- **One intent per commit** when shaping history; do not smuggle unrelated fixes under a vague chore.
- **Repo config first:** commitlint and local history beat generic blog style.
- **Honesty:** do not label a breaking API change as `chore` to silence release bots.
- **Redact:** never commit message content that belongs in a secret store.
- After writing messages intended for release automation, hand off aggregated notes to `changelog-and-release-notes`.

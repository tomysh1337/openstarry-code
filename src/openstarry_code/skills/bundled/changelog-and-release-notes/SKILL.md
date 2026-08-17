---
name: changelog-and-release-notes
description: >
  Maintain Keep a Changelog-style CHANGELOG entries and write user-facing release
  notes from commits, PRs, and version bumps. Use when changelog, release notes,
  更新日志, CHANGELOG.md, GitHub/GitLab releases, version announcements, or
  mapping Conventional Commits into Added/Changed/Fixed sections.
---

# Changelog And Release Notes

Turn shipped work into an accurate, scannable history for **humans** (operators,
users, integrators). Prefer user-facing impact over internal commit noise.

## Use When

- Adding or editing `CHANGELOG.md` / `CHANGES` / 更新日志
- Drafting GitHub/GitLab **Release** body or announcement copy
- Mapping a version bump (`vX.Y.Z`) to Added / Changed / Fixed / Security sections
- Summarizing merged PRs or Conventional Commits for a release cut
- Rewriting engineer-centric bullets into customer-readable notes

**Do not use as primary** for inventing product marketing unrelated to actual
changes, or for writing individual git commit subjects — use
`commit-message-conventions` for per-commit text.

## Repo Config First

Repository conventions **outrank** generic Keep a Changelog defaults:

1. **Existing changelog:** `CHANGELOG.md`, `CHANGELOG.rst`, `docs/changelog*`, `Changes.md`, locale-specific 更新日志 files — match heading levels, date format, and section names already in use.
2. **Versioning policy:** SemVer vs CalVer; `0.x` rules; whether unreleased work lives under `## [Unreleased]`.
3. **Automation:** Changesets (`.changeset/`), `release-please`, `semantic-release`, `git-cliff` / `cliff.toml`, `towncrier`, `standard-version`, `cocogitto`, GitHub Generated notes config (`.github/release.yml`).
4. **Commit rules:** commitlint / Conventional Commits types → which types appear in notes vs ignored (`chore`, `test`, `ci` often omitted from user notes).
5. **Audience docs:** `CONTRIBUTING.md` release sections, support matrix, upgrade guides linked from previous releases.
6. **Product language:** EN vs ZH, product names, "you" vs "we", trademark casing — copy recent release tone.

If the repo already generates notes from commits, **improve inputs** (commit quality, PR titles, labels) and only hand-edit the final notes when the project expects human curation.

## Workflow

### 1. Establish release bounds

```text
# Identify last release and current candidate
git tag --sort=-creatordate | head
git log <last-tag>..HEAD --oneline
git log <last-tag>..HEAD --pretty=format:"%h %s" 
```

- Confirm version number and date (ISO `YYYY-MM-DD` unless repo uses another form).
- Confirm channel: stable / RC / beta / hotfix — label clearly when not stable.
- List compare URL if the project links GitHub compares in the changelog.

### 2. Collect candidate changes

Sources (prefer evidence over memory):

| Source | Use |
| --- | --- |
| Commits since last tag | Primary inventory |
| Merged PR titles/descriptions | User intent and migration notes |
| Issue/ticket labels (`bug`, `enhancement`, `security`) | Section placement |
| Breaking-change footers / `!` commits | Upgrade callouts |
| Changeset files | Intended customer wording |

Exclude noise unless the repo includes it: formatting-only, CI-only, pure refactor with zero behavior change, revert pairs that cancel out.

### 3. Classify for Keep a Changelog sections

Default section order (omit empty sections):

| Section | Include |
| --- | --- |
| **Security** | Vulnerabilities fixed, auth hardening users should know |
| **Removed** | Features/APIs taken out |
| **Deprecated** | Still present; removal planned |
| **Added** | New capabilities |
| **Changed** | Behavior or defaults that existing users notice |
| **Fixed** | Bug fixes |
| **Performance** | Optional; use if the project already does |

Map Conventional Commits roughly as:

| Commit type | Changelog section |
| --- | --- |
| `feat` | Added (or Changed if it alters existing behavior) |
| `fix` | Fixed |
| `perf` | Changed or Performance |
| `refactor` | Usually omit; include only if behavior/contract shifts |
| `docs` | Omit from product notes unless docs are the product |
| `ci` / `test` / `chore` | Omit from user-facing notes |
| `BREAKING CHANGE` / `type!:` | Changed or Removed + prominent upgrade note |

Adjust mapping when release automation defines its own.

### 4. Rewrite for the audience

User-facing notes should answer: **What do I get or need to do?**

- Lead with outcome; put component names second.
- Name the user-visible surface (CLI flag, UI screen, API path, config key).
- Call out **actions required**: config renames, migrations, re-auth, min version bumps.
- Group related commits into **one** bullet when they ship as one story.
- Keep security notes honest but avoid exploit step-by-step detail; link to advisory IDs when public.
- Redact customer names, private URLs, tokens, and internal hostnames.

### 5. Structure the entry

**Keep a Changelog-style file entry:**

```markdown
## [Unreleased]

### Added
- …

## [1.4.0] - 2026-07-11

### Added
- Export reports as CSV from the dashboard.

### Fixed
- Refresh tokens no longer accepted after expiry.

### Changed
- **Breaking:** `GET /items` requires `X-Workspace-Id`. See upgrade notes below.
```

**Release / tag description (may be shorter):**

```markdown
## What's new
- …

## Fixes
- …

## Upgrade notes
- …
```

Link to full `CHANGELOG.md` when the release UI is a summary only.

### 6. Consistency pass

- Version heading matches the tag (`v` prefix policy: match existing tags).
- Newest entry **above** older ones.
- Each bullet is a complete, parallel phrase (start with a verb or consistent noun style — **match the file**).
- Same language as the rest of the changelog.
- Breaking changes duplicated into upgrade guide if the project keeps one.

### 7. Hand off

- If commits are too vague to summarize, fix message quality via
  `commit-message-conventions` for future history; for this release, recover
  intent from PR bodies and diffs.
- Do not invent features that are not in the tag range.

## Examples

### Good

```markdown
## [2.1.0] - 2026-07-11

### Added
- Two-factor authentication for web login (TOTP).

### Changed
- Password reset links expire after 30 minutes (was 24 hours).

### Fixed
- Billing CSV export truncated rows past 10,000.
```

```markdown
## [3.0.0] - 2026-07-11

### Removed
- Legacy `/v1/orders` endpoints. Use `/v2/orders`.

### Changed
- **Breaking:** configuration key `queue_workers` renamed to `workers.count`.
  Update deploy manifests before upgrading.
```

**Release blurb (product tone):**

```markdown
### Highlights
- Faster project search with cached filters
- Clearer error messages when SSO is misconfigured

### Upgrade notes
- Node 20+ is now required
```

### Bad

```markdown
## [2.1.0]

### Changed
- update code
- fix stuff
- refactor utils
- WIP
```

*Why bad:* no dates/sections useful to users; internal noise; empty meaning.

```markdown
### Added
- Modified `AuthService.java`, `TokenValidator.java`, and tests.
```

*Why bad:* file list, not user impact.

```markdown
### Fixed
- Fixed bug.
```

*Why bad:* no symptom or area; not verifiable.

```markdown
### Added
- Implemented revolutionary AI-powered synergy for all verticals.
```

*Why bad:* marketing fluff not grounded in the diff; oversell.

```markdown
### Security
- Full RCE exploit chain write-up with payload…
```

*Why bad:* dangerous detail in a public changelog; prefer advisory reference + impact summary.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CHANGELOG / release notes / 更新日志 | **This skill** | — |
| Single commit subject/body | `commit-message-conventions` | — |
| Code change quality before release | `code-quality-standards` | domain skill |
| Security advisory narrative | **This skill** (short user note) | formal advisory process outside this skill |
| Auto-generated notes only need label tuning | **This skill** (map labels/sections) | repo release bot docs |
| Pure version bump with no user deltas | **This skill** | document "no user-facing changes" if true |

## Checklist

- [ ] Repo changelog format, version scheme, and automation settings read first
- [ ] Range is correct: `<previous-tag>..<this-tag>` / Unreleased scope agreed
- [ ] Entries reflect **user-facing** impact; CI/test-only noise filtered
- [ ] Sections follow project taxonomy (Keep a Changelog or local variant)
- [ ] Breaking changes and required upgrade steps are explicit
- [ ] Security items listed without operational exploit detail; advisories linked if any
- [ ] Version, date, ordering, and compare links consistent with existing file
- [ ] Language/tone matches prior releases; no secrets or private hostnames
- [ ] Empty sections omitted; bullets grouped by story, not one bullet per tiny commit
- [ ] Tag/release body and `CHANGELOG.md` do not contradict each other

## Rules

- **Truth over polish:** never claim fixes or features outside the release range.
- **Humans first:** changelogs are for operators and users, not a dump of `git log`.
- **Repo config first:** match existing structure and generators before introducing Keep a Changelog from scratch.
- **Breakages visible:** breaking changes must not hide under "misc improvements."
- **Redact:** credentials, private URLs, customer identifiers stay out of public notes.
- Prefer improving Conventional Commit quality (`commit-message-conventions`) so the next release is cheaper to document.

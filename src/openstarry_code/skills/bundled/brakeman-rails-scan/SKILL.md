---
name: brakeman-rails-scan
description: >
  Run and triage Brakeman static analysis on Ruby on Rails apps you own:
  install/pin, repo config, confidence filters, JSON/SARIF reports, CI gates,
  ignore-file hygiene, and fix-then-rescan for SQLi, XSS, mass assignment,
  redirects, and related Rails sinks. Use when Brakeman, brakeman.yml,
  Rails SAST, brakeman -A, brakeman ignore, Rails security scan CI, or
  interpreting Brakeman High/Medium/Weak warnings on authorized codebases.
---

# Brakeman Rails Scan

Own **local and CI Brakeman** for Rails apps: pin the gem, honor repo config,
scan the right app root, triage by confidence and check type, gate PRs on
policy findings, and re-scan after fixes. Prefer existing `config/brakeman.yml`,
ignore files, and CI jobs. Hand full Rails hardening to
`rails-security-checklist`; hand gem CVEs to dependency-audit neighbors.

## When To Use

- Adding, fixing, or interpreting **Brakeman** on a Rails app or monorepo engine
- Wiring Brakeman into **CI** (fail on High/Medium, artifacts, required checks)
- Triaging warnings: confidence, check name, file/line, and false-positive ignores
- Diff-only or full scans before release; cleaning noisy or stale ignore entries
- Keywords: Brakeman, `brakeman.yml`, Rails SAST, `brakeman -A`, `.brakeman.ignore`

Do **not** use as primary for: general Rails checklist → `rails-security-checklist`;
gem CVE/`bundler-audit` only → dependency audit skills; unknown injection class
deep-dive → `injection-checking`; secrets vault/rotation →
`secrets-management-hygiene`; pipeline layout only → `ci-cd-pipeline-patterns`;
implementation baseline → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **App root:** `Rails.root` (engine paths, multi-app monorepo members)
2. **Brakeman config:** `config/brakeman.yml`, CLI flags in Makefile/Rake/CI
3. **Ignore file:** `config/brakeman.ignore` or `.brakeman.ignore` — owners + expiry
4. **Rails/Ruby version:** `Gemfile.lock` Brakeman pin vs floating latest
5. **Gate policy:** which confidence/severities fail CI; exception process
6. **Neighbors:** bundler-audit, RuboCop security, CodeQL, branch protection

Extend the real CI job and config; do not invent a second divergent ignore list.

## Workflow

### 1. Install and pin

```bash
# Prefer Gemfile :development / :test group, version-pinned
bundle add brakeman --group "development test" --version "~> 6.0"
bundle exec brakeman --version
```

Match CI Ruby/Bundler to the app. Document the pin in `Gemfile.lock`. Avoid
unguarded `gem install brakeman` on release-blocking jobs when the app uses Bundler.

### 2. Local full scan

From the Rails app root (matrix monorepo engines when multiple apps ship):

```bash
bundle exec brakeman
bundle exec brakeman -A                    # all checks, incl. optional
bundle exec brakeman -w2                   # min confidence (1=Weak..3=High)
bundle exec brakeman -f json -o brakeman.json
bundle exec brakeman -f sarif -o brakeman.sarif   # if supported by pin
```

Record command, app path, Brakeman version, and Rails version in any report.
Prefer **JSON/SARIF artifacts** over log-only output for triage and CI.

### 3. Scope and performance

| Need | Approach |
| --- | --- |
| Faster PR feedback | `--only-files` / changed paths when org allows; still run full on main |
| Noisy engine/vendor | Config `skip_files` / `skip_libs` only with documented reason |
| Force re-index | `--force` when cache looks stale after large moves |
| Quiet CI logs | `-q` plus file output; keep exit code meaningful |

Do not hide real app code under broad `skip_files` to “go green.”

### 4. CI gate

1. Checkout; setup Ruby from `.ruby-version` / `Gemfile`; `bundle install`.
2. Run **pinned** `bundle exec brakeman` with the same flags as local policy.
3. **Fail closed** per policy (commonly High+Medium, or `-w2` / org table).
4. Upload JSON/SARIF as artifacts; attach summary on PR when platform allows.
5. Required check via branch protection / `ci-cd-pipeline-patterns`.
6. Never print `RAILS_MASTER_KEY`, credentials, or production secrets in logs.

### 5. Triage, fix, ignore, verify

| Finding shape | Action |
| --- | --- |
| True positive (SQLi, XSS, mass assign, redirect, cmdi, …) | Fix at source; re-run Brakeman |
| Framework false positive | Prefer code/API change; else ignore with **reason + expiry + owner** |
| Deprecated check noise | Upgrade Brakeman; re-baseline ignores |
| Config-only (CSRF skip, `permit!`, render inline) | Fix config/controller; cross-check `rails-security-checklist` |
| Dependency CVE (not Brakeman) | Hand off to bundler-audit / SCA skills |

**Ignore hygiene:** every entry has check name, fingerprint/location, human
reason, owner, and review date. Delete stale ignores when code moves. Never
bulk-ignore High without security owner sign-off.

**Verify:** same pin and flags as CI are green; a deliberate High finding fails
the gate; monorepo shippable apps are all in the matrix; redacted reports only.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Brakeman install, scan, CI gate, ignore triage | **This skill** | — |
| Rails strong params, CSRF, sessions, headers checklist | `rails-security-checklist` | this for SAST evidence |
| Gem CVEs / bundler-audit / lockfile bumps | dependency audit / SCA skill | this for code sinks |
| Unclear multi-class injection methodology | `injection-checking` | this for Rails static hits |
| SQLi / XSS / SSRF deep dive | matching class skill | this for locations |
| Master key, credentials, ENV secrets | `secrets-management-hygiene` | this if Brakeman flags sinks |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, config, gate, and ignore policy are sound.

## Output Checklist

- [ ] Rails app root(s), existing `brakeman.yml` / ignore / CI job read first
- [ ] Brakeman version pinned via Bundler (not floating on gates)
- [ ] Full scan command documented; `-A` / confidence policy explicit
- [ ] JSON/SARIF (or org format) uploaded; tool + Rails version recorded
- [ ] Gate fails on policy severities; required check enforced
- [ ] Findings triaged: fix vs ignore with owner, reason, expiry
- [ ] No broad unjustified `skip_files`; monorepo matrix covers shippable apps
- [ ] Re-scan clean after fixes; secrets redacted from reports and logs
- [ ] Hand-offs: `rails-security-checklist`, injection class skills,
      dependency audit, `ci-cd-pipeline-patterns`, `code-quality-standards`
- [ ] Rules: repo-first config; evidence over ignore spam; authorized apps only

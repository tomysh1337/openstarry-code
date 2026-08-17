---
name: dependabot-config-hardening
description: >
  Harden GitHub Dependabot: complete .github/dependabot.yml coverage, safe
  schedules and groups, PR limits, private registries, ignore expiry, monorepo
  directories, Actions and Docker updates, and review/CI gates without blind
  auto-merge. Use when dependabot.yml, Dependabot security updates, package
  ecosystem entries, update grouping, open-pull-requests-limit, dependabot
  ignore, private registries, vendor allow, versioning-strategy, or hardening
  dependency bots on GitHub — hand pin/lock strategy to
  dependency-pinning-strategies and Renovate-only presets to that bot’s docs.
---

# Dependabot Config Hardening

Own **Dependabot YAML and update policy**: full ecosystem coverage, grouped
noise, secret-safe registries, and bot PRs that still pass checks and review—not lockfile pin theory or full SBOM/CVE inventory.

## When To Use

- Authoring or auditing `.github/dependabot.yml` / `dependabot.yaml`
- Enabling or tuning **version** and **security** updates per ecosystem
- Monorepo multi-`directory` / multi-`package-ecosystem` coverage gaps
- Groups, schedules, `open-pull-requests-limit`, cooldown, or PR thrash
- Private registries, vendor/allowlists, `insecure-external-code-execution`
- Mentions: Dependabot, dependabot.yml, security updates, dependency bot,
  grouped updates, Actions bumps, Docker updates via Dependabot

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Lockfiles, exact vs range, frozen CI | `dependency-pinning-strategies` |
| Registry namespace / typosquat confusion | `dependency-confusion` |
| SBOM, SCA/CVE, provenance, CI gates | `sbom-and-supply-chain` / `sbom-ci-enforcement` |
| Branch required checks / admin bypass | `branch-protection-rules` |
| CODEOWNERS path reviewers | `codeowners-review-routing` |
| Full pipeline shape / secrets in CI | `ci-cd-pipeline-patterns` |
| Renovate-only presets (no Dependabot) | document Renovate; keep this for GH Dependabot |

## Repo Config First

Org and repo policy **outrank** defaults below.

1. **Active config path:** `.github/dependabot.yml` (or `.yaml`); single source of truth
2. **Org Dependabot settings:** security updates, dependency graph, private registry secrets
3. **Ecosystems present:** npm/yarn/pnpm, pip/poetry/uv, bundler, cargo, gomod, maven/gradle, nuget, composer, docker, github-actions, terraform, etc.
4. **Monorepo roots:** workspace dirs, nested manifests/Dockerfiles — map each `directory`
5. **Branch protection:** required checks, code owners, bot merge permissions
6. **Existing ignore / pin debt:** eternal ignores, force-merge culture, dual Dependabot+Renovate conflicts
7. **Neighbors:** lockfiles, CODEOWNERS on lock/manifests, SCA workflows

**Precedence:** Follow live org Dependabot + repo YAML. Flag configs that omit
ecosystems, float Actions by mutable tags only, auto-merge majors without CI, or
store registry passwords in plaintext YAML.

## Workflow

### 1. Inventory coverage

| Check | Hardening target |
| --- | --- |
| Each deployable manifest root | Explicit `package-ecosystem` + `directory` |
| `.github/workflows` | `github-actions` at `/` (or workflow root) |
| Root and service Dockerfiles | `docker` per directory that owns the file |
| Missing lock/manifest pairs | Fix pins first (`dependency-pinning-strategies`) |

Prefer **one bot** for version PRs unless org splits security-only Dependabot from Renovate—never two bots fighting the same lockfile.

### 2. Schedule, limits, and grouping

1. **Interval:** weekly default; daily only when noise and CI capacity allow.
2. **`open-pull-requests-limit`:** bound the queue (e.g. 5–15) so reviews stay feasible.
3. **Groups:** batch patch/minor by ecosystem or app directory; keep **major** ungrouped or separate.
4. **Day/timezone:** align with review windows; avoid unplanned Friday major dumps.
5. **Cooldown** (when available): reduce flapping on rapid successive releases.

### 3. Versioning, ignores, and allow rules

1. **`versioning-strategy`:** match app vs library policy; apps usually favor lockfile-driven updates.
2. **`ignore`:** temporary only—record **reason + review date**; eternal ignores are silent CVE debt.
3. **`allow` / dependency-type:** optionally limit to direct deps if transitive noise dominates; do not drop security coverage without SCA elsewhere.
4. **`vendor: true`:** only when the repo truly vendors and CI understands vendor diffs.
5. **`insecure-external-code-execution`:** leave denied unless a documented ecosystem requires it.

### 4. Registries and secrets

1. Define **`registries:`** for private npm, Maven, Docker, NuGet, etc.; reference by name from each update entry.
2. Store tokens in **GitHub Dependabot secrets**, never in committed YAML or public fork logs.
3. Scope tokens **read-only**; rotate on leak; pair with `dependency-confusion` defenses.
4. Confirm private deps resolve without leaking creds into PR bodies or logs.

### 5. PR quality and merge gates

1. **Reviewers / assignees / labels:** route to owning teams; label `dependencies` for filters.
2. **Commit message prefix:** align with `commit-message-conventions` when using Conventional Commits.
3. **Target branch:** default trunk unless a release-train exception is documented.
4. **No blind auto-merge** of majors, install-script packages, or Actions majors without green checks and owner review (`branch-protection-rules`).
5. Prefer **grouped** patches with solid CI over force-merged single-dep spam.

### 6. Ecosystem notes and verify

| Ecosystem | Notes |
| --- | --- |
| **github-actions** | Prefer SHA-pinned actions; review third-party trust on bumps |
| **docker** | Pin digests where policy requires; review base image CVE notes |
| **npm / pnpm / yarn** | One entry per meaningful workspace `directory`; avoid duplicate thrash |
| **gomod / cargo / pip** | Lock/sum committed; bot PRs must keep frozen CI green |
| **terraform** | Module/provider updates separate from app language ecosystems |

**Verify:** Dependabot UI healthy (no auth errors); sample security/version PRs hit required checks; private registry resolves without secret echo; groups and ignore expiry documented.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| dependabot.yml, groups, limits, registries, security vs version updates | **This skill** | — |
| Lock/pin policy, frozen install, exact vs range | `dependency-pinning-strategies` | this for bot YAML |
| Typosquat / wrong registry host | `dependency-confusion` | registry blocks here |
| SBOM / CVE inventory | `sbom-and-supply-chain` | this for update cadence |
| Required checks, bot merge rights | `branch-protection-rules` | this for PR shape |
| Who reviews lock/manifest paths | `codeowners-review-routing` | this for labels/reviewers |
| CI install and cache keys | `ci-cd-pipeline-patterns` | frozen install + bot PRs |
| Config/manifest quality | `code-quality-standards` | **always** on YAML edits |

**Hand-offs:** Pin/lock → `dependency-pinning-strategies`; SCA/SBOM → `sbom-and-supply-chain`; protection → `branch-protection-rules`. Keep **this skill primary** for Dependabot YAML hardening.

## Output Checklist

- [ ] Sole active `.github/dependabot.yml`; syntax valid; dual-bot conflict checked
- [ ] Every critical ecosystem + monorepo directory has an update entry
- [ ] `github-actions` / `docker` entries present when those files exist
- [ ] Schedule, groups, and `open-pull-requests-limit` keep review load sane
- [ ] Majors gated; no blind auto-merge without CI + review
- [ ] Ignores have reason and expiry; no silent eternal pins
- [ ] Private `registries:` use Dependabot secrets; least-privilege tokens
- [ ] Vendor / `insecure-external-code-execution` flags exception-reviewed
- [ ] Reviewers/labels/target-branch align with CODEOWNERS and trunk policy
- [ ] Sample bot PR: checks green, secrets not leaked, lockfile coherent
- [ ] Hand-offs: pins → `dependency-pinning-strategies`; SBOM → `sbom-and-supply-chain`; gates → `branch-protection-rules`; quality → `code-quality-standards`

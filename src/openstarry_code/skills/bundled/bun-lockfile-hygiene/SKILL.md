---
name: bun-lockfile-hygiene
description: >
  Keep Bun installs reproducible: commit bun.lock (or migrate bun.lockb),
  frozen CI with bun ci / --frozen-lockfile, single package-manager story,
  workspace lock fidelity, and lock-diff review. Use when bun.lock, bun.lockb,
  bun install, bun ci, frozen-lockfile, Bun workspaces, lockfile migration,
  text lockfile, mixed npm/yarn/pnpm locks with Bun, or CI lock drift are in
  scope — hand multi-ecosystem pin/Renovate policy to dependency-pinning-strategies,
  npm lifecycle trust to npm-supply-chain-hygiene, and registry confusion to
  dependency-confusion.
---

# Bun Lockfile Hygiene

Own **Bun lockfile fidelity and install reproducibility**: authoritative lock
file, frozen CI, and `package.json` sync without mixed generators. Does not own
org-wide pin bots, SBOM gates, or full npm lifecycle policy.

## When To Use

- Adding, reviewing, or repairing **`bun.lock`** / legacy **`bun.lockb`**
- CI fails with **lockfile had changes, but lockfile is frozen** / InvalidLockfile
- Migrating **binary → text** lock (`bun.lockb` → `bun.lock`) or Bun major bumps
- Choosing **`bun ci`** vs `bun install` vs `--frozen-lockfile` / `--lockfile-only`
- Mixed trees: `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` beside Bun
- Workspaces, catalogs/overrides, or lock diffs after dep bumps
- Mentions: Bun lockfile, frozen lock, bun.lockb, reproducible bun install

Do **not** use as primary for: multi-ecosystem pins → `dependency-pinning-strategies`;
npm lifecycle deep-dive → `npm-supply-chain-hygiene`; registry confusion →
`dependency-confusion`; SBOM → `sbom-and-supply-chain` / `sbom-ci-enforcement`;
pipeline caches → `ci-cd-pipeline-patterns`; tokens → `secrets-management-hygiene`.

## Repo Config First

Repo and org package policy **outrank** defaults below.

1. **Installer story:** Bun-only vs accidental npm/yarn/pnpm on the same tree
2. **Lockfile present:** prefer committed **`bun.lock`** (text, Bun ≥1.2 default); note any **`bun.lockb`**
3. **Manifests:** root and workspace `package.json`; `workspaces`; `packageManager` / engines
4. **CI install:** `bun ci` or `bun install --frozen-lockfile`; Bun version pin (`oven-sh/setup-bun`, `.bun-version`)
5. **Registry / auth:** project `.npmrc` scopes; no tokens in git
6. **Lifecycle policy:** Bun `trustedDependencies` (and any `ignore-scripts` stance)
7. **Neighbors:** Dependabot/Renovate, SCA job, Docker/`bun install` layers, monorepo scripts

**Precedence:** Follow committed Bun lock + CI flags. Flag dual lockfiles, CI that runs bare `bun install` and rewrites the lock, or binary/text dual-commit without a migration plan.

## Workflow

### 1. Inventory

1. List every `package.json` (workspaces) and which lock file(s) exist at roots.
2. Classify lock state:

| State | Signal | Action |
| --- | --- | --- |
| **Healthy text** | Only `bun.lock` committed; CI frozen | Maintain |
| **Legacy binary** | `bun.lockb` only | Plan migrate to `bun.lock` |
| **Dual / mixed** | Both Bun locks or npm/yarn/pnpm locks too | Pick one manager; delete others after regenerate |
| **Missing lock** | Install mutates freely | Generate + commit for apps/services |
| **Drift** | Manifest ≠ lock; frozen CI fails | Regenerate lock intentionally; review diff |

3. Note Bun version local vs CI (lock format and resolve can differ across majors).

### 2. One lock, one installer

1. **Commit** the Bun lock for every deployable and product CI build.
2. Prefer **`bun.lock`** (text): readable diffs, better review. Migrate with team Bun version, e.g. regenerate via documented Bun flags (`--save-text-lockfile` / install path per current docs), then **delete `bun.lockb`** so only one Bun lock remains.
3. **Do not** keep `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` as a second source of truth on a Bun project—mixed generators corrupt trees and CI.
4. Never “fix” frozen CI by deleting the lock; regenerate on a controlled Bun version and commit with the manifest change.

### 3. Install and CI freeze

| Command | Role |
| --- | --- |
| `bun install` | Dev resolve; may update lock when manifests change |
| `bun install --frozen-lockfile` | Install exact lock; **fail** if lock would change |
| `bun ci` | CI-friendly frozen path (equivalent intent to frozen install) |
| `bun install --lockfile-only` | Refresh lock without needing a full local `node_modules` tree |

Rules:

1. **CI / release / image build:** `bun ci` or `bun install --frozen-lockfile` only.
2. Pin **Bun version** in CI to match the lock-producing toolchain when possible.
3. Cache keys must include **lockfile hash** + Bun/OS; a miss must still freeze from lock.
4. After any `package.json` bump, run install **locally (or bot)** so lock updates in the **same PR**; never land manifest-only changes that break frozen CI.
5. Do not hand-edit lock JSON/text for “quick fixes”—regenerate with Bun.

### 4. Review lock diffs

On every lock-touching PR, check:

1. **New packages** and unexpected transitive jumps
2. **Resolved hosts** / registry URLs (scope should match project `.npmrc`)
3. **Integrity / hash** changes without intentional upgrades
4. Git/HTTP/`file:` deps moving without a pin review
5. Lifecycle-bearing packages; align with Bun **`trustedDependencies`** policy when installs run scripts

Wide ranges in the manifest are fine only if the **lock** freezes what ships (apps always lock).

### 5. Verify

1. Clean `bun ci` (or frozen install) with cache miss: exit 0, lock **unchanged**.
2. Deliberately desync a dep range vs lock → frozen install **fails**.
3. Fresh clone on CI Bun version builds/tests green.
4. After text migration: only `bun.lock` remains; binary gone; frozen path still green.
5. No registry tokens or machine-local paths committed in lock/config.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| bun.lock / bun.lockb, bun ci, frozen install, Bun-only tree | **This skill** | — |
| Cross-ecosystem pins / Renovate schedule | `dependency-pinning-strategies` | this for Bun lock commands |
| npm lifecycle / postinstall malware deep-dive | `npm-supply-chain-hygiene` | this if tree is Bun-managed |
| Registry namespace confusion | `dependency-confusion` | this for Bun + npmrc hosts |
| SBOM / CVE gates | `sbom-ci-enforcement` | frozen install first |
| CI topology / lock-keyed caches | `ci-cd-pipeline-patterns` | this for install step body |
| Secrets in npmrc / CI | `secrets-management-hygiene` | this for lock auth surfaces |
| Manifest/CI quality | `code-quality-standards` | **always** on config changes |

Keep **this skill primary** until the Bun lock and frozen install path are correct; then hand off pins, SBOM, or lifecycle policy as needed.

## Output Checklist

- [ ] Workspaces + Bun version inventoried; single package-manager story
- [ ] Authoritative lock chosen: prefer committed **`bun.lock`**; no dual Bun/npm/yarn/pnpm truth
- [ ] Legacy `bun.lockb` migrated or explicitly retained with plan
- [ ] CI uses **`bun ci`** or **`bun install --frozen-lockfile`**; bare install not on green path
- [ ] Manifest and lock change **together**; no frozen drift
- [ ] Lock diffs reviewed (hosts, integrity, new pkgs, scripts / trustedDependencies)
- [ ] Cache keyed on lock + Bun; clean frozen install verified
- [ ] No tokens or laptop-only paths in lock/config
- [ ] Hand-offs: pins → `dependency-pinning-strategies`; npm scripts → `npm-supply-chain-hygiene`; confusion → `dependency-confusion`; SBOM → `sbom-ci-enforcement`
- [ ] `code-quality-standards` + `ci-cd-pipeline-patterns` when workflows change

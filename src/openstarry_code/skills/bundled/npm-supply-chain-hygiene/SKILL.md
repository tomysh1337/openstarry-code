---
name: npm-supply-chain-hygiene
description: >
  Harden the npm supply chain: committed lockfiles, frozen CI installs
  (npm ci), integrity hashes, .npmrc registry pin, and lifecycle-script
  risk (preinstall/install/postinstall/prepare). Use when package-lock.json,
  npm ci vs npm install, ignore-scripts, postinstall malware, registry.npmjs
  vs private registry, package.json scripts, or npm CI cache trust is in
  scope — hand multi-ecosystem pins to dependency-pinning-strategies,
  namespace confusion to dependency-confusion, and SBOM gates to
  sbom-ci-enforcement.
---

# npm Supply-Chain Hygiene

Own **npm install-time trust**: lockfile fidelity, CI install commands,
registry/auth config, and **lifecycle scripts** that run as the build user.
Does not own multi-ecosystem pin policy, SBOM legal format, or license law.

## When To Use

- Reviewing or fixing **`package-lock.json` / `npm-shrinkwrap.json`** drift
- CI uses **`npm install`** (rewrites lock) instead of **`npm ci`**
- Suspicious or unexpected **`preinstall` / `install` / `postinstall` / `prepare` / `prepublish`**
- Hardening **`.npmrc`** (registry, `always-auth`, scope maps, `ignore-scripts`)
- Audit of monorepo workspaces, optionalDeps, git/URL deps, or tarball installs
- Mentions: npm supply chain, lockfile integrity, lifecycle script, npm ci, postinstall

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Exact-vs-range / Renovate across ecosystems | `dependency-pinning-strategies` |
| Private vs public namespace confusion | `dependency-confusion` |
| SBOM generate/attest gates | `sbom-ci-enforcement` / `sbom-and-supply-chain` |
| License allow/deny | `license-compliance-scan` |
| Pipeline layout / fork PR secrets | `ci-cd-pipeline-patterns` |
| Registry token lifecycle / leak IR | `secrets-management-hygiene` |

## Repo Config First

Repo and org npm policy **outrank** defaults below.

1. **Manifests:** root and workspace `package.json`; engines / packageManager field
2. **Lockfile:** `package-lock.json` (or shrinkwrap); lockfileVersion; committed vs gitignored
3. **Installer:** npm vs yarn vs pnpm — one story; do not mix generators on the same tree
4. **CI jobs:** install command, cache key (lock hash), Node version (`.nvmrc` / setup-node)
5. **`.npmrc` / project + user:** registry, `@scope:registry`, `ignore-scripts`, proxy
6. **Script policy:** allowed lifecycle scripts, `ignore-scripts` in CI, review owners
7. **Neighbors:** Dependabot/Renovate, SCA job, private registry (Artifactory/GitHub Packages)

**Precedence:** Follow existing lock tooling and registry. Flag `npm install` that mutates
lock in CI, missing lock commit, or broad trust of third-party postinstall without review.

## Workflow

### 1. Inventory the resolve surface

1. List every `package.json` (workspaces via `workspaces` field or `packages/*`).
2. Confirm a **single** lockfile path CI uses; note lockfileVersion (v2/v3).
3. Table high-risk direct deps: git/HTTP URLs, `file:`, `link:`, `latest`/wide ranges,
   optionalDependencies that pull native toolchains, and packages with install scripts.
4. Capture `.npmrc` registry hosts and whether auth is required for all private scopes.

### 2. Lockfile and frozen CI

| Rule | Why |
| --- | --- |
| Commit lock for apps/services | Same tree in CI, laptop, and prod image build |
| **`npm ci`** in CI (not `npm install`) | Fails on lock/manifest mismatch; no silent rewrite |
| Cache keyed on lock hash | Poisoned or stale cache must not float versions |
| Review lock **diffs** | New packages, version jumps, resolved URL/host, integrity changes |
| Prefer integrity entries | Detect tarball swap when registry or CDN is compromised |

Never “fix” CI by deleting the lock or running `npm install` to force a green build.
Regenerate lock on a controlled runner with the team’s Node/npm major, then review the diff.

### 3. Lifecycle scripts (install-time code execution)

npm may run package scripts during install. Treat them as **untrusted code** until reviewed.

| Script | Typical trigger | Risk note |
| --- | --- | --- |
| `preinstall` / `install` / `postinstall` | Dependency install | Classic malware / crypto-miner vector |
| `prepare` | Install from git; local `npm install` | Runs on consumers of git deps |
| `prepublish` / `prepublishOnly` / `prepack` | Publish path | Can alter shipped tarball contents |
| Root `scripts` in app | Explicit `npm run` | Lower install risk; still review CI `npm run` |

Controls (pick what policy allows):

1. **`ignore-scripts=true`** in CI when the product does not need native compile steps;
   document exceptions (e.g. `sharp`, `esbuild`) installed in a controlled step.
2. Review **new or changed** install scripts on every lock/manifest PR.
3. Prefer packages that ship prebuilds over compile-at-install when possible.
4. Run installs in least-privilege CI (no cloud OIDC/deploy keys until after install if feasible).
5. Block unexpected network from install scripts in hardened runners when tooling exists.

### 4. Registry and auth hygiene

1. Pin default `registry=` and every `@scope:registry=` in committed project `.npmrc` or org template.
2. **Never** commit tokens; use CI secrets / OIDC to the private registry.
3. Fail closed if private scope resolves to `registry.npmjs.org` unexpectedly.
4. Avoid dual-index footguns that prefer public higher semver for internal names
   (`dependency-confusion` for full assessment).
5. Disable or gate `npm audit fix` that rewrites the tree without review in release branches.

### 5. Verify

1. Clean **`npm ci`** (cache miss): exit 0, lock unchanged. 2. Break lock vs manifest — `npm ci` fails.
3. Scripts-ignored path (if policy) still builds or exception list is explicit.
4. Dep-bump lock diff shows only expected name/version/integrity/resolved host; no secrets in logs.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| npm lock, `npm ci`, lifecycle scripts, `.npmrc` install trust | **This skill** | — |
| Cross-ecosystem pin/Renovate policy | `dependency-pinning-strategies` | this for npm details |
| Namespace / registry confusion | `dependency-confusion` | this for npmrc/ci |
| SBOM CI presence/attest | `sbom-ci-enforcement` | frozen `npm ci` first |
| License policy | `license-compliance-scan` | lock versions from here |
| Pipeline topology / caches / checks | `ci-cd-pipeline-patterns` | this for npm job body |
| npm tokens / leak / rotation | `secrets-management-hygiene` | this for token use sites |
| CI YAML / script quality | `code-quality-standards` | **always** |

Keep **this skill primary** for npm install-time hygiene; hand off SBOM, license, and org-wide pin bots when those are the main ask.

## Output Checklist

- [ ] Workspaces + lockfile path inventoried; one package manager story
- [ ] Lock committed for deployables; CI uses **`npm ci`** (or documented equivalent)
- [ ] Cache keyed on lock; no CI lock rewrite on green path
- [ ] Lifecycle scripts reviewed; `ignore-scripts` or exception list documented
- [ ] `.npmrc` scopes/registry pinned; no tokens in git
- [ ] Lock diffs checked for host/integrity/script-bearing new packages
- [ ] Verify: clean `npm ci`, fail on drift, no secret leakage
- [ ] Hand-offs: pins → `dependency-pinning-strategies`; confusion → `dependency-confusion`; SBOM → `sbom-ci-enforcement`; secrets → `secrets-management-hygiene`
- [ ] `code-quality-standards` + `ci-cd-pipeline-patterns` on workflow changes

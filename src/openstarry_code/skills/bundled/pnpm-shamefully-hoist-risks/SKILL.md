---
name: pnpm-shamefully-hoist-risks
description: >
  Assess and reduce pnpm shamefully-hoist / flat node_modules risk: phantom
  dependencies, undeclared requires, monorepo cross-package imports, and
  safer hoist alternatives (public-hoist-pattern, packageExtensions). Use when
  shamefully-hoist, public-hoist-pattern, hoist-pattern, node-linker=hoisted,
  phantom deps, flat node_modules, pnpm isolation breakages, or eslint/plugin
  resolve failures under strict pnpm are in scope — hand multi-ecosystem pins
  to dependency-pinning-strategies, npm lifecycle trust to
  npm-supply-chain-hygiene, and registry confusion to dependency-confusion.
---

# pnpm shamefully-hoist Risks

Own **pnpm hoisting policy and isolation tradeoffs**: when `shamefully-hoist`
(or equivalent flat linkers) hide missing declarations, widen the resolve
surface, and how to replace blanket hoist with narrow, documented exceptions.
Does not own lockfile pin strategy, SBOM gates, or registry namespace confusion.

## When To Use

- Enabling, reviewing, or removing **`shamefully-hoist=true`** in `.npmrc`
- **`public-hoist-pattern` / `hoist-pattern`** wildcards that effectively flatten the tree
- **`node-linker=hoisted`** (or legacy flat layout) adopted for “tooling compatibility”
- Runtime or CI failures that only appear under **strict pnpm** (missing module at
  require time) but green under hoisted/npm-like trees
- Phantom / undeclared dependencies, monorepo packages importing sibling deps
  without declaring them, or plugins that walk root `node_modules`
- Mentions: shamefully-hoist, public hoist, phantom dependency, pnpm strictness

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Lock pins, Renovate, frozen install policy | `dependency-pinning-strategies` |
| npm lifecycle scripts / `npm ci` hygiene | `npm-supply-chain-hygiene` |
| Namespace / dual-registry confusion | `dependency-confusion` |
| SBOM / SCA / provenance gates | `sbom-and-supply-chain` / `sbom-ci-enforcement` |
| Pipeline layout / cache keys | `ci-cd-pipeline-patterns` |

## Repo Config First

Repo and org package-manager policy **outrank** defaults below.

1. **Installer story:** pnpm only vs mixed npm/yarn generators on the same tree
2. **Config surfaces:** root/workspace `.npmrc`, `pnpm-workspace.yaml`, `package.json`
   `packageManager` / `pnpm.*` fields, env overrides in CI
3. **Hoist knobs:** `shamefully-hoist`, `public-hoist-pattern`, `hoist-pattern`,
   `node-linker`, `shamefully-hoist` in user vs project `.npmrc`
4. **Lockfile:** `pnpm-lock.yaml` committed; CI `pnpm install --frozen-lockfile`
5. **Workspaces:** package boundaries, shared tooling packages, app vs lib roles
6. **Compatibility debt:** comments/issues that forced hoist (ESLint, Jest, Metro, etc.)
7. **Neighbors:** Dependabot/Renovate, SCA job, private registry (`.npmrc` scopes)

**Precedence:** Prefer project-committed strict config over developer-global hoist.
Surface conflicts where CI is strict but local defaults hoist, or vice versa.

## Workflow

### 1. Inventory current hoist posture

1. Read project `.npmrc` / workspace npmrc fragments and CI env for hoist flags.
2. Classify posture:

| Posture | Signals | Risk level |
| --- | --- | --- |
| **Strict (default-ish)** | No shameful hoist; narrow public-hoist only | Baseline — good |
| **Targeted hoist** | Explicit package patterns (e.g. `*eslint*`) | Medium — document why |
| **Blanket hoist** | `shamefully-hoist=true` or `public-hoist-pattern=*` | High — phantom-dep cover |
| **Full flat linker** | `node-linker=hoisted` | High — npm-like layout |

3. Note whether hoist is temporary (migration) or permanent without owners.

### 2. Explain the risk model

pnpm’s strict layout exposes **undeclared** dependencies. Hoisting re-hides them.

| Failure mode | What happens | Why hoist “fixes” it badly |
| --- | --- | --- |
| **Phantom dependency** | Code `require`s a package not in its `package.json` | Package appears at root `node_modules` |
| **Peer/tooling resolve** | Plugins resolve from unexpected parents | Flattened tree mimics npm walk |
| **Monorepo leakage** | Package A imports B’s transitive dep | Shared root makes it resolvable |
| **Version surprise** | Wrong major selected after hoist collapse | Multiple versions dedupe to one path |
| **Portability break** | Works hoisted; fails strict CI or consumers | Environment-dependent resolve graph |

Hoist is **compatibility theater**, not a substitute for correct manifests.

### 3. Prefer fixes over shameful hoist

Apply in order; stop at the narrowest fix that unblocks:

1. **Declare the dependency** (or `devDependency` / `peerDependency`) in the package that imports it.
2. **`pnpm.packageExtensions`** (or `pnpm.peerDependencyRules`) to patch broken upstream manifests without flattening everything.
3. **Narrow `public-hoist-pattern`** for known tooling families only; comment the owning team and revisit date.
4. **Workspace protocol / explicit deps** for cross-package imports (`workspace:`) instead of relative accidental requires.
5. **`shamefully-hoist=true` or `node-linker=hoisted`** only as a **time-boxed** escape hatch with an issue tracking removal.

Never “fix CI” by enabling shameful hoist without recording the phantom deps found.

### 4. Detect phantoms before removing hoist

1. Turn off blanket hoist on a branch; run install + unit/lint/build.
2. Collect `Cannot find module` / unresolved import errors; map each to a declaring package.
3. Optionally use depcheck / pnpm-friendly lint rules / ESLint `import/no-extraneous-dependencies`.
4. Re-add **only** justified public-hoist patterns after declarations are fixed.
5. Ensure CI uses the **same** hoist settings as the committed project config (no silent global `.npmrc`).

### 5. Verify

1. Clean install with committed config (`--frozen-lockfile`); lock unchanged. 2. App and each workspace package build/test under **strict** settings.
3. Fresh clone without user-level hoist still works. 4. Lock/PR diff does not reintroduce `shamefully-hoist` or `public-hoist-pattern=*` without review notes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| shamefully-hoist, public-hoist, phantom deps, strict pnpm layout | **This skill** | — |
| Cross-ecosystem pins / Renovate / frozen policy | `dependency-pinning-strategies` | this for hoist flags |
| npm lifecycle / postinstall trust | `npm-supply-chain-hygiene` | this if pnpm hoist mixed with npm |
| Registry namespace confusion | `dependency-confusion` | npmrc scopes |
| SBOM / SCA gates | `sbom-ci-enforcement` | frozen install first |
| CI job topology / caches | `ci-cd-pipeline-patterns` | this for pnpmrc in jobs |
| Config/script quality | `code-quality-standards` | **always** |

Keep **this skill primary** for hoist/isolation policy; hand off pins, SBOM, and registry confusion when those dominate.

## Output Checklist

- [ ] Hoist posture classified (strict / targeted / blanket / flat linker)
- [ ] Config sources listed (project `.npmrc`, workspace, CI, user overrides)
- [ ] Phantom or monorepo leakage candidates identified from fail logs or tooling
- [ ] Fixes preferred: declare deps → packageExtensions → narrow public-hoist
- [ ] Blanket `shamefully-hoist` / `public-hoist-pattern=*` time-boxed or removed
- [ ] CI and local resolve settings aligned; frozen lock install
- [ ] Verify: strict clean install, workspace builds, no secret/token in npmrc
- [ ] Hand-offs: pins → `dependency-pinning-strategies`; npm scripts → `npm-supply-chain-hygiene`; confusion → `dependency-confusion`; SBOM → `sbom-ci-enforcement`
- [ ] `code-quality-standards` + `ci-cd-pipeline-patterns` on workflow/npmrc changes

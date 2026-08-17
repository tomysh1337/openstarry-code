---
name: gradle-dependency-locking
description: >
  Gradle dependency locking: enable locks, generate and commit lockfiles,
  update deliberately, and fail CI on drift so resolved graphs stay
  reproducible. Use when gradle.lockfile, dependencyLocking,
  lockAllConfigurations, --write-locks, resolution locks, locked
  configurations, or reproducible Gradle builds are in scope — hand
  multi-ecosystem pin policy to dependency-pinning-strategies and
  SBOM/CVE inventory to sbom-and-supply-chain.
---

# Gradle Dependency Locking

Own **Gradle’s built-in dependency locking**: which configurations lock, how
lockfiles are written and committed, and how CI refuses floating graphs. Prefer
repo Gradle version, multi-project layout, and existing lock paths. Hand
cross-ecosystem pin/update bots to `dependency-pinning-strategies`.

## When To Use

- Enabling or reviewing **`dependencyLocking`** / `lockAllConfigurations()`
- Generating, committing, or updating **`*.lockfile`** / `gradle.lockfile`
- **`--write-locks`**, partial updates, or per-configuration lock files
- CI that must **fail** when resolution drifts from committed locks
- Multi-project / composite builds where lock ownership is unclear
- Keywords: dependency locking, lockAllConfigurations, write-locks,
  resolutionStrategy locking, reproducible Gradle deps, lockfile conflict

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Cross-ecosystem lock/pin/bot policy | `dependency-pinning-strategies` |
| SBOM, SCA/CVE, provenance | `sbom-and-supply-chain` |
| Registry namespace confusion | `dependency-confusion` |
| CI graph/trust broadly | `ci-cd-pipeline-patterns` |
| Build script quality/tests | `code-quality-standards` |

## Repo Config First

Repo and org Gradle policy **outrank** defaults below.

1. **Gradle version / wrapper:** `gradle/wrapper/gradle-wrapper.properties`
2. **Build entrypoints:** root + subproject `build.gradle(.kts)`, `settings.gradle(.kts)`
3. **Existing locks:** `*.lockfile` locations; do not invent a second scheme
4. **Which configs lock:** `lockAllConfigurations()` vs selective locks
5. **CI tasks:** exact `./gradlew` flags (`--write-locks` only on intentional jobs)
6. **Neighbors:** version catalogs, BOM platforms, resolution rules, Renovate/Dependabot

**Precedence:** Follow existing lock layout and wrapper. Surface unlocked runtime
configs, committed unlock, or CI that regenerates locks on every build.

## Workflow

### 1. Inventory

Map projects and configurations that resolve for compile/runtime/test (and
plugin classpaths if the repo locks them). Note dynamic versions (`1.+`,
`latest.release`, ranges) and platforms/BOMs. List current lockfiles and owners.

### 2. Enable locking

```kotlin
dependencyLocking {
    lockAllConfigurations()
    // or lock only selected configurations per repo policy
}
```

Prefer the repo’s pattern (Kotlin DSL vs Groovy, convention plugins). Document
any intentional **unlocked** configurations and why.

### 3. Write and commit locks

```bash
./gradlew dependencies --write-locks
# or the repo’s documented resolve tasks that activate locking
```

Generate on a clean machine matching CI Java/Gradle. **Commit** lockfiles with
the build that requires them; never gitignore prod locks. Review diffs: new
modules, version jumps, unexpected repositories. Do not hand-edit lock contents.

### 4. Update deliberately

| Goal | Approach |
| --- | --- |
| Bump one coordinate | Change catalog/build version; re-run `--write-locks` |
| Refresh all locks | Coordinated PR; full resolve + review full lock diff |
| Merge conflict | Re-resolve with both parents’ intent; never delete locks |

Ship catalog/BOM edits and regenerated locks in the **same** PR. Bot PRs must
regenerate locks, not only the version line.

### 5. CI enforcement

Default pipeline: resolve/build **without** `--write-locks`; fail if graph ≠ lock.
Optional job may write locks and open a reviewable PR. Cache keys should include
lockfile content. Broader CI topology → `ci-cd-pipeline-patterns`.

### 6. Verify

Fresh clone + wrapper build succeeds without rewriting locks. A deliberate version
bump must require a lock update. Document commands run and coverage.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Gradle dependencyLocking, lockfiles, --write-locks, CI lock strictness | **This skill** | — |
| Multi-ecosystem pins, Renovate/Dependabot policy | `dependency-pinning-strategies` | this for Gradle locks |
| SBOM / CVE / provenance | `sbom-and-supply-chain` | this for locked tree |
| Registry confusion | `dependency-confusion` | lock + repository decls |
| Pipeline layout / caches | `ci-cd-pipeline-patterns` | this for lock flags |
| Build script quality | `code-quality-standards` | **always** on scripts |

- **`dependency-pinning-strategies`:** hand off org-wide pin/bot strategy; this skill owns Gradle lock APIs/files.
- **`code-quality-standards`:** always on `build.gradle(.kts)` / convention-plugin edits.
- Keep **this skill primary** until locking is enabled, committed, and CI-strict.

## Output Checklist

- [ ] Projects/configurations inventoried; dynamic versions noted
- [ ] Repo wrapper, DSL, and existing lock paths followed
- [ ] `dependencyLocking` enabled (all or selective per policy)
- [ ] Lockfiles generated via Gradle write path and committed
- [ ] Lock diffs reviewed on each intentional update
- [ ] Catalog/BOM bumps ship with regenerated locks in the same change
- [ ] CI builds without `--write-locks` and fails on drift
- [ ] Verify: clean clone build; deliberate bump requires lock update
- [ ] Routed: pin/bots → `dependency-pinning-strategies`; SBOM → `sbom-and-supply-chain`
- [ ] `code-quality-standards` on build-script changes

## Rules

- **Repo config first**; lockfiles are source of truth for resolved app versions.
- Never delete locks to clear conflicts—re-resolve. Prefer the Gradle wrapper.
- Do not claim lock write/verify without running the repo’s Gradle tasks.
- Hand SCA and multi-ecosystem pin policy to the skills above.

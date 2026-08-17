---
name: dependency-pinning-strategies
description: >
  Choose and enforce dependency pins: committed lockfiles, exact vs range
  versions, CI frozen installs, and Dependabot/Renovate update policy with
  supply-chain tradeoffs. Use when lockfiles, package-lock, yarn.lock,
  pnpm-lock, poetry.lock, go.sum, Cargo.lock, version ranges, caret/tilde,
  pin vs float, Dependabot, Renovate, or reproducible builds are in scope —
  hand SBOM/CVE inventory to sbom-and-supply-chain and license policy to
  license-compliance-scan.
---

# Dependency Pinning Strategies

Make **resolved trees reproducible and intentional**: lockfiles in git, frozen
CI installs, deliberate exact-vs-range policy, and Dependabot/Renovate that keep
human review. Owns **pin and update strategy** only—not SBOM/SCA or license law.

## When To Use

- Adding or fixing lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`,
  `poetry.lock`, `Pipfile.lock`, `go.sum`, `Cargo.lock`, `composer.lock`,
  `Gemfile.lock`, Gradle/`packages.lock.json`)
- Choosing **exact** pins vs **semver ranges** (`^`, `~`, `>=`, `*`, floating tags)
- CI install-from-lock only; Dependabot/Renovate groups, schedule, majors, ignore
- Reproducible builds, version drift, or blast-radius from unpinned installs
- Mentions: lockfile, pin deps, caret/tilde, Dependabot, Renovate, frozen install

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SBOM, SCA/CVE, provenance | `sbom-and-supply-chain` |
| SBOM CI gates / attestation | `sbom-ci-enforcement` |
| License allow/deny, NOTICE | `license-compliance-scan` |
| Registry namespace confusion | `dependency-confusion` |
| Pipeline layout / fork secrets | `ci-cd-pipeline-patterns` |
| Image digests / multi-stage | `dockerfile-best-practices` |

## Repo Config First

Repo and org package policy **outrank** defaults below.

1. **Manifests + lockfiles** present; monorepo workspace roots
2. **CI install commands** (`npm ci` vs `npm install`, Poetry/Cargo locked flags)
3. **Bot config:** `.github/dependabot.yml`, `renovate.json` / presets, org rulesets
4. **Registry config:** `.npmrc`, private indexes (confusion → `dependency-confusion`)
5. **App vs library:** libs may use consumer ranges; apps/services lock hard
6. **Existing SCA/license gates** — do not weaken via force-merge of bot PRs
7. **Neighbors:** Actions SHAs, image digests, toolchains (`.nvmrc`, `go.mod`)

**Precedence:** Follow existing lock tooling and bot presets. Surface conflicts that float prod deps, skip lock commits, or auto-merge majors without CI.

## Workflow

### 1. Classify the artifact

| Kind | Pin posture | Rationale |
| --- | --- | --- |
| **App / service / deployable** | Commit lock; frozen CI; exact or tight direct deps | Same tree in CI and prod |
| **Published library** | Semver ranges per ecosystem; still lock **dev** tooling | Consumer upgrade room; CI reproducible |
| **Internal package** | Org default; lock in consumer apps | Avoid dual truth across services |
| **Images / Actions / tools** | Digest or immutable SHA | Mutable tags float under you |

### 2. Lockfile rules

1. **Commit** lockfiles for every deployable and product CI build.
2. Never delete a lock to “fix conflicts” without regenerating on the team’s standard package-manager major.
3. **One installer story** (npm *or* yarn *or* pnpm; pip *or* Poetry *or* uv)—mixed generators corrupt trees.
4. **CI fails** on lock rewrite (`npm ci`, `yarn --immutable`, `pnpm --frozen-lockfile`, Cargo `--locked`, committed `go.sum` + verify).
5. Prefer **integrity hashes** (npm integrity, Poetry/Cargo/Go sums; pip hash mode when feasible).
6. Review lock **diffs**: new packages, jumps, URL/host changes, unexpected postinstall scripts.

### 3. Exact vs range (manifest policy)

| Spec | Meaning | Typical use |
| --- | --- | --- |
| Exact (`1.2.3`) | Only that version | Apps, high-risk deps, post-incident pins |
| Tilde (`~1.2.3`) | Patch float in minor | Rare without lock; avoid floating apps |
| Caret (`^1.2.3`) | Minor/patch in major | Library default; **apps still lock** |
| Wide (`*`, `latest`) | Unbounded float | **Avoid** on production resolve paths |
| Git/branch/URL | Moves unless commit-pinned | Prefer commit SHA + integrity |

**Rule:** ranges state *allowed* upgrades; the **lockfile** freezes what ships. Apps always lock. Libraries may range public deps; still lock CI/dev.

### 4. Dependabot / Renovate

1. One bot unless org mandates split; avoid dual conflicting configs.
2. **Schedule** + **group** patch/minor by ecosystem to cut noise.
3. **Separate majors**; human review + changelog/migration notes.
4. Require **green CI** (tests, frozen lock, SCA); no blind auto-merge of majors or install-script packages unless policy allows.
5. **ignore**/pin only with reason and **expiry** (eternal pins are silent debt).
6. Prefer lockfile-maintenance PRs over hand-edited lock JSON.
7. After merge: confirm prod install uses the new lock; regenerate SBOM when release policy requires (`sbom-and-supply-chain` / `sbom-ci-enforcement`).

### 5. Supply-chain tradeoffs

| Choice | Benefit | Cost / risk |
| --- | --- | --- |
| Strict lock + frozen CI | Reproducible, auditable | Needs bot or manual upgrades |
| Ranges without lock | “Always newest” illusion | Non-reproducible; silent break/malware versions |
| Auto-merge patches | Faster CVE fixes | Needs solid CI; watch mislabeled breaks |
| Pin forever (no bot) | Short-term stability | Stale CVEs, bit-rot |
| Digest-pin Actions/images | Resists tag rewrite | Plan deliberate base bumps |

Pinning **reduces surprise**; it does not replace SCA, license policy, or registry hygiene—hand those off below.

### 6. Verify

1. Fresh-runner frozen install (cache miss). 2. One deliberate direct-dep bump; lock coherent.
3. Bot PR + CI + lock diff; no surprise registry host. 4. Document app-lock vs lib-range policy.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Lockfiles, exact vs range, Renovate/Dependabot, pin tradeoffs | **This skill** | — |
| SBOM, CVE/SCA, provenance | `sbom-and-supply-chain` | this for pin policy |
| SBOM CI presence/attest gates | `sbom-ci-enforcement` | frozen install first |
| License allow/deny, NOTICE | `license-compliance-scan` | this for tree versions |
| Registry namespace confusion | `dependency-confusion` | lock URL integrity |
| CI stages / lockfile-keyed caches | `ci-cd-pipeline-patterns` | pin rules in jobs |
| Image digests | `dockerfile-best-practices` | app package pins |
| Manifest/CI quality | `code-quality-standards` | **always** on config |

**Hand-offs:** SBOM/CVE → `sbom-and-supply-chain` (+ `sbom-ci-enforcement` for gates); license → `license-compliance-scan`. Keep **this skill primary** for pin/update strategy only.

## Output Checklist

- [ ] Artifact kind classified (app vs library vs image/tool); pin posture chosen
- [ ] Lockfile committed (or explicit library exception with locked CI)
- [ ] CI frozen/immutable install; fails on lock drift
- [ ] Manifest ranges intentional; no `*` / `latest` on prod resolve paths
- [ ] Dependabot or Renovate: schedule, groups, majors gated, CI required
- [ ] Lock diffs reviewed (new pkgs, hosts, lifecycle scripts); integrity enabled
- [ ] Tradeoffs documented; no eternal pins without review path
- [ ] Hand-off: SBOM/CVE → `sbom-and-supply-chain`; license → `license-compliance-scan`
- [ ] `code-quality-standards` + `ci-cd-pipeline-patterns` on workflow/bot config


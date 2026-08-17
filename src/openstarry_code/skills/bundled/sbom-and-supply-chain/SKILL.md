---
name: sbom-and-supply-chain
description: >
  Generate and review Software Bills of Materials (SBOM), map direct and
  transitive dependencies, and harden software supply-chain hygiene across
  package managers, CI builds, and container images. Use when producing CycloneDX
  or SPDX SBOMs, reviewing third-party dependency risk, pinning and integrity
  policies, build provenance, or authorized supply-chain assessments — hand
  namespace/registry confusion to dependency-confusion and secret leaks to
  secrets-management-hygiene.
---

# SBOM And Supply Chain

## Scope And Authorization

- **In scope:** owned products and repos; org CI/CD; container registries you control; staging builds under SOW; authorized bug-bounty or vendor-assurance reviews that explicitly allow dependency / SBOM / supply-chain analysis of **named** targets.
- **Out of scope:** publishing malicious packages under third-party names; unsolicited mass registry scanning; compromising public maintainers; injecting malware into shared caches or public mirrors you do not own.
- Prefer **read-only inventory and resolve evidence** first. Gate install-script execution, canary publishes, and live registry mutation on written authorization (see `dependency-confusion`).
- Keep original lockfiles, CI logs, and generated SBOMs immutable; store derived risk tables and redacted reports separately.
- Redact registry tokens, `.npmrc` auth lines, private package coordinates when not required for remediation, and any secrets found in dependency trees (hand secret handling to `secrets-management-hygiene`).

## Use When

| Situation | Direction |
| --- | --- |
| Need CycloneDX/SPDX SBOM for a release, customer questionnaire, or audit | **This skill** |
| Review dependency freshness, licenses, known CVEs, and transitive depth | **This skill** |
| Harden pins, lockfiles, checksums, provenance, image digests | **This skill** |
| Private package name vs public registry resolve order | **`dependency-confusion`** (primary) |
| Engagement kickoff / multi-repo asset map before SCA | `recon-and-methodology` then this |
| Secrets in lockfiles, CI logs, or package tarballs | `secrets-management-hygiene` |
| Implementing CI gates / secure pipeline wiring | this + `ci-cd-pipeline-patterns` + `code-quality-standards` |
| ML model/dataset artifact chain (not general app deps) | `ai-ml-security` (subset) then this for code packages |

Do **not** use as primary for classic runtime injection (SQLi/XSS) — route to `injection-checking` and class skills after the app surface is known.

## Core Idea

A **Software Bill of Materials** answers: *what components, at which versions and hashes, came from where, into this build?*  
Supply-chain hygiene ensures those components are **intended**, **integrity-checked**, **minimally privileged at install time**, and **reproducible**.  
Your job: inventory → generate trustworthy SBOMs → analyze risk → enforce policy → verify in CI.

## Workflow

### 1. Inventory build inputs (before tooling)

1. List **roots**: application repos, monorepo packages, base images, IaC modules, browser extensions, mobile apps, Lambda layers.
2. Per root, collect:

   | Artifact | Examples |
   | --- | --- |
   | Manifests | `package.json`, `pyproject.toml` / `requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml` / `build.gradle*`, `*.csproj`, `Gemfile`, `composer.json` |
   | Lockfiles | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `go.sum`, `Cargo.lock`, `gradle.lockfile`, `packages.lock.json`, `Gemfile.lock`, `composer.lock` |
   | Image defs | `Dockerfile*`, compose, Helm values with image tags |
   | CI | workflows that install/build/publish |
   | Registries | npm scope config, PyPI index, Maven repos, NuGet feeds, container registries |

3. Flag missing lockfiles, dual indexes (`extra-index-url`), unpinned `latest` images, and postinstall/lifecycle scripts as high-priority hygiene issues.
4. If asset ownership is unclear, pause and complete scope via `recon-and-methodology`.

### 2. Generate SBOMs (reproducible, build-linked)

Prefer generating from the **same resolve path CI uses** (lockfile + install command), not from incomplete manifests alone.

| Ecosystem / target | Concrete techniques |
| --- | --- |
| Node (npm) | `npm ci` then Syft/Trivy/cdxgen on the project dir; or `npx @cyclonedx/cyclonedx-npm` against lockfile |
| Python | Poetry/pip-tools lock → Syft/cdxgen; ensure venv or container matches CI Python version |
| Go | `go list -m all` / Syft on module root with `go.sum` present |
| Java / Maven-Gradle | `mvn dependency:tree` / Gradle dependencies + Syft; include plugin classpath if policy requires |
| .NET | restore with lock file; Syft on project or publish output |
| Containers | Syft/Trivy on **image digest** after build: `syft packages registry:…@sha256:… -o cyclonedx-json` |
| Multi-stage images | SBOM the **final runtime image** and optionally the build stage if compilers ship into prod |

**Format choices:**

| Format | When |
| --- | --- |
| CycloneDX JSON | AppSec tooling, VEX, most SCA pipelines |
| SPDX | License compliance, some enterprise questionnaires |
| Both | Customer requires SPDX **and** security team uses CycloneDX |

Name outputs with product, version/git SHA, and format, e.g. `sbom-api-service-a1b2c3d.cdx.json`. Store next to release artifacts, not only on a laptop.

**Integrity of the SBOM itself:**

1. Generate in CI on trusted refs (`main`/tag), not only on developer machines.
2. Hash the SBOM file (`sha256sum`) and attach alongside release notes / attestations.
3. Prefer **build provenance** (SLSA-style attestations, Sigstore cosign attest, in-toto) linking commit → build → SBOM → image digest when the org supports it.

### 3. Review dependency risk (concrete analysis)

Work from the SBOM + lockfile, not from memory.

1. **Direct vs transitive:** mark which packages the app imports vs pulled-in; prioritize direct for upgrade control, transitive for unexpected reach (network, crypto, serialization).
2. **Known vulnerabilities:** run SCA (OSV, GHSA, vendor scanners) against the **same** SBOM/lockfile revision. Record CVE/GHSA id, fixed version, exploitability in *this* context (reachable function? dev-only? test scope?).
3. **License and policy:** deny-list copyleft or unknown licenses per org policy; flag dual-license ambiguity.
4. **Maintainer / publish signals (high level):** brand-new packages with huge version jumps, deleted GitHub repos, install scripts with network/`curl|sh`, typos of popular names — escalate typosquat and namespace issues to `dependency-confusion`.
5. **Abandoned / unmaintained:** years without release + open critical issues → plan replacement or vendor risk acceptance.
6. **Scope hygiene:** devDependencies / optional / peer deps that still ship into production images (mis-copied `node_modules`, wrong Docker stage).

```bash
# Illustrative authorized lab commands — adapt to org tools
syft packages dir:. -o cyclonedx-json > sbom.cdx.json
trivy sbom sbom.cdx.json
# Container by digest (preferred over mutable tag)
syft packages "ghcr.io/org/app@sha256:…" -o spdx-json > sbom.spdx.json
cosign verify --certificate-identity-regexp '…' "ghcr.io/org/app@sha256:…"
```

### 4. Supply-chain hygiene controls

Implement and review with `code-quality-standards` for policy-as-code quality:

| Control | Technique |
| --- | --- |
| Lockfiles committed | Require lockfile in PR CI; fail if install mutates lock without review |
| Integrity / checksums | npm `package-lock` integrity; Poetry/Cargo/Go sums; pip hash-checking mode where feasible |
| Pin actions and base images | GitHub Actions by SHA; container base `@sha256:…` or immutable digest in deploy |
| Disable untrusted lifecycle scripts | npm `ignore-scripts` in CI where compatible; review packages that require scripts |
| Registry policy | Single authoritative registry/proxy; no dual public+private merge for internal names → `dependency-confusion` |
| Allow / deny lists | Org-approved package prefixes; block risky licenses and known-malicious names |
| Minimal install surface | Production images: runtime deps only; multi-stage builds (`dockerfile-best-practices`) |
| Provenance | Sign images; attach SBOM attestation; verify on deploy |
| Secret hygiene | No tokens in package tarballs, `.env` in build context, or CI logs → `secrets-management-hygiene` |
| Update discipline | Dependabot/Renovate with grouped PRs, CI green required, human review for major majors / install scripts |

### 5. CI integration pattern

1. **PR:** resolve deps with frozen lockfile; optional fast SCA on changed manifests; fail on critical policy (e.g. install from non-allowlisted host).
2. **Main / tag:** full SBOM generation; SCA with severity gate; publish SBOM artifact; sign/attest.
3. **Deploy:** pull by digest; verify signature/provenance; reject `:latest` for production.
4. Pair pipeline structure with `ci-cd-pipeline-patterns` (fork PR secret isolation, cache poison resistance).

### 6. Authorized assessment angle (bounty / pentest vendor assurance)

When the program or SOW allows supply-chain review:

1. Confirm **in-scope** artifacts (public GitHub org packages, mobile app binaries, disclosed Docker Hub images, customer-provided SBOM).
2. Diff claimed SBOM vs what you extract from a release binary/image when both are available.
3. Check for **lockfile / registry confusion** signals without unauthorized squatting — hand deep namespace work to `dependency-confusion`.
4. Report missing SBOM, unsigned releases, or production images built from unpinned bases as process findings with clear business impact (update lag, incident response blindness).
5. Never claim “supply chain compromised” without evidence of malicious component or broken integrity control — separate **hygiene gap** from **active compromise**.

### 7. Remediation and verification

1. Upgrade or replace vulnerable packages; re-lock; regenerate SBOM; confirm advisory cleared or document exception with expiry.
2. Re-resolve offline or against allowlisted registry only — build must not silently fetch unexpected hosts.
3. For images: rebuild, new digest, new SBOM, signature still verifies.
4. Spot-check that secrets found during review were rotated if exposure was real (`secrets-management-hygiene`).

## Concrete Techniques Cheat Sheet

| Goal | Approach |
| --- | --- |
| SBOM from source tree | Syft/cdxgen/Trivy on repo after clean `ci`-equivalent install |
| SBOM from image | Syft/Trivy on digest; compare multi-arch manifests |
| License bill | SPDX SBOM or dedicated license scanner on lockfile |
| Reachability (optional) | Call-graph / SCA “reachable vuln” modes when available — mark residual risk if not |
| Install script audit | Review `package.json` scripts, Python `setup.py`/`pyproject` build backends, Ruby extensions |
| Typosquat screen | Compare internal names and top deps against public registry occupancy (`dependency-confusion`) |
| GitHub Actions supply chain | Pin actions to commit SHA; prefer official/org actions; review `pull_request_target` |
| Binary without source | Extract strings/deps from container layers or language-specific metadata; state confidence limits |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SBOM generation, SCA, pins, provenance, general dep hygiene | **This skill** | — |
| Private vs public package namespace / resolve order | `dependency-confusion` | this skill for SBOM evidence |
| Incomplete asset/repo/CI inventory | `recon-and-methodology` | then this skill |
| Secrets in deps, CI, images, or manifests | `secrets-management-hygiene` | this skill for discovery path |
| Secure implementation of gates and config-as-code | `code-quality-standards` | this skill for what to enforce |
| CI stage wiring, caches, fork PR trust | `ci-cd-pipeline-patterns` | this skill for SBOM job content |
| Dockerfile runtime surface | `dockerfile-best-practices` | this skill for image SBOM |
| ML model/dataset provenance | `ai-ml-security` | this skill for pip/npm around serving code |

## Checklist

- [ ] Scope and authorization confirmed for repos, registries, and images
- [ ] Manifests, lockfiles, Dockerbases, and CI install paths inventoried
- [ ] SBOM generated from CI-equivalent resolve path (CycloneDX and/or SPDX)
- [ ] SBOM named with product + version/SHA; hashed and stored with release
- [ ] Direct vs transitive mapped; high-risk install scripts noted
- [ ] SCA results triaged (severity, fix version, exploitability / context)
- [ ] License policy check done where required
- [ ] Registry and pin policy reviewed; confusion candidates handed to `dependency-confusion`
- [ ] Image tags avoided in prod; digests and (if available) signatures verified
- [ ] Secrets findings routed to `secrets-management-hygiene`; tokens redacted in reports
- [ ] CI gates: lockfile integrity, optional severity fail, SBOM publish on release
- [ ] Remediation retested with regenerated SBOM and clean resolve hosts
- [ ] Hygiene gaps vs active compromise clearly distinguished in write-up

## Rules

- Authorized targets only; no malicious public package publication.
- Prefer lockfile- and digest-backed evidence over “scanner said critical” without version context.
- Generate SBOMs from the real build path; a hand-edited component list is not an SBOM.
- One change at a time when validating upgrades (single package or coordinated set) so regressions are attributable.
- Do not exfiltrate private packages or customer SBOMs beyond the engagement agreement.
- Redact credentials and internal registry auth from all examples and tickets.
- Combine with `code-quality-standards` when writing or reviewing the enforcement code and pipeline config.
---

# Note

This skill is the **primary** entry for SBOM production and broad dependency supply-chain hygiene. For **namespace/registry confusion** attacks and defenses, switch primary skill to `dependency-confusion` and keep SBOMs as shared evidence.

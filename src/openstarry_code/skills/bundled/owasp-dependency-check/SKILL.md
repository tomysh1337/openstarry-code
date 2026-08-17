---
name: owasp-dependency-check
description: >
  Run and gate OWASP Dependency-Check (ODC) for multi-ecosystem SCA: CLI and
  build plugins, NVD data updates, suppression files, CVSS fail thresholds, and
  HTML/JSON/SARIF reports in local and CI pipelines. Use when dependency-check,
  OWASP Dependency-Check, ODC, dependency-check-maven, dependency-check-gradle,
  NVD API key, suppression.xml, failBuildOnCVSS, CPE/CVE jar scan, or wiring
  Dependency-Check into GitHub Actions/GitLab CI for owned or authorized code.
---

# OWASP Dependency-Check

Own **OWASP Dependency-Check (ODC)** scans and gates: install/pin the tool or
plugin, refresh vulnerability data, scan the right project paths, triage CPE/CVE
noise with suppressions, fail CI on policy CVSS, and recheck after upgrades.
Prefer repo plugins and existing CI jobs. Hand multi-lang SBOM inventory to
`sbom-and-supply-chain`; lockfile pin policy to `dependency-pinning-strategies`;
Go-only reachability gates to `go-govulncheck-workflow`.

## When To Use

- Adding or fixing **OWASP Dependency-Check** CLI, Maven, Gradle, or Ant plugins
- Interpreting **CPE matches**, CVSS scores, false positives, and suppressions
- Wiring **NVD API key**, data directory cache, and scheduled DB updates in CI
- Failing PRs/main on CVSS thresholds; HTML/JSON/XML/SARIF report artifacts
- Keywords: dependency-check, ODC, `dependency-check.sh`, failBuildOnCVSS,
  suppression.xml, NVD, CPE, OSS Index (if configured)

Do **not** use as primary for: lockfiles/ranges → `dependency-pinning-strategies`;
registry namespace confusion → `dependency-confusion`; multi-lang SBOM/provenance →
`sbom-and-supply-chain`; SBOM presence gates → `sbom-ci-enforcement`; license
allow/deny → `license-compliance-scan`; Go vulndb reachability →
`go-govulncheck-workflow`; CVE clocks → `vulnerability-sla-process`; pipeline
layout → `ci-cd-pipeline-patterns`; implementation quality → `code-quality-standards`.

## Repo Config First

Repo and org SCA policy **outrank** defaults below.

1. **Build roots:** `pom.xml`, `build.gradle*`, monorepo modules, lockfiles present
2. **Existing ODC config:** plugin blocks, `dependency-check-suppressions.xml`, props
3. **CI workflows:** current SCA jobs, cache keys, required check names
4. **Secrets:** `NVD_API_KEY` (or org equivalent)—never commit keys
5. **Gate policy:** CVSS fail threshold, severity allowlist, exception/expiry process
6. **Neighbors:** Dependabot/Renovate, SBOM job, license scan, branch protection

Extend the real build’s module roots; do not invent a divergent scan path.

## Workflow

### 1. Install and pin

Prefer the **build plugin** when the project is Maven/Gradle; otherwise pin CLI:

```bash
# CLI (org-approved version; avoid floating latest on gates)
dependency-check --version
```

Maven/Gradle: pin plugin version in the build file or parent BOM. Document the
pin in workflow or Makefile. Match Java runtime to plugin requirements.

### 2. Data update and NVD access

1. Set **NVD API key** via env/secret so updates are not rate-throttled to failure.
2. Cache the ODC **data directory** across CI runs; still refresh on schedule.
3. First run or stale cache: allow a longer job timeout for NVD download.
4. Record tool version + data update time in any report or ticket.

```bash
dependency-check --updateonly   # optional pre-warm
dependency-check --project "app" --scan ./path --format HTML --format JSON \
  --out ./odc-report --nvdApiKey "$NVD_API_KEY"
```

### 3. Scope the scan

| Target | How to include |
| --- | --- |
| App source + manifests | `--scan` project root / plugin default project |
| Built jars/wars | Scan `target/` or release artifact path |
| Multi-module | Each deployable module or aggregator root |
| Node/Python/etc. | Ensure lockfiles present; enable analyzers policy allows |

Exclude test-only or generated trees only with documented rationale. Prefer
scanning **what ships** plus **resolved dependency trees**.

### 4. CI gate

1. Restore ODC data cache; inject NVD key from secrets.
2. Run **pinned** CLI or plugin on each shippable path.
3. **Fail closed** with `failBuildOnCVSS` (or CLI equivalent) per org policy.
4. Upload HTML + JSON/SARIF as artifacts—not log-only.
5. Required check via branch protection / `ci-cd-pipeline-patterns`.
6. Never print API keys; redact internal coordinates if policy requires.

### 5. Triage, suppress, fix

| Finding shape | Action |
| --- | --- |
| True positive, direct dep | Upgrade; retest; regenerate lock if used |
| True positive, transitive | Bump intermediate; avoid eternal force/replace |
| Wrong CPE / false positive | Suppression with **reason + expiry**; link evidence |
| Unfixable / accepted risk | Ticket owner, SLA, time-boxed suppression |
| Analyzer noise (test jar) | Narrow scan path or documented exclude |

Suppressions are **exceptions**, not the default fix. After upgrades: rebuild,
re-run ODC with the same pin, confirm gate green. SLA → `vulnerability-sla-process`.

**Verify:** same pin/command as CI; intentional high-CVSS fixture fails the gate;
monorepo modules covered; cache does not permanently skip updates; secrets redacted.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| ODC CLI/plugin, NVD update, CVSS gate, suppressions | **This skill** | — |
| Lockfiles, pin vs range, Renovate/Dependabot | `dependency-pinning-strategies` | this after tree is stable |
| Multi-lang SBOM / SCA inventory | `sbom-and-supply-chain` | this for ODC gate |
| SBOM file/attest presence gate | `sbom-ci-enforcement` | this for CVE content |
| License allow/deny, NOTICE | `license-compliance-scan` | this for version evidence |
| Go-only govulncheck reachability | `go-govulncheck-workflow` | this if multi-lang ODC also runs |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection evidence |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, data update, scan scope, and gate policy are correct.

## Output Checklist

- [ ] Repo manifests, existing ODC/plugin config, and CI SCA job read first
- [ ] ODC CLI or plugin version pinned (not floating latest on release gates)
- [ ] NVD API key via secret; data directory cached and periodically refreshed
- [ ] Scan covers shippable modules/artifacts; formats HTML + machine-readable
- [ ] CVSS/fail policy clear; reports uploaded; required check enforced
- [ ] Findings triaged; suppressions have reason + owner + expiry
- [ ] Upgrades retested with same pin; monorepo matrix complete
- [ ] Secrets redacted; same pin/command as CI verified
- [ ] Hand-offs: `dependency-pinning-strategies`, `sbom-and-supply-chain` /
      `sbom-ci-enforcement`, `vulnerability-sla-process`, `code-quality-standards`
- [ ] Rules: repo-first pin; fix over silent suppress; authorized repos only

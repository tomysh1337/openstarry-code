---
name: maven-dependency-check
description: >
  Run and gate OWASP Dependency-Check on Maven projects: plugin config, NVD/API
  keys, suppressions, report formats, CI fail builds, and upgrade paths for
  owned Java/Maven modules. Use when dependency-check-maven, OWASP dependency
  check, Maven CVE scan, NVD API key, suppression.xml, dependency-check:check,
  failBuildOnCVSS, or wiring Dependency-Check into Maven CI/GitHub Actions.
---

# Maven Dependency-Check

Own **local and CI OWASP Dependency-Check** for Maven: pin the plugin, configure
NVD access, suppress false positives with evidence, fail on CVSS policy, and
fix-then-recheck. Prefer repo POMs and existing CI. Hand multi-lang SBOM/SCA to
supply-chain skills; pins/bots to `dependency-pinning-strategies`.

## When To Use

- Adding or fixing **`dependency-check-maven`** (or CLI) in Maven workflow/CI
- Interpreting findings: CPE/GAV match quality, direct vs transitive jars
- Setting **failBuildOnCVSS**, formats (HTML/JSON/SARIF), data-directory cache
- Managing **suppression.xml** with expiry, justification, and owner
- Keywords: OWASP Dependency-Check, NVD, CVE gate, `dependency-check:check`

Do **not** use as primary for: lock/pin → `dependency-pinning-strategies`; SBOM →
`sbom-and-supply-chain` / `sbom-ci-enforcement`; CVE clocks → `vulnerability-sla-process`;
pipeline layout → `ci-cd-pipeline-patterns`; Java style → `java-style-and-javadoc`;
quality baseline → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **POMs:** root/parent `pom.xml`, modules, BOM imports, pluginManagement
2. **Existing plugin:** `org.owasp:dependency-check-maven` version and goals
3. **CI:** Maven cache, required check names, secrets for NVD/API
4. **Data & suppressions:** committed suppressions file, shared data directory
5. **Gate policy:** CVSS fail threshold, exception/expiry process
6. **Neighbors:** Dependabot/Renovate, SBOM job, license scan, branch protection

Extend the real Maven reactor; do not invent a divergent module set.

## Workflow

### 1. Pin the plugin

In parent/root `pluginManagement`, pin a **known** version (not `LATEST`/`RELEASE`
on release-blocking jobs):

```xml
<plugin>
  <groupId>org.owasp</groupId>
  <artifactId>dependency-check-maven</artifactId>
  <version><!-- org-approved pin --></version>
</plugin>
```

Document the pin in POM and CI. Align JDK/Maven with the project toolchain.

### 2. Local scan

From the reactor root (or each deployable module if CI is matrixed):

```bash
mvn -q org.owasp:dependency-check-maven:check \
  -Dformats=HTML,JSON -DfailBuildOnCVSS=7
```

Prefer the POM-declared version. Record plugin version, Maven/JDK, and module path.

### 3. NVD / data directory

1. Prefer an **NVD API key** (org secret); never commit keys.
2. Cache the Dependency-Check **data directory** across CI runs (same path).
3. Fail clearly when DB update is blocked; document mirror/proxy if required.

### 4. Suppressions (false positives only)

1. Commit a **suppression file** and reference it from plugin config.
2. Suppress only with CVE/CPE id, **why**, owner, and **expiry**.
3. Prefer upgrading when the match is correct; review suppression diffs in PRs.

### 5. CI gate

1. Setup JDK/Maven; restore `.m2` and DC data cache.
2. Run **pinned** `dependency-check:check` (or `aggregate` for multi-module).
3. **Fail closed** on `failBuildOnCVSS`; upload HTML/JSON/SARIF; inject NVD key via secrets.

```yaml
- name: Dependency-Check
  run: mvn -B org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7
  env:
    NVD_API_KEY: ${{ secrets.NVD_API_KEY }}
```

(Wire the key into the plugin property name used by the repo.)

### 6. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| Direct dep, correct CPE | Bump version; retest |
| Transitive | Override/BOM or upgrade intermediate; avoid blind exclusions |
| Wrong CPE / unused artifact | Suppression with evidence + expiry |
| Test/provided only | Scope-aware triage; still fix if shipped |
| No fix available | Ticket + SLA (`vulnerability-sla-process`); time-box exception |

After bumps: `mvn -q test` (or verify). Pin debt → `dependency-pinning-strategies`.
Ticket SLA → `vulnerability-sla-process`.

**Verify:** same pin as CI is green; intentional old CVE fails; all shippable modules covered; redact private URLs/creds.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| OWASP Dependency-Check Maven local/CI, CVSS gate, suppressions | **This skill** | — |
| Lock/pin, Renovate/Dependabot for Maven | `dependency-pinning-strategies` | this for CVE content |
| Multi-lang SBOM / SCA inventory | `sbom-and-supply-chain` | this for Maven gate |
| SBOM file/attest presence gate | `sbom-ci-enforcement` | this for vuln content |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection evidence |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Java style after upgrades | `java-style-and-javadoc` | after build is green |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on POM/CI changes |

Keep **this skill primary** until plugin pin, data/NVD, suppressions, and gate behavior are correct.

## Output Checklist

- [ ] Root/parent POM, modules, and existing Maven CI job read first
- [ ] `dependency-check-maven` version pinned (not floating on gates)
- [ ] NVD/API access + data-dir cache configured; secrets not committed
- [ ] Scan covers shippable reactor modules (`check` / `aggregate` as needed)
- [ ] HTML/JSON/SARIF uploaded; plugin version recorded; required check enforced
- [ ] `failBuildOnCVSS` (or org policy) clear; findings triaged with owner/expiry
- [ ] Suppressions justified and expiring; upgrades preferred over suppress
- [ ] `mvn test`/`verify` after bumps; monorepo coverage complete; secrets redacted
- [ ] Hand-offs: `dependency-pinning-strategies`, `vulnerability-sla-process`,
      `sbom-and-supply-chain` / `sbom-ci-enforcement`, `code-quality-standards`
- [ ] Rules: repo-first pin; evidence over silent suppress; authorized modules only

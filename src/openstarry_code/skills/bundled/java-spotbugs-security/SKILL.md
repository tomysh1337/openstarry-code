---
name: java-spotbugs-security
description: >
  Run and gate SpotBugs (and FindSecBugs) for Java/JVM security static analysis:
  plugin setup, confidence/rank filters, Maven/Gradle/CI wiring, suppressions
  with owners, and triage of SECURITY-category bugs. Use when SpotBugs,
  FindBugs successor, FindSecBugs, spotbugs-maven-plugin, com.github.spotbugs
  Gradle plugin, Bug Rank / Confidence gates, or security-focused bytecode
  analysis on owned Java modules.
---

# Java SpotBugs Security

Own **SpotBugs** for Java/JVM security static analysis: enable **FindSecBugs**
(or equivalent SECURITY detectors), respect repo rank/confidence policy, wire
Maven/Gradle and CI gates, triage true positives with evidence, and suppress
only with owner + expiry. Prefer existing build plugins and report formats.
Hand style-only lint to Java style skills; hand dependency CVEs to SCA skills.

## When To Use

- Adding or hardening **SpotBugs** / **FindSecBugs** in local build or CI
- Interpreting SECURITY-category bugs (SQL injection, XSS, path traversal,
  crypto misuse, weak PRNG, XXE, hard-coded secrets, unsafe deserialization)
- Tuning **rank**, **confidence**, effort, and include/exclude filters
- Reviewing or adding `@SuppressFBWarnings` / XML exclude files safely
- Keywords: SpotBugs, FindSecBugs, spotbugsXml, spotbugsMain, BugInstance,
  SECURITY, conf, rank, spotbugs-annotations

Do **not** use as primary for: pure style/Javadoc → `java-style-and-javadoc`;
dependency CVE/SBOM → `sbom-and-supply-chain`; named runtime bug-class deep-dive
(SQLi, XXE, deserialization) → that domain skill after detection; pipeline
layout → `ci-cd-pipeline-patterns`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **Build system:** `pom.xml` / parent POM, `build.gradle(.kts)`, version catalog
2. **Existing SpotBugs:** plugin version, FindSecBugs version, include/exclude
   filters, `effort`, `threshold`, `failOnError`, report tasks
3. **CI workflows:** required check names, cache, JDK version matrix
4. **Suppressions:** `spotbugs-exclude.xml`, `@SuppressFBWarnings`, baselines
5. **Neighbors:** PMD, Error Prone, Checkstyle, Sonar, Dependency-Check
6. **Monorepo:** shippable modules first; justify generated-code excludes

Extend the real `spotbugs` / `spotbugsMain` job; do not invent a divergent
scanner with a looser rank policy.

## Workflow

### 1. Confirm toolchain and plugins

Pin `spotbugs-maven-plugin` or Gradle `com.github.spotbugs`, and add
`com.h3xstream.findsecbugs:findsecbugs-plugin` on the SpotBugs configuration.
Align **JDK** with the project toolchain. Prefer repo pins over `@latest`.

### 2. Prefer SECURITY-focused configuration

1. Enable **FindSecBugs** (or document core-SpotBugs-only).
2. Set **effort** high enough for security review (repo default if stricter).
3. Gate on **rank** / **confidence** (e.g. fail on High + SECURITY).
4. Include app/main sources; exclude generated code only with a written reason.
5. Emit **XML + HTML** (and SARIF if org-supported) as CI artifacts.

```bash
./mvnw -DskipTests spotbugs:spotbugs && ./mvnw spotbugs:check
./gradlew spotbugsMain
```

### 3. Run, collect, scope

Record plugin versions, module path, and filters. Diff new findings vs baseline
on PRs when the repo uses baseline mode. Limit noise from generated sources and
shaded third-party code. Re-run after filter changes to prove a known High
SECURITY bug still fails the gate.

### 4. Triage security findings

| Pattern / area | Action |
| --- | --- |
| Injection (SQL/XSS/cmd/EL) | Confirm sink + untrusted source; safe APIs / encoding |
| Path / file access | Canonicalize + allowlist |
| Crypto / PRNG / TLS | Replace weak algs; secure random |
| XXE / XML | Disable external entities; safe parser factory |
| Deserialization | No untrusted Java serialization; allowlist |
| Secrets in bytecode | Rotate; remove literals; secret store |
| Low-confidence / rank | Reproduce or FP with evidence only |

Prefer **code fix** over suppression. Ticket SLA → `vulnerability-sla-process`
when process requires it.

### 5. Suppressions (last resort)

Prefer **XML exclude** with bug pattern + class/method matchers. 
`@SuppressFBWarnings` must name the **bug code**, state **why**, and include
**owner**/ticket—never empty package-wide SECURITY suppressions. Time-box
baseline debt; CI must still fail on new High SECURITY outside baseline.

### 6. CI gate

Same JDK and plugin pins as local docs. Run on every shippable module; fail
closed per rank/confidence policy. Upload reports (not log-only). Required
status check; no secrets in config or reports. After fixes: clean rebuild so
bytecode matches source under review.

**Verify:** intentional High SECURITY fails the gate; unjustified suppressions
rejected in review; monorepo matrix covers deployable modules.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SpotBugs / FindSecBugs setup, gate, triage | **This skill** | — |
| Java naming / Javadoc only | `java-style-and-javadoc` | — |
| Named bug-class fix deep-dive | domain skill (SQLi, XXE, …) | this for detection |
| Dependency CVEs / SBOM | `sbom-and-supply-chain` | this for bytecode smells |
| Exception clocks / tickets | `vulnerability-sla-process` | this for detector evidence |
| Workflow YAML / required checks | `ci-cd-pipeline-patterns` | this for job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until plugin, SECURITY detectors, and gate policy
are correct.

## Output Checklist

- [ ] Repo Maven/Gradle SpotBugs config, filters, and CI job read first
- [ ] SpotBugs + FindSecBugs (or justified core-only) versions pinned
- [ ] Rank/confidence/effort policy documented; fail closed on High SECURITY
- [ ] Reports (XML/HTML/SARIF) uploaded; tool versions recorded
- [ ] Findings triaged with sink/source evidence; fixes preferred over suppress
- [ ] Suppressions scoped, justified, owned; no package-wide silent ignores
- [ ] Generated-code excludes justified; monorepo ship modules covered
- [ ] Clean rebuild after fixes; intentional bug fails the gate in verify
- [ ] Hand-offs: domain vuln skills, `sbom-and-supply-chain`,
      `vulnerability-sla-process`, `ci-cd-pipeline-patterns`, `code-quality-standards`
- [ ] Rules: repo-first config; SECURITY over style noise; owned code only

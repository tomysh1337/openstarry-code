---
name: sonarqube-quality-gate
description: >
  Configure and enforce SonarQube / SonarCloud Quality Gates in CI: gate conditions
  (coverage, duplications, ratings, new-code issues), waitForQualityGate / CE task
  polling, PR decoration, and fail-closed merge or release when the gate is red.
  Use when SonarQube quality gate, SonarCloud gate, sonar.qualitygate.wait,
  waitForQualityGate, CE task status, new code period, sonar-project.properties,
  branch analysis, PR decoration, or blocking merge on Sonar FAILED/ERROR.
---

# SonarQube Quality Gate

Own **Quality Gate definition, CI wait/fail, and PR/branch analysis wiring** for
SonarQube Server or SonarCloud on org-owned repos. Convert analysis into a binary
gate status (OK / WARN / ERROR) that merge and release can require. Hand multi-tool
SAST triage to `sast-dast-tooling-usage`; app fixes to `code-quality-standards`.

## When To Use

- Defining or tightening a **Quality Gate** (conditions on new/overall code)
- Wiring CI so analysis finishes and **gate status blocks** merge/deploy
- Debugging red gates: CE pending, missing token, wrong project key, no new-code baseline
- PR decoration / branch analysis vs main-only scans
- Mentions: quality gate, `sonar.qualitygate.wait`, `waitForQualityGate`, SonarCloud
  check, coverage on new code, duplications, maintainability/reliability/security rating

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Multi-tool SAST/DAST selection and noise triage | `sast-dast-tooling-usage` |
| Secure SDLC phase RACI / release exceptions | `secure-sdlc-checklist` |
| Pipeline layout, secrets, OIDC, caches | `ci-cd-pipeline-patterns` |
| Required check names on protected branches | `branch-protection-rules` |
| Implementation quality of application code | `code-quality-standards` |
| Dependency CVE/SBOM presence gates | `sbom-and-supply-chain` / `sbom-ci-enforcement` |
| Secrets hygiene beyond Sonar rules | `secrets-management-hygiene` |

## Repo Config First

Repo and org Sonar policy **outrank** examples here.

1. **Host:** SonarQube URL vs SonarCloud (`sonar.organization`); edition limits (PR decoration, branches)
2. **Identity:** `sonar.projectKey`, monorepo modules, existing dashboard bindings
3. **Config:** `sonar-project.properties`, Maven/Gradle plugin, scanner CLI, CI env (`SONAR_TOKEN`, host)
4. **New Code:** previous version, reference branch, days, or specific analysis — match “clean as you code”
5. **Quality Gate:** project vs org default; inherited conditions; who may edit
6. **CI:** analyze step, gate-wait step, exact **check name** for branch protection
7. **Scope:** `sonar.sources` / `tests` / exclusions (generated, vendor, build)
8. **Coverage:** LCOV/JaCoCo (etc.) produced **before** scanner; fail if missing when required

Extend the existing project key and gate; do not invent a second project that splits history.

## Workflow

### 1. Fix analysis identity and scope

1. One **project key** per deployable (or documented monorepo module map).
2. Include app sources; exclude `node_modules`, `vendor`, `dist`, generated stubs unless policy requires them.
3. Language plugins and build-wrapper for C/C++/Objective-C when needed.
4. Pass PR/branch metadata (`sonar.pullrequest.*` or `sonar.branch.name`) for decoration and new code.

### 2. Define the Quality Gate (conditions)

Prefer **new code** conditions for PR velocity; keep few **overall** floors for trunk health.

| Typical condition (illustrative) | Intent |
| --- | --- |
| Blocker+critical issues on new code = 0 | No new high-severity defects |
| Coverage on new code ≥ org floor (e.g. 80%) | Tests follow changes |
| Duplicated lines on new code ≤ cap | Limit copy-paste debt |
| Security/reliability/maintainability rating on new code | Rating thresholds |
| Security hotspots reviewed (if used) | Hotspots not left open |

Document WARN vs fail-closed ERROR. Avoid overall-legacy-only gates the team cannot clear in one PR.

### 3. Run scanner then wait for CE + gate

1. Build and produce **coverage/test reports** first.
2. Run analysis (Maven/Gradle `sonar:sonar`, `sonar-scanner`, or org image) with CI secret token — never commit tokens.
3. **Wait for Quality Gate** (not “analysis submitted” only): `sonar.qualitygate.wait=true`, CI `waitForQualityGate` / SonarCloud Action, or poll CE task then gate status.
4. **Fail the job** on ERROR (and WARN if policy says so); keep task id; redact tokens from logs.

### 4. Wire merge and release

1. Name the CI check exactly what `branch-protection-rules` requires.
2. PR: analyze + gate on PR head; require green decoration/status.
3. Main/release: full analysis; optional stricter overall conditions on release trains.
4. Exceptions: time-boxed “won’t fix”/FP with owner — not permanent `continue-on-error`.
5. Pair with `ci-cd-pipeline-patterns`; fix blocking findings under `code-quality-standards`.

### 5. Triage a red gate

| Symptom | Check |
| --- | --- |
| Gate timeout / never OK | CE queue, wait timeout, background task errors |
| Coverage 0% / N/A | Report path, `sonar.coverageReportPaths`, tests not in CI |
| No new-code metrics | New Code unset; first branch analysis; wrong reference branch |
| PR not decorated | Token permissions, PR params, org ALM binding |
| Local green, CI red | Exclusions, branch vs PR, coverage missing in CI |

Fix code or justified issue status; re-run; confirm gate OK on the same revision.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Sonar Quality Gate conditions, wait, PR/CI fail-closed | **This skill** | — |
| Multi-tool SAST/DAST and noise methodology | `sast-dast-tooling-usage` | this for Sonar gate mechanics |
| SSDLC gate placement / release exceptions | `secure-sdlc-checklist` | this for Sonar evidence |
| Workflow YAML, tokens, artifacts | `ci-cd-pipeline-patterns` | this for analyze+wait steps |
| Required status check on protected branch | `branch-protection-rules` | this for the Sonar job |
| Fixing bugs/vulns/maintainability in app code | `code-quality-standards` | **always** on remediations |
| Secrets vault/rotation beyond Sonar hits | `secrets-management-hygiene` | this if gate surfaces secrets |

**Required hand-offs:** multi-scanner strategy → `sast-dast-tooling-usage`; required checks → `branch-protection-rules`; code fixes → `code-quality-standards`.

## Output Checklist

- [ ] Repo Sonar host, project key, token location, and existing gate read first
- [ ] Sources/tests/exclusions and coverage paths match real CI build
- [ ] New Code period correct for PR/reference branch strategy
- [ ] Quality Gate conditions documented (new code + any overall floors)
- [ ] Analysis after build/coverage; token not in VCS or logs
- [ ] Job **waits** for CE + Quality Gate (not submit-only)
- [ ] Job fails closed on ERROR (and WARN if required)
- [ ] PR decoration / branch params set; check name matches branch protection
- [ ] Red-gate triage path known (coverage, new code, CE, ALM)
- [ ] Findings fixed under `code-quality-standards` or time-boxed with owner
- [ ] Paired with `ci-cd-pipeline-patterns` / `branch-protection-rules` / `sast-dast-tooling-usage` as needed

## Rules

- Owned projects only; treat Sonar tokens as secrets.
- Gate on **status after CE**, not scanner exit alone unless wait is enabled.
- Prefer new-code “clean as you code” over unattainable legacy-only gates.
- Do not silence gates with permanent `continue-on-error`; tune conditions or fix code.
- One project-key lineage per product; avoid splitting history without a migration plan.
- Redact tokens and sensitive snippets; keep analysis logs as evidence, not secrets store.

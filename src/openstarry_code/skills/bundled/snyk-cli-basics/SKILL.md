---
name: snyk-cli-basics
description: >
  Install, authenticate, and run the Snyk CLI for open-source SCA, Snyk Code,
  container images, and IaC on owned repositories and CI. Use when snyk test,
  snyk code test, snyk container test, snyk iac test, snyk monitor, SNYK_TOKEN,
  .snyk policy, severity threshold gates, SARIF/JSON Snyk output, or wiring Snyk
  into GitHub Actions/GitLab CI for authorized org apps and images.
---

# Snyk CLI Basics

Own **local and CI Snyk CLI** for dependency, code, container, and IaC scans on
**org-owned** projects: pin the CLI, auth safely, pick the subcommand, set fail
thresholds, export JSON/SARIF, and fix-then-recheck. Prefer repo policy (`.snyk`,
org settings, existing CI) over ad-hoc flags. Hand multi-tool SAST/DAST to
`sast-dast-tooling-usage`; SBOM to `sbom-and-supply-chain`; CVE clocks to
`vulnerability-sla-process`.

## When To Use

- Installing or upgrading **Snyk CLI**; `snyk auth` / `SNYK_TOKEN` in CI
- Running **`snyk test`**, **`snyk code test`**, **`snyk container test`**,
  **`snyk iac test`**, or **`snyk monitor`** on owned repos/images
- Gating PRs/main on severity; JSON/SARIF; `.snyk` ignores/patches
- Monorepo selection (`--file`, `--all-projects`, package roots)
- Keywords: Snyk CLI, Snyk SCA, Snyk Code, Snyk Container, Snyk IaC, SNYK_TOKEN

Do **not** use as primary for: multi-scanner SAST/DAST → `sast-dast-tooling-usage`;
lockfiles → `dependency-pinning-strategies`; SBOM → `sbom-and-supply-chain` /
`sbom-ci-enforcement`; CVE SLA → `vulnerability-sla-process`; pipeline layout →
`ci-cd-pipeline-patterns`; vault design → `secrets-management-hygiene`.

## Repo Config First

Repo and org Snyk policy **outrank** defaults below.

1. **Manifests / lockfiles** and monorepo workspace roots
2. **Policy:** `.snyk` (ignores, patches); org ignore rules
3. **CI:** existing Snyk/SCA jobs, required checks, severity gates
4. **Auth:** `--org`, CI `SNYK_TOKEN` (never commit or log)
5. **Scope:** which projects/images ship vs experimental
6. **Neighbors:** Dependabot/Renovate, CodeQL/Semgrep, image scan, SBOM job

Extend the real install/build path; do not invent a second dependency tree.

## Workflow

### 1. Install, pin, authenticate

```bash
npm install -g snyk@1.1294.0   # org-approved pin — not floating latest
snyk --version && snyk auth    # interactive local
# CI: SNYK_TOKEN from secrets only; never echo the token
```

Document the pin in Makefile/workflow. Confirm product entitlements
(Open Source / Code / Container / IaC).

### 2. Choose the scan surface

| Goal | Command | Needs |
| --- | --- | --- |
| Open-source deps (SCA) | `snyk test` | Manifest + lock preferred |
| First-party code | `snyk code test` | Source; Code product |
| Container image | `snyk container test <image>` | Built image / Dockerfile |
| IaC misconfig | `snyk iac test <path>` | Terraform/K8s/etc. |
| Track in Snyk UI | `snyk monitor` | Same project identity as test |

Prefer **lockfile-backed** SCA. Monorepos: explicit `--file` or careful
`--all-projects` when CI budget allows.

### 3. Local, container, and IaC scans

```bash
snyk test --severity-threshold=high --json-file-output=snyk-oss.json
snyk code test --severity-threshold=high --sarif-file-output=snyk-code.sarif
docker build -t org/app:local . && snyk container test org/app:local --file=Dockerfile
snyk iac test ./infra --severity-threshold=medium
```

Record CLI version, path, and org. Scan the **same** image digest CI ships.
Treat findings as hypotheses until reachability is triaged.

### 4. Policy, ignores, gates, CI

1. Prefer **fix** (upgrade/replace) over ignore.
2. Justified ignores in **`.snyk`** with reason + **expiry**; review on cadence.
3. Gate with `--severity-threshold` per org policy; fail closed.
4. `snyk monitor` tracks snapshots—it does not replace the PR gate.
5. CI: pin CLI → inject `SNYK_TOKEN` → scan after install/image build → upload
   JSON/SARIF → required check (`ci-cd-pipeline-patterns`). No token in logs.

```yaml
- run: npm install -g snyk@1.1294.0
- run: snyk test --severity-threshold=high --json-file-output=snyk-oss.json
  env: { SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }} }
```

### 5. Triage, fix, verify

| Shape | Action |
| --- | --- |
| Direct dep CVE | Bump; refresh lock; retest |
| Transitive | Upgrade intermediate; avoid eternal pin without owner |
| Snyk Code TP | Fix sink under `code-quality-standards`; retest |
| Base image only | Rebase; rebuild; rescan digest |
| Acceptable risk | `.snyk` ignore + owner + expiry → `vulnerability-sla-process` |

**Verify:** same pin/flags as CI; intentional vuln fails gate; ship paths covered;
secrets redacted. No eternal Critical ignores without owner.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Snyk CLI install/auth/test/code/container/iac/monitor | **This skill** | — |
| Multi-tool SAST/DAST methodology | `sast-dast-tooling-usage` | this for Snyk commands |
| Lockfiles / frozen installs / Renovate | `dependency-pinning-strategies` | this after tree locked |
| SBOM / multi-SCA inventory | `sbom-and-supply-chain` | this for Snyk gate |
| SBOM presence/attest gates | `sbom-ci-enforcement` | this for vuln content |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection evidence |
| Workflow YAML, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Token/vault lifecycle | `secrets-management-hygiene` | this for SNYK_TOKEN use |
| Fix quality / tests / review | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, auth, subcommands, and gate are correct.

## Output Checklist

- [ ] Manifests, `.snyk`, org ID, and existing Snyk/SCA CI job read first
- [ ] CLI pinned; `SNYK_TOKEN` via secrets only (never committed/logged)
- [ ] Correct surface: `test` / `code test` / `container test` / `iac test` / `monitor`
- [ ] Lockfile-backed SCA where applicable; monorepo ship roots covered
- [ ] Severity threshold matches policy; JSON/SARIF uploaded with CLI version
- [ ] Findings triaged (fix vs time-boxed `.snyk` ignore with owner)
- [ ] Same pin/command as CI verified; intentional fail path proven
- [ ] Hand-offs: `sast-dast-tooling-usage`, `dependency-pinning-strategies`,
      `sbom-and-supply-chain` / `sbom-ci-enforcement`, `vulnerability-sla-process`,
      `ci-cd-pipeline-patterns`, `code-quality-standards`
- [ ] Rules: repo-first; fix over eternal ignore; authorized targets only

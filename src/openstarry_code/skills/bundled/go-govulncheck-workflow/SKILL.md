---
name: go-govulncheck-workflow
description: >
  Run and gate Go vulnerability checks with govulncheck locally and in CI:
  module/source analysis, binary mode, JSON outputs, version pins, and
  actionable upgrade paths for owned Go modules. Use when govulncheck,
  golang.org/x/vuln, Go CVE scanning, go vuln DB, vulndb CI gate, Go dependency
  vulnerability check, or wiring govulncheck into GitHub Actions/GitLab CI.
---

# Go govulncheck Workflow

Own **local and CI `govulncheck`** for Go modules and binaries: pin the tool,
choose source vs binary mode, interpret reachability, fail pipelines on policy
findings, and fix-then-recheck. Prefer the repo toolchain and CI jobs. Hand
SCA/SBOM to supply-chain skills; hand `go.mod` graph work to `go-module-hygiene`.

## When To Use

- Adding or fixing **`govulncheck`** in developer workflow or CI
- Interpreting findings: package vs call-site, **reachable** vs import-only
- Scanning a **built binary** or container entrypoint (binary mode)
- Failing PRs/main on known Go vulns; JSON/SARIF-style artifacts
- Keywords: govulncheck, golang.org/x/vuln, Go vulndb, Go CVE gate, `GOVULNDB`

Do **not** use as primary for: tidy/replace/MVS → `go-module-hygiene`; Go style
→ `go-style-conventions`; multi-lang SBOM/SCA → `sbom-and-supply-chain`; SBOM
presence → `sbom-ci-enforcement`; CVE clocks → `vulnerability-sla-process`;
pipeline layout → `ci-cd-pipeline-patterns`; code quality → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **`go.mod` / `go.work`:** module roots, `go`/`toolchain`, monorepo members
2. **CI workflows:** existing Go setup, cache keys, required check names
3. **Tool version:** pin `govulncheck` (module tag), not floating `@latest`
4. **Gate policy:** all findings vs reachable-only; exception/expiry process
5. **Network:** `GOPROXY`, private modules, optional vulndb mirror (`GOVULNDB`)
6. **Neighbors:** Dependabot/Renovate, SBOM job, license scan, branch protection

Extend the real build job’s module roots; do not invent a divergent path.

## Workflow

### 1. Install and pin

```bash
go install golang.org/x/vuln/cmd/govulncheck@v1.1.4   # org-approved pin
govulncheck -version
```

Match CI Go/`GOTOOLCHAIN` to the project `go` line. Document the pin in the
workflow or Makefile. Avoid `@latest` on release-blocking jobs.

### 2. Local scan (source / module)

From each module root (matrix over `go.work` members when multi-module):

```bash
go mod download
govulncheck ./...
govulncheck -json ./... > govulncheck.json
```

Source mode uses the **module graph + call graph**. Prefer **reachable**
vulnerable symbols over import-only noise. Record command, module path, and
tool version in any report.

### 3. Binary mode (shipped artifact)

When risk is the **built binary** (build tags, CGO, `GOOS`/`GOARCH`, entrypoint):

```bash
go build -o ./bin/app ./cmd/app && govulncheck -mode=binary ./bin/app
```

Scan the **same** artifact CI ships (same flags/tags); binary results can differ.

### 4. CI gate

1. Setup Go from `go.mod`; restore module cache; download modules.
2. Install **pinned** `govulncheck`; run on each deployable module path.
3. **Fail closed** per policy. Prefer blocking reachable issues when the tool
   distinguishes them; document if you block all.
4. Upload JSON (SARIF if org-supported) as an artifact—not log-only.
5. Required checks via `ci-cd-pipeline-patterns` / branch protection.
6. Reuse job `GOPRIVATE`/auth; never print tokens.

```yaml
- uses: actions/setup-go@v5
  with: { go-version-file: go.mod }
- run: go install golang.org/x/vuln/cmd/govulncheck@v1.1.4
- run: govulncheck ./...
```

### 5. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| Reachable in direct dep | Bump require; tidy; retest |
| Reachable via transitive | Upgrade intermediate; avoid eternal `replace` |
| Import-only / unreachable | Track upgrade; warn-only only with owner+expiry |
| Stdlib / toolchain | Raise `go`/`toolchain`; re-run CI |
| Dead path / build tag | Prove with tags or binary scan; fix or time-box |

After bumps: `go mod tidy` + `go test ./...` (rebuild if binary-gated). Module
debt → `go-module-hygiene`. Ticket SLA → `vulnerability-sla-process`.

**Verify:** same pin as CI is green; intentional old vuln pin fails the gate;
every shippable monorepo module is in the matrix; redact private URLs/creds.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| govulncheck local/CI, Go vulndb gate, binary mode | **This skill** | — |
| go.mod tidy, replace, MVS, private fetch | `go-module-hygiene` | this after graph is sound |
| Go code style | `go-style-conventions` | after vuln fix compiles |
| Multi-lang SBOM / SCA inventory | `sbom-and-supply-chain` | this for Go gate |
| SBOM file/attest presence gate | `sbom-ci-enforcement` | this for vuln content |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection evidence |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, scan mode, and gate behavior are correct.

## Output Checklist

- [ ] Repo Go version, module roots, and existing CI Go job read first
- [ ] `govulncheck` version pinned (not floating `@latest` on gates)
- [ ] Source scan on `./...` per shippable module; binary mode for ship artifacts
- [ ] JSON/SARIF uploaded; tool version recorded; required check enforced
- [ ] Gate policy clear (reachable vs all); findings triaged with owner/expiry
- [ ] tidy + tests (and rebuild) after upgrades; monorepo matrix complete
- [ ] Private auth safe; secrets redacted; same pin/command as CI verified
- [ ] Hand-offs: `go-module-hygiene`, `vulnerability-sla-process`,
      `sbom-and-supply-chain` / `sbom-ci-enforcement`, `code-quality-standards`
- [ ] Rules: repo-first pin; reachable over silent ignore; authorized modules only


---
name: gosec-go-security
description: >
  Run and triage securego/gosec static analysis on owned Go modules: rule
  selection, severity/confidence gates, nosec discipline, JSON/SARIF CI
  artifacts, and fix-then-recheck for common G-rules. Use when gosec, securego,
  Go SAST, G101 secrets, G201 SQL, G204 exec, G304 file path, G401 weak crypto,
  #nosec, or wiring gosec into Makefile/GitHub Actions/GitLab CI.
---

# Gosec Go Security

Own **`gosec` (securego/gosec)** for Go source: install/pin, scan module roots,
interpret rule IDs, gate CI on severity/confidence, and remediate findings with
evidence. Prefer repo config and existing CI jobs. Hand dependency CVEs to
`go-govulncheck-workflow`; hand `go.mod` graph work to `go-module-hygiene`.

## When To Use

- Adding or fixing **`gosec`** in local workflow or CI for Go modules
- Interpreting **G-rule** findings (secrets, SQL, exec, path, TLS, crypto)
- Tuning **include/exclude**, severity, confidence, or `#nosec` policy
- Producing **JSON/SARIF** artifacts and failing PRs on high-impact issues
- Keywords: gosec, securego, Go SAST, `#nosec`, `gosec ./...`, G101, G104,
  G201, G204, G304, G401, G404, G601

Do **not** use as primary for: reachable dependency CVEs →
`go-govulncheck-workflow`; tidy/replace/MVS → `go-module-hygiene`; Go style →
`go-style-conventions`; secret rotation/IR → `secrets-management-hygiene`;
pipeline layout → `ci-cd-pipeline-patterns`; code quality →
`code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **`go.mod` / `go.work`:** module roots, `go`/`toolchain`, monorepo members
2. **Existing gosec config:** `.gosec.json`, Makefile targets, CI job flags
3. **Tool version:** pin `gosec` release (or module tag), not floating `@latest`
4. **Gate policy:** which severities/confidence fail; exception/`#nosec` process
5. **Exclude paths:** generated code, `vendor`, mocks, third_party
6. **Neighbors:** govulncheck, staticcheck/golangci-lint, secret scanners, branch protection

Extend the real build job’s module roots; do not invent a divergent scan path.

## Workflow

### 1. Install and pin

```bash
go install github.com/securego/gosec/v2/cmd/gosec@v2.21.4   # org-approved pin
gosec -version
```

Match CI Go/`GOTOOLCHAIN` to the project `go` line. Document the pin in the
workflow or Makefile. Avoid `@latest` on release-blocking jobs.

### 2. Local scan

From each shippable module root (matrix over `go.work` members when multi-module):

```bash
gosec ./...
gosec -fmt=json -out=gosec.json ./...
gosec -fmt=sarif -out=gosec.sarif ./...
```

Useful flags only if repo has no stronger config: `-exclude`/`-include` for rule
IDs; `-exclude-dir` for `vendor`/`testdata`/generated; `-exclude-generated` when
supported; `-nosec=false` to audit suppressions. Prefer fix over blanket
`-exclude=G104`. Load repo config with `-conf` when present. Record command,
module path, and tool version in any report.

### 3. Rule triage map

| Rules (examples) | Theme | Typical fix |
| --- | --- | --- |
| G101 | Hardcoded credentials | Remove; inject via env/secret store |
| G104 / G103 | Unchecked errors / unsafe | Handle errors; avoid `unsafe` without review |
| G201 / G202 | SQL format / concat | Parameterized queries / bound args |
| G204 | Subprocess with variable | Fixed argv; no shell; validate inputs |
| G301–G306 | File perms / tempfile | Restrictive modes; safe temp APIs |
| G304 / G305 | File path / zip slip | Clean/join under root; validate archives |
| G401 / G501 | Weak crypto (MD5/SHA1/DES) | SHA-256+, AES-GCM, modern TLS min |
| G402 | TLS skip-verify / weak min | Verify certs; modern `MinVersion` |
| G404 | Weak random (`math/rand`) | `crypto/rand` for secrets/tokens |
| G601 | Range-loop memory alias | Copy loop var when taking address |

Prove each finding with **file:line**. Prefer **code fix** over `#nosec`. If
suppress: `#nosec Gxxx` with **reason + owner + expiry**—never repo-wide silence.

### 4. CI gate

1. Setup Go from `go.mod`; restore module cache.
2. Install **pinned** `gosec`; run per shippable module path.
3. **Fail closed** on HIGH (and org-defined MEDIUM) unless excepted.
4. Upload JSON/SARIF as artifacts—not log-only.
5. Required check via branch protection / `ci-cd-pipeline-patterns`.
6. Reuse `GOPRIVATE` auth; never print tokens.

```yaml
- uses: actions/setup-go@v5
  with: { go-version-file: go.mod }
- run: go install github.com/securego/gosec/v2/cmd/gosec@v2.21.4
- run: gosec -fmt=sarif -out=gosec.sarif ./...
```

### 5. Fix, verify, hand off

Fix true positives; re-run the **same** pin and paths as CI. Secret hits →
rotate first (`secrets-management-hygiene`). Dependency CVEs →
`go-govulncheck-workflow`. Module bumps → tidy + tests (`go-module-hygiene` if
graph-heavy). Apply `code-quality-standards` on production code changes.

**Verify:** CI pin matches local; intentional G101/G204 sample fails the gate;
monorepo matrix covers every shippable module; redact secrets in artifacts.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| gosec SAST, G-rules, nosec policy, CI SAST gate | **This skill** | — |
| Go dependency CVE / vulndb / binary vuln scan | `go-govulncheck-workflow` | parallel or after SAST |
| go.mod tidy, replace, MVS, private fetch | `go-module-hygiene` | this after graph is sound |
| Hardcoded secret rotation / leak IR | `secrets-management-hygiene` | this for detection evidence |
| Go formatting, errors, idioms | `go-style-conventions` | after security fix compiles |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for gosec job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, rule policy, and gate behavior are correct.

## Output Checklist

- [ ] Repo Go version, module roots, and existing gosec/CI config read first
- [ ] `gosec` version pinned (not floating `@latest` on gates)
- [ ] Scan `./...` per shippable module; excludes justified
- [ ] JSON/SARIF uploaded; tool version recorded; required check enforced
- [ ] Findings triaged by rule ID with file:line; true positives fixed
- [ ] `#nosec` rare, rule-scoped, reasoned, owned; no silent global disable
- [ ] Secrets handled rotate-first; no credentials in reports
- [ ] Same pin/command as CI verified; monorepo matrix complete
- [ ] Hand-offs: `go-govulncheck-workflow`, `go-module-hygiene`,
      `secrets-management-hygiene`, `code-quality-standards`
- [ ] Rules: repo-first pin; fix over suppress; authorized modules only

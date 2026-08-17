---
name: bandit-python-scan
description: >
  Run and gate Bandit (PyCQA) on owned Python trees: config discovery,
  severity/confidence policy, excludes, JSON/SARIF outputs, CI fail-closed
  gates, and triage of B-rules into fixes or owned suppressions. Use when
  Bandit, bandit -r, pyproject.toml tool.bandit, .bandit.yaml, B101/B608,
  Python SAST CI gate, or wiring Bandit into pre-commit/GitHub Actions/GitLab.
---

# Bandit Python Scan

Own **local and CI Bandit** for Python packages and apps: discover repo config,
scan source (not venv/site-packages), interpret B-test IDs with severity and
confidence, fail pipelines on policy findings, and fix-then-recheck. Prefer the
repo’s existing Bandit config and job. Hand dep CVE/SCA to supply-chain skills;
hand style/typing to language companions; hand secret lifecycle to secrets hygiene.

## When To Use

- Adding, fixing, or interpreting **Bandit** in dev workflow or CI
- Choosing **config** (CLI, `.bandit` / `bandit.yaml`, `pyproject.toml` `[tool.bandit]`)
- Gating PRs on high/medium issues; JSON/SARIF/HTML artifacts
- Triaging **B-rules** (e.g. `assert`, `exec`, `subprocess`, SQL, weak crypto, hard-coded passwords)
- Keywords: Bandit, PyCQA Bandit, `bandit -r`, `skips`, `exclude_dirs`, Python SAST gate

Do **not** use as primary for: Ruff/Flake8/mypy style → `python-style-and-typing` /
`prettier-eslint-editorconfig` peers; multi-lang SBOM/SCA → `sbom-and-supply-chain`;
secret inventory/rotation IR → `secrets-management-hygiene`; pipeline topology →
`ci-cd-pipeline-patterns`; general code baseline → `code-quality-standards`;
runtime injection exploit methodology → injection skills after a finding.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **Config files:** `pyproject.toml` `[tool.bandit]`, `.bandit`, `bandit.yaml` /
   `bandit.yml`, `setup.cfg` `[bandit]` — **extend**, do not fork a second policy
2. **Targets:** package roots (`src/`, app modules); never scan `.venv` / `venv` /
   `site-packages` / build artifacts as first-class paths
3. **Excludes / skips:** existing `exclude_dirs`, `skips`, `# nosec` / `# nosec Bxxx`
   with owners; tests often skip `B101` deliberately
4. **CI:** pre-commit `bandit` hook, workflow job name, required checks, pin version
5. **Severity policy:** which levels fail the gate (e.g. high+medium) and exception process
6. **Neighbors:** Ruff security rules, Semgrep, secret scanners, Dependabot — avoid
   duplicate noisy gates without a clear primary owner

**Precedence:** Follow the repo config and pin. Surface missing config, scanning
only tests, or blanket `skips` that hide high-severity rules without expiry.

## Workflow

### 1. Install and pin

```bash
python -m pip install "bandit==1.7.10"          # org-approved pin; example only
# or: pip install "bandit[toml]==…" when reading pyproject.toml
bandit --version
```

Pin Bandit (and extras such as `toml`) in CI/requirements-dev; avoid floating
`latest` on release-blocking jobs. Document the pin next to the workflow or lockfile.

### 2. Discover config and scope

```bash
# Prefer explicit -c when the repo already has a file
bandit -r src -c pyproject.toml
bandit -r . -c .bandit
```

Inventory entrypoints, `tests/`, scripts, and generated code. Default recursive
scan should match what CI gates (same roots and excludes).

### 3. Local scan and machine output

```bash
bandit -r src -ll -ii                 # example: medium+ severity & confidence
bandit -r src -f json -o bandit.json
bandit -r src -f sarif -o bandit.sarif   # if supported by installed version
bandit -r src -f txt
```

Record **command, paths, Bandit version, config path**, and severity/confidence
flags. Prefer JSON/SARIF for triage artifacts over log-only output.

### 4. CI gate

1. Install **pinned** Bandit into the job (or pre-commit rev pin).
2. Run the **same** roots/config as local policy; fail closed per severity policy.
3. Upload JSON/SARIF as artifacts; do not print secrets from hard-coded-password hits.
4. Required check via branch protection (`ci-cd-pipeline-patterns`).
5. Matrix monorepos by package root when multiple shippable trees exist.

### 5. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| True positive (e.g. `shell=True`, SQL concat, weak hash for security) | Fix code; re-run Bandit |
| Test-only `assert` (`B101`) | Exclude tests or skip `B101` in test paths only |
| Intentional pattern with review | Narrow `# nosec Bxxx` + comment owner/reason; prefer config skip scoped to path |
| Hard-coded secret/password rule | Rotate if real; remove from tree (`secrets-management-hygiene`) |
| False positive from generated/vendor code | Exclude path; do not disable rule globally |

After fixes: re-run Bandit with the **same pin and flags** as CI; add/adjust tests
when behavior changes (`code-quality-standards`). SLA/exception tickets →
`vulnerability-sla-process` when findings track as security debt.

**Verify:** clean gate on intentional-safe tree; known bad sample fails CI; monorepo
roots covered; suppressions are path-scoped and owned; secrets redacted in reports.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Bandit local/CI, B-rules, config, Python SAST gate | **This skill** | — |
| Python style, typing, formatters | `python-style-and-typing` | after security fix compiles |
| Secret lifecycle, rotation, leak IR | `secrets-management-hygiene` | this for Bandit hard-coded hits |
| Dep/CVE inventory, SBOM | `sbom-and-supply-chain` | this for source AST issues |
| Workflow YAML, required checks | `ci-cd-pipeline-patterns` | this for Bandit job body |
| Exception clocks, vuln tickets | `vulnerability-sla-process` | this for detection evidence |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until pin, config, scan roots, and gate policy are correct.

## Output Checklist

- [ ] Repo Bandit config, targets, excludes, and CI job read first
- [ ] Bandit version pinned (not floating `@latest` / unpinned pre-commit on gates)
- [ ] Scan roots match shippable packages; venv/build dirs excluded
- [ ] Severity/confidence policy documented; fail-closed where required
- [ ] JSON/SARIF (or agreed format) produced; tool version recorded
- [ ] Findings triaged: fix vs path-scoped skip/`# nosec` with owner
- [ ] Hard-coded secret hits handled without echoing values; rotation if real
- [ ] Same pin/command as CI verified; monorepo matrix complete if multi-root
- [ ] Hand-offs: `python-style-and-typing`, `secrets-management-hygiene`,
      `ci-cd-pipeline-patterns`, `vulnerability-sla-process`, `code-quality-standards`
- [ ] Rules: repo-first config; no global silent skips for high severity; owned code only

---
name: sast-dast-tooling-usage
description: >
  When and how to run Static Application Security Testing (SAST) and Dynamic
  Application Security Testing (DAST), configure sensible baselines, and triage
  scanner noise into actionable work. Use when SAST, DAST, 静态扫描, 动态扫描,
  CodeQL, Semgrep, ZAP, Burp scan, Sonar security rules, or CI security scan
  gates for org-owned applications.
---

# SAST / DAST Tooling Usage

Operate **application security scanners** as part of an authorized engineering
or AppSec workflow: choose the right tool class, run at the right lifecycle
point, and convert results into **verified, owned findings** — not raw CSV
dumps. This skill is **defensive tooling methodology**, not a guide to
weaponize scan output against third parties.

## Scope And Authorization

- **In scope:** Org repositories, CI, staging/lab environments, and applications
  you own or are explicitly contracted to assess.
- **Out of scope:** Pointing DAST or aggressive active scanners at third-party
  production systems without written authorization; using SAST results to build
  exploit kits for off-scope targets.
- **DAST** is active testing: prefer **non-production** or explicitly approved
  windows; respect rate limits, auth test accounts, and data-minimization rules.
- Keep raw scanner exports and production URLs out of public tickets; redact
  tokens, session cookies, and PII from evidence.
- Org-standard tools, severity gates, and exception processes **outrank** the
  product examples below.

## Use When

- Introducing or tuning **SAST** (static) or **DAST** (dynamic) in CI or AppSec
- Chinese/English teams: **静态扫描**, **动态扫描**, 代码审计工具, 漏扫, 安全门禁
- Triaging large result sets: false positives, duplicates, “noise”
- Choosing **when** to fail a PR vs inform vs schedule deep scan
- Pairing scanners with secure SDLC verify/release gates
  (`secure-sdlc-checklist`)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full secure lifecycle / phase RACI | `secure-sdlc-checklist` |
| Design-time STRIDE / DFD | `threat-modeling-stride` |
| Secure coding and review baseline | `code-quality-standards` |
| Unit test design (not scanner config) | `unit-testing-style` |
| Dependency CVE/SBOM inventory focus | `sbom-and-supply-chain` |
| Secrets-in-repo / vault patterns | `secrets-management-hygiene` |
| External bounty process / report craft | `bug-bounty-methodology` |
| Confirmed vuln class deep exploitation | Matching class skill (authorized) |
| CI YAML structure only | `ci-cd-pipeline-patterns` |

## Core Idea

| Class | Analyzes | Strengths | Blind spots |
| --- | --- | --- | --- |
| **SAST** | Source/bytecode without running full app | Early PR feedback; dataflow patterns; secrets-adjacent rules | Framework magic, multi-repo context, runtime config, authZ business rules |
| **SCA** (often bundled) | Dependencies / lockfiles | Known CVEs, licenses | Reachability; “Critical” that is not callable |
| **Secret scan** | High-entropy / known key patterns | Stops credential commits | Business-logic “secret” misuse |
| **DAST** | Running app via HTTP(S) | Real routing, auth, config, some XSS/SQLi classes | Heavy noise; incomplete crawl; business logic; often weak multi-step authz |
| **IAST / hybrid** (if org has it) | Runtime + instrumentation | Higher precision in lab | Agent cost; env fidelity |

**Rule:** SAST for **every PR** (fast rules) + **full** on main/release; DAST on
**staging** per release or nightly — not as the only control, and not as a
substitute for `threat-modeling-stride` or human authZ review.

## Workflow

### 1. Place scanners on the lifecycle

Map to `secure-sdlc-checklist` verification/release:

| Moment | Prefer | Avoid |
| --- | --- | --- |
| Pre-commit / IDE | Lightweight secret scan, optional Semgrep subset | Full DAST |
| PR | SAST diff-aware or full with cache; SCA on lockfile change; unit tests | Prod DAST; fail on every Low info |
| Merge to main | Full SAST + SCA + image scan; secret scan history-aware | Silent `continue-on-error` on Critical |
| Staging deploy | Authenticated DAST / API scan; smoke | Unthrottled prod scans |
| Release gate | Policy severities cleared or excepted | “We’ll triage after ship” |
| Scheduled | Deep SAST packs, full crawl DAST, dependency refresh | Same noisy rules with no baseline |

### 2. Select and baseline tools (org-first)

1. Prefer **already licensed / org-standard** scanners (GitHub CodeQL, Semgrep
   AppSec packs, SonarQube/SonarCloud security, Checkmarx, Fortify, Veracode,
   Snyk Code, Semgrep + Trivy/Grype for SCA/images, ZAP / Burp Enterprise /
   vendor DAST for dynamic).
2. **Baseline** before enforcing fail: run 1–2 sprints in audit mode; measure
   true-positive rate; suppress only with justification.
3. Pin rule packs / query suites by version; record **policy file** in repo
   (e.g. `semgrep.yml`, CodeQL config, ZAP context).
4. Separate **security** findings from pure style/quality (hand style to
   language skills / Sonar maintainability as non-blocking if policy allows).

### 3. Configure SAST for signal

| Setting | Practice |
| --- | --- |
| Language packs | Enable only languages present; disable unused |
| Scope | Include app code; exclude generated, vendored (or scan vendored separately) |
| Severity | Map tool severity → org Critical/High/Med/Low once |
| Diff-aware PR | Comment on changed lines when tool supports it; full scan on main |
| Custom rules | Add org anti-patterns (forbidden APIs, raw SQL helpers) after first noise pass |
| Secrets | Dedicated secret scanner (gitleaks/trufflehog/platform) — not only SAST |
| Supply chain | SCA on lockfile; image scan on final digest → `sbom-and-supply-chain` |

**Concrete techniques (illustrative — adapt to org CLI):**

```bash
# Semgrep (PR-friendly rulesets; authorized org repos)
semgrep scan --config p/owasp-top-ten --config p/security-audit --error

# CodeQL (CI init/analyze pattern — use org workflow)
# Initialize → build → analyze; upload SARIF to code scanning

# Gitleaks
gitleaks detect --source . --redact --exit-code 1

# Trivy filesystem / image (SCA + misconfig; pair with SBOM skill)
trivy fs --severity HIGH,CRITICAL --exit-code 1 .
trivy image --severity HIGH,CRITICAL "ghcr.io/org/app@sha256:…"
```

Wire jobs via `ci-cd-pipeline-patterns`: least privilege, no secrets in logs,
SARIF/artifact retention, required check names matching branch protection.

### 4. Configure DAST safely

1. **Target:** staging or ephemeral PR env with **synthetic data**.
2. **Auth:** dedicated test users (dual role for authz smoke); store creds in CI
   secrets; never personal prod SSO sessions.
3. **Context:** openapi/swagger seed, sitemap, or recorded login sequence; set
   in-scope hosts only.
4. **Throttle:** RPS limits; exclude logout/destructive admin; deny-list password
   reset flood and payment capture if not in scope.
5. **API mode:** prefer OpenAPI-driven active scan over blind spider when specs exist
   (`api-recon-and-docs` for map quality).
6. **TLS/lab:** only intercept systems you own; no random Internet targets.

```bash
# OWASP ZAP baseline (passive-leaning) vs full active — start baseline in CI
# zap-baseline.py -t https://staging.app.example -r zap-report.html
# Full active scans: scheduled or pre-release, not every PR, unless policy says so
```

**Burp / commercial DAST:** use project config, resource pools, application
login, and extension policy approved by AppSec; export evidence for triage, not
only executive PDF scores.

### 5. Triage noise (core skill)

Treat every finding as **hypothesis** until verified.

#### 5.1 Intake

| Field | Capture |
| --- | --- |
| ID | Tool finding id + fingerprint (rule + location + sink) |
| Tool / rule | Name, version, rule pack |
| Location | File:line or URL + param |
| Severity (tool) | Raw |
| Severity (org) | After triage |
| Status | True positive / false positive / acceptable risk / duplicate |
| Owner / due | Required for TP at High+ |
| Evidence | Minimal repro or why FP |

#### 5.2 False-positive patterns (SAST)

| Pattern | Triage action |
| --- | --- |
| Sink not reachable | Confirm with call graph / tests; mark FP or “unreachable” with review date |
| Sanitizer unrecognized | Add engine annotation / custom sanitizer model; prefer fixing if weak |
| Test/fixture only | Scope exclude `*_test.*` when policy allows; keep if tests ship |
| Generated code | Exclude or fix generator |
| Framework-safe API | Document FP; contribute rule tune upstream/org pack |
| Duplicate of SCA CVE | Link to SCA ticket; one owner |

#### 5.3 False-positive / low-value patterns (DAST)

| Pattern | Triage action |
| --- | --- |
| Missing header only (no impact) | Info/backlog unless org hard-requires headers |
| Cookie flags on non-session cookies | Verify cookie purpose before High |
| Login CSRF / logout CSRF | Check program/policy; often low unless impact |
| XSS in dead reflected param filtered by WAF only | Verify without relying on WAF; fix app if reflected |
| “SQL injection” from time-based noise | Manual confirm; never mass-exploit |
| Issues on out-of-scope third-party host | Close out-of-scope; fix allowlist |
| Same root cause, many URLs | Collapse to one finding + instance list |

#### 5.4 True-positive handling

1. **Minimize PoC** — enough to prove impact; no destructive payloads on shared staging.
2. **Root cause** — map to code control (missing encode, raw query, open redirect allowlist).
3. **Fix** — implement under `code-quality-standards`; add regression via
   `unit-testing-style` (or integration test) for the control.
4. **Retest** — same scanner rule + manual path; require clean on the fingerprint.
5. **Exception** — if deferred: owner, expiry, compensating control, link to
   `secure-sdlc-checklist` release record.

#### 5.5 Noise reduction loop

1. Track **% FP** and **median time-to-triage** per rule.
2. Disable or demote rules with sustained high FP and low TP (with AppSec sign-off).
3. Promote custom rules that catch real org bugs.
4. Never “fix” noise by deleting the required CI check — tune policy instead.

### 6. Severity and gates

| Org severity | Typical gate |
| --- | --- |
| Critical | Block release / block merge when reachable on protected branches |
| High | Block release; PR block if in changed code (policy variant) |
| Medium | Fix within SLA; may not block every PR |
| Low / Info | Backlog; do not train teams to ignore by mixing with Critical |

Map **tool CVSS-ish scores** carefully: SAST “Critical SQL” in a dead admin
import path may triage lower after reachability; DAST “High” missing CSP is
often not Critical. Document overrides.

### 7. Human + design supplements (scanners miss these)

Hand off when scanners are the wrong tool:

| Gap | Next skill |
| --- | --- |
| Business logic, multi-step authZ, IDOR design | Class skills + design `threat-modeling-stride` |
| Secure code structure, error handling | `code-quality-standards` |
| Unit-level regressions for fixes | `unit-testing-style` |
| External hunter process | `bug-bounty-methodology` |
| Secret lifecycle beyond regex hits | `secrets-management-hygiene` |
| Full SSDLC placement | `secure-sdlc-checklist` |

### 8. Reporting and metrics

| Metric | Why |
| --- | --- |
| Open Critical/High age | SLA health |
| FP rate by rule | Tuning backlog |
| Mean time to remediate (MTTR) | Engineering + AppSec load |
| % releases with exception | Process smell if rising |
| Coverage | Languages/repos with SAST; apps with DAST auth context |

Export SARIF/JSON to the org finding system when available; avoid spreadsheet-only SSOT.

## Good / Bad Patterns

### CI SAST gate

**Good** — security job required on PR; SARIF uploaded; Critical fails; policy file versioned.

**Bad** — `continue-on-error: true` on CodeQL forever; results only on a laptop; no owner for findings.

### DAST timing

**Good** — nightly authenticated ZAP against staging OpenAPI; report triaged before release train.

**Bad** — full active scan against production from a shared CI token every PR; password-reset endpoint flooded.

### Triage

**Good** — fingerprint, status, linked fix PR, retest note, FP suppressions reviewed quarterly.

**Bad** — bulk “won’t fix” on 400 findings without sampling; severity argued only by tool default.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SAST/DAST setup, CI gates, triage noise, 静态扫描 | **This skill** | — |
| Where scans sit in SSDLC phases | `secure-sdlc-checklist` | this skill for tool ops |
| Design threats scanners will miss | `threat-modeling-stride` | this skill later for verify |
| Implementing fixes from true positives | `code-quality-standards` | **always** |
| Regression tests for fixed sinks | `unit-testing-style` | this skill for retest rule |
| Dependency CVE / SBOM / image provenance | `sbom-and-supply-chain` | this skill if bundled in same pipeline |
| Secrets found or vault design | `secrets-management-hygiene` | this skill for secret-scan job |
| Pipeline wiring, OIDC, artifacts | `ci-cd-pipeline-patterns` | this skill for scan job content |
| External authorized hunting process | `bug-bounty-methodology` | this skill for in-house scanners only |
| Confirmed class deep-dive (XSS, SQLi, …) | Matching class skill | this skill for discovery breadcrumb |

### Routing notes (required helpers)

- **`code-quality-standards`:** every true-positive fix and secure default in code.
- **`unit-testing-style`:** lock the fix with focused regression tests where a unit boundary exists.
- **`threat-modeling-stride`:** when scan noise reveals missing design controls or new surfaces need modeling first.
- **`bug-bounty-methodology`:** do not confuse internal DAST with bounty; use bounty skill for program scope and reports.
- **`secure-sdlc-checklist`:** parent process for gates and exceptions; this skill owns scanner craft.

## Checklist

- [ ] Authorization and target env confirmed (especially for DAST)
- [ ] Org-standard tools and severity mapping selected; policy files in VCS
- [ ] SAST/SCA/secrets on PR and full on main/release; DAST on staging schedule
- [ ] Baseline period completed before hard fail (or risk accepted explicitly)
- [ ] Generated/vendor paths scoped intentionally
- [ ] DAST auth context, host allowlist, throttle, and synthetic data in place
- [ ] Findings triaged: TP/FP/duplicate/exception with owners for High+
- [ ] FP suppressions justified and time-boxed or reviewed on cadence
- [ ] True positives fixed under `code-quality-standards` + regression tests
- [ ] Retest evidence tied to commit/image digest
- [ ] Release gate: no unowned Critical; exceptions in release record
- [ ] Metrics: FP rate, MTTR, open High age reviewed
- [ ] Reports redacted; no off-scope active scanning
- [ ] Design/authZ gaps routed to `threat-modeling-stride` / class skills, not ignored as “scanner clean”

## Rules

- Scanners **assist** review; green scans ≠ secure system.
- Triage before panic; panic before ignoring Critical without owner.
- Prefer fixing code and tuning rules over permanent global suppressions.
- DAST only on authorized, rate-limited targets with test accounts.
- One root cause → one primary ticket; link instances.
- Pair every merge-blocking security gate with a human exception path that expires.
- Hand lifecycle governance to `secure-sdlc-checklist` and code quality to
  `code-quality-standards`; stay the expert on **run + triage**.
---

# Note

This skill is the **primary** entry for SAST/DAST operation and noise triage.
Place jobs on the timeline with `secure-sdlc-checklist`, fix code with
`code-quality-standards`, lock behavior with `unit-testing-style`, model what
scanners miss with `threat-modeling-stride`, and keep external bounty process
under `bug-bounty-methodology`.

---
name: retirejs-scan-basics
description: >
  Detect known-vulnerable JavaScript and Node libraries with Retire.js (CLI):
  js/node path scans, severity gates, ignore files, JSON/CycloneDX output, and
  CI fail-closed wiring for owned frontends and Node apps. Use when retire.js,
  retire CLI, JS library CVE scan, jquery/angular/bootstrap known-vuln detect,
  static vendor/*.js scanning, node_modules retire check, or wiring Retire.js
  into npm scripts / GitHub Actions / GitLab CI.
---

# Retire.js Scan Basics

Own **local and CI Retire.js** for known-vulnerable JS libraries and Node
packages: pin the CLI, choose js vs node targets, set severity/exit policy,
triage to upgrades or time-boxed ignores, and recheck. Prefer repo scripts and
existing CI. Hand multi-lang SCA/SBOM to supply-chain skills; lock/graph hygiene
to `npm-supply-chain-hygiene`.

## When To Use

- Adding or fixing **Retire.js** in developer workflow or CI
- Scanning **static JS** (CDN copies, `vendor/`, bundles) for known-bad versions
- Scanning **Node** trees / `node_modules` for library advisories
- Interpreting component name, detected version, CVE/advisory, severity
- Failing PRs on medium+ (or org policy) findings with JSON artifacts
- Keywords: retire, retire.js, JS known vulnerabilities, jquery CVE scan

Do **not** use as primary for: npm lock/graph/confusion →
`npm-supply-chain-hygiene` / `dependency-confusion`; pins →
`dependency-pinning-strategies`; multi-lang SBOM/SCA → `sbom-and-supply-chain`;
SBOM gates → `sbom-ci-enforcement`; CVE clocks → `vulnerability-sla-process`;
pipeline layout → `ci-cd-pipeline-patterns`; XSS exploit paths →
`xss-cross-site-scripting`; code quality → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **Package roots:** `package.json` / workspaces; static asset roots
2. **Existing scripts/CI:** `npm run` targets, cache, required check names
3. **Tool pin:** pin `retire` (or lockfile) — not floating `@latest` on gates
4. **Scan scope:** js/node paths; excludes (`dist` only if rebuilt each job)
5. **Gate policy:** severity threshold, exit-on-findings, ignorefile owner+expiry
6. **Neighbors:** npm audit/OSV, Dependabot/Renovate, SBOM job, CSP/XSS reviews

Extend real build/test jobs; do not invent a divergent tree root.

## Workflow

### 1. Install and pin

```bash
npm install -D retire@4.5.1   # org-approved pin
npx retire --version
```

Document the pin in `package.json` / lockfile or CI. Avoid unpinned globals on
release-blocking jobs.

### 2. Local scan (js + node)

From each relevant package/static root:

```bash
npx retire --path . --severity medium --outputformat text
npx retire --path . --outputformat json --outputpath retire-report.json
npx retire --jspath ./public --nodepath ./node_modules   # optional narrow
```

Retire matches **library signatures and versions** (filename, content hashes,
package metadata) against its vuln repo. Record CLI version, paths, and severity
threshold in any report.

### 3. Ignore and exclude policy

Use ignore lists only for **accepted risk** with owner, ticket, and expiry —
never silent permanent suppressions. Exclude caches you do not ship; still scan
**what production serves**.

```bash
npx retire --path . --ignorefile .retireignore.json --exclude node_modules/.cache
```

### 4. CI gate

1. Checkout; install deps so `node_modules` / vendored JS exist.
2. Run **pinned** `retire` on the same roots developers use.
3. **Fail closed** on severity policy (e.g. medium+ fails the job).
4. Upload JSON (or CycloneDX if enabled) — not log-only.
5. Required check via `ci-cd-pipeline-patterns` / branch protection.
6. Never print registry tokens; redact private package paths.

```yaml
- run: npm ci
- run: npx retire --path . --severity medium --outputformat json --outputpath retire.json
- uses: actions/upload-artifact@v4
  with: { name: retire-report, path: retire.json }
```

### 5. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| Direct known-vuln app dep | Bump package; refresh lockfile; retest |
| Vendored/static old jquery/etc. | Upgrade or remove unused vendor copy |
| Transitive Node dep | Upgrade parent or package-manager override |
| False positive (wrong lib/version) | Prove hash/version; narrow path or time-box ignore |
| Dead asset / no patch | Drop from ship path, mitigate (CSP), or SLA ticket |

After upgrades: reinstall, rebuild assets, re-run the **same** command as CI.
Pin debt → `dependency-pinning-strategies`. SLA → `vulnerability-sla-process`.
**Verify:** CI pin green; intentional old lib fails gate; every ship workspace in
matrix; secrets redacted.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Retire.js CLI local/CI, JS known-vuln gate | **This skill** | — |
| npm lock, scripts, registry, install hygiene | `npm-supply-chain-hygiene` | this after installable |
| npm confusion / typosquat | `dependency-confusion` | this for version CVE |
| Pin/lock ranges | `dependency-pinning-strategies` | this for scan evidence |
| Multi-lang SBOM/SCA or SBOM file gate | `sbom-and-supply-chain` / `sbom-ci-enforcement` | this for Retire content |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| XSS impact from vulnerable widget | `xss-cross-site-scripting` | after version confirmed |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI |

Keep **this skill primary** until pin, paths, and gate are correct.

## Output Checklist

- [ ] Repo package roots, static JS paths, and existing CI read first
- [ ] `retire` pinned (not `@latest` on gates); severity + exit policy clear
- [ ] js/node paths match production ship set; excludes justified
- [ ] JSON uploaded; tool version recorded; required check enforced
- [ ] Ignores have owner + ticket + expiry; no silent permanent suppressions
- [ ] Upgrades rebuild assets; same command as CI green; monorepo matrix complete
- [ ] Tokens/private paths redacted; intentional old lib fails the gate
- [ ] Hand-offs: `npm-supply-chain-hygiene`, `dependency-pinning-strategies`,
      `vulnerability-sla-process`, `sbom-and-supply-chain` / `sbom-ci-enforcement`,
      `code-quality-standards`
- [ ] Rules: repo-first pin; ship-path over silent ignore; authorized targets only

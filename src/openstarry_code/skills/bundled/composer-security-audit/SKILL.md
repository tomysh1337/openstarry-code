---
name: composer-security-audit
description: >
  Run and gate PHP Composer dependency vulnerability checks with composer
  audit locally and in CI: Packagist/GitHub security advisories, composer.lock
  scans, JSON output, abandoneds, ignore policy, and upgrade paths for owned
  PHP apps. Use when composer audit, Composer CVE scanning, Packagist security
  advisories, FriendsOfPHP advisories, abandoned package warnings, PHP lockfile
  SCA gate, or wiring composer audit into GitHub Actions/GitLab CI for PHP.
---

# Composer Security Audit

Own **local and CI `composer audit`** for PHP: require committed
**`composer.lock`**, interpret Packagist advisories, fail pipelines on policy
findings, and fix-then-recheck. Prefer the repo toolchain. Hand multi-lang
SCA/SBOM to supply-chain skills; lock/pin bots to `dependency-pinning-strategies`.

## When To Use

- Adding or fixing **`composer audit`** in developer workflow or CI
- Interpreting Packagist advisories, patched versions, and **abandoned** signals
- Scanning apps from a committed **`composer.lock`** (with/without `--no-dev`)
- Failing PRs/main on known PHP dependency vulns; JSON artifacts for triage
- Keywords: composer audit, Packagist security, PHP CVE gate, security-advisories

Do **not** use as primary for: lock/pin bots → `dependency-pinning-strategies`;
multi-lang SBOM/SCA → `sbom-and-supply-chain`; SBOM presence →
`sbom-ci-enforcement`; CVE clocks → `vulnerability-sla-process`; pipeline layout
→ `ci-cd-pipeline-patterns`; code quality → `code-quality-standards`; registry
confusion → `dependency-confusion`.

## Repo Config First

Repo and org policy **outrank** defaults below.

1. **`composer.json`:** package roots, path repos, monorepo members
2. **`composer.lock`:** committed for apps (required for reproducible audit)
3. **CI workflows:** PHP/Composer setup, cache keys, required check names
4. **Composer version:** pin PHP + Composer; need **Composer ≥ 2.4** for `audit`
5. **Auth/repos:** `auth.json` (never commit secrets), private Packagist/Satis
6. **Gate policy:** all vs severity floor; `--no-dev`; abandoned warn vs fail; exception/expiry
7. **Neighbors:** Dependabot/Renovate Composer, SBOM job, branch protection

Extend the real install job’s root; do not invent a divergent path.

## Workflow

### 1. Toolchain and lock

```bash
php -v && composer --version    # require ≥ 2.4 for `composer audit`
composer validate --no-check-publish
```

Match CI PHP minor and Composer major to production. Prefer **committed
`composer.lock`**; without it, coverage is weaker—generate per
`dependency-pinning-strategies`.

### 2. Local scan

From the directory that owns **`composer.lock`**:

```bash
composer install --no-interaction --prefer-dist
composer audit
composer audit --format=json > composer-audit.json
composer audit --no-dev                 # prod tree when policy says so
composer audit --abandoned=report       # or fail per org policy
```

Audit checks the **locked graph** against known advisories. Record command,
project path, PHP/Composer versions, and whether `--no-dev` was used.

### 3. Config and ignores

| Concern | Practice |
| --- | --- |
| Ignore advisory | Explicit id + **owner + expiry** ticket |
| Abandoned packages | Upgrade/replace; no eternal silent ignore |
| Dev-only vulns | `--no-dev` only if dev never ships; else fix/track |
| Hard compile fail | Optional `roave/security-advisories` (dev) |

Never mass-ignore. Every ignore is debt (`vulnerability-sla-process`).

### 4. CI gate

1. Setup PHP; restore cache; ensure **`composer.lock`** present.
2. `composer install --no-interaction --prefer-dist`; fail on lock drift if
   required.
3. Run **`composer audit`** (optional `--no-dev`, JSON) at each shippable root; matrix monorepo locks.
4. **Fail closed** per policy; upload JSON; enforce required check.
5. Reuse private auth secrets; never print tokens.

```yaml
- uses: shivammathur/setup-php@v2
  with: { php-version: "8.3", tools: composer }
- run: composer install --no-interaction --prefer-dist
- run: composer audit
```

### 5. Triage, fix, verify

| Finding shape | Action |
| --- | --- |
| Direct dep, fix published | Bump; `composer update <pkg>`; test |
| Transitive only | Upgrade intermediate; avoid eternal aliases |
| Abandoned | Replace/fork with ownership; re-lock; re-audit |
| No fix yet | Owner+expiry ignore, or isolate |
| Dev-only / not in image | Prove with `--no-dev` + image; still track |

After bumps: run repo tests. SLA → `vulnerability-sla-process`. **Verify:** same
PHP/Composer as CI; intentional old vuln fails gate; all lock roots scanned;
redact private URLs/creds.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| composer audit local/CI, Packagist advisories, abandoned | **This skill** | — |
| composer.lock pin/update bots, frozen installs | `dependency-pinning-strategies` | this after lock exists |
| Multi-lang SBOM / SCA inventory | `sbom-and-supply-chain` | this for PHP audit gate |
| SBOM file/attest presence gate | `sbom-ci-enforcement` | this for vuln content |
| CVE clocks, exception tickets | `vulnerability-sla-process` | this for detection evidence |
| Private vs public resolve / confusion | `dependency-confusion` | this after registry fixed |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for job body |
| Fix quality, tests, review baseline | `code-quality-standards` | **always** on code/CI changes |

Keep **this skill primary** until lockfile, Composer version, and gate are set.

## Output Checklist

- [ ] Repo PHP/Composer, roots, `composer.lock`, and existing CI job read first
- [ ] Composer ≥ 2.4; runtime pinned (not floating latest on gates)
- [ ] Scan from lockfile root(s); JSON uploaded; `--no-dev` policy documented
- [ ] Ignores/abandoneds have owner/expiry; no silent mass-ignore
- [ ] Gate policy clear; required check enforced; monorepo matrix complete
- [ ] Updates use locked workflow; tests pass after bumps
- [ ] Private auth safe; secrets redacted; same pin/command as CI verified
- [ ] Hand-offs: `dependency-pinning-strategies`, `vulnerability-sla-process`, `sbom-and-supply-chain` / `sbom-ci-enforcement`, `code-quality-standards`
- [ ] Rules: repo-first pin; no silent mass-ignore; authorized packages only

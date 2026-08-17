---
name: renovat-bot-security
description: >
  Harden Mend Renovate (self-hosted or app) for supply-chain and CI safety:
  token least privilege, auto-merge gates, allowScripts/ignoreScripts,
  hostRules secrets, registry allowlists, custom/regex managers, and PR
  trust under branch protection. Use when Renovate config, renovate.json,
  renovate.json5, .github/renovate.json, self-hosted Renovate, Mend Renovate
  app, auto-merge dependency PRs, hostRules, encrypted secrets, allowScripts,
  packageRules security, Renovate token scope, or bot-driven dependency
  update risk is in scope — hand lockfile pin policy to
  dependency-pinning-strategies and CVE/SBOM inventory to sbom-and-supply-chain.
---

# Renovate Bot Security

Secure **how Renovate proposes and merges dependency updates**: bot identity,
token scope, config surface (`renovate.json` / presets), install-time script
risk, registry hosts, and auto-merge under required CI. Owns Renovate
**control-plane and PR trust** only—not general pin strategy or full SCA.

## When To Use

- Adding, reviewing, or hardening `renovate.json`, `renovate.json5`,
  `.github/renovate.json`, or org/shared Renovate presets
- Self-hosted Renovate (Docker/K8s/CLI) or Mend/GitHub Renovate app permissions
- Auto-merge, vulnerability alerts, grouping, majors, or lockfile maintenance
- `hostRules`, encrypted secrets, private registries, `allowScripts` /
  `ignoreScripts`, custom/regex managers, `postUpgradeTasks`, `binarySource`
- Mentions: Renovate bot, renovate config, auto-merge deps, Renovate token,
  hostRules, packageRules, dependency dashboard, 依赖机器人安全

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Lockfiles, exact vs range, freeze CI installs | `dependency-pinning-strategies` |
| SBOM, CVE inventory, provenance | `sbom-and-supply-chain` / `sbom-ci-enforcement` |
| Registry namespace / public fallback confusion | `dependency-confusion` |
| Branch protection, required checks, CODEOWNERS | `branch-protection-rules` |
| CI layout, fork secrets, cache keys | `ci-cd-pipeline-patterns` |
| License allow/deny | `license-compliance-scan` |

## Repo Config First

Repo and org Renovate policy **outrank** the defaults below.

1. **Config files:** root / `.github` `renovate.json(5)`, `package.json#renovate`,
   `extends` presets (org, `config:recommended`, custom)
2. **Bot identity:** GitHub App vs PAT vs self-hosted platform token; write scope
3. **Existing gates:** required checks, CODEOWNERS, ruleset bot bypass
4. **Registries:** private hosts; secrets only via `hostRules` / platform store
5. **SCA/license gates** on PRs — do not auto-merge around them
6. **Self-hosted runtime:** image digest, env mounts, egress, who edits scheduler
7. **Neighbors:** Dependabot dual-bot conflict, release-please, digest bots

**Precedence:** Org preset and token policy win. Flag write-all tokens, broad
auto-merge, install scripts enabled, or plaintext registry passwords in config.

## Workflow

1. **Inventory the control plane.** Config path(s), `extends` chain, onboarding
   state, dashboard; hosted app vs self-hosted cron; managers in use
   (`npm`, `pip`, `docker`, `github-actions`, custom).

2. **Least-privilege bot identity.** Prefer a **GitHub App** (or equivalent)
   limited to needed repos; avoid classic PAT with org admin. Self-hosted:
   rotated short-lived token. Separate registry `hostRules` credentials from
   the platform git token. Never commit raw passwords; keep
   `exposeSensitiveEnvInLog` off.

3. **Config trust and `extends`.** Prefer org-controlled presets; pin or vendor
   third-party presets; review `extends` like code. CODEOWNERS on
   `renovate.json*`. Reject `postUpgradeTasks` / shell that run without review.

4. **Install scripts and execution surface.** Default **deny** lifecycle scripts
   (`ignoreScripts`); `allowScripts` only for named packages with justification.
   Treat `binarySource=install` and custom managers that fetch binaries as high
   risk. Regex managers: tight file match + version extract; no open untrusted
   URL templates. Minimal `allowedEnv` / `customEnvVariables` (no cloud creds).

5. **Registry and host allowlisting.** Explicit tight `hostRules` hostnames.
   Align with `dependency-confusion` (scoped names, no dual-index footguns).
   Review Docker bases and Actions updates; prefer digest-aware rules for tags.

6. **Auto-merge and PR trust.** No blanket `automerge` on majors or unscoped
   packages. Automerge only after **required CI green** (e.g. patch/minor in
   known ecosystems). Same branch protection as humans; bot bypass only if CI
   is mandatory and audited. Group for noise, not to hide risky jumps.
   Vulnerability/OSV PRs still need CI—prioritize, do not force-merge.

7. **Ops hygiene.** Cap concurrent PRs/schedules; untrusted forks must not run
   privileged Renovate workflows; limit who can trigger dashboard retries.

8. **Verify.** Staging: token cannot push outside allowed repos; automerge
   blocked on red CI; scripts not run for random new deps; hostRule secrets
   never logged. Document break-glass for emergency CVE bumps.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Renovate config, token, auto-merge, hostRules, allowScripts, bot PR trust | **This skill** | — |
| Lockfiles, exact vs range, freeze install | `dependency-pinning-strategies` | this for bot update policy |
| SBOM / CVE / provenance | `sbom-and-supply-chain` | this for alert/merge path |
| SBOM CI gates | `sbom-ci-enforcement` | automerge must respect gates |
| Registry namespace confusion | `dependency-confusion` | hostRules / registry list |
| Required checks, CODEOWNERS, bot bypass | `branch-protection-rules` | Renovate exceptions |
| CI secrets, fork PRs, job design | `ci-cd-pipeline-patterns` | Renovate job identity |
| Config-as-code quality | `code-quality-standards` | **always** on renovate files |

## Output Checklist

- [ ] Config paths + `extends` inventoried; untrusted presets flagged
- [ ] Bot identity least-privilege (scope, rotation; no org-admin PAT)
- [ ] Secrets via hostRules / encrypted / platform store; no log exposure
- [ ] Install scripts denied by default; allowScripts allowlisted if any
- [ ] Custom/regex managers and postUpgradeTasks reviewed or removed
- [ ] Registry hosts explicit; confusion-safe resolve path
- [ ] Automerge narrow (no blind majors); requires green CI + protection
- [ ] CODEOWNERS / review required on Renovate config changes
- [ ] Dual-bot conflict (Dependabot) resolved or documented
- [ ] Self-hosted: image, egress, who edits the scheduler
- [ ] Verified: fail-CI blocks merge; secret redaction; scope boundary
- [ ] Hand-offs: pins → `dependency-pinning-strategies`; CVE/SBOM → supply-chain

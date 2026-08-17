---
name: secrets-in-ci-pipelines
description: >
  CI/CD secrets hygiene: prefer OIDC and short-lived federated cloud roles over
  long-lived tokens, scope secrets by environment, block fork-PR access, and
  keep credentials out of logs and artifacts. Use when GitHub Actions/GitLab
  OIDC, static AWS/GCP/Azure keys in CI, PATs in workflows, secret masking,
  environment protection, or CI credential leak review.
---

# Secrets In CI Pipelines

Harden **how CI jobs obtain, use, and dispose of credentials** on pipelines you
own or are authorized to review. Focus is **OIDC / workload identity vs
long-lived tokens**, secret scoping, and leak prevention — not general app vault
design or full pipeline stage layout.

## Scope And Authorization

- **In scope:** Org/repo workflows, runners, environment secrets, OIDC trust
  policies, and CI identity to cloud/package registries under ownership or
  written engagement scope.
- **Out of scope:** Stealing or replaying third-party CI secrets; abusing found
  tokens; weakening prod gates “to test.”
- Prefer non-prod roles and canary secrets for experiments. **Rotate first** on
  live exposure; redact tokens from tickets, logs, and chat.
- Treat `pull_request_target` + untrusted checkout as high risk without review.
- Pair lifecycle policy with `secrets-management-hygiene`; stage layout with
  `ci-cd-pipeline-patterns`.

## Use When

- Workflows use static cloud keys / long-lived PATs when OIDC is available
- Designing or reviewing **OIDC** trust (`id-token: write`, cloud role `sub`/`aud`,
  GitLab OIDC, Azure federated credentials)
- Secrets leak into CI logs, artifacts, caches, or Docker build contexts
- Fork PRs or untrusted branches may read environment secrets
- Environment protection / branch filters missing for prod credentials
- Mentions: CI secrets, OIDC federation, long-lived tokens, fork PR secrets

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| App/runtime vault, rotation, .env hygiene | `secrets-management-hygiene` |
| Full CI stages, cache, artifacts, fail-fast | `ci-cd-pipeline-patterns` |
| App code that loads secrets at runtime | `code-quality-standards` |
| Terraform state/IAM module hardening | `terraform-security-basics` |

## OIDC Vs Long-Lived Tokens

| Approach | Prefer when | Watch-outs |
| --- | --- | --- |
| **OIDC / workload identity** | Cloud supports federation from CI IdP | Mis-bound `sub` is dangerous; test trust changes |
| **Environment static secrets** | Vendor has no federation | Long-lived; rotate; env-scope only |
| **Org-wide shared keys** | Almost never | Every workflow can steal; no env split |
| **PATs / deploy keys** | Git/API automation only | Fine-grained + short life; no admin PAT in all jobs |

**Rule:** If federation exists, **prefer OIDC**. Keep static secrets only with
owner, expiry, least privilege, and protected environments.

## Workflow

### 1. Inventory identities and secret surfaces

1. List workflows, triggers (PR/push/tag/schedule/dispatch), and jobs that need
   cloud/registry/API credentials.
2. Catalog secret **names** (not values): store, consumer, env, rotation, fork access.
3. Note runner type (hosted vs self-hosted) — shared self-hosted expands theft impact.
4. Flag debug (`ACTIONS_STEP_DEBUG`, `set -x`) on release/deploy jobs.

### 2. Prefer OIDC; bind trust tightly

1. Least-privilege job `permissions`; grant `id-token: write` only where needed.
2. Cloud trust conditions: org/repo, ref or environment, workflow identity when supported.
3. Split **plan/read** vs **deploy/write** roles; prod only from protected env + trusted ref.
4. Deny assume from fork PR contexts; never share prod role with external `pull_request`.
5. Document role names/ARNs in runbooks — not long-lived access keys.

### 3. Scope remaining static secrets

1. Production credentials only in **protected environments** (approvals, branch rules).
2. Distinct staging vs prod values; never prod keys in PR lint jobs.
3. One consumer principal per secret when practical; single package/project scope.
4. Time-box break-glass PATs; pin third-party actions by SHA; pass minimal secrets.

### 4. Stop leak paths

1. Mask secrets; never echo, `printenv`, or log URLs that embed tokens.
2. Avoid secrets in `$GITHUB_ENV`, world-readable files, or Docker build args —
   use secret mounts / BuildKit secrets.
3. Do not upload secrets in artifacts, coverage, or crash dumps.
4. Block secret access when executing untrusted PR code; isolate self-hosted runners.

### 5. Rotate, revoke, verify

1. On exposure: **revoke/rotate first**, then scrub logs/artifacts, then audit cloud activity
   (`secrets-management-hygiene`).
2. Prove OIDC path works in staging; disable static keys when unused.
3. Confirm fork PRs cannot read prod secrets.
4. Apply `code-quality-standards` to credential scripts; `ci-cd-pipeline-patterns`
   when restructuring job trust boundaries.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CI OIDC vs long-lived tokens, fork isolation, job secret leaks | **This skill** | — |
| Org-wide vault, inventory, rotation, leak IR | `secrets-management-hygiene` | this skill for CI injection |
| Pipeline stages, cache, artifacts, deploy gates | `ci-cd-pipeline-patterns` | this skill for credential model |
| Scripts/actions handling credentials | `code-quality-standards` | this skill for CI threat model |
| App SSRF/metadata (not CI store) | `ssrf-server-side-request-forgery` / `cloud-metadata-ssrf-defenses` | this skill if CI role is victim |

- **`secrets-management-hygiene`:** canonical lifecycle; CI is one injection path.
- **`ci-cd-pipeline-patterns`:** stage/cache/artifact design over credential model.
- **`code-quality-standards`:** baseline for scripts and custom actions.
- **`ssrf-server-side-request-forgery`:** app-side fetch issues, not pipeline wiring.

## Checklist

- [ ] CI identities and secret names inventoried (no plaintext values)
- [ ] OIDC/workload identity used where the provider supports it
- [ ] Trust policy binds repo/ref/environment; prod role not assumable from forks
- [ ] Job permissions least privilege; `id-token: write` only where needed
- [ ] Static secrets environment-scoped, least privilege, owned, rotatable
- [ ] Prod secrets blocked from untrusted PR / fork contexts
- [ ] No secrets in logs, artifacts, caches, or image layers
- [ ] Third-party actions pinned; minimal secret inputs
- [ ] Self-hosted runner isolation reviewed for secret-bearing jobs
- [ ] Leak response rotate-first documented (`secrets-management-hygiene`)
- [ ] Pipeline structure aligned with `ci-cd-pipeline-patterns`
- [ ] Credential scripts meet `code-quality-standards`

## Rules

- Short-lived, scoped, federated identity beats shared long-lived keys.
- A secret available to an untrusted PR job is already compromised in principle.
- Masking is not enough — do not materialize secrets in artifacts or layers.
- Defensive and authorized only; never abuse discovered CI tokens outside scope.
- Re-review OIDC subjects and env gates when workflows, runners, or roles change.

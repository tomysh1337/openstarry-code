---
name: gitlab-ci-security-basics
description: >
  Harden GitLab CI/CD for owned projects: .gitlab-ci.yml trust boundaries,
  protected/masked variables, environment protection, CI_JOB_TOKEN least
  privilege, runner isolation, fork/MR secret exposure, include/template
  supply chain, and deploy gates. Use when GitLab CI security, .gitlab-ci.yml
  review, CI/CD variables, protected environments, CI_JOB_TOKEN, shared
  runners, pipeline secrets, merge request pipelines, include remote, or
  GitLab deploy job hardening.
---

# GitLab CI Security Basics

Secure **GitLab CI/CD** for repositories and groups you own or are authorized
to harden. Prefer existing group/instance policies and shared templates over a
parallel pipeline stack. Pair general stage/cache design with
`ci-cd-pipeline-patterns` and secret lifecycle with `secrets-management-hygiene`.

## When To Use

- Authoring or reviewing `.gitlab-ci.yml`, `*.gitlab-ci.yml` includes, or CI components
- CI/CD variables (masked, protected, environment-scoped, file type) and secret leakage
- Protected branches/tags, protected environments, and manual prod deploy gates
- `CI_JOB_TOKEN`, project/group access tokens, deploy tokens, and job permissions
- Shared vs project runners, privileged Docker, Docker socket, and shell runners
- Fork / external MR pipelines and rules that must not receive protected secrets
- Mentions: GitLab CI security, pipeline secrets, MR pipeline trust, include remote,
  CI_JOB_TOKEN, protected environment, 流水线安全

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Multi-platform CI stages, cache keys, fail-fast layout | `ci-cd-pipeline-patterns` |
| Secret inventory, vault, rotation, .env hygiene | `secrets-management-hygiene` |
| Branch/MR approval, force-push, CODEOWNERS gates | `branch-protection-rules` |
| Dockerfile non-root / layer secrets | `dockerfile-best-practices` |
| SBOM generate/attest gates | `sbom-ci-enforcement` |
| App code quality inside jobs | `code-quality-standards` |

## Repo Config First

Group, instance, and project CI settings **outrank** examples in this skill.

1. **Pipeline files:** root `.gitlab-ci.yml`, `include:` local/project/remote/component paths, CI/CD Catalog usage
2. **CI/CD variables:** project vs group vs instance; protected/masked/expanded; environment scope; file vs env
3. **Protected refs:** protected branches/tags that unlock protected variables and deploy jobs
4. **Environments:** protected environments, required approvers, deployment tiers (prod vs review)
5. **Runners:** shared, group, or project; tags; executor (docker/kubernetes/shell); privileged flag
6. **Token policy:** CI job token allowlist / inbound job token scope; project access token lifetime
7. **MR pipeline mode:** merge request pipelines, merged results, fork trust, secret exposure to MRs
8. **Compliance:** required pipeline config, scan execution policies, secret push protection if licensed

**Precedence:** Documented group/instance policy wins. Flag unprotected prod
variables, privileged shared runners on untrusted code, and remote includes
without pin or ownership.

## Workflow

1. **Map trust levels.** Separate jobs for: fork/external MR → internal MR →
   default branch → tag/release → manual/scheduled prod. Never give lower-trust
   pipelines the same variables or runner tags as prod deploy.

2. **Lock secrets to protected paths.**
   - Mark deploy/prod variables **protected** + **masked** (or file type); scope
     by environment (`production`, not `*`)
   - Ensure only protected branches/tags run jobs that need those variables
   - Disable or carefully control “Expand variable reference” for untrusted input
   - Prefer OIDC/JWT (`id_tokens`) to cloud roles over long-lived AK/SK in variables

3. **Control who can run privileged work.**
   - Prod deploy: `environment: production` + protected environment approvals +
     `rules` limited to default branch or tags; prefer `when: manual` for prod
   - Deny deploy on `merge_request_event` and untrusted sources
   - Pin images (`image: registry/image:tag@sha256:…` when policy requires)

4. **Harden `CI_JOB_TOKEN` and tokens.**
   - Limit job token access to needed projects (allowlist / limit outbound)
   - Do not grant API `api` scope tokens to every pipeline; use least privilege
   - Never echo tokens; avoid `set -x` around auth; mask custom variables
   - Rotate project/group access tokens and deploy tokens on schedule and on leak

5. **Runner and executor isolation.**
   - Prefer docker/k8s executors over shell for multi-tenant; no `privileged: true`
     unless buildkit/dind is required and job code is trusted
   - Never mount `docker.sock` into jobs that run untrusted MR code
   - Tag sensitive runners (`prod-deploy`) and select them only from trusted rules
   - Treat shared runners as hostile multi-tenant: no host secrets, no privileged

6. **Supply chain of pipeline config.**
   - Prefer `include: local` or same-group project includes; pin remote/component
     refs to immutable SHA or version, not floating `main`
   - Review third-party CI components like application deps; own critical templates
   - Block user-controlled variables from becoming `script` fragments (injection)

7. **Artifacts, cache, and logs.**
   - Do not put secrets in artifacts or cache paths; expire artifacts tightly on MRs
   - Restrict `artifacts:reports` and pages if they could leak tokens or internal URLs
   - Fail closed on secret detection / SAST when org policy requires; avoid
     `allow_failure: true` on security gates without a follow-up required job

8. **Verify.** Open an external/fork MR: confirm protected variables absent and
   deploy jobs skipped. Push to protected branch: confirm masked logs and gated
   prod. Attempt pipeline variable override of critical settings; confirm
   project settings block unauthorized overrides.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| GitLab CI secrets, runners, job token, MR trust, includes, protected envs | **This skill** | — |
| Generic multi-CI stages, caching, fail-fast, artifacts layout | `ci-cd-pipeline-patterns` | this skill for GitLab controls |
| Vault/rotation/.env/secret inventory | `secrets-management-hygiene` | this skill for GitLab variable flags |
| Protected branch/MR approvals, force-push | `branch-protection-rules` | this skill for CI variable unlock on protected refs |
| Image build hygiene | `dockerfile-best-practices` | this skill for job `image`/dind risk |
| SBOM gate in pipeline | `sbom-ci-enforcement` | this skill for job trust level |
| Scripts/YAML quality | `code-quality-standards` | always with implementation |

## Output Checklist

- [ ] Repo/group CI files, variables, runners, and protected refs inventoried first
- [ ] Trust levels split: fork MR / internal MR / default branch / tag / prod
- [ ] Prod secrets protected + masked (or file); environment-scoped; not on MRs
- [ ] Deploy jobs use protected environments, narrow `rules`, manual/tag as required
- [ ] OIDC/`id_tokens` preferred over long-lived cloud keys in CI variables
- [ ] `CI_JOB_TOKEN` and access tokens least-privilege; no token echo in logs
- [ ] Runners non-privileged for untrusted code; no docker.sock on MR jobs
- [ ] Includes/components pinned or owned; no untrusted remote `main`
- [ ] Artifacts/cache free of secrets; short retention on untrusted pipelines
- [ ] Security jobs not silently `allow_failure` without a required gate
- [ ] Verified: fork MR lacks protected vars; prod path gated and logged safely
- [ ] Paired with `ci-cd-pipeline-patterns` / `secrets-management-hygiene` / CQS as needed

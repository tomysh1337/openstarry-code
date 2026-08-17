---
name: docker-hub-rate-limit-ci
description: >
  Diagnose and fix Docker Hub pull rate limits in CI: anonymous vs authenticated
  quotas, shared runner IPs, mirrors, private base caches, and registry migration.
  Use when CI fails with toomanyrequests, 429, Docker Hub rate limit, docker.io
  pulls flaky on GitHub Actions/GitLab/shared runners, or hardening image pulls
  against Hub throttling — hand Dockerfile structure to dockerfile-best-practices;
  hand pipeline stages/secrets/OIDC to ci-cd-pipeline-patterns.
---

# Docker Hub Rate Limit CI

Keep **CI image pulls reliable** when jobs hit **Docker Hub** (`docker.io`)
anonymous or free-tier quotas. Prefer **authenticated pulls**, **pull-through /
private mirrors**, and **non-Hub bases** over retry spam. Owned CI only; never
paste Hub tokens into logs or public workflow dumps.

## When To Use

- Jobs fail with `toomanyrequests`, HTTP **429**, or “You have reached your pull
  rate limit” against `registry-1.docker.io` / `docker.io`
- Flaky `docker pull` / `docker build` bases, Compose services, or kind/minikube
  loads on **shared runners** (shared egress IP)
- Planning Hub login/PAT, pull-through mirror, or move bases to GHCR/ECR/GCR/ACR
- Mentions: Docker Hub rate limit, anonymous pull limit, CI docker pull 429

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage, non-root, layer secrets | `dockerfile-best-practices` |
| Pipeline stages, OIDC, fork PR secret isolation | `ci-cd-pipeline-patterns` |
| Image sign/verify (Cosign) | `container-image-signing` |
| Compose host mounts / privilege review | `docker-compose-security` |
| Workflow/script quality baseline | `code-quality-standards` |

## Repo Config First

Repo and org CI/registry policy **outrank** examples below.

1. Workflows: `.github/workflows/*`, `.gitlab-ci.yml`, Jenkins/Buildkite
2. Pull sources: Hub tags vs private registry vs mirror hostname
3. Secrets: `DOCKERHUB_USERNAME`/`TOKEN`, org PAT, cloud registry OIDC
4. Runner type: hosted vs self-hosted vs shared SaaS (egress IP matters)
5. Base-image policy: approved digests, internal mirror, Hub bans
6. Build cache: Buildx GHA/registry cache, pre-warmed runner images
7. Neighbors: Dockerfile layout, pipeline secrets, image signing gates

**Precedence:** Extend existing login/mirror patterns. Surface unauthenticated
Hub pulls on hosted runners, `:latest` thrash, and tokens in debug logs.

## Workflow

### 1. Confirm it is Hub rate limit

1. Capture log: registry host, image ref, status/message.
2. Separate **rate limit** from auth failure, network, or platform outage.
3. Note **anonymous vs logged-in**, runner kind, matrix concurrency.
4. Inventory jobs pulling `docker.io/*` or unqualified official images (→ Hub).

### 2. Reduce Hub dependency (preferred long-term)

| Approach | When | Notes |
| --- | --- | --- |
| **Private/org registry** | GHCR/ECR/GCR/ACR/Harbor | Mirror bases once; CI pulls internal |
| **Pull-through cache** | Harbor/Artifactory/cloud | One auth upstream; many CI clients |
| **Vendor non-Hub bases** | Policy allows | e.g. `public.ecr.aws`, `gcr.io` |
| **Pin digests + layer cache** | Still on Hub short-term | Buildx cache-from/to cuts full pulls |

Copy bases into the org registry; point Dockerfiles/Compose at **explicit non-Hub
refs** (or daemon registry mirrors).

### 3. Authenticate remaining Hub pulls

1. Create a **Hub PAT** (read/pull) or bot; store in **environment/org secrets**.
2. Before Hub pull/build: `docker login` or `docker/login-action` (username+token).
   Cover Buildx/buildkit remote builders that pull bases.
3. Login only in jobs that need Hub; least-privilege `permissions`; **never**
   expose secrets to fork PRs.
4. Self-hosted: prefer daemon mirror or pre-pulled bases over per-job Hub creds
   when policy allows.

```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### 4. Cut pull volume and storms

1. Reuse job images/artifacts/services; avoid N identical base pulls per matrix.
2. Cache layers (`type=gha` / registry cache); pin tags/digests deliberately.
3. Sync/refresh mirrors on a **single** trusted pipeline, not every PR.
4. Do not paper over 429s with blind `retry:` loops.

### 5. Verify and operate

1. Re-run under realistic concurrency; confirm pulls stay green.
2. Document mirror vs Hub ownership, secret names, rotation owner.
3. Alert on recurring 429s as config debt. Apply `code-quality-standards` to
   workflow YAML; pair with `ci-cd-pipeline-patterns` and
   `dockerfile-best-practices`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Hub 429/toomanyrequests, CI pull quota, mirror/login for docker.io | **This skill** | — |
| Dockerfile multi-stage / non-root / layer hygiene | `dockerfile-best-practices` | this for pull source |
| Pipeline graph, OIDC, fork secrets, job permissions | `ci-cd-pipeline-patterns` | this for Hub login/mirror |
| Cosign/Sigstore image identity | `container-image-signing` | after pulls reliable |
| Compose security (sockets, privileges) | `docker-compose-security` | this if Compose→Hub |
| Workflow quality | `code-quality-standards` | **always** on CI edits |

**Hand-off:** Dockerfile body → **`dockerfile-best-practices`**. CI topology/secrets
→ **`ci-cd-pipeline-patterns`**. This skill owns **Hub quota diagnosis**,
**authenticated pull**, **mirror/private base strategy**, and **pull-volume**
controls.

## Output Checklist

- [ ] Failure classified as Hub rate limit (host, message, anonymous vs auth)
- [ ] All CI Hub/unqualified official pull sites inventoried
- [ ] Repo secrets, runner type, mirror/registry policy read first
- [ ] Prefer private registry or pull-through; refs updated off Hub where possible
- [ ] Remaining Hub pulls use secret-backed login (not fork PRs)
- [ ] Layer/registry cache and matrix concurrency cut duplicate pulls
- [ ] Digests/tags pinned; no endless unauthenticated retry
- [ ] Tokens redacted; rotation owner documented
- [ ] Dockerfile → `dockerfile-best-practices`; pipeline → `ci-cd-pipeline-patterns`; CQS on YAML

## Rules

- Anonymous Hub pulls on **shared egress IPs** are unreliable by default.
- Prefer **mirror/private bases** over plan upgrades alone; auth remaining Hub pulls.
- Never commit or echo tokens. Do not “fix” quotas with blind retries.
- Owned CI only; do not probe third-party Hub accounts or scrape credentials.

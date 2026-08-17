---
name: dockerfile-best-practices
description: >
  Author and review Dockerfiles for multi-stage builds, non-root runtime,
  layer caching, and secrets that never land in image layers. Use when
  Dockerfile, Docker best practices, Docker 最佳实践, container image build,
  multi-stage build, non-root user, .dockerignore, image hardening, or
  reducing image size/attack surface for services and CI build images.
---

# Dockerfile Best Practices

Produce Dockerfiles that are fast to rebuild, small enough to ship, and safe
enough to run. Prefer the repository’s existing base images, registry, and
orchestration conventions over inventing a second house style.

## Use When

- Writing or reviewing a `Dockerfile`, multi-stage `Dockerfile.*`, or image
  build script
- Fixing slow rebuilds, bloated images, root-as-default runtime, or secrets
  baked into layers
- Adding `.dockerignore`, HEALTHCHECK, or non-root `USER` for services
- Choosing base tags (`slim` / distroless / chainguard) and pin strategy
- User mentions: Dockerfile, Docker best practices, Docker 最佳实践,
  multi-stage, image hardening, non-root container, layer cache

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| CI workflow / pipeline stages, GHA secrets, artifact upload | `ci-cd-pipeline-patterns` |
| Application code quality inside the image | `code-quality-standards` |
| Authorized container breakout / host boundary research | `container-escape-techniques` |
| Shell script style for entrypoints | `shell-script-style` |

## Repo Config First

Repo config and neighboring Dockerfiles **outrank** this skill’s defaults.

1. **Existing Dockerfiles:** copy patterns from the closest service image in
   the monorepo (base image org, multi-stage layout, `USER`, healthcheck)
2. **Base image policy:** private mirror, approved digest pins, distroless vs
   distro, language runtime versions in `go.mod` / `.nvmrc` / `runtime.txt`
3. **Orchestration:** Kubernetes securityContext, Compose `user:`, ECS task
   definition — align image `USER` with what the platform overrides
4. **Build system:** BuildKit, `docker buildx`, Kaniko, Cloud Native Buildpacks,
   Bazel/rules_docker — use the project’s builder flags and cache mounts
5. **Registry & tagging:** immutable digests in prod, branch/sha tags in CI,
   never `latest` as the only production pin unless the platform enforces digests
6. **Secrets tooling:** BuildKit secrets (`--secret`), CI OIDC to cloud,
   external secret stores — never invent `ARG PASSWORD` if the repo already
   uses secret mounts
7. **Ignore files:** existing `.dockerignore` / `.containerignore`; extend,
   do not replace with a weaker set
8. **Security scanners:** Trivy, Grype, Docker Scout, org policy gates in CI

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that leave root runtime, unpinned bases, or secrets in layers.

## Workflow

1. **Define the runtime contract.** Process command, ports, config via env/files,
   required files at runtime, whether the process drops privileges, and whether
   a shell is needed (usually not for prod).
2. **Choose multi-stage layout.** Separate: dependency fetch → build/test →
   minimal runtime. Runtime stage copies only artifacts and required shared libs.
3. **Order layers for cache.** Least-changing instructions first (base, OS
   packages, dependency manifests), app source last. Copy lockfiles before
   full source; run install before `COPY` of app code.
4. **Exclude build junk.** Write/update `.dockerignore` (`.git`, tests if not
   needed, `node_modules`, local env files, docs, CI caches).
5. **Inject secrets only at build time.** Prefer BuildKit `--secret` / SSH
   mounts; never `ENV`/`ARG` for long-lived credentials; never `COPY` `.env`
   or key files into layers that ship.
6. **Run as non-root.** Create a fixed UID/GID user; `USER` before `CMD`/`ENTRYPOINT`;
   ensure writable paths (tmp, cache) are owned correctly; document if the
   orchestrator must set `runAsNonRoot`.
7. **Harden runtime.** Minimal base; drop package managers from final image when
   practical; pin versions/digests; set `STOPSIGNAL` if needed; add `HEALTHCHECK`
   only when the platform does not own probes (or match K8s probes).
8. **Verify.** Build with BuildKit; confirm non-root (`docker run --rm img id`);
   inspect history for secret-looking layers; run org scanner; smoke-test the
   entrypoint; measure image size vs previous.

## Core Practices

### Multi-stage

- **Builder stage:** compilers, headers, test toolchains, full SDK
- **Runtime stage:** JRE/slim runtime, static binary, or distroless
- Copy with explicit paths: `COPY --from=build /out/app /app`
- Prefer named stages (`AS deps`, `AS build`, `AS runtime`) for readability and
  targeted rebuilds (`--target`)

### Layer caching

- One logical concern per `RUN` when it aids cache (deps vs app compile), but
   combine related `apt-get update && install && clean` to avoid stale indexes
- Use BuildKit cache mounts for package managers when the builder supports them:
  `RUN --mount=type=cache,target=/root/.cache/go-build ...`
- Avoid `COPY . .` before dependency install
- Prefer lockfiles (`package-lock.json`, `go.sum`, `poetry.lock`, `Cargo.lock`)

### Non-root and filesystem

- Numeric `USER 65532:65532` (or project UID) helps Kubernetes `runAsNonRoot`
- Directories the app writes must be chowned in the Dockerfile or tmpfs/emptyDir
- Do not require root solely for binding low ports; use high ports or platform
  `cap_net_bind_service` deliberately

### Secrets not in the image

| Bad pattern | Prefer |
| --- | --- |
| `ENV API_KEY=...` / `ARG TOKEN` then `RUN curl -H $TOKEN` left in history | `RUN --mount=type=secret,id=token ...` |
| `COPY .env` / private keys into image | Mount at runtime or inject via orchestrator |
| Multi-line `RUN` that echoes credentials into files kept in final stage | Write only to build-stage paths never copied forward |
| “Delete secret in next layer” after `ADD` | Still recoverable from earlier layers — never copy secret layers |

### Base images and tags

- Pin by digest for production (`image@sha256:…`) when policy allows
- Prefer minimal/maintained bases over full `ubuntu` + ad-hoc cleanup
- Rebuild on a schedule for CVE patches even when Dockerfile is unchanged

### `.dockerignore` (minimum ideas)

```
.git
.gitignore
**/.env
**/.env.*
**/node_modules
**/__pycache__
**/*.md
.ci
.github
Dockerfile*
.dockerignore
```

Tune per language; do not ignore files the build actually needs (e.g. `go.sum`).

## Good / Bad Examples

### Multi-stage Node service

**Good**

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN useradd --uid 10001 --user-group --create-home appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER 10001:10001
EXPOSE 8080
CMD ["node", "dist/server.js"]
```

**Bad**

```dockerfile
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
ENV NODE_ENV=production
# runs as root; dev deps + source + secrets from context all in one layer soup
CMD ["node", "src/server.js"]
```

### Layer caching (Go)

**Good**

```dockerfile
FROM golang:1.22-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/api ./cmd/api

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/api /api
USER nonroot:nonroot
ENTRYPOINT ["/api"]
```

**Bad**

```dockerfile
FROM golang:1.22
WORKDIR /src
COPY . .
RUN go build -o /api ./cmd/api
# any source edit busts module download; final image still has full toolchain
CMD ["/api"]
```

### Secrets during build (private module / npm)

**Good** — BuildKit secret mount (token never in image config/history as ENV)

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci --omit=dev
```

Build: `docker buildx build --secret id=npmrc,src=$HOME/.npmrc .`

**Bad**

```dockerfile
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > ~/.npmrc \
 && npm ci \
 && rm ~/.npmrc
# ARG/ENV values and intermediate layers remain recoverable
```

### Non-root + writable dirs (Python)

**Good**

```dockerfile
FROM python:3.12-slim-bookworm AS runtime
RUN useradd --uid 10001 --user-group appuser \
 && mkdir -p /app /tmp/app \
 && chown -R appuser:appuser /app /tmp/app
WORKDIR /app
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app ./app
USER 10001:10001
ENV HOME=/tmp/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Bad**

```dockerfile
FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
# root; no .dockerignore assumed; credentials in tree may be copied
CMD ["python", "app.py"]
```

### apt packages without cache bloat

**Good**

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
```

**Bad**

```dockerfile
RUN apt-get update
RUN apt-get install -y curl
# lists left on disk; separate layers freeze a stale index risk pattern
```

## Misconfiguration awareness (not an escape guide)

Weak images increase blast radius if a process is compromised. For defensive
review only, watch for:

- Root runtime + writable host mounts / `docker.sock` mounts (platform issue;
  call out in review — deep host-boundary research is `container-escape-techniques`)
- Secrets in image history (`docker history`, layer dump)
- Overly broad `COPY . .` including keys, `.git`, CI credentials
- Privileged-by-default Compose samples checked into the repo

Do **not** use this skill to develop escape exploits; harden and document risks.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Dockerfile structure, multi-stage, non-root, layer cache, secrets-in-image | **This skill** | — |
| GitHub Actions / CI stages, pipeline caching, fail-fast, artifacts | `ci-cd-pipeline-patterns` | this skill for image build steps |
| App code reliability/security inside the container | `code-quality-standards` | this skill for packaging |
| Container breakout / privileged misconfig research (authorized) | `container-escape-techniques` | this skill for image-side misconfig awareness only |
| Entrypoint / helper shell style | `shell-script-style` | this skill for when the script runs |
| Registry CVE policy, SBOM gates in pipeline | `ci-cd-pipeline-patterns` | this skill for image contents |

## Checklist

- [ ] Neighboring Dockerfiles, base-image policy, and builder (BuildKit/Kaniko/…) identified
- [ ] Multi-stage: build tools not present in final runtime image
- [ ] Dependency manifests copied and installed before full source `COPY`
- [ ] `.dockerignore` excludes `.git`, local env/secrets, and irrelevant caches
- [ ] No secrets in `ENV`/`ARG` final config; no `COPY` of `.env` or private keys
- [ ] Build-time credentials use secret mounts (or equivalent), not layer-baked tokens
- [ ] Final stage runs as non-root (`USER`); writable paths owned correctly
- [ ] Base tags pinned (version and/or digest) per org policy; not unpinned `latest` for prod
- [ ] Package installs clean caches; image scanned when tooling exists
- [ ] `CMD`/`ENTRYPOINT` match orchestrator probes/ports; smoke test under non-root
- [ ] Cross-check Compose/K8s for `docker.sock`, privileged, or root overrides that undo hardening

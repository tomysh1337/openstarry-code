---
name: distroless-image-adoption
description: >
  Adopt and migrate application runtimes to distroless (or equivalent minimal
  non-shell) container images: multi-stage copy-in, language base choice
  (static/base/cc/java/nodejs/python), nonroot UIDs, CA/tzdata, and debug
  without a package manager. Use when distroless migration, gcr.io/distroless,
  Chainguard/wolfi minimal runtime, no-shell final image, static binary into
  distroless, distroless java/nodejs base, or shrinking production attack
  surface by dropping apt/apk/shell from the runtime stage.
---

# Distroless Image Adoption

Ship **production images without a shell, package manager, or extra OS userland**.
Multi-stage: build in a full SDK image, copy into a **pinned distroless (or
org-approved minimal) runtime**. Owned images only.

## When To Use

- Migrating final stages from `ubuntu`/`debian`/`alpine`/`*-slim` to **distroless**,
  Chainguard, or another **no-shell** runtime base
- Choosing `static`, `base`, `cc`, `java*`, `nodejs*`, or `python*` variants
- Fixing post-migration failures: CA certs, glibc/musl, shared libs, shell-form
  `CMD`, non-root writes; planning debug without `docker exec` shell
- Keywords: distroless, gcr.io/distroless, nonroot, Chainguard, wolfi, minimal
  runtime, no package manager in prod image

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage, layer cache, secrets-in-layers | `dockerfile-best-practices` |
| Cosign/Sigstore sign-verify, admission by digest | `container-image-signing` |
| SBOM generate/publish, fail-if-missing gates | `sbom-ci-enforcement` |
| CI topology, OIDC, build cache | `ci-cd-pipeline-patterns` |
| K8s Pod Security / securityContext | `kubernetes-pod-security` |
| Breakout research / app code quality | `container-escape-techniques` / `code-quality-standards` |

## Repo Config First

Repo and platform policy **outrank** examples below.

1. **Approved bases:** org mirror of `gcr.io/distroless/*`, Chainguard, or internal
   minimal images — do not invent a second public base family
2. **Digest pins:** prod `@sha256:…` vs tags; CVE rebuild cadence
3. **Neighbor Dockerfiles:** language variant, UID, stage names already in use
4. **Builder:** BuildKit/buildx/Kaniko/Bazel multi-stage and secret mounts
5. **Orchestration:** K8s `runAsNonRoot`/`runAsUser`/readOnlyRootFilesystem,
   Compose `user:`, ECS user — align with image UID
6. **Probes, debug, scanners:** platform HTTP/TCP probes; `*-debug` non-prod only;
   Trivy/Grype/Scout on final digests

**Precedence:** Follow the repo. Surface unpinned `latest`, root runtime, debug
bases in prod, or full-distro finals when a minimal base is already approved.

## Workflow

### 1. Fitness and variant

| Good fit | Poor / delay |
| --- | --- |
| Stateless service; fixed binary or language runtime | Needs shell, apt-at-start, or in-container package updates |
| Config via env/files; logs to stdout/stderr | Assumes `/bin/bash`, `curl`, or `apt` at runtime |
| Static Go/Rust or supported JVM/Node/Python base | Native deps need full distro with no known copy list |

If the app shells out to CLI tools in prod, **remove those calls** or keep a slim
distro final — do not fake a shell into distroless.

| Artifact | Typical base |
| --- | --- |
| Fully static (`CGO_ENABLED=0`) | `distroless/static-*:nonroot` |
| Dynamically linked / needs libc | `distroless/base-*` or `cc-*` |
| Java / Node / Python | matching `java*` / `nodejs*` / org Python image |

Prefer **`:nonroot`**. Pin by **digest** in prod when policy allows.

### 2. Multi-stage layout

1. **Build:** full SDK; produce `/out` or `/app` artifact tree.
2. **Runtime:** approved distroless only — **no** package installs.
3. `COPY --from=build` binaries, prod deps, and required data only.
4. Set `USER` nonroot for K8s alignment; `ENTRYPOINT`/`CMD` as **JSON exec form**
   with absolute paths (shell form fails without `/bin/sh`).

```dockerfile
# syntax=docker/dockerfile:1
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

### 3. Runtime contract, debug, rollout

1. Writable paths via emptyDir/tmpfs; set `HOME`/`XDG_*` under nonroot if needed.
2. Test `readOnlyRootFilesystem` early; mutable state off the image FS.
3. Prefer high ports; PID 1-friendly process; TLS trust in base + custom CA PEM.
4. Timezones from image data or mounts — never apt-install in the final stage.
5. CI smoke-test digest; debug via `*:debug`/ephemeral containers **non-prod only**.
6. Confirm non-root + `runAsNonRoot`; scan final digest; note size/CVE delta; apply CQS.
7. Document incident debug without a prod shell; roll out canary → fleet with rollback.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Distroless / no-shell final image adoption | **This skill** | — |
| Dockerfile multi-stage, cache, secrets | `dockerfile-best-practices` | this when final is distroless |
| Sign/verify, admission trust | `container-image-signing` | this for image contents |
| SBOM gates / supply-chain publish | `sbom-ci-enforcement` | this for runtime composition |
| CI graph / Pod securityContext | `ci-cd-pipeline-patterns` / `kubernetes-pod-security` | this for runtime/UID |
| Dockerfile/app implementation quality | `code-quality-standards` | **always** on shipped config |

Keep **this skill primary** for base choice, copy-in layout, nonroot, and no-shell
ops; hand general Dockerfile teaching to `dockerfile-best-practices` for full distros.

## Output Checklist

- [ ] Repo approved bases, digests, neighbor Dockerfiles, securityContext read first
- [ ] Fitness: no runtime shell/package-manager need; config/logs externalized
- [ ] Correct variant + **nonroot**; multi-stage with no apt/apk/shell in final
- [ ] `ENTRYPOINT`/`CMD` JSON exec form with absolute paths
- [ ] Writable paths, TLS/custom CA, probes verified without in-image shell helpers
- [ ] Debug strategy documented; **debug tags not used as prod digests**
- [ ] Final digest scanned; size/CVE delta noted
- [ ] Routed: Dockerfile → `dockerfile-best-practices`; signing → `container-image-signing`; SBOM → `sbom-ci-enforcement`; CQS on changes

## Rules

- **No package manager and no shell in prod digests** — install only in build stages.
- Prefer **`:nonroot` + digest pins** over root or floating `latest`.
- **Exec-form** entrypoints only; shell-form `CMD` is incompatible with distroless.
- Debug images for **non-prod investigation** only; redact registry credentials; owned systems only.

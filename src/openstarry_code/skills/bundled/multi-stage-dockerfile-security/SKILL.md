---
name: multi-stage-dockerfile-security
description: >
  Harden multi-stage Dockerfiles so build toolchains, secrets, and VCS
  context never reach the runtime image. Use when multi-stage Dockerfile
  security, COPY --from leakage, builder secrets in final layers, distroless
  or scratch runtime stages, BuildKit secret mounts across stages, or
  reviewing stage boundaries for supply-chain and attack-surface reduction.
---

# Multi-Stage Dockerfile Security

Keep **build** and **runtime** trust boundaries strict: compilers, package
managers, tokens, and source trees stay in disposable stages; the final image
ships only the process, configs, and shared libs it needs. Defensive review and
authorized hardening of owned Dockerfiles only.

## When To Use

- Authoring or reviewing multi-stage `Dockerfile` / `Dockerfile.*` with `AS`
  stages and `COPY --from=`
- Secrets, `.npmrc`, SSH keys, or private module tokens used at **build** time
- Final image still contains SDK, git, shell, test fixtures, or full source
- Choosing distroless/scratch/chainguard runtime vs fat single-stage builds
- Mentions: multi-stage security, stage leakage, builder contamination,
  `--mount=type=secret`, non-root final stage, minimal runtime image

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General Dockerfile cache/size/non-root style (broader) | `dockerfile-best-practices` |
| Compose privileged, ports, docker.sock, runtime mounts | `docker-compose-security` |
| Cosign/Sigstore sign and admission by digest | `container-image-signing` |
| CI pipeline graph, OIDC job wiring, artifact upload | `ci-cd-pipeline-patterns` |
| Lab container breakout / host boundary research | `container-escape-techniques` |
| App code quality inside the image | `code-quality-standards` |

## Repo Config First

Repo and platform policy **outrank** defaults below.

1. Neighbor multi-stage Dockerfiles (stage names, base org, final `USER`)
2. Approved bases and digests (builder vs runtime catalogs, private mirrors)
3. Builder: BuildKit / buildx / Kaniko flags, secret mount IDs, SSH mounts
4. `.dockerignore` / `.containerignore` — extend existing, do not weaken
5. Orchestration: K8s `securityContext`, Compose `user:`, ECS user — align
   final `USER` with platform overrides
6. Registry policy: intermediate stages never tagged as prod; pin by digest
7. Scanners/gates (Trivy/Grype/Scout) and any CI `--target` usage
8. Language pin files (`go.mod`, lockfiles) that dictate builder tags

**Precedence:** Follow repo patterns. Surface conflicts that leave root runtime,
unpinned `latest`, secrets in final config/history, or full toolchains in ship
images.

## Workflow

### 1. Map stages and the ship target

List every `FROM … AS name` and the default final stage (last `FROM`). Note CI
`--target`; prod must build **runtime** only. Trace what each stage produces and
what later stages copy.

### 2. Enforce stage roles

| Stage role | Allowed | Forbidden on ship path |
| --- | --- | --- |
| deps / fetch | Manifests, lockfiles, package download | Long-lived secrets as final `ENV`/`ARG` |
| build / test | Compilers, linters, full source, tests | Publishing this stage as the prod tag |
| runtime | Artifacts, minimal runtime, ca-certs | SDK, git, package managers, `.git` |

Prefer named stages (`AS deps`, `AS build`, `AS runtime`) for safe
`--target runtime`.

### 3. Copy only what runtime needs

1. Explicit paths only: `COPY --from=build /out/app /app` — never whole `/src`
   or `COPY --from=build / /`.
2. Omit build caches, tests, `.git`, IDE files, and unused dependency trees.
3. `COPY --chown=` (or chown then `USER`) so the process is non-root.
4. Prefer static binaries or a known slim runtime base over copying builder
   rootfs fragments “to make it work.”

### 4. Secrets stay off the ship image

| Bad | Prefer |
| --- | --- |
| `ARG`/`ENV` token then “delete” in a later layer | `RUN --mount=type=secret,id=…` (BuildKit) |
| `COPY .npmrc`/keys into a stage that feeds final | Secret mount only in deps/build; never `COPY --from` those paths |
| Write creds under `/src` then copy `/src` forward | Copy only `/out` (or equivalent) artifacts |
| Assume delete-after-`ADD` erases secrets | Never introduce secret files into layers that feed final |

Secret/SSH mounts do not persist as layers when used correctly; `ARG`/`ENV` and
`COPY` do. Inspect **final** digest history and image config only.

### 5. Harden runtime and verify

1. Fresh minimal `FROM` for runtime — do not reuse the builder image as final.
2. Non-root `USER` (numeric UID helps `runAsNonRoot`); correct ownership on
   writable paths; no shell unless product-required.
3. Pin builder and runtime tags/digests; avoid prod `latest`.
4. `.dockerignore`: `.git`, `**/.env*`, host keys/`node_modules`, unused docs.
5. Order: lockfiles → install → source → build → copy artifact to runtime.
6. BuildKit build; confirm no toolchain in final; scan digest; smoke-test
   entrypoint. Apply `code-quality-standards` to entrypoint scripts. Runtime
   Compose/K8s undoing non-root → `docker-compose-security`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Multi-stage boundaries, COPY --from leakage, build secrets vs final image | **This skill** | — |
| Broader Dockerfile style, cache, .dockerignore, HEALTHCHECK | `dockerfile-best-practices` | this for stage security depth |
| Compose ports, privileged, sock mounts | `docker-compose-security` | this for image stages |
| Image sign/verify/admission | `container-image-signing` | this pre-sign contents |
| CI stages, OIDC, buildx wiring | `ci-cd-pipeline-patterns` | this for Dockerfile stages |
| Secret rotation / leak IR beyond Dockerfile | `secrets-management-hygiene` | this for layer/stage paths |
| Lab breakout research | `container-escape-techniques` | this for image misconfig only |
| Scripts/app code quality in image | `code-quality-standards` | **always** when editing code |

- **`dockerfile-best-practices`:** general image authoring; this skill owns
  **stage trust boundaries** and cross-stage secret/artifact leakage.
- **`docker-compose-security`:** stack settings can reintroduce root, mounts,
  and sockets after a clean multi-stage image.
- **`container-image-signing`:** signs digests; does not fix fat or secret-laden
  stages.

## Output Checklist

- [ ] Repo Dockerfiles, bases, builder, ignore files, and USER policy read first
- [ ] Stages named; prod `--target` is runtime-only; builder not published as prod
- [ ] Runtime `FROM` is minimal and separate from builder base
- [ ] `COPY --from` uses explicit artifact paths only (no whole source trees)
- [ ] No secrets via final `ENV`/`ARG`; no secret files in final layers
- [ ] Build credentials use BuildKit secret/SSH mounts (or org equivalent)
- [ ] Final stage non-root; writable paths owned; no unnecessary shell/SDK/git
- [ ] Bases pinned per policy; `.dockerignore` excludes VCS/env/keys
- [ ] Final digest scanned and smoke-tested; config/history free of tokens
- [ ] Hand-offs: Compose → `docker-compose-security`; sign →
  `container-image-signing`; CI → `ci-cd-pipeline-patterns`; CQS on code
- [ ] Residuals documented (required shell, root exception) with owner/expiry

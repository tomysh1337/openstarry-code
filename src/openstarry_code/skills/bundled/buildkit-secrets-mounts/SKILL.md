---
name: buildkit-secrets-mounts
description: >
  BuildKit secret and SSH mounts so build-time credentials never land in image
  layers, history, or ARG/ENV. Use when docker buildx --secret, RUN --mount=type=secret,
  type=ssh private git/npm/registry auth, Dockerfile secret mounts, or replacing
  ARG TOKEN / COPY .npmrc build patterns on owned images and CI.
---

# BuildKit Secrets Mounts

Inject **build-time** credentials with BuildKit **secret** and **SSH** mounts so
tokens never appear in image config, layers, or `docker history`. Prefer repo
builder flags and secret IDs. Hand org lifecycle/scanning/IR to
`secrets-management-hygiene`.

## When To Use

- `RUN --mount=type=secret` / `type=ssh` for private modules, registries, or git
- `docker build` / `buildx build --secret id=…,src=…|env=…` in CI or local
- Replacing `ARG TOKEN`, `ENV` credentials, or `COPY` of `.npmrc`/keys into layers
- Proving a final image has **no** build secret in config or history
- Keywords: BuildKit secrets, secret mount, buildx --secret, Dockerfile SSH mount,
  private go/npm/pip registry at build, `# syntax=docker/dockerfile:1`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Multi-stage, non-root, layer cache, `.dockerignore` | `dockerfile-best-practices` |
| Org inventory, scanners, rotation, leak IR | `secrets-management-hygiene` |
| CI job graph, OIDC, fork isolation broadly | `ci-cd-pipeline-patterns` |
| Compose runtime secrets / privileged mounts | `docker-compose-security` |
| Runtime vault/KMS injection (not image build) | `secrets-management-hygiene` |
| Implementation/tests baseline | `code-quality-standards` |

## Repo Config First

Repo Dockerfiles, builder, and CI secret names **outrank** samples below.

1. **Syntax:** `# syntax=docker/dockerfile:1` (or pin) — required for mounts
2. **Secret IDs:** existing names (`npmrc`, `git_auth`, `netrc`) — **extend**
3. **Builder:** `DOCKER_BUILDKIT=1`, `docker buildx`, bake files, remote builders
4. **CI store:** platform secret → `--secret id=…,env=…` or temp `src=` (`0600`)
5. **SSH / ignore:** agent vs key; `.dockerignore` excludes `.env`, keys, token `.npmrc`
6. **Neighbors/scanners:** Kaniko/Buildpacks only if mounts work; org image gates

**Precedence:** Follow the repo. Surface `ARG`/`ENV` tokens, secret files `COPY`’d
into shipping stages, and “delete secret in next layer” patterns.

## Workflow

### 1. Inventory and prefer mounts

List build-time secrets and stages. They must **not** reach the final image.

| Bad | Prefer |
| --- | --- |
| `ARG NPM_TOKEN` + write `.npmrc` | `RUN --mount=type=secret,id=npmrc,target=…` |
| `ENV` long-lived cloud keys | Secret mount or runtime role (not image) |
| `COPY .npmrc` / `id_rsa` into layers | Mount at `RUN`; keep out of build context |
| `RUN … && rm secret` after bake-in | Earlier layers still hold the secret |

Enable BuildKit and mount-capable Dockerfile syntax.

### 2. Author mounts

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc,mode=0400 \
    npm ci --omit=dev
```

```dockerfile
RUN --mount=type=ssh \
    git clone git@github.com:org/private-mod.git /src/mod
```

Fail-closed for required private deps. Set `uid`/`gid`/`mode` for non-root builders.

### 3. Pass secrets at build

```bash
docker buildx build --secret id=npmrc,src=$HOME/.npmrc -t app:local .
docker buildx build --secret id=npm_token,env=NPM_TOKEN -t app:ci .
docker buildx build --ssh default -t app:ssh .
```

Match Dockerfile `id`. Prefer file/env mounts over echoing tokens into a layer.

### 4. Stages, cache, CI, verify

- Secrets only in **build/deps** stages; final stage copies **artifacts only**
- Never `COPY --from=build` secret paths; `type=cache` is **not** a secret store
- Avoid `set -x` / high debug that prints credentials in `RUN`
- CI: platform secrets or OIDC→SM → `--secret`; deny fork PRs private-registry
  secrets; mask logs. Broader pipeline trust → `ci-cd-pipeline-patterns`
- Verify: success with secret; fail-closed without; history/config/FS clean;
  scanners clean; edits use `code-quality-standards`

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| BuildKit `--secret` / `type=secret` / `type=ssh` | **This skill** | — |
| Multi-stage, non-root, layer order, ignore files | `dockerfile-best-practices` | this for credential mounts |
| Org inventory, leak IR, rotation | `secrets-management-hygiene` | this for build-time injection |
| CI OIDC, env protection, fork isolation | `ci-cd-pipeline-patterns` | this for `--secret` flags |
| Compose/runtime secret files | `docker-compose-security` | this if image build embeds secrets |
| Dockerfile/CI script quality and tests | `code-quality-standards` | **always** on changes |

- **`dockerfile-best-practices`:** packaging/layout; this skill owns mounts and layer-absence proofs.
- **`secrets-management-hygiene`:** lifecycle/scanners/IR; this skill is the BuildKit mechanism.
- **`ci-cd-pipeline-patterns`:** who may see secrets; this skill is the CLI/Dockerfile contract.
- **`code-quality-standards`:** always when editing Dockerfiles, bake files, or build scripts.

## Output Checklist

- [ ] Build-time secrets inventoried (names/owners only; no plaintext in notes)
- [ ] Repo syntax directive, secret IDs, buildx/CI patterns followed
- [ ] No `ARG`/`ENV`/committed files hold long-lived build credentials
- [ ] `RUN --mount=type=secret` (and `type=ssh` if needed) at point of use
- [ ] Build CLI passes matching `--secret` / `--ssh`; CI uses platform secrets
- [ ] Secrets limited to build stages; final image is artifacts-only
- [ ] Cache mounts not used as secret store; debug does not dump tokens
- [ ] Fork/untrusted PR cannot consume private registry secrets
- [ ] Verified: history/config/FS free of secrets; fail-closed without secret
- [ ] Routed: layout → `dockerfile-best-practices`; lifecycle → `secrets-management-hygiene`; CI → `ci-cd-pipeline-patterns`
- [ ] `code-quality-standards` applied on Dockerfile and build-script changes

## Rules

- **Never** bake credentials into layers, image config, or git — mounts only at `RUN`.
- Deleting a secret in a later layer does **not** remove it from history.
- Document secret **IDs**/CI names beside the Dockerfile. Runtime secrets use vault/orchestrator, not build mounts.
- Owned images and authorized CI only; redact tokens from logs, tickets, and examples.

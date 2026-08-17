---
name: ci-cd-pipeline-patterns
description: >
  Design and review CI/CD pipelines for clear stages, secret hygiene, dependency
  and build caching, fail-fast feedback, and durable artifacts. Use when CI/CD,
  GitHub Actions, GitLab CI, pipeline, 持续集成, workflow YAML, deploy gates,
  OIDC to cloud, cache, artifacts, or matrix builds for product repos.
---

# CI/CD Pipeline Patterns

Produce pipelines that fail early on real defects, keep secrets out of logs and
fork PRs, reuse caches safely, and publish auditable artifacts. Prefer the
repository’s existing CI platform and org reusable workflows over a greenfield
stack.

## Use When

- Authoring or reviewing `.github/workflows/*`, `.gitlab-ci.yml`, Azure Pipelines,
  CircleCI, Buildkite, Jenkins declarative pipelines, or similar
- Structuring stages: lint → typecheck → unit → build → integration → scan → deploy
- Wiring secrets, OIDC cloud auth, environments/approvals, and protected branches
- Speeding pipelines with dependency/build caches without poisoning trust
- Publishing artifacts, images, SBOMs, coverage, or deploy bundles
- User mentions: CI/CD, GitHub Actions, pipeline, 持续集成, 流水线, workflow,
  fail-fast, cache, artifacts, deploy gate

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Dockerfile multi-stage / non-root / image layer secrets | `dockerfile-best-practices` |
| Application code standards inside jobs | `code-quality-standards` |
| Commit message / changelog release prose | `commit-message-conventions` / `changelog-and-release-notes` |
| Shell style of scripts invoked by CI | `shell-script-style` |
| Container escape research | `container-escape-techniques` |

## Repo Config First

Repo and org CI config **outrank** this skill’s defaults.

1. **Platform files:** `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`,
   `Jenkinsfile`, `bitbucket-pipelines.yml`, Buildkite `pipeline.yml`
2. **Org reuse:** required reusable workflows, composite actions, shared
   pipeline templates, org secret scanning / billing runners
3. **Branch protection & environments:** required checks, review gates,
   environment protection (prod approvals), deployment branches
4. **Package & runtime pins:** `.nvmrc`, `go.mod`, `Package.swift`, asdf/mise,
   language version matrices already in use
5. **Cache keys & registries:** existing cache key schemes, npm/pypi/maven
   proxies, container registry names, artifact retention policy
6. **Secret sources:** GitHub Environments / org secrets, OIDC (`cloud` roles),
   Vault, sealed secrets — never introduce long-lived AK/SK if OIDC exists
7. **Path filters & monorepo tools:** `paths:`, `dorny/paths-filter`, Nx/Turborepo
   affected, Bazel — match the monorepo’s change detection
8. **Compliance gates:** mandatory CodeQL/Semgrep/Trivy, license checks,
   signed commits, provenance (`attestations`)

**Precedence:** Follow repo/org policy when it conflicts with examples below.
Surface conflicts that skip tests on main, expose secrets to fork PRs, or
deploy without a gate.

## Workflow

1. **Map the change types.** PR validation vs main merge vs tag release vs
   scheduled nightlies vs manual `workflow_dispatch`. Different trust levels.
2. **Define stages and fail-fast order.** Cheap static checks first; expensive
   integration/e2e after build artifacts exist; deploy only from trusted refs
   with explicit environment protection.
3. **Isolate privileges.** Build jobs: read-only contents + package write as
   needed. Deploy jobs: separate environment secrets, least privilege OIDC,
   no shared “god” token across jobs that run untrusted PR code.
4. **Wire secrets correctly.** Repository/environment secrets; mask outputs;
   never `echo` secrets; prefer OIDC short-lived creds; block secret access on
   `pull_request` from forks (use `pull_request_target` only with extreme care).
5. **Add caching with correct keys.** Key on lockfile hash + OS + runtime
   version; restore-keys for partial hits; never cache untrusted PR build
   outputs into a shared key used by protected branches without isolation.
6. **Produce artifacts.** Upload test reports, coverage, binaries, SBOMs, and
   images with retention and digests; promote the same artifact across envs
   (build once, deploy many).
7. **Gate deploy.** Environment approvals, smoke tests, optional canary;
   pin image digests; record provenance.
8. **Verify the pipeline itself.** Run on a draft PR; confirm fail-fast;
   confirm fork PR cannot read secrets; confirm cache hit ratios; confirm
   required status checks match actual job names.

## Core Practices

### Stages (typical product repo)

| Stage | Purpose | Fail-fast notes |
| --- | --- | --- |
| Checkout + setup | Pin tool versions | Use official setup actions; hash-pin third-party actions when policy requires |
| Lint / format | Style gate | Parallel with typecheck when independent |
| Unit tests | Fast correctness | Matrix OS/runtime only when value > cost |
| Build | Compile / bundle / image | Reuse for later jobs via artifacts |
| Integration / e2e | Real deps or testcontainers | After unit green; optional path filters |
| Security scan | SCA, image, SAST | Non-optional on main/release; severity policy explicit |
| Publish | Packages / images | Only trusted refs; sign/attest if required |
| Deploy | Env promote | Manual or auto with protection rules |

### Secrets

- Prefer **OIDC** to AWS/GCP/Azure over static cloud keys
- Scope secrets to **environments** (staging vs prod), not one global secret
- Set job `permissions:` to least privilege (GitHub Actions default is often too wide historically — set explicit `contents: read` etc.)
- Never pass secrets into untrusted PR code execution contexts
- Redact: tools may print URLs with tokens; configure mask / avoid verbose curl

### Caching

- **Safe:** package manager dirs keyed by lockfile (`~/.npm`, Go module cache, pip)
- **Risky:** caching entire `node_modules` across major Node upgrades without key churn; caching Docker layers without BuildKit/registry cache policy
- **Unsafe:** writing cache from fork PRs into keys restored on `main` without namespace isolation
- Invalidate deliberately when tooling major-bumps

### Fail-fast

- Run independent jobs in parallel; use a single required “gate” job that
  depends on all checks if branch protection allows only one name
- `fail-fast: true` on matrices when one cell failure should stop the rest
  (disable only for diagnostic matrices)
- Do not `continue-on-error: true` on security or unit jobs without an explicit
  follow-up required job

### Artifacts

- Build once on `main`/tag; promote artifact or image digest through envs
- Name artifacts with job + sha; set retention
- Keep PR artifacts short-lived; do not publish release packages from PR builds

## Good / Bad Examples

### GitHub Actions — PR CI with fail-fast stages

**Good**

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: npm
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: npm
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-${{ github.sha }}
          path: coverage/
          retention-days: 7

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".nvmrc"
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist-${{ github.sha }}
          path: dist/
```

**Bad**

```yaml
name: ci
on: [push]
jobs:
  all:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install   # no lockfile integrity; no cache
      - run: npm run lint || true
      - run: npm test || true   # never fails the pipeline
      - run: echo "TOKEN=${{ secrets.PROD_DEPLOY_KEY }}" >> $GITHUB_ENV
      - run: ./deploy.sh prod  # deploy on every branch push with prod secret
```

### Secrets and OIDC (AWS example sketch)

**Good**

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-prod-deploy
          aws-region: us-east-1
      - run: ./scripts/deploy.sh
```

**Bad**

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: |
          export AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }}
          export AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}
          # long-lived keys; available to any job that can read secrets;
          # easy to leak into logs via set -x or debug
```

### Caching — lockfile-keyed

**Good**

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: go-build-${{ runner.os }}-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      go-build-${{ runner.os }}-
```

**Bad**

```yaml
- uses: actions/cache@v4
  with:
    path: .
    key: workspace-${{ github.ref }}   # caches source/secrets risk; unstable; huge
```

### Docker image build in CI (pairs with dockerfile skill)

**Good**

```yaml
- uses: docker/setup-buildx-action@v3
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
- uses: docker/build-push-action@v6
  with:
    context: .
    push: ${{ github.ref == 'refs/heads/main' }}
    tags: ghcr.io/org/app:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
    secrets: |
      npmrc=${{ secrets.NPM_RC }}
```

**Bad**

```yaml
- run: |
    echo "${{ secrets.NPM_TOKEN }}" > .npmrc
    docker build -t app:latest .
    docker push app:latest
    # token file may end up in build context; :latest only; no digest pin;
    # secrets may appear in logs if buildkit print is verbose
```

### GitLab CI — stages sketch

**Good**

```yaml
stages: [lint, test, build, deploy]

default:
  image: node:22-bookworm

lint:
  stage: lint
  script: [npm ci, npm run lint]
  cache:
    key:
      files: [package-lock.json]
    paths: [node_modules/]
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

test:
  stage: test
  script: [npm ci, npm test]
  artifacts:
    when: always
    reports:
      junit: junit.xml
    paths: [coverage/]
    expire_in: 7 days

deploy_prod:
  stage: deploy
  script: [./scripts/deploy.sh]
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_TAG
  when: manual
```

**Bad**

```yaml
build:
  script:
    - npm install
    - npm test
    - ./deploy.sh
  # one job, no stages, deploys on every pipeline including MRs
  only: [branches]
```

### Matrix fail-fast

**Good**

```yaml
strategy:
  fail-fast: true
  matrix:
    node: [20, 22]
```

**Bad**

```yaml
strategy:
  fail-fast: false
  matrix:
    node: [16, 18, 20, 22]
# long green-wait when every cell is required and one early failure is enough
# (acceptable only when you intentionally gather full matrix diagnostics)
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CI/CD stages, secrets, caching, fail-fast, artifacts, GHA/GitLab pipelines | **This skill** | — |
| Dockerfile multi-stage, non-root, image layer cache, secrets not in image | `dockerfile-best-practices` | this skill for build-push job wiring |
| Production code quality in jobs under test | `code-quality-standards` | this skill for when/how checks run |
| Image/runtime misconfig that weakens isolation (awareness) | `dockerfile-best-practices` | `container-escape-techniques` only for authorized host-boundary research |
| Release notes / version tags prose | `changelog-and-release-notes` | this skill for publish job |
| Commit message gates | `commit-message-conventions` | optional CI commitlint job |

## Checklist

- [ ] Platform and org reusable workflows / required checks identified
- [ ] PR vs main vs tag vs schedule flows separated with correct trust levels
- [ ] Stages ordered fail-fast: lint/type → unit → build → heavy tests → scan → deploy
- [ ] Job `permissions` least privilege; deploy isolated from untrusted PR code
- [ ] Secrets from environment/OIDC; not echoed; not available to fork PRs
- [ ] Caches keyed by lockfile + OS + tool version; no untrusted cache poison path
- [ ] Artifacts uploaded with retention; **build once, promote digest** for deploy
- [ ] Image builds use `dockerfile-best-practices` (secret mounts, non-root, pins)
- [ ] Deploy gated (environment protection / manual / tag); no prod on every push
- [ ] Required status check names match actual jobs; matrix policy intentional
- [ ] Third-party actions pinned (tag or SHA per org policy); no silent `continue-on-error` on critical gates
- [ ] Logs free of tokens; scanners/SAST policy applied on protected branches

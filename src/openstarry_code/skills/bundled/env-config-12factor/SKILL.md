---
name: env-config-12factor
description: >
  Twelve-factor style application config: store config in the environment,
  strict separation of code from config, typed/validated env loading, and no
  secrets baked into images or git. Use when env config, 12-factor, 环境变量配置,
  twelve-factor config, dotenv, config via environment, stage/prod config split,
  missing env fail-fast, or reviewing how services read DATABASE_URL and flags.
---

# Env Config (12-Factor)

Treat **config as environment-injected data**, not as code branches or files
that differ by packing the same binary differently per host. Prefer the
repository’s existing config loaders, env naming, and secret stores over a
second scheme. This skill is **ops and application configuration design** for
systems you own.

## Use When

- Designing or reviewing **how a service loads config** (env vars, platform
  config maps, feature flags that are config not code)
- Applying **12-factor config** (III. Config): strict split of code / config /
  credentials across local, stage, and prod
- Adding or hardening **env validation**, required vs optional keys, defaults,
  and fail-fast startup
- Preventing **secrets and env-specific values in images, git, or compile-time
  constants**
- Migrating from checked-in `config.prod.json` / hard-coded hosts to env or
  platform injection
- User mentions: env config, 12-factor, twelve-factor, 环境变量配置, dotenv,
  `.env`, `DATABASE_URL`, config map, 12 要素, environment-based config

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Secret lifecycle, vault, rotation, leak response | `secrets-management-hygiene` |
| Dockerfile layers, multi-stage, secrets not in image build | `dockerfile-best-practices` |
| Metrics/traces/RED for runtime health | `observability-metrics-tracing` |
| Log field/redaction style | `logging-message-style` |
| General reliability/security/tests in app code | `code-quality-standards` |
| Feature rollout cohorts and kill switches | `feature-flag-patterns` |
| CI secret scopes / OIDC wiring | `ci-cd-pipeline-patterns` |

## Repo Config First

Repo and platform config conventions **outrank** this skill’s defaults.

1. **Existing loader:** `pydantic-settings`, `envalid`, `envconfig`, Spring
   `Environment`, .NET `IConfiguration`, `viper`, custom `config` packages —
   extend them; do not invent a parallel parser
2. **Env naming:** `SERVICE_FOO_BAR` vs nested `__` separators; documented
   prefixes in README or internal runbooks — **match existing names**
3. **Sample files:** `.env.example`, `config.sample.yaml`, Helm `values.yaml`
   comments — placeholders only; keep in sync when keys change
4. **Platform injection:** Kubernetes ConfigMap/Secret, ECS task env, systemd
   `EnvironmentFile`, Cloud Run / App Service settings, Doppler/Vault agent —
   prefer the org standard path
5. **Secret vs non-secret split:** which keys come from Secret Manager vs plain
   ConfigMap — do not put credentials in plain config maps if the repo already
   separates them
6. **Build-time vs runtime:** public `NEXT_PUBLIC_*` / compile-time flags already
   used by frontends — document which keys are **baked** (non-secret only) vs
   **runtime**
7. **Ignore rules:** `.gitignore` / `.dockerignore` for `.env`, `.env.*`, local
   overrides — extend, do not weaken
8. **Validation gates:** startup checks, CI “config schema” tests, or admission
   policies already in tree

**Precedence:** If repo rules conflict with examples below, follow the repo.
Surface conflicts that bake secrets into images, commit real `.env` files, or
silent-default production credentials.

## Twelve-Factor Config (operational reading)

| Factor idea | Practice here |
| --- | --- |
| Config in the **environment** | Resource locators, credentials, and deploy-specific toggles via env (or platform equivalent that surfaces as env) |
| **Strict separation** | Same artifact (image/binary) for every deploy; only env/config injection changes |
| **No config in code** | No `if prod hostname == …` with hard-coded URLs; no prod passwords in source |
| **Granular env** | Prefer many clear keys over one opaque mega-JSON blob (unless the platform already standardizes a single sealed file) |
| **Backing services as attached resources** | DB, cache, queue URLs are config — swap by changing env, not rebuilding |

Related 12-factor habits this skill **touches but does not own:**

- **Logs as event streams** → `logging-message-style` + `observability-metrics-tracing`
- **Admin processes** (migrate, one-shot jobs) share the same config contract
- **Disposability / port binding** — document `PORT` and graceful shutdown; deep
  reliability stays with `code-quality-standards` / domain skills

## What Goes In Env vs What Does Not

| Put in env / platform config | Keep out of env (or never as secret env in git) |
| --- | --- |
| DB/cache/queue URLs and pool sizes | Source code and dependency versions |
| Listen `PORT`, public base URL, CORS origins | Large static assets and templates |
| Log level, sample rate, feature defaults that vary by env | Long prose docs (use files in image, not env) |
| Timeout/retry budgets when they differ by env | Secrets **values** in git, Dockerfile `ENV`, or world-readable ConfigMaps |
| Identity of backing services (hosts, topic names) | Per-request user data |

**Rule of thumb:** if it changes between deploys of the **same** release artifact,
it is config. If changing it requires a new build of business logic, it is code.

## Workflow

### 1. Inventory config surfaces

1. List every deploy-specific value the process needs: URLs, credentials, limits,
   feature defaults, third-party endpoints.
2. Mark each: **secret** / **sensitive** / **public**, and **required** /
   **optional** per environment.
3. Map current sources: hard-coded, `.env`, ConfigMap, Secret, build arg, flag
   service.
4. Note drift: keys present in stage but undocumented; keys in code with silent
   prod defaults.

Output: config inventory (names + purpose + owner) — **no live secret values**.

### 2. Align with repo and platform

1. Read existing settings module and neighboring services’ env lists.
2. Confirm injection path (K8s, Compose, PaaS) and secret store
   (`secrets-management-hygiene`).
3. Confirm image build does not copy `.env` or set secret `ENV`
   (`dockerfile-best-practices`).
4. Reuse naming and validation libraries already in the monorepo.

### 3. Define the config contract

1. **Names:** stable, uppercase env style (or repo standard); prefix by service
   when multiple apps share a namespace.
2. **Types:** parse ints/bools/durations/URLs explicitly; reject `"true "` and
   ambiguous truthiness where the stack allows.
3. **Required vs optional:** required keys **fail startup** in prod/stage; local
   may use documented defaults only for non-secrets.
4. **Defaults:** safe local-only defaults (e.g. `localhost`); **never** default
   to a real shared prod credential or production URL in library code.
5. **Secrets:** reference by env **name** only in code; values from platform /
   vault at runtime (`secrets-management-hygiene`).
6. Publish/update **`.env.example`** (or equivalent) with placeholders and
   one-line purpose comments.

### 4. Implement load and validation

Apply `code-quality-standards` for implementation hygiene:

1. Load once at process start (or documented hot-reload path); fail closed on
   missing/invalid required config.
2. Validate formats (URL schemes, port ranges, enum allow-lists) before
   accepting traffic.
3. Separate **secret-bearing** fields in memory types if that helps redaction;
   never print full config dumps at INFO.
4. Prefer typed settings objects over scattered `os.Getenv` across the codebase.
5. For multi-service monorepos, keep per-service env lists explicit.

### 5. Wire deploy paths (no secrets in the image)

1. **Image:** same image tag promoted stage → prod; only env/secret mounts change
   (`dockerfile-best-practices`).
2. **Orchestrator:** ConfigMap for non-secrets; Secret/SM/CSI for credentials.
3. **Local:** gitignored `.env` from `.env.example`; never prod keys on laptops
   without policy exception.
4. **CI:** inject test env in the job; do not commit CI-only secrets; avoid
   baking test secrets into images.

### 6. Observe and operate

1. On boot, log **which config keys were loaded** (names only) and non-secret
   effective values needed for support (e.g. `log_level=info`, `http_port=8080`)
   using `logging-message-style`.
2. **Never** log secret values, full connection strings with passwords, or
   private keys.
3. Expose readiness that fails when required backing config is missing; pair
   golden signals with `observability-metrics-tracing`.
4. Document how on-call changes a value (platform UI/CLI) and whether a restart
   is required.

### 7. Verify

1. Boot with missing required var → non-zero exit and clear error (no stack of
   unrelated NPEs only).
2. Boot with invalid type/enum → clear validation error naming the key.
3. Image inspect / history: no secret env; `.env` not in layers.
4. Stage deploy uses non-prod credentials; prod keys only in prod scope.
5. `.env.example` matches code’s required set (CI check if available).

## Config Design Practices

### Naming

| Guidance | Example |
| --- | --- |
| Prefix when shared cluster env | `BILLING_DB_URL` not bare `URL` |
| Boolean clarity | `ENABLE_WIDGETS=true` not `WIDGETS=1` unless repo standard is numeric |
| Durations with units in name or typed parse | `SHUTDOWN_TIMEOUT_SEC=30` or `30s` with a parser |
| Avoid overlapping synonyms | One of `DATABASE_URL` / `DB_DSN`, not both live |

### Layering (recommended mental model)

```text
defaults (safe, non-secret, code or sample)
  → file/env for local dev (.env gitignored)
    → platform ConfigMap / process env
      → platform secrets / vault (highest precedence for secret keys)
```

Do not implement six override layers if the repo already has one clear chain.

### Build-time config (frontends and compiled-in public values)

- Only **non-secret**, **public** values may be inlined at build (CDN base URL,
  public analytics key explicitly classified public).
- Document rebuild requirement when build-time keys change.
- API secrets, private client secrets, and DB URLs stay **runtime** server-side.

### Feature flags vs env config

- **Env:** deploy-time or rarely changed operational settings.
- **Flag service:** per-user/cohort rollout and instant kill switch —
  `feature-flag-patterns`.
- Do not invent a second flag system in ad-hoc env vars if a flag platform exists.

## Good / Bad Examples

### Typed startup load (sketch)

**Good**

```python
# settings.py — illustrative; match repo library
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn
    port: int = Field(default=8080, ge=1, le=65535)
    log_level: str = Field(default="info")
    payments_api_key: str  # required; from env/secret inject — no default

    def non_secret_summary(self) -> dict:
        return {
            "port": self.port,
            "log_level": self.log_level,
            "database_host": self.database_url.host,  # not password
        }

settings = Settings()  # raises on missing/invalid
```

**Bad**

```python
import os
DB = os.getenv("DATABASE_URL", "postgresql://root:prodpw@prod-db/app")
# silent prod default; password in source; no validation
```

### Sample env for developers

**Good** — `.env.example` (committed)

```bash
# Copy to .env (gitignored). Never put production secrets here.
DATABASE_URL=postgresql://app:changeme@localhost:5432/app
PORT=8080
LOG_LEVEL=debug
PAYMENTS_API_KEY=replace-me
```

**Bad** — committed `.env` with live credentials

```bash
DATABASE_URL=postgresql://app:SuperSecret@db.prod.internal/app
PAYMENTS_API_KEY=sk_live_51H…
```

### Same artifact, different deploy config

**Good**

```text
image: registry.example/billing:1.4.2   # identical digest in stage and prod
stage env: DATABASE_URL=…stage…  LOG_LEVEL=debug
prod  env: DATABASE_URL=…prod…   LOG_LEVEL=info
secrets: from SM / K8s Secret / vault agent — not in image
```

**Bad**

```text
Dockerfile.prod: ENV DATABASE_URL=postgresql://…prod…
Dockerfile.stage: ENV DATABASE_URL=postgresql://…stage…
# or distinct images rebuilt only to change hostnames
```

### Fail-fast vs late crash

**Good**

```text
startup: validate required env → log non-secret summary → listen
missing PAYMENTS_API_KEY → exit 1 "missing required config: PAYMENTS_API_KEY"
```

**Bad**

```text
listen immediately; first payment request crashes with TypeError: NoneType
# or worse: falls back to a hard-coded “demo” key that still hits a shared API
```

### Logging config at boot

**Good** (structured, redacted — `logging-message-style`)

```text
event=config_loaded port=8080 log_level=info db_host=db.internal payments_key=***
```

**Bad**

```text
print(os.environ)  # dumps secrets into aggregated logs
```

### Kubernetes-style split (illustrative)

**Good**

```yaml
# non-secret
envFrom:
  - configMapRef: { name: billing-config }
env:
  - name: PAYMENTS_API_KEY
    valueFrom:
      secretKeyRef: { name: billing-secrets, key: payments_api_key }
```

**Bad**

```yaml
env:
  - name: PAYMENTS_API_KEY
    value: "sk_live_…"   # plaintext in manifest committed to git
```

## Anti-Patterns

- Committing real `.env`, `application-prod.yml` with passwords, or kube secrets
  as plain YAML
- `ENV SECRET=…` or `ARG`/`ENV` credential patterns in Dockerfiles
- Different **code** branches per environment instead of config (`if env == prod`
  with hard-coded hosts)
- Optional secrets that “work” with empty string and fail only for customers
- Mega-JSON in one env var with no schema or version field
- Logging full settings structs including secret fields
- Using prod backing services from local `.env` “for convenience”
- Documenting secrets in README or tickets in plaintext
- Silent coercion (`PORT=""` → `0`) that binds incorrectly
- Duplicating the same key under five names without a deprecation plan

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Env/config contract, 12-factor config, 环境变量配置, dotenv layout | **This skill** | — |
| Vault/SM, rotation, leak response, what counts as secret | `secrets-management-hygiene` | this skill for env naming/injection shape |
| Image build, multi-stage, no secrets in layers, `.dockerignore` | `dockerfile-best-practices` | this skill for runtime env contract |
| Boot metrics, readiness, RED/USE, correlation of config errors | `observability-metrics-tracing` | this skill for which keys are required |
| Config load implementation, validation, tests, error handling | `code-quality-standards` | **always** on code changes |
| Boot/log field style, redaction of secret config | `logging-message-style` | this skill for what must never be logged |
| Progressive delivery / runtime flags | `feature-flag-patterns` | this skill for deploy-time env |
| CI injecting env/secrets into jobs | `ci-cd-pipeline-patterns` | `secrets-management-hygiene` |

### Routing notes (required helpers)

- **`secrets-management-hygiene`:** primary for secret storage, rotation, and
  leakage; this skill ensures secrets are **referenced** via env/platform and
  never baked into code or images.
- **`dockerfile-best-practices`:** primary when the failure mode is “secret or
  env file ended up in the image”; keep runtime config out of layers.
- **`observability-metrics-tracing`:** wire readiness/SLIs so bad or missing
  config surfaces as operator signals, not only process crash loops.
- **`code-quality-standards`:** always apply when implementing or reviewing the
  loader, validation, and fail-fast paths.
- **`logging-message-style`:** boot and error logs must name keys and redact
  values; never dump `environ`.

## Checklist

- [ ] Repo loader, env naming, sample files, and platform injection path inventoried
- [ ] Config inventory: each key has purpose, secret?/required?, owner (no live values)
- [ ] Same release artifact for stage/prod; only env/secrets differ
- [ ] No secrets in git, image `ENV`/`ARG`, or plain committed manifests
- [ ] `.env.example` (or equivalent) placeholders match required keys; real `.env` ignored
- [ ] Typed parse + validation; required keys fail startup with clear key names
- [ ] No silent prod credentials or production URLs as code defaults
- [ ] Secret keys injected via platform/vault (`secrets-management-hygiene`)
- [ ] Dockerfile/context cannot COPY `.env` / keys (`dockerfile-best-practices`)
- [ ] Boot logs non-secret summary only (`logging-message-style`)
- [ ] Readiness/metrics consider config/backing dependencies (`observability-metrics-tracing`)
- [ ] Local/stage/prod secret separation enforced; no prod keys on laptops by default
- [ ] Build-time inlined values are non-secret and documented
- [ ] `code-quality-standards` applied on config module changes
- [ ] Admin/migrate jobs use the same config contract as the service

## Rules

- **Repo config first** — match existing loaders and names; fill gaps only.
- **Code / config / secrets** are three different things; do not merge them in
  git or in the image.
- Prefer **fail-fast at startup** over partial boot with latent misconfig.
- Env **names** are public API of the service contract; rename with deprecation.
- Never log or commit secret **values**; rotate first if they leak
  (`secrets-management-hygiene`).
- Methodology for **owned systems and authorized hardening** only.
---

# Note

This skill owns **twelve-factor-style env/config contracts** and safe loading.
Pair with `secrets-management-hygiene` for credential lifecycle,
`dockerfile-best-practices` for image boundaries,
`observability-metrics-tracing` for operational signals,
`logging-message-style` for redacted boot/error logs, and
`code-quality-standards` whenever config code is written or reviewed.

---
name: secrets-management-hygiene
description: >
  Secrets management hygiene for org-owned code and platforms: keep secrets out
  of source, use vault/platform secret stores, least-privilege injection, rotation
  and revocation, and safe logging. Use when secrets management, 密钥管理, .env
  secrets, API keys in repo, vault patterns, secret rotation, credential leak
  remediation, or CI/runtime secret injection design.
---

# Secrets Management Hygiene

Establish and review **how secrets are created, stored, injected, rotated, and
revoked** in systems you own or are authorized to harden. This skill is
**defensive process and design methodology** — not guidance for stealing or
abusing third-party credentials.

## Scope And Authorization

- **In scope:** Org repositories, CI, cloud accounts, vaults, and runtime
  environments under your team’s ownership or written engagement scope.
- **Out of scope:** Using discovered secrets against systems you do not own;
  credential stuffing; buying/selling dumps; bypassing another tenant’s vault.
- On suspected **live production secret exposure:** follow org IR — contain,
  rotate, revoke, audit access — before broad documentation of the raw secret.
- Prefer **synthetic canaries** and non-production keys in examples, tests, and demos.
- Redact secrets from tickets, screenshots, threat models, and chat. Never paste
  live keys into prompts or skill examples.

## Use When

- Secrets appear (or might appear) in **source, images, tickets, or logs**
- Designing **vault / KMS / platform secret** patterns for apps and CI
- Setting or reviewing **rotation**, dual-control, and emergency revocation
- Chinese/English teams: **密钥管理**, 密钥轮换, 凭据泄漏, `.env` / secrets.yml
- Hardening local dev (`.env`), staging, and production secret paths
- Post-incident: leaked key in git history, CI log, or package artifact

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| STRIDE workshop / design threat register | `threat-modeling-stride` |
| General code reliability/security/tests baseline | `code-quality-standards` |
| Log structure and redaction style only | `logging-message-style` |
| Dependency provenance / SBOM gates | `sbom-and-supply-chain` |
| Authorized attack-surface inventory | `recon-and-methodology` |
| Dockerfile layer secret pitfalls detail | `dockerfile-best-practices` |
| CI job trust boundaries / OIDC wiring detail | `ci-cd-pipeline-patterns` |

## What Counts As A Secret

Treat as secret unless policy explicitly declassifies:

| Class | Examples |
| --- | --- |
| Auth material | Passwords, API keys, PATs, refresh tokens, session secrets |
| Crypto keys | Private keys, signing keys, encryption keys, HMAC secrets |
| Cloud & infra | Access keys, service-account JSON, kubeconfig user certs |
| Integration | Webhook signing secrets, OAuth client secrets, SMTP creds |
| Sensitive config | DB URLs **with** passwords, private package tokens |
| Bootstrap | Seed encryption keys, recovery codes, MFA backup material |

**Usually not secrets (still minimize):** public client ids (confirm app type),
non-sensitive feature flags, public JWKS URLs, documentation hostnames.

## Principles

| Principle | Practice |
| --- | --- |
| No secrets in VCS | Not in source, history-friendly commits, sample configs, or IaC without sealed/encrypted form |
| Separate by env | Distinct values for local / stage / prod; never promote prod secrets to lower envs |
| Least privilege | Scope tokens to service + action + resource; short TTL where possible |
| Inject at runtime | Platform secret store, CSI, env from orchestrator — not bake into images |
| Encrypt in storage | Vault/KMS/sealed secrets; protect encryption keys as higher-tier secrets |
| Rotate & revoke | Planned rotation + emergency revoke path with ownership |
| Detect leakage | Secret scanning on push/CI; canary tokens; log redaction |
| Dual control for break-glass | High-impact secrets need approval or split knowledge per policy |

## Workflow

### 1. Inventory secrets and owners

1. List secret **names** (not values): purpose, consumer service, env, store location, owner, last rotation, blast radius.
2. Classify **tier** (e.g., break-glass signing key vs low-risk webhook).
3. Map **injection path:** local `.env`, CI, k8s secret, cloud SM, app vault agent.
4. Flag **orphans** (unused), **shared** (one key many apps), and **human-held** long-lived keys.

Output: living secret inventory (SSOT) with owners — no plaintext values in the sheet.

### 2. Eliminate secrets from code and artifacts

1. Search repo and CI artifacts for high-entropy strings, `AKIA`, `-----BEGIN`, `api_key`, `password=`, connection strings (use org-approved scanners: gitleaks, trufflehog, native GitHub/GitLab secret scanning).
2. Replace committed secrets with **references** (`SECRET_NAME`, vault path, SM ARN).
3. Provide **`.env.example`** / `config.sample` with **placeholder** values only.
4. Ensure `.gitignore` / `.dockerignore` exclude `.env`, key files, kubeconfigs, `*.pem`.
5. If history contains secrets: **rotate first**, then history purge / allowlist per IR — do not assume delete-from-HEAD is enough.
6. Block reintroduction: pre-commit or CI secret scan as required check.

### 3. Choose storage and injection pattern

Prefer org-standard platforms; do not invent a second vault without need.

| Context | Preferred pattern |
| --- | --- |
| Local dev | Developer secret store or short-lived personal tokens; `.env` **gitignored**; never prod keys |
| CI/CD | Platform secrets / OIDC → cloud roles; environment-scoped; no fork-PR secret access |
| Runtime (k8s) | External Secrets / CSI / native secrets from SM; avoid plain Secret manifests in git unencrypted |
| Runtime (VM/serverless) | Instance role / task role + SM read; no long-lived keys on disk |
| Mobile/SPA | No confidential secrets in clients; use backend-for-frontend or public+PKCE patterns |
| Human break-glass | Password manager / privileged access workstation; audited checkout |

**Anti-pattern:** long-lived cloud access keys in repo or laptop env for prod deploy when OIDC/workload identity exists.

### 4. Application consumption hygiene

When implementing or reviewing app code (`code-quality-standards` baseline):

1. Load secrets at **startup or just-in-time** from env/platform APIs — not hardcoded defaults.
2. Fail closed if required secrets missing in prod; never fall back to a public sample key.
3. Keep secrets in **memory only** as needed; avoid writing to temp files or crash dumps.
4. Do not put secrets in URLs (query strings appear in logs and proxies).
5. Separate **data-plane** and **control-plane** credentials.
6. For multi-tenant products: no shared “super” integration key across tenants if tenant isolation is required.

### 5. Logging, metrics, and errors

Apply `logging-message-style` for message design:

1. Never log Authorization headers, cookies, raw tokens, private keys, or full secret-bearing configs.
2. Redact known field names (`password`, `token`, `secret`, `client_secret`, `private_key`).
3. Prefer stable error codes over “auth failed: <upstream body that might echo the key>.”
4. Audit **use** of break-glass and admin secret access (who/when/why), not the secret value.
5. CI logs: mask platform secrets; avoid `set -x` around export of credentials; disable debug on release jobs.

### 6. Rotation, revocation, and dual-running

1. Document **rotation procedure** per secret class: generate → inject → verify → retire old.
2. Prefer **dual-running** (accept old + new) for short overlap when consumers are many.
3. Automate rotation where the platform supports it (SM rotation lambdas, vault dynamic secrets).
4. On leak: **revoke/rotate immediately**, then assess access logs; open IR ticket.
5. Time-box emergency exceptions (hotfixes that temporarily weaken controls) with expiry.

### 7. Supply chain and build path

Hand deep packaging/provenance work to `sbom-and-supply-chain`:

1. Registry tokens and signing keys are high-tier secrets — scope publish rights tightly.
2. Do not embed install-time tokens in published packages or container layers.
3. Prefer OIDC federation to package registries over static `NPM_TOKEN` in every fork workflow.
4. Sign/attest release artifacts with keys that never leave HSM/KMS when policy requires.

### 8. Verify and gate

1. Secret scan clean on default branch and release tags.
2. Runtime: process environment and config endpoints do not expose secrets to low-priv callers.
3. Stage deploy using non-prod secrets; prod deploy uses environment protection + least privilege.
4. Chaos check: revoke a stage secret and confirm app fails safely and alerts.
5. Document residual accepted risks (e.g., third-party SaaS that only supports long-lived keys).

## Good / Bad Patterns

### Config samples

**Good**

```bash
# .env.example — placeholders only
DATABASE_URL=postgresql://app:changeme@localhost:5432/app
PAYMENTS_API_KEY=replace-me
```

**Bad**

```bash
# committed .env with real credentials
DATABASE_URL=postgresql://app:SuperSecretProd@db.internal:5432/app
PAYMENTS_API_KEY=sk_live_51H…
```

### Runtime injection (sketch)

**Good** — platform injects; app reads env name only:

```text
Orchestrator/SM → env PAYMENTS_API_KEY → process
Image and git contain zero secret values
```

**Bad** — secret in image or source:

```text
Dockerfile: ENV PAYMENTS_API_KEY=sk_live_…
# or COPY secrets.json /app/
```

### CI identity

**Good** — short-lived federated creds (OIDC) to cloud role with deploy-only IAM.

**Bad** — static `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` available to all jobs including untrusted PR contexts.

### Rotation

**Good** — issue new key → deploy consumers → monitor → disable old key within SLA.

**Bad** — “rotate yearly if we remember”; old keys remain valid indefinitely after employee leave.

## Incident Mini-Playbook (authorized / org)

1. **Confirm** exposure path (public repo, log, package, screenshot).
2. **Rotate/revoke** before wide discussion of the value.
3. **Inventory** systems that accepted the secret; review access logs for abuse.
4. **Remove** from git HEAD and plan history remediation if needed.
5. **Add** scanning/gates to prevent recurrence.
6. **Record** timeline and residual risk; reopen threat model if trust assumptions broke
   (`threat-modeling-stride`).

Never use a leaked third-party secret for validation against systems outside scope.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Secrets in code, vault design, rotation, .env, 密钥管理 | **This skill** | — |
| Secure coding of loaders, validation, error paths | `code-quality-standards` | **always** on implementation |
| Log redaction, audit event shape, no secret fields | `logging-message-style` | this skill for what must never appear |
| Signing keys, package tokens, provenance, SBOM gates | `sbom-and-supply-chain` | this skill for secret lifecycle |
| Finding where secrets are used across estate (authorized) | `recon-and-methodology` | this skill for remediation patterns |
| Design-time spoofing/disclosure of credentials | `threat-modeling-stride` | this skill for mitigations |
| Dockerfile secrets not in layers | `dockerfile-best-practices` | this skill for runtime/vault |
| CI secret scopes, OIDC, fork PR isolation | `ci-cd-pipeline-patterns` | this skill for inventory/rotation policy |
| K8s secret misconfig assessment (authorized lab) | `kubernetes-pentesting` | this skill for hygiene fixes |

### Routing notes (required helpers)

- **`code-quality-standards`:** implementation and review baseline when changing code that loads or handles secrets.
- **`logging-message-style`:** primary for log templates and field policy; this skill defines secret classes to redact.
- **`sbom-and-supply-chain`:** when secrets intersect package publish, signing, or dependency trust.
- **`recon-and-methodology`:** when engagement needs authorized discovery of exposure surfaces before hygiene work.

## Checklist

- [ ] Secret inventory exists (names, owners, env, store, rotation) without plaintext values
- [ ] No secrets in git, container layers, published packages, or `.env` committed files
- [ ] `.env.example` / samples use placeholders; ignore rules cover secret files
- [ ] Runtime/CI injection from platform store or OIDC; least privilege and env separation
- [ ] Prod secrets never used on developer laptops or shared slack
- [ ] Logging and CI output redaction verified (`logging-message-style`)
- [ ] Rotation procedure and emergency revoke path documented and owned
- [ ] Secret scanning gated on protected branches; history leak handled via rotate-first
- [ ] High-tier keys (signing, break-glass) have dual control / audit per policy
- [ ] Supply-chain publish/sign credentials scoped (`sbom-and-supply-chain`)
- [ ] `code-quality-standards` applied on code that reads secrets
- [ ] Residual long-lived vendor keys listed with compensating controls and review date

## Rules

- Rotate before you document a live leak in detail; redact forever in secondary systems.
- Prefer short-lived, scoped, federated identity over static shared passwords.
- One consumer principal per secret when practical — shared keys block safe rotation.
- Local convenience never justifies prod keys in personal shells or screenshots.
- Methodology for **defense and authorized hardening** only — not credential abuse.
- When architecture assumptions change, update the threat model and this inventory together.
---

# Note

This skill owns **secret lifecycle hygiene**. Pair with `threat-modeling-stride`
for design workshops, `logging-message-style` for sink redaction, and
`sbom-and-supply-chain` when build/publish credentials and provenance are in play.

---
name: vault-agent-injection
description: >
  HashiCorp Vault Agent Injector on Kubernetes: pod annotations, Agent vs
  template rendering, Kubernetes auth and other methods, secret rotation, and
  avoiding long-lived tokens in images or manifests. Use when designing or
  reviewing vault.hashicorp.com/* annotations, Injector sidecars, Consul
  Template configs, Agent auto-auth, or runtime secret delivery for owned
  clusters — not embedding static Vault tokens in Deployments.
---

# Vault Agent Injection (Kubernetes)

Deliver secrets via the **Vault Agent Injector** (mutating webhook + sidecar/init)
so pods read rendered files from a shared volume instead of baking long-lived
Vault tokens into images or Git. Defensive design and authorized review only.

## Scope And Authorization

- **In scope:** org-owned clusters/Vault; staging/lab; GitOps annotation review;
  read-only policy/role inventory under ROE.
- **Out of scope:** unauthorized Vault/K8s access; using injected secrets outside
  engagement; disabling prod auth to “prove” breakage.
- Prefer static manifests and non-prod inject first; gate live auth tests.
- Redact tokens, role IDs, AppRole secrets, JWT client secrets, and paths.
- Org secret lifecycle/IR → `secrets-management-hygiene`. Live cluster methodology
  → `kubernetes-pentesting` (authorized only).

## When To Use

- Adding or reviewing `vault.hashicorp.com/agent-inject*` annotations
- Choosing **init-only** vs **sidecar Agent** (continuous renew/render)
- Configuring templates (`agent-inject-secret`, `agent-inject-template`)
- Wire-up of **Kubernetes auth**, JWT/OIDC, or AppRole for injectors
- Secret **rotation**, lease renew, and consumer file reload behavior
- Eliminating static `VAULT_TOKEN` / root tokens in Deployments or CI
- Keywords: Vault Injector, Agent sidecar, Consul Template, auto-auth,
  agent-inject, vault.hashicorp.com, Kubernetes auth role, secret rotation

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org secret inventory, git/.env leak IR, rotation playbooks | `secrets-management-hygiene` |
| Pod PSS/PSA, privileged, hostPath | `kubernetes-pod-security` |
| Live cluster RBAC/secrets dump (lab) | `kubernetes-pentesting` |
| Helm values/`--set` packaging of inject annotations | `helm-chart-security` |
| App/IaC code quality baseline | `code-quality-standards` |
| Azure Key Vault (not HashiCorp) | `azure-keyvault-basics` |

## Agent Vs Template

| Mode | Behavior | Prefer when |
| --- | --- | --- |
| **Init only** | Agent writes secrets once, exits | Boot-time static secrets; no mid-life refresh |
| **Sidecar Agent** | Stays up; renews leases; re-renders | Dynamic secrets, short TTLs, certs, DB creds |
| **Templates** | Consul Template → files on shared volume | Multi-key paths, custom formats, file consumers |

Do **not** confuse Injector with Vault CSI or External Secrets — different
delivery paths; pick one pattern per workload class.

## Workflow

### 1. Inventory consumers and Vault paths

List Deployments/STS/Jobs needing secrets; map path, engine (KV/DB/PKI), TTL,
owner. Confirm Injector webhook and trusted Agent image. Inventory names/paths
only — no plaintext values.

### 2. Auth method (never long-lived pod tokens)

| Method | Notes |
| --- | --- |
| **Kubernetes auth** | Default: SA JWT → Vault role bound to ns/SA |
| **JWT/OIDC** | Federated identity when K8s auth unavailable |
| **AppRole** | Avoid embedding `role_id`/`secret_id` in pod env |
| **Token** | Static Vault tokens in manifests/images = **critical** |

Vault role: least-privilege policies, bound SAs, short token TTL. Separate
deploy-time vs runtime identities when possible.

### 3. Annotations and templates

1. `agent-inject: "true"`; optional status annotation after inject.
2. Per secret: `agent-inject-secret-<name>` → Vault path.
3. Custom render: `agent-inject-template-<name>` (Consul Template body).
4. Auth: `auth-path`, `role`; `agent-pre-populate-only` for init-only.
5. TLS/CA annotations for private Vault; pin Agent image digest; set limits.
6. Fail closed if required paths missing — no prod fallback secrets in the image.

### 4. Rotation and consumer behavior

1. Prefer dynamic secrets or short KV versions with dual-running keys.
2. Sidecar re-renders on renew; app must **reload** files (SIGHUP/watch/restart) —
   one-shot read at boot defeats TTL.
3. Cutover: new version → verify → revoke old lease/version.
4. On leak: revoke leases/tokens and SA bindings, then rotate dependents
   (`secrets-management-hygiene`). Never log rendered files or Agent debug dumps.

### 5. Hardening and report

Shared volume perms (not world-readable); Agent non-root when PSS allows;
NetworkPolicy pods → Vault only. No root/orphan tokens in Git, ConfigMaps, or
layers. Report by blast radius (static token > over-broad policy > init-only with
dynamic DB creds). Cite annotation keys and role names — never live tokens.
Exceptions: owner + expiry.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Injector annotations, Agent vs template, K8s auth, inject rotation | **This skill** | — |
| Org scanning, .env, leak IR, inventory | `secrets-management-hygiene` | this for inject path |
| Pod securityContext / PSA | `kubernetes-pod-security` | this for sidecar constraints |
| Live cluster secret/RBAC assessment | `kubernetes-pentesting` | this for Injector root cause |
| Helm packaging of annotations/values | `helm-chart-security` | this for Vault semantics |
| App reload logic, charts, tests | `code-quality-standards` | **always** on implementation |
| Azure Key Vault | `azure-keyvault-basics` | — |

- **`secrets-management-hygiene`:** lifecycle/IR; this skill owns Injector delivery.
- **`kubernetes-pod-security`:** PSA/restricted may constrain sidecars.
- **`code-quality-standards`:** file-watch/reload and manifest quality.
- **`kubernetes-pentesting`:** authorized attack-surface work, not default path.

## Output Checklist

- [ ] Scope/authorization recorded (owned cluster + Vault / ROE only)
- [ ] Workloads mapped to Vault paths, engines, TTLs, owners (no values)
- [ ] Injector present; Agent image pinned/trusted
- [ ] Auth via K8s/JWT (or justified) — **no** static Vault tokens in pods
- [ ] Vault roles least-privilege; bound SA/ns documented
- [ ] Init-only vs sidecar matches secret dynamism
- [ ] Templates reviewed; fail-closed without prod fallback secrets
- [ ] Rotation/renew + app reload verified for short TTL secrets
- [ ] Volume perms, NetworkPolicy to Vault, PSS alignment addressed
- [ ] No secrets in Git/images; evidence redacted
- [ ] Exceptions owned with review date; code uses `code-quality-standards`
- [ ] Routed: org IR → `secrets-management-hygiene`; live cluster → `kubernetes-pentesting`

---
name: helm-chart-security
description: >
  Helm chart security review for owned/authorized apps: values secrets, privileged
  pods, default service accounts, NetworkPolicy gaps, chart provenance/signing,
  and --set / CI secret leaks. Use when reviewing Chart.yaml, values.yaml,
  templates, helm install/upgrade flags, OCI/chart museum supply chain, or
  hardening org Helm releases before or after deploy.
---

# Helm Chart Security

Review and harden **Helm charts and release practices** so packaged workloads do
not ship secrets in values, grant excess pod power, bind the default
ServiceAccount, omit network isolation, or install untrusted packages. Defensive
and authorized only. Live cluster RBAC/secrets → `kubernetes-pentesting`. Org
secret lifecycle → `secrets-management-hygiene`.

## Scope And Authorization

- **In scope:** charts, values, umbrellas, and Helm CI you own or are contracted
  to review; staging/lab; read-only `helm template` / `helm get` under ROE.
- **Out of scope:** installing untrusted charts into shared prod to “see impact”;
  abusing discovered kubeconfigs/values secrets outside scope; unapproved prod
  upgrades.
- Prefer **static render** (`helm template`, `helm lint`) before live change.
- Treat values files, secret plugin output, and CI logs as **sensitive**; redact.
- Privileged/breakout proofs only on lab hosts (`container-escape-techniques`).

## When To Use

- Reviewing `Chart.yaml`, `values.yaml`, `templates/*`, hooks, chart tests
- Secrets in committed values, missing SealedSecrets/SOPS/ESO, or `--set` secrets
- `privileged`, hostPath, hostNetwork/PID/IPC, or broad capabilities in templates
- Charts using default ServiceAccount or needless SA token automount
- Missing NetworkPolicy templates or values that disable isolation in prod
- Unsigned/unpinned OCI or repo charts; floating dependency versions
- Keywords: Helm security, values secrets, helm --set leak, chart provenance,
  privileged pod, default service account, Helm NetworkPolicy

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Live cluster RBAC, etcd, kubelet, secret dump (lab) | `kubernetes-pentesting` |
| NetworkPolicy design / CNI deep-dive | `kubernetes-network-policy` |
| Vault/SM rotation, .env, org secret scanning | `secrets-management-hygiene` |
| Image non-root / layer secrets | `dockerfile-best-practices` |
| Lab container→host breakout | `container-escape-techniques` |
| Compose (not Helm) | `docker-compose-security` |
| Template helpers, tests, CI scripts quality | `code-quality-standards` |

## Workflow

### 1. Inventory and render

1. List chart roots, umbrellas, `Chart.lock`/deps, env values files, install source
   (local tgz, Helm repo, OCI).
2. Render statically: `helm lint .` then
   `helm template rel . -f values.yaml -f values-prod.yaml`.
3. Note hooks, Jobs/CronJobs, CRDs, and who may `helm upgrade -i`.

### 2. Values secrets and `--set` leaks

| Pattern | Prefer |
| --- | --- |
| Plain secrets in committed `values*.yaml` | External Secrets / CSI / sealed; see `secrets-management-hygiene` |
| `--set password=…` / `--set-string token=…` | `--set-file`, out-of-band values, or secret-store refs (no shell/CI history) |
| ConfigMap or plain env for credentials | `Secret` + tight RBAC; never log secret env |
| Chart tests / `helm --debug` dumping values | Placeholders only; redact CI logs |

Scan values and pipelines for high-entropy strings. **Rotate first** if anything
live was committed, then remove (`secrets-management-hygiene`).

### 3. Privileged pods and hardening defaults

On rendered Pods/Deployments/DaemonSets/Jobs/hooks, expect:

- `privileged: false`; `allowPrivilegeEscalation: false`
- non-root (`runAsNonRoot` / fixed UID); drop `ALL` capabilities
- no hostPath / hostNetwork / hostPID / hostIPC unless documented node agent
- resource requests/limits; pin image tags/digests per policy

Secure **defaults** in values (`podSecurity.*`); do not ship `privileged: true`
for convenience. Image build side → `dockerfile-best-practices`.

### 4. Default ServiceAccount

- Create a **dedicated** SA; never leave pods on `default`.
- `automountServiceAccountToken: false` when the app does not call the API.
- Roles/RoleBindings: least verbs/resources; no casual `cluster-admin` binds.

### 5. NetworkPolicy and exposure

- Ship default-deny + explicit allow templates (or document external policy).
- Values must not silently disable all policies in prod without owner/expiry.
- Review Service `LoadBalancer`/`NodePort` and Ingress defaults for admin UIs.
- Policy semantics → `kubernetes-network-policy`; chart owns packaging/on-by-default.

### 6. Chart provenance and CI

- Pin dependency versions; commit lockfile; avoid `version: "*"`.
- Prefer signed/provenance-verified OCI or org-mirrored HTTPS repos before prod.
- CI: no unredacted `helm get values -a` / `--debug`; env-scoped kubeconfig only.
- Apply `code-quality-standards` to helpers, unittest, and install scripts.
- Live can-i / secret-list validation → `kubernetes-pentesting` when authorized.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Helm values, templates, SA, provenance, `--set` leaks | **This skill** | — |
| Live cluster RBAC, secrets API, kubelet, ns attack surface | `kubernetes-pentesting` | this for chart root cause |
| NetworkPolicy rules / default-deny design | `kubernetes-network-policy` | this for chart packaging |
| Vault, rotation, git secret IR, scanning | `secrets-management-hygiene` | this for values/`--set` paths |
| Image build non-root / layers | `dockerfile-best-practices` | this for pod template defaults |
| Privileged/hostPath breakout (lab) | `container-escape-techniques` | this for chart evidence |
| Chart code, tests, CI scripts | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for chart/release packaging; switch when work moves to
live cluster exploitation, org-wide secret process, or CNI policy detail.

## Output Checklist

- [ ] Scope clear; prefer `helm template`/`lint` before live change
- [ ] Charts, deps/lock, values files, install source inventoried
- [ ] No plaintext secrets in committed values; `--set` secret patterns removed
- [ ] Secret injection via store/sealed/CSI; rotate-first on any leak
- [ ] Pod defaults: non-privileged, non-root, dropped caps, no host ns/path
- [ ] Dedicated SA; default SA avoided; automount minimized; RBAC least privilege
- [ ] NetworkPolicy (or documented external) default-deny oriented for prod
- [ ] Service/Ingress exposure intentional; admin not open by default
- [ ] Dependencies pinned; provenance/signature verified per org policy
- [ ] CI does not log full values/debug secrets; kubeconfig least privilege
- [ ] Findings cite chart paths and rendered kinds; residuals owned with expiry
- [ ] Routed: runtime → `kubernetes-pentesting`; NetPol → `kubernetes-network-policy`;
      secrets → `secrets-management-hygiene`; images → `dockerfile-best-practices`;
      breakout lab → `container-escape-techniques`; code → `code-quality-standards`

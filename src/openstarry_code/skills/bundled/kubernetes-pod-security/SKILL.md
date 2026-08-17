---
name: kubernetes-pod-security
description: >
  Harden Kubernetes workloads with Pod Security Standards (baseline/restricted),
  PSA labels, securityContext (runAsNonRoot, capabilities, privileged, hostPath),
  and PodSecurityPolicy migration. Use when reviewing Deployments/Pods for PSS
  violations, enforcing namespace PSA, dropping Linux capabilities, banning
  privileged/hostPath, or replacing legacy PSP — owned/lab clusters only.
---

# Kubernetes Pod Security (PSS / PSA / securityContext)

Harden **pod/container securityContext** and **Pod Security Admission (PSA)**
against Pod Security Standards (PSS). Owned, staging, lab, or ROE clusters only.

## Scope And Authorization

- **In scope:** owned/lab/ROE namespaces; GitOps/Helm review; PSA staged enforce.
- **Out of scope:** unauthorized scanning; privileged prod pods to “prove” escape;
  hostPath/docker.sock abuse outside lab.
- Prefer read-only inventory and `kubectl --dry-run=server` before enforce.
- Lab breakout → `container-escape-techniques`. Redact tokens/secrets.
- NetworkPolicy → `kubernetes-network-policy`. RBAC/API → `kubernetes-pentesting`.

## When To Use

- PSS levels **privileged** / **baseline** / **restricted**
- Namespace labels `pod-security.kubernetes.io/{enforce,audit,warn}`
- `privileged`, `allowPrivilegeEscalation`, broad `capabilities.add`
- Missing `runAsNonRoot`, `seccompProfile`, or `readOnlyRootFilesystem`
- `hostPath`, `hostNetwork`/`hostPID`/`hostIPC`, docker.sock mounts
- Migrating deprecated **PodSecurityPolicy (PSP)** to PSA + PSS

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| NetworkPolicy / default-deny / CNI policy | `kubernetes-network-policy` |
| RBAC, secrets, API/kubelet attack surface | `kubernetes-pentesting` |
| Lab container→host breakout | `container-escape-techniques` |
| Image USER / non-root build | `dockerfile-best-practices` |
| Compose privileged/sock (not K8s) | `docker-compose-security` |
| Manifests, tests, CI policy gates | `code-quality-standards` |

## Workflow

### 1. Inventory PSA and workloads

1. Record cluster version, in-scope namespaces, PSA mode.
2. List PSA labels (enforce/audit/warn + level + version).
3. Inventory Deploy/DS/STS/Job/CronJob and raw Pods.
4. Do not blanket-restrict CNI/CSI system ns without a plan.

```bash
kubectl get ns -L pod-security.kubernetes.io/enforce,pod-security.kubernetes.io/audit,pod-security.kubernetes.io/warn
kubectl get deploy,ds,sts,job,cronjob,po -n <ns> -o wide
```

### 2. Choose PSS level

| Level | Intent |
| --- | --- |
| **privileged** | Unrestricted; break-glass/infra only (owner + expiry) |
| **baseline** | Block known-bad (privileged, host ns/path, risky caps) |
| **restricted** | App default: non-root, drop ALL, no priv-esc, seccomp |

Prefer **restricted** for apps; **baseline** only as a migration step.

### 3. securityContext (pod + container)

Set both levels; container fields override when present.

| Control | Restricted-oriented target |
| --- | --- |
| `runAsNonRoot: true` | Required; add numeric UID/GID if image needs it |
| `allowPrivilegeEscalation: false` | Always for app containers |
| `capabilities.drop: ["ALL"]` | Re-add only documented caps (e.g. `NET_BIND_SERVICE`) |
| `privileged: true` | Forbidden for apps — critical finding |
| `readOnlyRootFilesystem: true` | Prefer; emptyDir for writable paths |
| `seccompProfile.type: RuntimeDefault` | Required under restricted |
| `hostPath` / host* namespaces | Deny for apps; justify node agents only |
| Volumes | emptyDir, configMap, secret, PVC — not host FS/sock |

```bash
kubectl get pods -n <ns> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.hostNetwork}{"\t"}{.spec.hostPID}{"\t"}{range .spec.containers[*]}{.name}={.securityContext.privileged}{" "}{end}{"\n"}{end}'
```

### 4. PSA rollout

1. **warn** + **audit** at target level on staging.
2. Fix controller templates until audit is clean (not one-off pods).
3. **enforce** non-prod → soak → prod change window.
4. Time-box exemptions; re-check quarterly.
5. initContainers and sidecars must meet the same level.

### 5. PSP → PSA migration

1. Inventory PSPs, bindings, and covered service accounts.
2. Map each PSP rule to PSS baseline/restricted (hostPath, priv, caps, volumes).
3. Dual-run: retain PSP until PSA audit matches intent; then enforce PSA.
4. Remove PSP only after enforce is proven and disable path is planned.
5. Legacy PSP “allow” is often over-permissive — not equal to restricted.

### 6. Findings

Flag privileged apps; root without `runAsNonRoot`; `CAP_SYS_ADMIN`/`ALL`; hostPath
`/` or docker.sock; missing PSA enforce; PSP-only controls. Fix via GitOps + PSA;
prove with dry-run admission — not prod breakout.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| PSS/PSA, securityContext, hostPath/privileged/caps | **This skill** | — |
| NetworkPolicy / default-deny | `kubernetes-network-policy` | this skill for pod SC |
| Cluster RBAC/secrets/API assessment | `kubernetes-pentesting` | this skill for workloads |
| Lab escape (privileged/hostPath/sock) | `container-escape-techniques` | this skill for evidence |
| Image non-root / minimal base | `dockerfile-best-practices` | this skill for runtime SC |
| Compose (not K8s) | `docker-compose-security` | — |
| Charts/tests/CI gates | `code-quality-standards` | this skill for PSS intent |

- **`kubernetes-network-policy`:** east-west traffic; PSA is not NetworkPolicy.
- **`kubernetes-pentesting`:** full authorized cluster methodology.
- **`container-escape-techniques`:** lab-only host-boundary validation.
- **`dockerfile-best-practices`** / **`code-quality-standards`:** image USER and policy-as-code fixes.

## Output Checklist

- [ ] Scope/authorization recorded (owned/lab/ROE only)
- [ ] PSA labels inventoried per in-scope namespace
- [ ] Target PSS level chosen (restricted preferred for apps)
- [ ] Controllers checked for privileged, hostPath, hostNetwork/PID/IPC
- [ ] `runAsNonRoot`, no priv-esc, drop ALL documented
- [ ] add-caps and volume exceptions have owner + expiry
- [ ] seccomp / read-only root addressed on restricted track
- [ ] PSA warn→audit→enforce; no surprise prod enforce
- [ ] PSP migration mapped (if legacy) with dual-control exit criteria
- [ ] Network → `kubernetes-network-policy`; breakout → `container-escape-techniques`
- [ ] Images → `dockerfile-best-practices`; code → `code-quality-standards`
- [ ] Secrets redacted; residual exceptions listed with owner/expiry

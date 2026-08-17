---
name: kubernetes-rbac-least-privilege
description: >
  Kubernetes RBAC least-privilege review for owned clusters: ServiceAccounts,
  Roles/ClusterRoles, RoleBindings/ClusterRoleBindings, verb/resource scoping,
  and bind-escalation footguns. Use when hardening default SA usage, trimming
  cluster-admin, splitting deploy vs runtime identities, reviewing can-i rights,
  or rewriting overly broad Role rules in org-owned or authorized clusters —
  not for abusing third-party Kubernetes control planes.
---

# Kubernetes RBAC Least Privilege

Design and harden **Kubernetes RBAC** so humans, CI, controllers, and app
ServiceAccounts hold only the API verbs and resources they need. Defensive work
for **org-owned or explicitly authorized clusters** — not control-plane abuse.

## Scope And Authorization

- **In scope:** Roles, ClusterRoles, RoleBindings, ClusterRoleBindings,
  ServiceAccounts, aggregation labels, and `can-i` / SubjectAccessReview on
  clusters you own or are contracted to assess; GitOps/Helm/Terraform that
  declare those objects.
- **Out of scope:** Foreign clusters; stolen kubeconfigs; mass-exporting
  Secrets/etcd; unapproved prod elevation; container breakout (lab →
  `container-escape-techniques`).
- Prefer **read-only inventory** first. Gate role/binding mutations behind
  change windows. Redact kubeconfigs, SA tokens, and Secret data.
- Secrets lifecycle → `secrets-management-hygiene`. Pod securityContext/PSA →
  `kubernetes-pod-security`. Live adversarial assessment →
  `kubernetes-pentesting` (authorized only). Manifest quality →
  `code-quality-standards`.

## When To Use

- Reviewing or rewriting **Role / ClusterRole** rules and bindings
- Workloads still use the **default** ServiceAccount or mount unused tokens
- CI, operators, or humans hold **cluster-admin** or `*` verbs on daily paths
- Splitting **deploy** (apply manifests) from **runtime** (app SA) identities
- Over-broad `secrets` list, `create pods`, `escalate`, `bind`, or `impersonate`
- Mentions: K8s RBAC least privilege, RoleBinding, ClusterRoleBinding, can-i,
  service account token, cluster-admin, aggregate-to-admin

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Live pentest of secrets, kubelet, etcd (lab) | `kubernetes-pentesting` |
| privileged / hostPath / PSA / securityContext | `kubernetes-pod-security` |
| NetworkPolicy design | `kubernetes-network-policy` |
| Helm chart packaging of SA/RBAC defaults | `helm-chart-security` |
| Org secret rotation / leak IR | `secrets-management-hygiene` |
| Lab container→host breakout | `container-escape-techniques` |
| Manifest/module quality and tests | `code-quality-standards` |

## Workflow

### 1. Inventory identities

Record cluster, namespaces, env, and authorization. List humans (OIDC groups),
CI deploy SAs, operators, and per-app ServiceAccounts. Flag god ClusterRoles
and apps still on `default`.

```bash
# Owned/authorized cluster — read-first
kubectl auth whoami
kubectl get sa,role,rolebinding -A
kubectl get clusterrole,clusterrolebinding
kubectl get clusterrolebinding -o wide | grep -E 'cluster-admin|edit|admin'
```

### 2. Map subjects → roles → rules

```bash
kubectl describe clusterrolebinding SOME_BINDING
kubectl describe rolebinding -n "$NS" SOME_BINDING
kubectl get clusterrole SOME_ROLE -o yaml
kubectl auth can-i --list --as=system:serviceaccount:$NS:$SA
kubectl auth can-i get secrets --as=system:serviceaccount:$NS:$SA -A
```

Matrix: subject → Role/ClusterRole → apiGroups/resources/verbs → namespace vs
cluster. Note aggregation (`rbac.authorization.k8s.io/aggregate-to-*`).

### 3. Flag high-risk patterns

| Pattern | Why it matters |
| --- | --- |
| `cluster-admin` or `*` verbs/resources on daily subjects | Full API control |
| `get/list/watch` on `secrets` cluster-wide | Credential harvest |
| `create` pods + weak PSS / hostPath / arbitrary SA mount | Escape / token steal |
| `escalate` / `bind` on high roles | Self-grant stronger roles |
| `impersonate` users/groups/SAs | Become another principal |
| Bindings to `system:unauthenticated` / over-broad groups | Anonymous or org-wide power |
| `resources: ["*"]` / `apiGroups: ["*"]` | Future CRDs inherit access |
| App pods on `default` SA; CI SA equals runtime SA | Shared or inflated blast radius |

**Escalation (defensive):** principals that create RoleBindings or hold
`bind`/`escalate` must not attach cluster-admin to themselves. Prefer
namespace-scoped Roles for app teams.

### 4. Redesign and verify

1. **Dedicated SA per workload**; `automountServiceAccountToken: false` when
   the app does not call the API.
2. Prefer **Role + RoleBinding** over ClusterRole unless cluster scope is real.
3. Enumerate verbs and resources/resourceNames from need — start narrow.
4. Split **human/OIDC**, **CI deploy**, and **runtime** identities.
5. Avoid cluster-wide `secrets` list; use projected tokens, CSI, or external
   stores with tight consumer RBAC.
6. Operators: separate SA + minimal rules; CRD install ≠ day-2 runtime.
7. Companion: PSA/securityContext via `kubernetes-pod-security` (not RBAC substitutes).
8. Change in **non-prod** first; re-run `can-i` and smoke tests; watch `Forbidden`.
9. Document residual exceptions (owner, expiry). Ship under `code-quality-standards`.
   Authorized attack-path checks → `kubernetes-pentesting`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| RBAC rules, bindings, SA least privilege, can-i redesign | **This skill** | — |
| Adversarial secrets/kubelet/etcd assessment (lab) | `kubernetes-pentesting` | this for intended RBAC fix |
| Pod privileged / hostPath / PSA | `kubernetes-pod-security` | this for SA mount rights |
| NetworkPolicy isolation | `kubernetes-network-policy` | this for API identity scope |
| Helm chart SA/RBAC packaging | `helm-chart-security` | this for rule semantics |
| Token/Secret leak IR, rotation | `secrets-management-hygiene` | this for who can read Secrets |
| Manifests, operators, policy-as-code tests | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for Role/Binding design; switch for live offensive assessment, pod isolation, NetPol detail, or org secret process.

## Output Checklist

- [ ] Authorization and cluster/namespace scope recorded (owned/authorized only)
- [ ] Subjects inventoried: humans/groups, CI, operators, per-app SAs
- [ ] Roles/bindings mapped; `can-i --list` for high-risk SAs
- [ ] No unjustified `cluster-admin` / `*` on daily humans, CI, or runtime SAs
- [ ] Dedicated SA per workload; default avoided; automount minimized
- [ ] Namespace Roles preferred; ClusterRoles justified and minimal
- [ ] Secrets access scoped; escalate/bind/impersonate reviewed
- [ ] Deploy vs runtime identities split; exceptions owned with expiry
- [ ] Verified in non-prod; Forbidden/can-i rechecked after change
- [ ] Routed: live → `kubernetes-pentesting`; pods → `kubernetes-pod-security`;
      NetPol → `kubernetes-network-policy`; secrets IR → `secrets-management-hygiene`;
      code → `code-quality-standards`
- [ ] No live SA tokens or kubeconfig material in reports

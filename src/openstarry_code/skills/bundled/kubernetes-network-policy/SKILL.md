---
name: kubernetes-network-policy
description: >
  Design and review Kubernetes NetworkPolicy (and CNI-equivalent policy) for
  default-deny, least-privilege pod egress/ingress, namespace isolation, and
  safe exceptions. Use when NetworkPolicy, Calico/Cilium policy review, pod
  network segmentation, or authorized cluster network hardening 鈥?not for
  attacking clusters without authorization.
---

# Kubernetes NetworkPolicy Design And Review

Design and review **Kubernetes NetworkPolicy** (and CNI-native equivalents) so
workloads only send/receive traffic product intent requires. Authorized
defensive work and lab clusters only.

## Scope And Authorization

- **In scope:** clusters/namespaces you own or may assess; staging/lab first;
  policy YAML review without hostile packet injection on prod.
- **Out of scope:** unauthorized foreign-cluster scanning; pivoting through
  policy gaps outside engagement; destructive net tests on shared prod without
  a change window.
- Prefer read-only inventory and dry-run before enforcing default-deny live.
- Confirm the **CNI** implements policy (Calico, Cilium, Antrea, vendor). Stock
  NetworkPolicy is a no-op if the CNI ignores it.
- Redact API endpoints, tokens, customer CIDRs, and sensitive pod IPs.
- Broader RBAC/secrets/node work 鈫?`kubernetes-pentesting`. Lab breakout 鈫?  `container-escape-techniques`. Images 鈫?`dockerfile-best-practices`.
  Implementation 鈫?`code-quality-standards`.

## Use When

- Writing/reviewing `NetworkPolicy`, admin/CNI CRDs, or Helm network rules
- Default-deny ingress/egress, namespace isolation, locked egress (DNS/API/DB)
- Auditing allow-all empty selectors, missing policies, or wide `ipBlock`s
- Mentions: NetworkPolicy, K8s segmentation, Calico/Cilium policy, default-deny

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| K8s RBAC, secrets, etcd, cluster pentest | `kubernetes-pentesting` |
| Container/node breakout (lab) | `container-escape-techniques` |
| Dockerfile / image hardening only | `dockerfile-best-practices` |
| Docker Compose ports/networks | `docker-compose-security` |
| Charts/controllers/tests quality | `code-quality-standards` |

## Workflow

### 1. Cluster network facts

1. K8s version, CNI, whether NetworkPolicy (or CRDs) are enforced.
2. Namespaces, tenants, Ingress/LB, mesh (which layer is source of truth).
3. North-south vs east-west paths; protect `kube-system`/CNI with care 鈥?not
   blanket allow-all.

### 2. Inventory traffic needs

Per app/Helm release: listen ports; client peers (pods/ns/CIDRs); egress (DNS,
API, DB, cloud, SaaS); probe sources for **this** CNI. Prefer flow logs/metrics
over guesswork.

### 3. Posture

| Posture | When |
| --- | --- |
| Default-deny ingress **and** egress | Sensitive namespaces |
| Default-deny ingress only | Transitional hardening |
| CNI CRD allow/deny | Cilium/Calico beyond vanilla NP |

Once an ingress (or egress) policy **selects** a pod, unspecified traffic of that
direction is denied. **Unselected** pods stay open 鈥?select all app pods.

### 4. Design least privilege

1. Stable labels (`app.kubernetes.io/name` or org scheme); select labels, not names.
2. Ingress: required `from` (pod/namespace/ipBlock) + ports/protocols only.
3. Egress: explicit DNS, then data stores/APIs; avoid `0.0.0.0/0` without
   documented gateway + expiry.
4. Cross-namespace deny by default; allow named producer/consumer pairs.
5. Flag `hostNetwork`/`hostPort` (policy bypass risk) for broader review.
6. GitOps policies; apply `code-quality-standards` for YAML/tests/dry-run CI.

### 5. Safe rollout

1. Audit/alert mode if CNI supports it; else non-prod first.
2. Ship allows **before** default-deny on live traffic.
3. Validate Service, Ingress, DNS, Jobs, and kubelet probes.
4. Versioned rollback path; watch partial-port misses.

### 6. Assessment findings

Flag: namespaces with zero policies; empty selectors with broad `from`/`to`;
ingress from all namespaces without need; egress allow-all on sensitive apps;
selectors that miss real labels (false safety); CNI not enforcing; mesh/NP
conflicts. Report paths and severity 鈥?no out-of-scope pivots.

### 7. Hand off

RBAC/secrets/node 鈫?`kubernetes-pentesting`. Privileged/hostPath breakout 鈫?`container-escape-techniques` (lab). Image surface 鈫?`dockerfile-best-practices`.
Compose-only 鈫?`docker-compose-security`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| NetworkPolicy design / default-deny / review | **This skill** | 鈥?|
| K8s RBAC, secrets, cluster attack surface | `kubernetes-pentesting` | this skill for net slice |
| Lab container/node escape | `container-escape-techniques` | `kubernetes-pentesting` |
| Workload image baselines | `dockerfile-best-practices` | this skill for traffic |
| Compose (not K8s) security | `docker-compose-security` | 鈥?|
| Policy-as-code structure/tests | `code-quality-standards` | this skill for intent |

- **`kubernetes-pentesting`:** full authorized cluster assessment.
- **`container-escape-techniques`:** host boundary after network is crossed.
- **`dockerfile-best-practices`:** reduce listen/tooling surface in images.
- **`code-quality-standards`:** charts, operators, policy tests.

## Checklist

- [ ] Authorization recorded; CNI enforces policy (or documented CRD path)
- [ ] Trust zones and mesh vs NP ownership documented
- [ ] Per-app peers and egress (incl. DNS) inventoried
- [ ] Labels stable and matched by selectors; no accidental unselected pods
- [ ] Default-deny posture set; cross-ns allows explicit only
- [ ] No unjustified `0.0.0.0/0` or empty-selector allow-all
- [ ] Staged rollout; probes/DNS/Ingress verified
- [ ] No unauthorized pivot/destructive tests
- [ ] RBAC/escape items routed to `kubernetes-pentesting` /
      `container-escape-techniques`
- [ ] Images follow `dockerfile-best-practices` when in scope
- [ ] Manifests/tests follow `code-quality-standards`; exceptions have owner/expiry

## Rules

- Incomplete allows break apps; missing selection leaves holes.
- Verify CNI behavior on *this* cluster.
- Prefer staging and flow evidence over prod trial-and-error.
- Authorized clusters only; policy is not a substitute for mTLS or authz.

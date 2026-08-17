---
name: service-mesh-mtls-rollout
description: >
  Plan and execute progressive service-mesh mTLS rollouts on owned clusters:
  baseline inventory, PERMISSIVE then STRICT, canary namespaces, DestinationRule
  / peer policy alignment, plaintext exception budgets, and evidence-based
  cutover. Use when enabling mesh mTLS (Istio PeerAuthentication, Linkerd
  automatic mTLS, Consul Connect, similar), migrating east-west from plaintext
  to mutual TLS, debugging mode mismatch 503s, or staging STRICT without
  breaking legacy clients — not for AuthorizationPolicy design, L3 NetworkPolicy,
  or non-mesh app client-cert design alone.
---

# Service Mesh mTLS Rollout

Safely roll **mesh mutual TLS** from off/permissive to **STRICT** (or equivalent)
on **owned or authorized** meshes. Focus is staged east-west identity + encryption,
rollback, and proof — not full mesh authorization design.

## When To Use

| Situation | Direction |
| --- | --- |
| Turn on or tighten mesh mTLS (PERMISSIVE → STRICT) | **This skill** |
| Canary namespaces/workloads before mesh-wide STRICT | **This skill** |
| Align PeerAuthentication / DestinationRule / Linkerd mode | **This skill** |
| Document plaintext exceptions and exception expiry | **This skill** |
| Prove mTLS with metrics, istiod/proxy status, controlled probes | **This skill** |
| Debug mTLS mode mismatch (503, connection reset, mixed peers) | **This skill** |
| Path/method/JWT AuthorizationPolicy design | `istio-authz-basics` |
| L3/L4 NetworkPolicy only | `kubernetes-network-policy` |
| App-level client certs outside the mesh | `mtls-client-auth-basics` |
| Public/private cert issuance (non-mesh CA) | `cert-manager-basics` |

Keywords: mesh mTLS, PeerAuthentication STRICT, ISTIO_MUTUAL, PERMISSIVE,
sidecar injection, SPIFFE identity, east-west encryption, Linkerd mTLS.

## Scope And Authorization

- **In scope:** org-owned meshes and clusters; staging/lab first; production only
  with change window, owners, and rollback; CTF/lab meshes you control.
- **Out of scope:** third-party clusters; forcing STRICT on shared prod without
  approval; capturing or replaying customer traffic outside engagement; disabling
  mTLS to “fix” production without a tracked exception.
- Prefer **read-only inventory + canary** before cluster-wide STRICT.
- Treat mesh CA roots, intermediates, SPIFFE trust bundles, and proxy admin as
  secrets (`secrets-management-hygiene`); never paste private keys.
- mTLS authenticates and encrypts peers; it does **not** replace path/method
  authz, NetworkPolicy, or app authn.

## Workflow

### 1. Inventory and readiness

1. Mesh product and version (Istio sidecar/ambient, Linkerd, Consul, other).
2. Injection coverage: labels, namespaces, DaemonSet/ambient vs sidecar.
3. Current mTLS mode mesh-wide and per-namespace/workload exceptions.
4. Gateways, headless Services, multi-cluster, raw TCP/gRPC, and non-injected
   clients that still speak plaintext.
5. Observability: mTLS success metrics, proxy logs, control-plane health.

```bash
# Owned/lab cluster examples (adapt to mesh)
kubectl get peerauthentication,destinationrule -A
istioctl proxy-status   # or linkerd check / consul members
```

### 2. Target posture

| Posture | Meaning | Use |
| --- | --- | --- |
| DISABLE / off | Plaintext EW | Legacy only; short-lived |
| PERMISSIVE | Accept plain + mTLS | Transition / canary peers |
| STRICT | Require mTLS | Goal for sensitive namespaces |
| App `ISTIO_MUTUAL` / mesh mode | Client originates mTLS | Align with peer policy |

Define success: % of EW bytes on mTLS, zero plaintext on STRICT ports, SLOs held.

### 3. Stage the rollout

1. **Fix injection** on canary workloads; healthy proxies before mode change.
2. Ship **PERMISSIVE** (or mesh default accept-both) on canary namespace.
3. Align client TLS mode (`DestinationRule` `ISTIO_MUTUAL`, Linkerd identity,
   Connect intentions readiness) so traffic *can* use mTLS.
4. Verify canary **positive** (mesh→mesh OK) and **negative** (plaintext rejected
   only after STRICT).
5. Expand namespace-by-namespace; then mesh-wide STRICT when exceptions are listed.
6. Keep **versioned rollback** (prior PeerAuthentication / mesh config).

Order matters: allows and PERMISSIVE capacity **before** STRICT on live producers.

### 4. Exceptions and edge cases

| Case | Handling |
| --- | --- |
| Non-injected jobs / VMs | Inject, external workload identity, or time-boxed plain port |
| Health probes | Prefer mesh-aware probes; avoid accidental STRICT break |
| Gateway / north-south | Separate edge TLS from EW mTLS; do not conflate hops |
| Multi-cluster | Trust domain and east-west gateways before STRICT |
| TCP / DB ports | Port-level policy; document if app TLS double-wraps |

Every plaintext exception needs **owner, ports, and expiry**.

### 5. Validate and harden

1. Metrics: mTLS connection counters, 503 spikes, latency budget.
2. Controlled probes from allowed SA/identity; fail closed under STRICT.
3. Confirm no critical Deployment left unselected or uninjected.
4. Pair later with `istio-authz-basics` for deny-by-default; keep
   `kubernetes-network-policy` for L3/L4; code/policy quality →
   `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Progressive mesh mTLS enablement and STRICT cutover | **This skill** |
| AuthorizationPolicy, JWT, path/method mesh authz | `istio-authz-basics` |
| Pod NetworkPolicy / CNI L3-L4 | `kubernetes-network-policy` |
| Non-mesh client-cert mTLS design | `mtls-client-auth-basics` |
| cert-manager / ACME / private CA issuance | `cert-manager-basics` |
| Mesh CA keys, trust bundles, secret storage | `secrets-management-hygiene` |
| Cluster RBAC / broad K8s assessment | `kubernetes-pentesting` |
| Policy-as-code, tests, CI quality | `code-quality-standards` |

Keep **this skill primary** for mTLS mode cutover; hand authz to
`istio-authz-basics` and L3 segmentation to `kubernetes-network-policy`.

## Output Checklist

- [ ] Authorization/scope: cluster, mesh product/version, namespaces
- [ ] Injection coverage and non-mesh clients inventoried
- [ ] Baseline mTLS mode and DestinationRule/peer policy state
- [ ] Target STRICT (or equivalent) and success metrics defined
- [ ] Canary order: PERMISSIVE → client mutual → STRICT
- [ ] Positive/negative probe evidence; rollback documented
- [ ] Plaintext exceptions: owner, ports, expiry
- [ ] Gateway vs sidecar hop / multi-cluster trust noted if relevant
- [ ] Secrets/CA redacted; hygiene / authz / NP / cert-manager routed as needed
- [ ] Residual gaps with owner; config changes reproducible

---
name: istio-authz-basics
description: >
  Design and review Istio service-mesh authorization and peer mTLS:
  AuthorizationPolicy (ALLOW/DENY, principals, JWT, path/method),
  PeerAuthentication STRICT, deny-by-default, and common gaps. Use when
  hardening or assessing owned Istio meshes, drafting mesh authz YAML,
  debugging 403/RBAC_ACCESS_DENIED, or verifying JWT and mTLS policy —
  not for generic Kubernetes NetworkPolicy or unauthorized cluster attacks.
---

# Istio Authorization And Peer mTLS Basics

Hardening and authorized assessment of **Istio** identity-aware access:
`AuthorizationPolicy`, `PeerAuthentication` (mTLS), deny-by-default, JWT claim
rules, and HTTP path/method matches. Mesh data plane only — not NetworkPolicy.

## When To Use

| Situation | Direction |
| --- | --- |
| Write/review `AuthorizationPolicy` (ALLOW/DENY/CUSTOM) | **This skill** |
| `PeerAuthentication` STRICT / PERMISSIVE / DISABLE mTLS | **This skill** |
| Mesh deny-by-default, principal / namespace / SA rules | **This skill** |
| JWT `requestPrincipals`, claims, issuers with mesh authz | **This skill** |
| Path, method, host, header match on HTTP routes | **This skill** |
| Debug mesh 403 / `RBAC_ACCESS_DENIED` / mTLS failures | **This skill** |
| Pod L3/L4 NetworkPolicy only (no mesh identity) | `kubernetes-network-policy` |
| Cluster RBAC, secrets, node attack surface | `kubernetes-pentesting` |
| App-layer JWT abuse (tokens, alg none) | `api-auth-and-jwt-abuse` |
| Generic mTLS outside Istio | `mtls-client-auth-basics` |

## Scope And Authorization

- **In scope:** org-owned meshes, staging/lab clusters, CTF/lab Istio installs,
  or written engagements naming namespaces and policies you may change.
- **Out of scope:** third-party clusters; weakening prod STRICT mTLS or deleting
  deny policies without change window and rollback; mass probing unrelated apps.
- Prefer **config inventory + canary allows** before cluster-wide deny.
- Treat SPIFFE/serviceAccount identity, JWT signing keys, and mesh CA material
  as secrets — redact (`secrets-management-hygiene`). Mesh authz is **not**
  object-level API authz (hand IDOR to `idor-broken-object-authorization`).

## Workflow

### 1. Inventory mesh control surface

1. Confirm Istio (or ambient); note revision and data-plane mode.
2. Map injected namespaces, Services, Gateways, VirtualServices.
3. Collect `PeerAuthentication`, `AuthorizationPolicy`, `RequestAuthentication`,
   and relevant `DestinationRule`.
4. Note TLS hop (Gateway vs sidecar) — wrong hop yields false safety.

```bash
# Owned/lab cluster only
kubectl get peerauthentication,authorizationpolicy,requestauthentication -A
istioctl x authz check <pod>   # when available
```

### 2. Identity and mTLS baseline

| Control | Secure direction | Failure mode |
| --- | --- | --- |
| `PeerAuthentication` | Namespace/mesh **STRICT** | PERMISSIVE forever; plaintext EW |
| `DestinationRule` TLS | `ISTIO_MUTUAL` where needed | Mode mismatch → 503 |
| Principals | `cluster.local/ns/X/sa/Y` | `*` principals; unbound SA |
| Port exceptions | Documented, minimal | App ports left non-mTLS |

mTLS **authenticates** peers; it does not authorize methods/paths — use
`AuthorizationPolicy` for that.

### 3. Deny-by-default AuthorizationPolicy

DENY is evaluated before ALLOW. If any ALLOW policy **selects** a workload and
no rule matches, the request is denied. Workloads with **no** policy stay open
to authenticated mesh peers (subject to mTLS).

1. Add `RequestAuthentication` when end-user JWT identity is required.
2. Explicit **DENY** for unauthenticated admin or known-bad paths/methods.
3. Narrow **ALLOW** by `source.principals` / namespaces and `to.operation`
   (hosts, methods, paths, ports).
4. Prefer workload `selector` labels; avoid mesh-wide ALLOW without review.
5. Path matches need HTTP; TCP rules are port-only.

### 4. JWT, path, and method rules

| Area | Check |
| --- | --- |
| JWT | Missing token fails closed on sensitive routes |
| Issuer / aud | Match `RequestAuthentication`; no weak multi-issuer glue |
| Claims / principals | Role/tenant mapped; no `*` on admin APIs |
| Paths | Exact/prefix carefully; avoid admin path `*` overbreadth |
| Methods | Split read (GET/HEAD) vs mutate (POST/PUT/PATCH/DELETE) |
| Hosts / gRPC | Align hosts with Gateway/VS; gRPC uses full method paths |

Sidecar bypass or unselected workloads skip mesh rules — still enforce app authz.

### 5. Validate, gaps, remediate

1. **Positive:** allowed SA + path + method under STRICT succeeds.
2. **Negative:** wrong SA, missing JWT, wrong method, prefix edge cases,
   plaintext when STRICT expected.
3. **Flag:** no policy on sensitive Deployments; ALLOW without `from`; path `*`
   on admin; long-lived PERMISSIVE; authz only at Gateway while pods open;
   NetworkPolicy still needed for L3/L4.
4. Ship allows in staging, then deny; keep rollback; apply
   `code-quality-standards` to policy-as-code.

## Routing

| Need | Skill |
| --- | --- |
| Istio AuthorizationPolicy, PeerAuthentication, JWT/path rules | **This skill** |
| Kubernetes NetworkPolicy / CNI L3-L4 | `kubernetes-network-policy` |
| Cluster RBAC, secrets, broad K8s assessment | `kubernetes-pentesting` |
| App JWT attacks / token misuse | `api-auth-and-jwt-abuse` |
| Non-mesh mTLS design | `mtls-client-auth-basics` |
| Object-level API authz (BOLA) | `idor-broken-object-authorization` |
| Mesh CA / JWT secret hygiene | `secrets-management-hygiene` |
| Policy YAML / CI quality | `code-quality-standards` |

## Output Checklist

- [ ] Scope: cluster, namespaces, mesh revision recorded
- [ ] PeerAuthentication posture (STRICT vs PERMISSIVE exceptions)
- [ ] Workloads selected; deny-by-default intent clear
- [ ] ALLOW lists principals/namespaces and path/method/host limits
- [ ] JWT RequestAuthentication + claim/principal rules if used
- [ ] Positive and negative checks evidenced (403 / mTLS)
- [ ] Gateway vs sidecar enforcement hop noted
- [ ] NetworkPolicy considered when L3-L4 still required
- [ ] Secrets/CA/JWT handled per `secrets-management-hygiene`
- [ ] Residual gaps with owner/expiry; redacted evidence

## Rules

- **Owned or explicitly authorized meshes only.**
- mTLS authenticates; AuthorizationPolicy authorizes — use both.
- Unselected workloads are not mesh default-deny.
- Prefer least-privilege principals and paths; time-box wide ALLOW.
- Do not disable STRICT or drop DENY in prod without rollback.

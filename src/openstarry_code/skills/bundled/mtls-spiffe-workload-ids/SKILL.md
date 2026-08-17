---
name: mtls-spiffe-workload-ids
description: >
  SPIFFE/SPIRE workload identity for mTLS: SPIFFE IDs (spiffe:// trust domain
  path), SVIDs (X.509 and JWT), Workload API attestation, trust bundles, and
  peer ID authorization. Use when designing or reviewing SPIRE agents/servers,
  mapping Kubernetes SA/node selectors to SPIFFE IDs, wiring Envoy/Istio/gRPC
  mTLS to SVIDs, debugging SVID fetch/rotation failures, or verifying that
  services authorize on SPIFFE path not shared secrets — not for generic TLS
  reverse engineering or attacking third-party SPIRE deployments.
---

# SPIFFE / SPIRE Workload mTLS Identities

Establish **cryptographic workload identity** with SPIFFE IDs and short-lived
SVIDs so service-to-service mTLS authenticates **who** the peer is (path under
a trust domain), not a static password or long-lived client cert alone.

## When To Use

| Situation | Direction |
| --- | --- |
| Design SPIFFE IDs / trust domains / path conventions | **This skill** |
| SPIRE server, agent, registration entries, selectors | **This skill** |
| X.509-SVID or JWT-SVID issuance, rotation, Workload API | **This skill** |
| mTLS peer authn using SPIFFE URI SAN; authz on ID path | **This skill** |
| Federation / trust bundle exchange between domains | **This skill** |
| Debug empty SVID, wrong ID, bundle mismatch, agent down | **This skill** |
| Generic require-and-verify client certs (no SPIFFE) | `mtls-client-auth-basics` |
| Istio AuthorizationPolicy / PeerAuthentication only | `istio-authz-basics` |
| Public/private CA issuance without SPIRE | `cert-manager-basics` |
| TLS capture / pin RE on owned targets | `tls-plaintext-acquisition` |

## Scope And Authorization

- **In scope:** org-owned clusters and SPIRE installs, staging/lab trust domains,
  CTF/lab meshes, or written engagements that name SPIRE/SPIFFE surfaces you may
  configure or assess.
- **Out of scope:** registering false entries on production SPIRE without change
  control; exfiltrating SVIDs/bundles from systems you do not own; weakening
  attestation selectors to bypass identity in live prod without rollback.
- Prefer **lab trust domains** and non-prod agents before production registration.
- Treat SPIRE server keys, join tokens, agent sockets, SVIDs, and trust bundles
  as high-tier secrets — redact (`secrets-management-hygiene`). Identity is not
  object-level API authz (hand BOLA to `idor-broken-object-authorization`).

## Workflow

### 1. Fix the identity model

1. Choose a **trust domain** (e.g. `prod.example.org`) — stable, org-owned DNS-like
   name; avoid env-only domains that force cross-env federation by accident.
2. Define **SPIFFE ID** paths: `spiffe://<trust_domain>/<path>` (often
   `ns/<ns>/sa/<sa>` or `workload/<name>`). Document uniqueness and least privilege.
3. Prefer **X.509-SVID** for mTLS; use **JWT-SVID** when hop-by-hop TLS already
   exists and identity must ride in application credentials.
4. Map each deployable unit (SA, process, VM) to exactly one intended SPIFFE ID.

### 2. Attestation and registration (SPIRE)

| Piece | Role | Failure mode |
| --- | --- | --- |
| SPIRE Server | Issues SVIDs; holds authority | Over-broad entries; weak CA ops |
| SPIRE Agent | Node attestation; Workload API | Shared agent socket → ID steal |
| Selectors | Bind entry to k8s SA, unix user, etc. | Loose selectors → wrong SVID |
| Registration entry | SPIFFE ID + parent + selectors | Stale entry after rename |

1. Inventory server/agent versions, data store, and node attestation method.
2. Registration: parent ID (agent/node), selectors, SPIFFE ID, TTL, DNS SANs only if needed.
3. Lock Workload API socket (UID/GID, CSI driver, or equivalent); no world-readable agent sockets.
4. Rotate join tokens / bootstrap material; never bake long-lived server keys into images.

### 3. Workload consumption and mTLS

1. Workload obtains SVID + bundle via Workload API (or platform sidecar/CSI).
2. TLS stack presents X.509-SVID; validates peer against **trust bundle** and
   expected SPIFFE ID (URI SAN), not only CA signature.
3. **Authorize** on SPIFFE path (allow-list of peer IDs or path prefixes) in
   proxy policy or app middleware — mTLS alone is authn.
4. Plan **rotation**: short TTL; graceful reload; overlap so mid-flight connections
   do not fail on expiry.

### 4. Federation and multi-domain

1. Exchange **trust bundles** only over authenticated admin channels.
2. Federated peers: accept foreign trust domain IDs only where product needs
   cross-domain calls; document allowed foreign ID patterns.
3. Avoid `*` peer acceptance; prefer explicit ID or path-prefix allow-lists.

### 5. Validate and diagnose (authorized)

| Symptom | Checks |
| --- | --- |
| No SVID | Agent health, selectors match runtime, entry exists |
| Wrong SPIFFE ID | Registration path vs actual SA/labels; duplicate entries |
| Handshake fail | Bundle stale, clock skew, wrong trust domain, URI SAN missing |
| Authz 403 after mTLS | Peer ID not on allow-list; policy on wrong hop |
| ID confusion | Shared volume/socket; container escape to agent |

Positive: intended peer ID connects. Negative: wrong SA, missing SVID, foreign
domain without federation, expired SVID rejected. Apply `code-quality-standards`
when implementing verifiers and policy-as-code.

## Routing

| Need | Skill |
| --- | --- |
| SPIFFE IDs, SPIRE, SVIDs, Workload API, peer ID mTLS | **This skill** |
| Generic client-cert mTLS without SPIFFE | `mtls-client-auth-basics` |
| Istio PeerAuthentication / AuthorizationPolicy | `istio-authz-basics` |
| cert-manager / ACME / non-SPIRE issuance | `cert-manager-basics` |
| gRPC channel mTLS testing | `grpc-security-testing` |
| SVID/bundle/server key storage and rotation | `secrets-management-hygiene` |
| K8s RBAC / cluster attack surface (authorized) | `kubernetes-pentesting` |
| TLS RE / capture (owned) | `tls-plaintext-acquisition` |
| Verifier code, tests, policy CI quality | `code-quality-standards` |

Keep **this skill primary** for SPIFFE/SPIRE identity; switch for mesh YAML-only
Istio rules, non-SPIFFE cert ops, or packet-level TLS RE.

## Output Checklist

- [ ] Scope/authorization: cluster, trust domain(s), SPIRE env recorded
- [ ] SPIFFE ID scheme documented (domain + path uniqueness)
- [ ] Registration entries and selectors match real workloads (no over-broad)
- [ ] Workload API / socket exposure reviewed; join tokens protected
- [ ] X.509-SVID vs JWT-SVID choice justified; TTL and rotation known
- [ ] mTLS: peer URI SAN + trust bundle validation (not CA-only)
- [ ] Authz allow-list of peer SPIFFE IDs or path prefixes defined
- [ ] Federation/bundle exchange (if any) authenticated and minimal
- [ ] Positive/negative tests: right ID, wrong ID, expired, no SVID
- [ ] Secrets redacted; routed: Istio YAML → `istio-authz-basics`; generic mTLS →
      `mtls-client-auth-basics`; keys → `secrets-management-hygiene`; code →
      `code-quality-standards`

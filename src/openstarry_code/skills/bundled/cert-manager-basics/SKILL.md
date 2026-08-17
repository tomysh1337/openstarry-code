---
name: cert-manager-basics
description: >
  Kubernetes cert-manager basics for owned or authorized clusters: Issuer and
  ClusterIssuer design, ACME HTTP-01/DNS-01 challenges, Certificate CRDs,
  renewal and Secret delivery, and private CA issuers. Use when installing or
  reviewing cert-manager, debugging Certificate/Order/Challenge failures,
  choosing HTTP-01 vs DNS-01, automating TLS for Ingress, or issuing internal
  certs from a private CA — not for general TLS reverse engineering or attacking
  third-party ACME/DNS without authorization.
---

# cert-manager Basics

Operate and review **cert-manager** so Kubernetes workloads get correct TLS:
public ACME (Let's Encrypt and peers) or org **private CA**, with reliable
renewal into Secrets. Defensive/platform work only — not packet-level TLS RE
(`tls-plaintext-acquisition`).

## When To Use

| Situation | Direction |
| --- | --- |
| Design/review `Issuer` / `ClusterIssuer`, ACME account, solvers | **This skill** |
| `Certificate` CRDs, dnsNames/SANs, duration, renewBefore, usages | **This skill** |
| HTTP-01 ingress solver vs DNS-01 (DNS API credentials) choice | **This skill** |
| Stuck Ready=False: Order, Challenge, CertificateRequest, events | **This skill** |
| Private CA (`CA` issuer), self-signed bootstrap, intermediate chain | **This skill** |
| Renewal cadence, Secret rotation into Ingress/Gateway/app mounts | **This skill** |
| Edge headers / cipher policy only | `nginx-security-headers` |
| mTLS client trust / require-and-verify | `mtls-client-auth-basics` |
| ACME/DNS API keys or CA private keys in git | `secrets-management-hygiene` |
| HTTPS plaintext capture / pin bypass RE | `tls-plaintext-acquisition` |

## Scope And Authorization

- **In scope:** clusters, DNS zones, and ACME accounts you own or may configure;
  staging first; read-only `kubectl get/describe` under ROE; lab private CAs.
- **Out of scope:** challenges on domains you do not control; abusing stolen
  DNS credentials; weakening prod TLS without a change window; TLS RE as the
  primary goal.
- Prefer **staging ACME** until HTTP-01/DNS-01 succeed end-to-end.
- Treat ACME account keys, DNS tokens, and CA private keys as high-tier secrets;
  redact from tickets, chat, and logs. Avoid forced re-issuance (rate limits/ToS).

## Workflow

### 1. Inventory platform facts

1. cert-manager version, install method (Helm/manifests), feature gates.
2. Who may create `Certificate` vs cluster-scoped issuers (namespace isolation).
3. Ingress/Gateway controller, public DNS ownership, private-only workloads.
4. Existing TLS Secrets vs cert-manager-managed (`cert-manager.io/*` annotations).

### 2. Choose Issuer vs ClusterIssuer

| Kind | Use when |
| --- | --- |
| `Issuer` (namespaced) | Per-team/env isolation; different ACME or CA per namespace |
| `ClusterIssuer` | Shared org ACME/CA; many namespaces reference one issuer |

Use `issuerRef: { name, kind: Issuer|ClusterIssuer }`. Prefer namespaced Issuers
unless cluster-wide policy is intentional.

### 3. ACME: HTTP-01 vs DNS-01

| Challenge | Requirements | Prefer when |
| --- | --- | --- |
| **HTTP-01** | :80 reachable to solver on the auth path | Public HTTP; single-domain |
| **DNS-01** | DNS API write (or webhook) + provider Secret | Wildcards; no public :80 |

HTTP-01: match solver `ingress.class`/template to the real controller. DNS-01:
least-privilege IAM/RBAC on the DNS Secret (`secrets-management-hygiene`). Use
ACME **staging** until `Ready=True`.

### 4. Certificate CRD and Secret delivery

1. Set `secretName`, `dnsNames` (and `ipAddresses` if needed), `issuerRef`.
2. Align `duration` / `renewBefore` with org policy and CA limits (ACME ~90d;
   renewBefore often 15–30d before expiry).
3. Set `usages` (server auth, etc.) to match workload; avoid over-broad EKUs.
4. Confirm Secret is used by Ingress/Gateway/app; plan reload after renew.

### 5. Private CA path

1. Bootstrap: self-signed Issuer → CA `Certificate` → `CA` Issuer/ClusterIssuer,
   or import an existing CA key pair Secret.
2. Distribute trust anchors to clients (bundles, mesh, OS) — signing alone is not trust.
3. Separate intermediate vs root lifecycle; protect CA keys. Client mTLS identity
   mapping → `mtls-client-auth-basics`.

### 6. Diagnose failures (authorized)

```text
Certificate → CertificateRequest → Order → Challenge(s) → Secret
```

1. `kubectl describe certificate,order,challenge,certificaterequest` (in scope).
2. Controller logs: ACME/DNS API errors, rate limits.
3. HTTP-01 token path reachable? DNS-01 TXT present? CAA blocking the CA?
4. Clock skew, wrong issuerRef, two Certificates sharing one `secretName`.

### 7. Hardening and hand-off

- RBAC: who creates ClusterIssuers and reads CA/DNS Secrets.
- Charts → `helm-chart-security`; live RBAC/secrets assessment →
  `kubernetes-pentesting`. Edge policy → `nginx-security-headers`. Code →
  `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Issuer/ClusterIssuer, ACME, Certificate, renewal, private CA | **This skill** |
| ACME account key, DNS token, CA key storage/rotation | `secrets-management-hygiene` |
| mTLS client cert trust and require/verify | `mtls-client-auth-basics` |
| nginx/edge headers and TLS policy (not issuance) | `nginx-security-headers` |
| Helm install/values of cert-manager charts | `helm-chart-security` |
| Cluster RBAC / secret exposure (authorized) | `kubernetes-pentesting` |
| TLS plaintext RE / capture (owned) | `tls-plaintext-acquisition` |
| Manifests, controllers, tests quality | `code-quality-standards` |

Keep **this skill primary** for issuance automation; switch for edge policy,
mTLS identity, org secret process, or RE.

## Output Checklist

- [ ] Scope/authorization recorded (cluster, DNS zones, ACME env)
- [ ] Issuer vs ClusterIssuer justified; issuerRef correct
- [ ] ACME solver: HTTP-01 reachability or DNS-01 zone + credential hygiene
- [ ] Staging ACME proven before production issuer
- [ ] Certificate: dnsNames/SANs, duration, renewBefore, usages set
- [ ] Secret delivered to Ingress/Gateway/workload; reload path known
- [ ] Private CA: chain, trust distribution, CA key protection (if used)
- [ ] Failures traced via CertificateRequest/Order/Challenge + events
- [ ] RBAC on issuers and DNS/CA Secrets reviewed; secrets redacted
- [ ] Routed: keys → `secrets-management-hygiene`; mTLS → `mtls-client-auth-basics`;
      edge → `nginx-security-headers`; code → `code-quality-standards`

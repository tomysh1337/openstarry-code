---
name: tls-certificate-lifecycle
description: >
  Own the TLS certificate lifecycle for systems you control: key generation,
  CSR, issuance (public CA, private CA, ACME), chain assembly, deployment,
  renewal, revocation, inventory, and expiry monitoring. Use when designing or
  reviewing cert create/issue/deploy/renew/revoke flows, fixing expiry outages,
  inventorying leaf and intermediate certs, choosing ACME vs commercial CA vs
  internal PKI, or hardening private-key handling — not for unauthorized
  third-party TLS interception or general packet-level TLS reverse engineering.
---

# TLS Certificate Lifecycle

Operate **create → issue → deploy → monitor → renew → revoke** for TLS server
(and, when in scope, client) certificates on owned or authorized systems.
Defensive platform and ops work — not breaking others’ TLS.

## When To Use

| Situation | Direction |
| --- | --- |
| Key/CSR generation, SANs, key algorithm/size policy | **This skill** |
| Public CA, private CA, or ACME issuance path selection | **This skill** |
| Deploy leaf + intermediate chain; reload/hot-swap without downtime | **This skill** |
| Renewal cadence, dual-cert grace, expiry monitoring / paging | **This skill** |
| Revocation (CRL/OCSP), compromise response, re-key | **This skill** |
| Inventory of certs by host, env, owner, notAfter | **This skill** |
| Kubernetes cert-manager Issuer/Certificate automation | `cert-manager-basics` |
| Edge headers, ciphers, HSTS (not issuance) | `nginx-security-headers` |
| mTLS client trust / require-and-verify | `mtls-client-auth-basics` |
| Private key / ACME account secret storage | `secrets-management-hygiene` |
| HTTPS plaintext capture / pin bypass RE | `tls-plaintext-acquisition` |

## Scope And Authorization

- **In scope:** domains, hosts, load balancers, and CAs you own or may configure;
  staging ACME first; lab private CAs; read-only inventory under written ROE.
- **Out of scope:** issuing or validating challenges for domains you do not
  control; abusing stolen DNS/ACME credentials; intercepting third-party TLS;
  weakening prod TLS without a change window and rollback.
- Prefer **staging ACME** and canary hosts until chain and reload succeed.
- Treat private keys, ACME account keys, and CA material as high-tier secrets;
  redact PEMs and serials from tickets when policy requires. Avoid forced
  re-issuance that trips CA rate limits or ToS.

## Workflow

### 1. Inventory

| Field | Capture (no private keys in tickets) |
| --- | --- |
| Identity | CN/SANs, serial, issuer, fingerprint (SHA-256) |
| Validity | notBefore, notAfter, days remaining |
| Placement | host/LB/CDN/Ingress secret path; who reloads |
| Key | algorithm (RSA/ECDSA), size/curve; HSM/KMS vs file |
| Owner / env | team, service, test vs prod |
| State | active, dual-run, expiring, revoked, orphaned |

### 2. Create (key + CSR)

1. Generate key with org policy (prefer ECDSA P-256 or RSA ≥ 2048; document exceptions).
2. CSR: exact `dnsNames` / IPs; avoid over-broad wildcards without ownership proof.
3. Keep private key offline from tickets/chat; set filesystem mode and ownership.
4. Prefer HSM/KMS or vault-backed keys when the platform already supports them.

### 3. Issue

| Path | Prefer when |
| --- | --- |
| **ACME** (Let’s Encrypt/peers) | Public names; automate renew; HTTP-01 or DNS-01 |
| **Commercial/public CA** | Org requires branded EV/OV or long-lived policy |
| **Private CA / internal PKI** | Internal names, mTLS mesh, air-gapped |

Use ACME **staging** until Ready. DNS-01 for wildcards; least-privilege DNS API
credentials (`secrets-management-hygiene`). Kubernetes automation →
`cert-manager-basics`.

### 4. Deploy and chain

1. Serve **full chain**: leaf + intermediates; do not ship root as “required”
   unless clients need an explicit trust pin (rare for public Web PKI).
2. Match file/secret names to consumer (nginx, Envoy, app, Ingress TLS secret).
3. Plan **reload** or dual-listener swap so renew does not drop connections.
4. Verify from outside: hostname, SAN match, chain complete, clock skew.

```bash
# Owned host only
openssl s_client -connect app.example:443 -servername app.example </dev/null 2>/dev/null \
  | openssl x509 -noout -dates -subject -ext subjectAltName
```

### 5. Monitor and renew

1. Alert before expiry (common: 30/14/7 days); page on <7d for prod.
2. RenewBefore must beat deploy + ACME lag (often 15–30d for short-lived certs).
3. Dual-run only with a finite grace window; retire old cert/key on schedule.
4. After renew: confirm live notAfter, chain, and successful process reload.

### 6. Revoke and compromise

| Trigger | Action |
| --- | --- |
| Key leak / host compromise | **Revoke** at CA; re-key; redeploy; audit access |
| Wrong SAN / decommission | Revoke or let expire per policy; drop from inventory |
| Name transfer / offboarding | Stop auto-renew; revoke if still trusted externally |

Document CRL/OCSP expectations. For internal mTLS, re-key and push trust updates
rather than relying on client OCSP alone when policy demands.

### 7. Hardening hand-off

Private keys/ACME secrets → `secrets-management-hygiene`. Edge ciphers/HSTS →
`nginx-security-headers`. Client cert auth → `mtls-client-auth-basics`.
Automation/tests → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Cert create / issue / deploy / renew / revoke / inventory | **This skill** |
| cert-manager Issuer, Certificate CRD, ACME solvers on K8s | `cert-manager-basics` |
| Private key, ACME account, CA key storage and rotation | `secrets-management-hygiene` |
| nginx/edge TLS policy and security headers | `nginx-security-headers` |
| mTLS client identity and trust store | `mtls-client-auth-basics` |
| TLS plaintext RE / capture (owned) | `tls-plaintext-acquisition` |
| Config/code quality, tests, safe change | `code-quality-standards` |

Keep **this skill primary** for the end-to-end cert lifecycle; switch when the
problem is only K8s CRDs, edge ciphers/headers, mTLS identity, or RE capture.

## Output Checklist

- [ ] Scope/authorization recorded (domains, hosts, CA/ACME env)
- [ ] Inventory: SANs, issuer, notAfter, placement, owner (no private PEMs)
- [ ] Key policy met; CSR SANs match intended names only
- [ ] Issuance path justified (ACME staging proven before prod when applicable)
- [ ] Full chain deployed; external verify of SAN, dates, chain
- [ ] Reload/hot-swap path documented; dual-run retired on schedule if used
- [ ] Expiry monitors and renewBefore windows set; alert owners named
- [ ] Revoke/re-key path known for compromise; secrets redacted
- [ ] Routed: K8s automation → `cert-manager-basics`; keys → `secrets-management-hygiene`;
      edge → `nginx-security-headers`; mTLS → `mtls-client-auth-basics`; code → CQS

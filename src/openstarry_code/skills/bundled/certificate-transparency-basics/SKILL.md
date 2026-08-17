---
name: certificate-transparency-basics
description: >
  Certificate Transparency (CT) logs and Signed Certificate Timestamps (SCTs)
  for authorized recon, mis-issuance detection, and TLS evidence. Use when
  querying CT logs for hostnames, verifying SCTs in certificates or TLS
  handshakes, monitoring org domains for unexpected issuance, or documenting
  CT inclusion for compliance and incident response — not for abusing third-party
  log infrastructure or mass-harvesting unrelated Internet assets.
---

# Certificate Transparency Basics (Logs And SCT)

Work with **public CT logs** and **SCTs** so issuance is discoverable and
auditable. Owned/authorized domains, in-scope bounty assets, labs, and defensive
monitoring only — not unscoped bulk collection.

## When To Use

| Situation | Direction |
| --- | --- |
| Discover certs/SANs for in-scope domains via CT | **This skill** |
| Verify SCTs (X.509 extension, TLS handshake, or OCSP) | **This skill** |
| Alert on unexpected CA or subdomain issuance | **This skill** |
| Incident: who issued this cert / when was it logged? | **This skill** |
| Client CT policy / qualified log list awareness | **This skill** |
| ACME issuance automation in Kubernetes | `cert-manager-basics` |
| Edge TLS headers/ciphers only | `nginx-security-headers` |
| TLS plaintext capture / pin bypass RE | `tls-plaintext-acquisition` |
| Secret/key material in repos or stores | `secrets-management-hygiene` |

Do **not** use as primary for pure ACME solver debugging, cipher audits, or
general web recon without a CT angle.

## Workflow

### 1. Define scope and questions

1. List apex domains, known wildcards, and brands in scope.
2. State the goal: asset inventory, mis-issuance hunt, SCT compliance, or IR.
3. Prefer **read-only** public log queries and local cert inspection first.

### 2. Query CT for issuance evidence

Public indexes (e.g. crt.sh, Censys, org SIEM CT feeds) aggregate many logs.
For each in-scope name:

1. Collect leaf certs and precertificates: subject, SANs, issuer, notBefore/After,
   serial, fingerprint.
2. Note wildcards (`*.example.com`) and surprising subdomains or sister brands.
3. Deduplicate by fingerprint; keep **first-seen log time** vs cert `notBefore`.
4. Flag issuers outside the org allowlist or unexpected validation methods.

Treat CT hits as **hints**: DNS may no longer serve those hosts; confirm
ownership and live exposure under engagement rules before high-severity claims.

### 3. Understand SCTs and delivery

An **SCT** is a log’s promise that a (pre)certificate was or will be included.
Browsers may require SCTs from qualified logs.

| Delivery | Where you see it |
| --- | --- |
| X.509 extension | `signedCertificateTimestampList` in leaf/precert |
| TLS extension | `signed_certificate_timestamp` during handshake |
| OCSP stapling | SCT list in OCSP response |

1. On owned endpoints, capture the chain (browser, `openssl s_client`, approved scanners).
2. Record **how many** SCTs, **which** logs, and timestamp alignment with issuance.
3. Missing or insufficient SCTs may violate current client CT policy — cite the
   policy version you claim, not folklore.

### 4. Logs, Merkle trees, and inclusion (essentials)

1. Logs are append-only; entries are Merkle-tree leaves (cert or precert).
2. **Precertificates** (poison extension) let CAs obtain SCTs before final issue
   without the precert being a usable server cert.
3. Inclusion/consistency proofs audit log honesty; day-to-day recon usually stops
   at “observed in log X at time T.”
4. Prefer **qualified** public logs for client-acceptance checks; retired or
   untrusted logs do not satisfy modern CT policy.

### 5. Mis-issuance monitoring and CAA

1. Baseline known CAs, name patterns, and staging vs prod issuers.
2. Alert on: new CA, unexpected wildcard, private/internal names in public CT,
   mass reissue spikes, or lookalikes if brand scope includes them.
3. Respond: CA contact / lifecycle, revoke when required, close inventory gaps.
4. After findings, verify **CAA** DNS matches the intended CA set (CT shows what
   *was* issued; CAA constrains who *may* issue).
5. Filter noise: known ACME renewals and CDN-managed certs after allowlisting.

### 6. Evidence pack

Store query terms, raw export (redact if needed), cert PEMs or fingerprints,
SCT summary, timestamps, and live host confirmation. Keep originals immutable;
work from copies.

## Routing

| Need | Skill |
| --- | --- |
| CT log search, SCT verification, mis-issuance monitoring | **This skill** |
| cert-manager / ACME issuance in cluster | `cert-manager-basics` |
| nginx/edge TLS and security headers | `nginx-security-headers` |
| TLS capture, MITM lab, pin bypass (owned) | `tls-plaintext-acquisition` |
| Private keys, ACME account keys, CA material | `secrets-management-hygiene` |
| Broad estate recon plan | `recon-and-methodology` |
| Safe code/config for monitors or parsers | `code-quality-standards` |

Keep **this skill primary** for log/SCT work; hand off issuance automation,
edge hardening, secrets, or capture RE when those dominate.

## Output Checklist

- [ ] Authorization and domain/hostname scope recorded
- [ ] CT query terms and sources documented (index/API/log)
- [ ] Issuance set: SANs, issuers, validity, fingerprints, first-seen times
- [ ] Unexpected names/CAs/wildcards called out with evidence
- [ ] SCT presence/path (cert / TLS / OCSP) and log identities noted where checked
- [ ] Live confirmation status for high-value names (or explicit “CT-only”)
- [ ] Mis-issuance/inventory gaps with next steps (CAA, revoke, monitor)
- [ ] Redaction applied when sharing exports; secrets not dumped from PEMs
- [ ] Routed: ACME/K8s → `cert-manager-basics`; keys → `secrets-management-hygiene`;
      edge → `nginx-security-headers`; capture RE → `tls-plaintext-acquisition`

## Scope And Authorization

- **In scope:** domains/certs you own; SOW/bug-bounty assets; public CT data for
  those names; lab monitoring pipelines you operate.
- **Out of scope:** mapping/attacking third parties without permission via CT;
  DoS or abuse of log/index APIs; forging SCTs or log responses; mass scraping
  beyond engagement needs.
- Prefer **rate-limited**, cache-friendly queries; respect index ToS.
- CT is public history — still minimize publishing full SAN dumps of unreleased
  hostnames when policy requires discretion.
- CT presence is not proof of live compromise; pair with DNS/HTTP/ownership checks.

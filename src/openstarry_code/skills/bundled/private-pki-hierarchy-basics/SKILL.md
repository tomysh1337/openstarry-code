---
name: private-pki-hierarchy-basics
description: >
  Design and review private PKI hierarchies for owned or authorized environments:
  offline root CA, intermediate and issuing CAs, pathLen and name constraints,
  trust anchors, CRL/OCSP distribution, and key custody. Use when planning or
  reviewing an internal CA tree, root vs intermediate lifecycle, subordinate CA
  issuance, trust-store distribution, private hierarchy depth, or hardening
  enterprise PKI — not for public ACME-only issuance, third-party CA compromise,
  or unauthorized certificate forgery.
---

# Private PKI Hierarchy Basics

Build and review **private PKI** so internal TLS, mTLS, code signing, and device
identity rest on a clear **root → intermediate → leaf** trust chain. Focus is
hierarchy design, constraints, and operations—not TLS RE or cert-manager alone.

## When To Use

| Situation | Direction |
| --- | --- |
| Design offline root + one or more intermediate/issuing CAs | **This skill** |
| Choose hierarchy depth, pathLenConstraint, name constraints | **This skill** |
| Separate TLS server, client/mTLS, and code-signing issuing CAs | **This skill** |
| Root/intermediate lifecycle, re-sign, rollover, decommission | **This skill** |
| Trust-anchor distribution to OS, browsers, meshes, devices | **This skill** |
| CRL, OCSP, AIA/CDP URLs, offline-root operational model | **This skill** |
| Review over-broad subordinate CA rights or missing EKU/keyUsage | **This skill** |
| Public ACME / cert-manager Issuer automation only | `cert-manager-basics` |
| Client mTLS verify/require mapping | `mtls-client-auth-basics` |
| CA private keys, HSM pins, vault layout | `secrets-management-hygiene` |
| Edge TLS policy / headers (not hierarchy) | `nginx-security-headers` |

## Workflow

### 1. Inventory trust needs

1. Record environments, apps, and cert purposes (server TLS, client mTLS, mesh,
   device, code signing).
2. List existing private roots, intermediates, mixed public trust, and where
   anchors live (OS store, images, mesh, MDM).
3. Note issuance volume, online vs offline needs, and compliance (audit, dual
   control, key custody).

### 2. Choose hierarchy shape

| Layer | Role | Custody |
| --- | --- | --- |
| **Root CA** | Trust anchor; signs intermediates only | Offline HSM/air-gapped; rare use |
| **Intermediate / policy CA** | Optional policy or region layer | Restricted online or offline |
| **Issuing CA** | Signs end-entity certificates | Online HSM/KMS; high availability |
| **Leaf** | Workload, user, device, or code identity | Short-lived where possible |

Prefer **two-tier** (root + issuing) for small estates; **three-tier** when
regions, BU isolation, or policy CA separation is required. Avoid deep trees
without need—each extra CA increases ops and trust-store cost.

### 3. Constrain subordinates

1. **basicConstraints:** CA=true only on CAs; leaves CA=false.
2. **pathLenConstraint** so intermediates cannot mint unbounded sub-CAs (often
   pathLen=0 on the issuing CA under the root).
3. **nameConstraints** (permitted/excluded DNS, IP, directory names) when a
   subordinate serves a bounded namespace—test client support.
4. Restrict **keyUsage** / **EKU** on issuing CAs and profiles (serverAuth vs
   clientAuth vs codeSigning)—no “do everything” CAs.
5. Prefer distinct issuing CAs per purpose over one multi-EKU mega-CA.

### 4. Keys, algorithms, and profiles

1. Root/intermediate: RSA-4096 or P-384 (or org-approved); HSM/KMS; never CA
   keys in git or shared disk.
2. Leaf: shorter lifetimes; automate reissue; align with workload loaders.
3. Profiles: required SANs, validity, SKI/AKI, unique serials; ban weak
   signatures (MD5/SHA-1).
4. Plan **AIA** (caIssuers) and **CDP/OCSP** URLs reachable by clients; offline
   root may omit OCSP.

### 5. Operate root and intermediates

1. Root stays offline except scheduled intermediate issuance, CRL signing (if
   root signs CRLs), and planned rollover.
2. Dual control for root ceremonies; log who, when, and what.
3. Intermediate compromise: revoke, re-issue under root, redistribute chains;
   root compromise forces full re-anchor and emergency IR.
4. Overlap validity during rollover so clients hold old and new anchors/chains.

### 6. Distribute trust and verify chains

1. Ship **root** (and needed intermediates) to trust stores; apps must present
   full chain to a known anchor—signing alone is not trust.
2. Validate sample leaves (OpenSSL/`certutil`): path, EKU, expiry, revocation.
3. K8s issuance automation → `cert-manager-basics` (this skill for CA tree);
   client identity → `mtls-client-auth-basics`; keys/IR →
   `secrets-management-hygiene`; code → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Private root/intermediate tree, pathLen, name constraints, CA lifecycle | **This skill** |
| cert-manager Issuer/Certificate automation | `cert-manager-basics` |
| mTLS client trust and require-and-verify | `mtls-client-auth-basics` |
| CA key / HSM / vault custody and leak IR | `secrets-management-hygiene` |
| Edge TLS ciphers/headers (not CA design) | `nginx-security-headers` |
| Public ACME challenge debugging only | `cert-manager-basics` |
| Manifests, scripts, config quality | `code-quality-standards` |

Keep **this skill primary** for hierarchy design and CA constraints; hand off
issuance automation, mTLS app config, and secret process as above.

## Output Checklist

- [ ] Authorization and environments in scope recorded (owned/authorized only)
- [ ] Trust purposes inventoried (server, client, code, device) and mapped to CAs
- [ ] Hierarchy diagram: root → intermediate(s) → issuing → leaf
- [ ] Root offline custody and ceremony process documented
- [ ] pathLenConstraint and nameConstraints set where applicable
- [ ] Issuing CAs split or constrained by keyUsage/EKU and purpose
- [ ] AIA/CDP/OCSP reachability and CRL/OCSP update cadence defined
- [ ] Algorithms and leaf lifetimes meet policy; no weak signatures
- [ ] Trust-anchor distribution plan for OS, mesh, images, devices
- [ ] Rollover and intermediate-compromise playbooks drafted
- [ ] Routed: automation → `cert-manager-basics`; mTLS → `mtls-client-auth-basics`;
      keys → `secrets-management-hygiene`; code → `code-quality-standards`
- [ ] Secrets, passphrases, and private keys redacted from reports

## Scope And Authorization

- **In scope:** Private CAs and hierarchies you own or are authorized to design,
  operate, or review; lab/root ceremonies; trust-store changes on owned systems;
  read-only review of certs, CRLs, and CA config under ROE.
- **Out of scope:** Forging certificates for third parties; attacking public CAs;
  installing rogue roots on systems you do not control; weakening production
  trust without an approved change window; TLS traffic decryption as the goal.
- Prefer non-prod for experiments. Gate root ceremonies, online CA key export,
  and mass trust-store pushes. Redact private keys, HSM credentials, and
  enrollment secrets from tickets, chat, and logs.
- Do not treat “internal network” alone as authorization to reissue production
  intermediates or replace enterprise trust anchors.

---
name: dnssec-deployment-basics
description: >
  Deploy and operate DNSSEC on zones you own or are authorized to manage: key
  models (KSK/ZSK or CSK), signing algorithms, DS publication at the parent,
  chain-of-trust validation, key rollover, NSEC/NSEC3, and failure triage.
  Use when enabling DNSSEC, fixing BOGUS/SERVFAIL after signing, publishing or
  rotating DS/CDS/CDNSKEY, planning algorithm or key rollovers, choosing NSEC
  vs NSEC3, or verifying resolver validation for org-owned DNS — not for
  attacking third-party zones or DNSSEC denial research without authorization.
---

# DNSSEC Deployment Basics

Sign and maintain **DNSSEC** so resolvers can authenticate answers for zones
you control. Focus on chain of trust, safe rollovers, and operational checks.

## When To Use

| Situation | Direction |
| --- | --- |
| Enable DNSSEC on an authoritative zone (BIND, Knot, PowerDNS, cloud DNS) | **This skill** |
| Choose KSK+ZSK vs CSK; algorithm (ECDSA P-256, Ed25519) and key sizes | **This skill** |
| Publish DS at registrar/parent; CDS/CDNSKEY automation | **This skill** |
| Key/algorithm rollover; RRSIG and DS dual-publish timing | **This skill** |
| NSEC vs NSEC3; opt-out and iteration pitfalls | **This skill** |
| BOGUS, SERVFAIL, missing DS, clock skew, stale RRSIG after deploy | **This skill** |
| Edge TLS / HTTP headers only (no DNS integrity) | `nginx-security-headers` |
| ACME DNS-01 tokens and zone API credentials | `cert-manager-basics`, `secrets-management-hygiene` |
| DNS rebinding / app SSRF via hostname | `dns-rebinding-attacks` |
| Packet/PCAP protocol work on DNS | `NetworkProtocolAnalysisSkill` |

## Scope And Authorization

- **In scope:** DNS zones, registrars, and authoritative servers you **own** or
  may reconfigure under written ROE; lab and staging zones first.
- **Out of scope:** signing or mutating third-party zones; mass DS changes on
  domains you do not control; DNSSEC stripping on shared prod without approval.
- Prefer **staging** or low-traffic apex before production cutover. Plan registrar
  DS changes with dual-publish windows.
- Treat private keys (`.private`, HSM, cloud KMS) as secrets; redact from tickets
  and logs (`secrets-management-hygiene`).

## Workflow

### 1. Inventory zone and parent

1. Confirm authoritative NS set, SOA serial practice, and who can edit DS at the
   parent (registrar API vs registry EPP).
2. Note current DNSSEC state: unsigned, partially signed, or validating BOGUS.
3. List RR types that must stay available during rollout (MX, ACME TXT, CDN).
4. Clean orphan parent DS for dead keys before re-signing.

### 2. Choose key model and algorithm

| Model | Use when |
| --- | --- |
| **KSK + ZSK** | Separate infrequent KSK (DS) from frequent ZSK (zone RRSIGs) |
| **CSK** (single key) | Smaller zones / providers that only expose one signing key |

Prefer **ECDSAP256SHA256** or **ED25519** where software and parent allow; avoid
weak algorithms on new zones. Align TTL/RRSIG validity with rollover windows.

### 3. Sign the zone (authoritative)

1. Generate keys offline or via managed DNSSEC (HSM/KMS when available).
2. Enable signing: publish DNSKEY + RRSIGs for relevant RRSets; include NSEC or
   NSEC3 for denial-of-existence.
3. Ensure secondaries receive signed data (AXFR/IXFR or provider replication)
   before advertising DS.
4. Raise SOA serial; verify all NS answer consistently against **your**
   authorities before relying on public validating resolvers.

### 4. Publish DS and complete the chain

1. From the KSK/CSK DNSKEY, compute **DS** (digest type 2 SHA-256 preferred when
   parent supports it; publish what the parent accepts).
2. Submit DS at registrar/parent; wait for parent propagation.
3. Optional: publish **CDS/CDNSKEY** if parent consumes them for automated DS.
4. Only after DS is visible in the parent, treat the zone as fully enrolled.

### 5. Validate end-to-end

```text
Root → TLD DS/DNSKEY → parent DS → child DNSKEY → RRSIGs on data
```

1. Query with a validating resolver (`delv` / `dig +dnssec +multi`) for apex, a
   subdomain, and a known-nonexistent name (NSEC/NSEC3 proof).
2. Expect **AD** on success when DO is set; investigate BOGUS/SERVFAIL before
   blaming application clients.
3. Confirm multi-NS consistency and parent NS/glue still match.

### 6. Rollover without breaking validators

1. **ZSK:** pre-publish new DNSKEY → sign with new ZSK → remove old after
   max(RRSIG lifetime, TTL) margin.
2. **KSK/CSK:** dual-publish DNSKEYs → add new DS before removing old → wait
   parent+resolver caches → retire old key.
3. **Algorithm:** dual signatures and dual DS until caches expire; never drop
   the only validating path early.
4. Document calendar, owners, and registrar contact for emergency DS revert.

### 7. NSEC vs NSEC3 and ops hygiene

| Choice | Notes |
| --- | --- |
| **NSEC** | Simpler; zone walking possible — often fine for public SaaS zones |
| **NSEC3** | Raises enumeration cost; keep iterations modest; salt policy |

Monitor RRSIG expiry, failed transfers, and DS mismatches. Protect private keys
and DNS API tokens. Zone automation code → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| DNSSEC enable, DS, rollover, NSEC/NSEC3, validation triage | **This skill** |
| DNS API keys, KSK material, HSM/KMS secrets lifecycle | `secrets-management-hygiene` |
| ACME DNS-01 / cert automation using the zone | `cert-manager-basics` |
| nginx/edge TLS policy (not DNS authenticity) | `nginx-security-headers` |
| DNS rebinding application risks | `dns-rebinding-attacks` |
| PCAP / deep DNS protocol tooling | `NetworkProtocolAnalysisSkill` |
| Safe change practice for zone automation code | `code-quality-standards` |

## Output Checklist

- [ ] Owned/authorized zone and parent DS path recorded; staging preferred first
- [ ] Key model (KSK/ZSK or CSK) and algorithm chosen and documented
- [ ] Zone signed; all NS serve consistent DNSKEY + RRSIGs + NSEC/NSEC3
- [ ] DS (or CDS/CDNSKEY path) published at parent; digest type recorded
- [ ] Validating resolver shows AD for positive data; denial proofs work
- [ ] No orphan/mismatched DS; multi-NS and parent NS glue checked
- [ ] Rollover plan: dual-publish windows, TTLs, RRSIG lifetimes, owners
- [ ] Private keys and DNS API credentials via `secrets-management-hygiene`
- [ ] Residual risks noted (algorithm support, NSEC walk, registrar lag)
- [ ] Helpers routed only when needed (ACME, edge TLS, PCAP, CQS)

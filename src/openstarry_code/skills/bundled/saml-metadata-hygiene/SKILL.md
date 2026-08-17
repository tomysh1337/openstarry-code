---
name: saml-metadata-hygiene
description: >-
  SAML 2.0 metadata trust and hygiene for owned or authorized SP/IdP
  integrations: EntityID pinning, signing-certificate import, ACS/SSO endpoint
  allowlists, metadata URL fetch controls, expiry/rotation, and admin dual
  control. Use when reviewing federation metadata XML, IdP/SP metadata upload
  or auto-refresh, certificate rollover, or trust-store hygiene — not for
  attacking third-party IdP production outside engagement scope.
---

# SAML Metadata Hygiene

Review **how SAML metadata is obtained, validated, stored, and rotated** so
SP/IdP trust anchors stay intentional. Complements runtime checks in
`saml-sso-basics`; this skill owns the **metadata trust plane**.

## When To Use

- Importing or auto-refreshing **IdP/SP metadata** (XML file, URL, vendor UI)
- Reviewing **EntityID**, signing/encryption certs, ACS, and SSO endpoint lists
- Certificate **rollover**, dual-cert windows, or expired metadata/certs
- Hardening admin paths that upload metadata or change federation trust
- Keywords: SAML metadata, EntityDescriptor, KeyDescriptor, metadata URL, cert pin

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Runtime SAMLResponse signature, Audience, ACS acceptance | `saml-sso-basics` |
| Private key / vault / rotation for signing material | `secrets-management-hygiene` |
| SP library code, parsers, config-as-code quality | `code-quality-standards` |
| OAuth/OIDC client registration | `oauth-oidc-misconfiguration` |
| Deep SSRF via metadata URL | `ssrf-server-side-request-forgery` |

## Scope And Authorization

- **In scope:** org-owned SP/IdP apps, staging federation, labs/CTFs, written
  assessments that name the SP and any IdP/tenant you may reconfigure.
- **Out of scope:** swapping metadata on third-party SaaS IdPs you do not own;
  publishing live signing keys or production `SAMLResponse` blobs.
- Prefer **staging** for cert swap and metadata-URL experiments; dual-review prod.
- Treat signing **private** keys as secrets — redact; rotate on exposure
  (`secrets-management-hygiene`). Assessment only — no workforce SSO outages.

## Workflow

### 1. Inventory federation trust

Record role (SP/IdP), EntityIDs (env-separated), metadata source (upload/URL/IaC),
refresh policy, signing policy (Response/Assertion/both), ACS/SSO URLs + bindings,
and who can change trust. Download only from **authorized** endpoints; keep
originals immutable.

### 2. Validate document integrity

1. Confirm well-formed `EntityDescriptor` from the expected peer — not an
   unauthenticated paste from chat.
2. If metadata is **signed**, verify with a **pre-established** trust anchor.
   Do not bootstrap trust solely from a key inside the same untrusted file.
3. Use SAML-aware, XXE-safe parsers; implement loaders under `code-quality-standards`.

### 3. Pin EntityID and endpoints

| Control | Secure direction | Weak outcome |
| --- | --- | --- |
| EntityID | Exact match; separate per env | Accept any; shared prod/dev |
| ACS (SP) | Exact URL allowlist at IdP | Wildcards; attacker ACS |
| SSO / SLO (IdP) | HTTPS; host allowlist on SP | HTTP; open-ended endpoints |
| Bindings | Only needed bindings enabled | Unused Artifact/SOAP exposed |

Cross-check UI vs metadata vs IaC so drift cannot reintroduce stale ACS/EntityIDs.

### 4. Certificate and KeyDescriptor hygiene

1. Import **signing** certs from trusted metadata only; runtime must **pin** IdP
   signing cert(s) and ignore untrusted in-message `KeyInfo` (`saml-sso-basics`).
2. Record thumbprint/SKI, validity, key usage, algorithm (RSA-2048+ or org-approved).
   Flag expired certs still trusted; encryption vs signing confusion; multi-cert bags.
3. Rollover: dual-cert window → verify SSO → retire old; document owners/SLA.
4. **Private** keys never in metadata. Key lifecycle → `secrets-management-hygiene`.

### 5. Metadata URL auto-refresh (if used)

| Check | Expectation |
| --- | --- |
| Transport | HTTPS; valid server cert; no cleartext fallback |
| Destination | Allowlisted host/path; admin-auth for URL changes |
| SSRF | Block link-local, cloud metadata IPs, internal ranges unless explicit |
| Integrity | Signed metadata + pin, or thumbprint compare on change |
| Change control | Alert on EntityID/ACS/cert delta; approve high-impact diffs |
| Failure mode | Fail closed; bounded refresh; no empty trust on error |

Deep SSRF → `ssrf-server-side-request-forgery`. Here: allowlist + fail-closed.

### 6. Admin controls, verify, remediate

1. Trust edit: strong admin auth, audit (who/when/thumbprint/EntityID), dual
   control for production; no private keys in git.
2. After trust change: happy-path SSO as test user; reject attacker-signed
   cert/metadata (`saml-sso-basics`).
3. Remediation: pin EntityID + signing certs from trusted import; exact ACS/SSO
   allowlists; HTTPS; env-separated EntityIDs; dual-cert rollover; fail closed
   on refresh/parse errors; implement under `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Metadata import, cert pin, ACS/EntityID allowlist, refresh | **This skill** | — |
| Runtime signature, Audience, Destination, ACS acceptance | `saml-sso-basics` | this skill for trust anchors |
| Signing private keys, vault, rotation, leak IR | `secrets-management-hygiene` | this skill for public cert path |
| SP/IdP code, XML parser hardening, config modules | `code-quality-standards` | this skill for federation policy |
| Metadata URL as SSRF | `ssrf-server-side-request-forgery` | this skill for allowlist/fail-closed |

### Required helpers

- **`saml-sso-basics`:** prove runtime still enforces pinned certs, audience, ACS.
- **`secrets-management-hygiene`:** private key lifecycle; never commit signing keys.
- **`code-quality-standards`:** safe metadata loaders, pin/allowlist tests, no secret logs.

## Output Checklist

- [ ] Authorization covers SP and any IdP/tenant/metadata URL exercised
- [ ] EntityIDs, ACS/SSO, bindings, source, refresh policy recorded
- [ ] Metadata integrity: signed? verified against which anchor?
- [ ] Signing cert inventory: thumbprints, validity, signing vs encryption
- [ ] Pinning confirmed: runtime ignores untrusted KeyInfo (SSO tests)
- [ ] Auto-refresh: HTTPS, allowlist, fail-closed, change alerts (or N/A)
- [ ] Admin dual control / audit; no private keys in metadata/git/tickets
- [ ] Post-change SSO + reject attacker cert (`saml-sso-basics`)
- [ ] Secrets via `secrets-management-hygiene`; code via `code-quality-standards`
- [ ] Residual risks (vendor-only UI, long dual-cert windows) documented

## Rules

- Metadata is a **trust control plane** — wrong import equals attacker IdP.
- Public certs in metadata are normal; **private** keys are never metadata.
- Prefer exact allowlists; separate environments by EntityID; fail closed on refresh.
- Authorized/org-owned only; redact keys/assertions; pair claims with `saml-sso-basics`.

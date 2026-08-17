---
name: saml-nameid-format-pitfalls
description: >-
  SAML 2.0 NameID format pitfalls for authorized SP/IdP review: email vs
  persistent vs transient identity keys, Format attribute mismatch, mutable
  subject linking, SPNameQualifier confusion, and account-merge ATO paths.
  Use when SAML Subject/NameID, NameIDPolicy, or post-ACS account linking is
  in scope and wrong principal binding or format drift is suspected.
---

# SAML NameID Format Pitfalls

How the SP **chooses, compares, and links** SAML `NameID` after trust checks.
Complements `saml-sso-basics`; this skill owns **subject identity semantics**.

## When To Use

- SP maps users from `NameID` (email, UUID, UPN) or treats Format loosely
- IdP / `NameIDPolicy` advertise one Format; ACS accepts another
- Account linking: auto-create, email match, re-login rename
- Keywords: NameID, NameIDPolicy, persistent, transient, emailAddress,
  unspecified, SPNameQualifier, NameQualifier, subject, account merge

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Signature, Audience, Destination, ACS | `saml-sso-basics` |
| Signature wrapping / wrong identity node | `saml-signature-wrapping-awareness` |
| Metadata cert pin / EntityID allowlists | `saml-metadata-hygiene` |
| EncryptedAssertion crypto order | `saml-assertion-encryption` |
| Multi-vector ATO / post-ACS SID reuse | `account-takeover-methodology` / `session-fixation-management` |

## Scope And Authorization

- **Authorized only:** owned SP apps, labs/CTFs, or written scope naming the SP
  and any IdP/tenant driven with dual test users. Prefer staging federation.
- No third-party IdP production abuse, workforce identities, or stolen assertion
  replay. Redact emails/employee/persistent IDs publicly; ACS offline. No SSO outages.

## Workflow

### 1. Inventory NameID contract

| Field | Capture |
| --- | --- |
| Requested Format | `NameIDPolicy Format` in AuthnRequest (if any) |
| Issued Format | `NameID Format=` on Subject |
| Value shape | email, UUID, UPN, opaque, empty |
| Qualifiers | `NameQualifier`, `SPNameQualifier`, `SPProvidedID` |
| SP lookup key | external id column / email unique index |
| Linking policy | auto-create, match-by-email, admin-provision only |
| Allowlist | Formats SP accepts (config / code) |

Decode authorized `SAMLResponse` offline. Record **Format URI** and raw value.

| Short Format | Semantics | Safe durable local key? |
| --- | --- | --- |
| `persistent` | Stable opaque per SP–IdP pair | Prefer |
| `emailAddress` | Mutable mailbox | Risky sole key |
| `transient` | One-shot / short-lived | Never |
| `unspecified` | IdP-defined; ambiguous | Only with strict allowlist |
| WDQN / Kerberos / X509 DN | Dir- or cert-tied | Env-specific; normalize carefully |

### 2. Format accept / reject matrix

| Probe | Secure behavior |
| --- | --- |
| Omit `Format` | Reject or documented default only |
| Wrong Format URI for same value | Reject or consistent re-key — no silent remap |
| `transient` stored as durable account id | Fail closed; no identity drift |
| `emailAddress` after IdP mailbox change | Re-verify link; no silent account swap |
| `unspecified` when policy requires persistent | Reject |
| Empty / whitespace NameID | Reject |
| Case / NFKC email variants | Document normalize; no dual-account collision ATO |

**Evidence:** valid trust path, ACS accepts, SP session principal ≠ intended map.

### 3. Qualifiers and multi-SP collision

- Persistent NameID is **per relying party**; foreign SP persistent id ≠ local.
- Scope join keys by IdP EntityID (+ SP EntityID for multi-app).
- Do not ignore `SPNameQualifier` / `NameQualifier` when multi-IdP or multi-SP.
- Global unique email without IdP scope → cross-tenant / cross-IdP merge risk.
- Caching `transient` as username → identity drift across sessions.

### 4. Account linking and ATO chains

With dual users you control:

1. Pre-create local user email E; SAML NameID E without extra proof → note if
   SP requires invite/verified link.
2. IdP user A asserts victim email **only when you control both sides in lab**
   → unverified email link = ATO-class finding.
3. Rename NameID on second login → duplicate, orphan, or stolen row?
4. AuthZ must not prefer unsigned/secondary attrs (`mail`, `uid`) over signed
   Subject (`saml-sso-basics`). High-impact merge → `account-takeover-methodology`.
   ACS SID reuse → `session-fixation-management`.

### 5. Alignment and remediation

1. Align AuthnRequest `NameIDPolicy`, IdP config, SP allowlist, and DB key.
2. Prefer **persistent** opaque external id; email as contact with verified change.
3. Reject unknown Formats; never default `unspecified` → email guess.
4. Implement under `code-quality-standards`: Format allowlist, normalize unit
   tests, scoped keys, no bare string-concat identity.
5. Log Format + redacted subject hash on failures — not raw PII NameIDs at info.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| NameID Format, linking, mutable subject keys | **This skill** | — |
| Signature / Audience / ACS / Destination | `saml-sso-basics` | this after trust holds |
| Verified node ≠ loaded NameID | `saml-signature-wrapping-awareness` | this for subject choice |
| Metadata NameIDFormats vs runtime | `saml-metadata-hygiene` | this for ACS mapping |
| Merge → full ATO narrative | `account-takeover-methodology` | this for subject proof |
| Session id reuse across ACS | `session-fixation-management` | — |
| SP mapping code and tests | `code-quality-standards` | this for policy |

**Selection:** primary when the bug is **who the SP thinks the subject is**
(Format/value/qualifiers), not whether the assertion was signed for this SP.

## Output Checklist

- [ ] Authorization covers SP and dual test users / lab IdP
- [ ] NameIDPolicy, Format URI, value shape, qualifiers; SP join key / linking policy
- [ ] Format matrix: omit, wrong URI, transient-as-durable, unspecified, empty
- [ ] Email/mutable key, rename, qualifier/multi-IdP/SP scope, merge probes
- [ ] Attrs vs NameID precedence; impact; allowlist/persistent/scoped-key remediation
- [ ] Secrets redacted; trust issues paired with `saml-sso-basics`

## Rules

- Dual-account or lab IdP proof required — not theory alone.
- `transient` is never a durable account primary key; email NameID is often mutable.
- No ATO claim without SP session bound to the unintended principal.
- Authorized targets only; redact subject identifiers in public reports.

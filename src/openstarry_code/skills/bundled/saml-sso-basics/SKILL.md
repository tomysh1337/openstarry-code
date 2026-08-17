---
name: saml-sso-basics
description: >-
  High-level authorized assessment of SAML SSO misconfigurations: signature
  validation, assertion/response signing, audience restriction, ACS URL
  handling, and related SP/IdP trust issues. Use when enterprise SAML login,
  Assertion Consumer Service, or SAMLResponse parameters appear in scope.
---

# SAML SSO Basics (Authorized Assessment)

High-level methodology for **SAML 2.0** service-provider (SP) and in-scope identity-provider (IdP) integrations. Focus: signature trust, audience, ACS, and assertion acceptance — not a full cryptographic break toolkit.

## Use When

| Situation | Direction |
| --- | --- |
| App offers **SAML SSO**, enterprise login, or “Login with company IdP” | **This skill** |
| Traffic shows `SAMLRequest`, `SAMLResponse`, `RelayState`, ACS endpoints | **This skill** |
| Need SP checklist: signature required?, `Audience`/`Recipient`, destination | **This skill** |
| OAuth/OIDC “Sign in with…” (not SAML) | `oauth-oidc-misconfiguration` |
| JWT access tokens after SSO, without SAML XML issues | `api-auth-and-jwt-abuse` |
| Cookie session not rotated after SAML ACS | `session-fixation-management` |
| Multi-vector ATO including SAML as one surface | `account-takeover-methodology` + this for SAML depth |
| Attacking commercial SaaS IdP production outside engagement | **Out of scope** |

Keywords: SAML, SSO, ACS, Assertion Consumer Service, SAMLResponse, IdP metadata, EntityID, Audience, Signature wrapping (awareness), unsigned assertion.

## Scope And Authorization

- **Authorized assessments only**: owned apps, labs, CTFs, or written engagement scope that names the SP and any IdP/tenant you may test.
- Prefer **test IdP** or customer-authorized staging IdP. Do **not** attack third-party IdP production (Okta, Azure AD, Google, etc.) beyond the **SP’s** configuration mistakes and any IdP app **explicitly** in scope.
- Use dual test identities (IdP user V and attacker-controlled IdP user A) when federation allows. Never replay stolen production assertions from real employees.
- Treat `SAMLResponse`, assertions, session cookies, and metadata signing keys as **secrets**: redact; store offline; do not publish raw Base64 responses with live signatures in public write-ups.
- This skill is **assessment methodology**. Do not use it to deploy persistent backdoors, mass-create IdP users, or disrupt production SSO for all employees.
- XML signature crypto research beyond configuration flaws (e.g. novel CVE exploit development against third-party products) needs separate authorization and is outside this basics skill.

## Core Model

```text
User → IdP authenticates → IdP issues SAML Response/Assertion
  → Browser POST/Redirect to SP ACS
  → SP validates signature, conditions, audience, recipient/destination
  → SP establishes local session for NameID / attributes
```

| Trust control | Failure mode (high-level) | Impact class |
| --- | --- | --- |
| **Signature on Response and/or Assertion** | Accept unsigned or partially signed; sign wrong node | Forge identity → ATO |
| **Signing key / cert trust** | Trust any cert in message; weak metadata import | Attacker signs as “IdP” |
| **Audience (`AudienceRestriction`)** | Missing or wrong EntityID accepted | Token confusion / cross-SP |
| **Recipient / Destination / ACS** | Assertion accepted at wrong ACS or open redirect-like ACS | Cross-app or token theft |
| **Conditions time (`NotBefore`/`NotOnOrAfter`)** | No skew check; infinite validity | Replay |
| **Subject confirmation** | Bearer conf without binding checks where required | Replay / mix-up |
| **NameID / attributes** | SP trusts mutable attrs for authZ without provisioning rules | Privilege confusion |
| **RelayState** | Open redirect after SSO | Post-login phishing hop |

**Good proof:** Controlled mutation of an **in-scope** SAML flow yields SP session as a principal you should not obtain (e.g. unsigned assertion accepted for V; audience for SP-B accepted on SP-A), with request/response evidence.  
**Bad proof:** “SAML exists”; missing HTTP-only flags alone; theoretical wrapping without SP accepting a crafted message you demonstrated in lab/scope.

## Workflow

### 1. Map the SAML deployment

Record:

| Field | Capture |
| --- | --- |
| SP EntityID | From metadata or config UI |
| ACS URLs | HTTP-POST and HTTP-Redirect bindings |
| IdP EntityID / SSO URL | In-scope IdP only |
| Metadata source | Static XML, URL fetch, vendor UI |
| What is signed | Response, Assertion, both; encrypted assertion? |
| NameID format | email, persistent, transient |
| Attribute → role mapping | groups, admin flags |
| SP session | cookie name; regenerate on ACS? |

Download **SP metadata** and **IdP metadata** only from authorized endpoints. Note `WantAssertionsSigned`, signing certs, and ACS list.

Typical browser trace:

```text
GET  /saml/login → redirect to IdP SSO with SAMLRequest
POST IdP login
POST SP ACS  SAMLResponse=...&RelayState=...
Set-Cookie: session=...
```

Decode `SAMLRequest`/`SAMLResponse` (Base64, often deflated for Redirect binding) in a local tool or Burp SAML extension — **offline**, on copies of traffic you are allowed to capture.

### 2. Baseline happy path

1. Complete SSO as test user V.
2. Save raw ACS POST (redact later).
3. Confirm local session identity (email, user id).
4. Note whether a **pre-ACS** anonymous cookie is rotated (`session-fixation-management` if not).

### 3. Signature validation (primary)

High-level tests against the **SP** (authorized lab/staging preferred):

| Probe | Idea | Expected secure behavior |
| --- | --- | --- |
| Strip signature | Remove `ds:Signature` from Response/Assertion | Reject |
| Strip assertion sig only | Response signed, assertion unsigned (if SP wants assertion signed) | Reject if policy requires assertion sig |
| Empty signature / broken digest | Corrupt `DigestValue` or `SignatureValue` | Reject |
| Comment / whitespace tweaks | XML same-doc variations | Still validate correctly or reject; no auth bypass |
| Re-sign with attacker cert | Embed attacker `KeyInfo` and signature | Reject unless SP pins IdP cert from metadata |
| Partial signing | Sign outer Response but alter unsigned Assertion (if only response checked poorly) | Must not accept altered subject |

Document **exactly** which element the SP requires signed. Many real bugs are “signature present anywhere” or “verify signature but parse different node than verified” (signature wrapping **awareness**):

- **Awareness only:** classic wrapping places a signed assertion alongside an unsigned malicious assertion; broken SP verifies one and loads the other.
- In authorized tests, use established lab payloads or carefully controlled duplicates **only** on systems you may test; prove with dual NameIDs (benign signed vs attacker-controlled).
- Do not claim wrapping without showing SP session attributes match the **unverified** node.

If encryption (`EncryptedAssertion`) is used, note whether SP decrypts then skips signature checks — still require signature on enclosing response or decrypted assertion per deployment policy.

### 4. Audience restriction

Inspect `AudienceRestriction` / `Audience` in the assertion:

| Probe | Idea |
| --- | --- |
| Missing Audience | SP accepts any? |
| Wrong Audience | EntityID of another app or attacker value |
| Multiple Audience values | SP checks only first; include both legit and foreign |
| Typo / trailing slash / HTTP vs HTTPS EntityID | Parser mismatch |

**Secure baseline:** SP requires Audience to match **this SP’s EntityID** (exact, per metadata).  
**Finding:** SP accepts assertion minted for another audience or with audience omitted → cross-service token acceptance risk (severity depends on who can obtain such assertions — usually needs compromised/evil IdP app registration or multi-SP IdP abuse **in scope**).

### 5. ACS, Destination, and Recipient

| Control | Where | Test |
| --- | --- | --- |
| **ACS URL** | Where browser sends `SAMLResponse` | Can Response be POSTed to a different path/host still processed? |
| **Destination** | Response attribute | Mismatch with actual ACS — should fail |
| **Recipient** | SubjectConfirmationData | Should match ACS |
| **ACS open redirect** | Registration of ACS in IdP | If SP allows ACS on attacker host via config flaw, codes/assertions go to attacker |

Probes (authorized):

1. Replay valid `SAMLResponse` to alternate path on same host (`/saml/acs` vs `/saml/acs2`).
2. Change Host/XFH only if Host skill is in scope — SP must not trust client Host for Audience/ACS decisions (`http-host-header-attacks` helper).
3. Confirm IdP-registered ACS list is **exact match** (no subdomain or path prefix wildcards you control).

### 6. Replay, lifetime, and binding

| Check | Action |
| --- | --- |
| Replay | Resubmit same `SAMLResponse` to ACS; second should fail (one-time) if SP tracks IDs |
| Expired | Wait or adjust `NotOnOrAfter` (re-sign only if you control IdP signing in lab) | SP rejects outside window + skew |
| InResponseTo | Missing/wrong correlation to `SAMLRequest` id | SP should bind login flow |
| HTTP-Redirect vs POST | Large responses; tampering visibility | Prefer POST + signature; document weak binding |
| RelayState | `RelayState=https://attacker.tld/` | Open redirect after SSO → `open-redirect` |

Do not brute-force or spam ACS in production; one replay pair is enough evidence.

### 7. NameID, attributes, and provisioning

After a valid signature path (or if SP skips signature — critical):

| Risk | Test (authorized dual users) |
| --- | --- |
| Attribute injection | If you control IdP attributes for A, set `admin=true` / groups | SP must map from trusted IdP claims with allowlists |
| NameID change on re-login | Persistent vs email NameID account linking | Linking to existing password account without proof → ATO chain |
| Unsigned attr statement | Attrs outside signed assertion | Must not affect authZ |
| Account linking | SAML email matches local user | Confirm verification rules; pair with `account-takeover-methodology` |

### 8. Metadata and SP configuration hygiene

| Area | What to verify |
| --- | --- |
| IdP cert pin | SP stores IdP signing cert from trusted metadata import — not “any KeyInfo” |
| Metadata URL fetch | If SP fetches IdP metadata by URL, SSRF risk → `ssrf-server-side-request-forgery` |
| TLS to IdP | Metadata and SSO over HTTPS |
| Dual control | Admin UI to upload new IdP cert requires strong auth (admin ATO is separate) |
| Logout (SLO) | Optional; signed LogoutRequest validation if exposed |

### 9. Session establishment after ACS

1. Compare session cookie pre- and post-ACS (`session-fixation-management`).
2. Map SP session user to assertion NameID — mismatch is a finding.
3. If SP mints JWT after SAML, validate JWT path with `api-auth-and-jwt-abuse` separately.
4. CSRF on “link SAML to account” while password session active → `csrf-cross-site-request-forgery`.

### 10. Remediation guidance (report-ready)

Pair implementation notes with `code-quality-standards` where SP code is in scope:

- Require cryptographic signature on **Assertion** (and Response per policy); verify using **pinned** IdP certificates from trusted metadata — ignore untrusted `KeyInfo`.
- Validate **Audience** = SP EntityID; **Destination**/**Recipient** = this ACS URL; enforce `NotBefore`/`NotOnOrAfter` with small skew; enforce one-time assertion IDs.
- Parse XML with a SAML-aware, XXE-safe stack; never deserialize untrusted DTD (`xxe-xml-external-entity` if XML parser is loose).
- Use well-maintained SAML libraries; keep wrapping-relevant patches current.
- Exact-match ACS registration at IdP; no attacker-controlled ACS.
- Regenerate SP session on successful SSO; invalidate on logout.
- Treat attribute-based roles carefully; admin elevation only from trusted claim allowlists.
- Prefer separate EntityIDs per environment (dev/stage/prod) to reduce cross-env assertion reuse.

## Routing

| Need | Skill |
| --- | --- |
| SAML signature, audience, ACS, assertion acceptance (this surface) | **This skill** |
| OAuth / OIDC (not SAML) | `oauth-oidc-misconfiguration` |
| JWT minted after or instead of SAML | `api-auth-and-jwt-abuse` |
| SP session fixation at ACS | `session-fixation-management` |
| Multi-vector ATO planning including SAML | `account-takeover-methodology` |
| Password-reset path parallel to SSO | `password-reset-poisoning` |
| IDOR after SSO session | `idor-broken-object-authorization` |
| RelayState open redirect | `open-redirect` |
| Metadata URL SSRF | `ssrf-server-side-request-forgery` |
| XXE via SAML XML parser | `xxe-xml-external-entity` |
| Host header confuses ACS base URL | `http-host-header-attacks` |
| Secure SP implementation review | `code-quality-standards` |

## Checklist

- [ ] Authorization covers SP and any IdP/tenant exercised
- [ ] SP/IdP EntityIDs, ACS URLs, bindings, and signing policy documented
- [ ] Baseline SSO as test user captured (redacted)
- [ ] Signature required: strip/corrupt/re-sign-with-attacker-cert results recorded
- [ ] Audience missing/wrong tested
- [ ] Destination / Recipient / ACS mismatch tested
- [ ] Replay and lifetime behavior noted
- [ ] RelayState redirect checked
- [ ] Attribute / NameID linking risks reviewed with dual test users
- [ ] Post-ACS session rotation checked
- [ ] Impact: session as unintended principal or clear reject-all-secure baseline
- [ ] Remediation: pin certs, require signed assertions, enforce audience/ACS/time/one-time ID
- [ ] No third-party IdP abuse outside scope; secrets redacted

## Rules

- **Authorized only.** SP misconfig and in-scope IdP apps — not opportunistic attacks on global IdP infrastructure.
- High-level SAML assessment: prefer configuration and acceptance-logic flaws over unpublished crypto exploits.
- Dual-account or lab IdP proofs only; never weaponize against real workforce identities.
- Signature wrapping claims need demonstrate-able SP acceptance of the unverified identity node.
- Distinguish **SAML** issues (this skill) from **OAuth/OIDC** (`oauth-oidc-misconfiguration`) and pure **JWT** API flaws (`api-auth-and-jwt-abuse`).
- Decode and mutate copies of messages locally; avoid pasting live `SAMLResponse` blobs into public issues.
- If SSO succeeds securely, say so — a clean negative result is valuable.
---

# Note

Basics skill for **SAML SSO misconfiguration** on authorized targets. For full identity-takeover prioritization across reset, session, OAuth, JWT, and IDOR, use `account-takeover-methodology` as orchestrator.

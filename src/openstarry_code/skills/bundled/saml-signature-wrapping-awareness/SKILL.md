---
name: saml-signature-wrapping-awareness
description: >-
  Authorized lab methodology for SAML XML signature wrapping (XSW) awareness:
  verify-vs-parse node mismatch, duplicated assertions, and SP acceptance of
  unsigned identity. Use when SAMLResponse XML is in scope and signature
  wrapping, XSW, or “signed node ≠ used node” is the focus.
---

# SAML Signature Wrapping Awareness (Authorized Labs)

Deepen SAML signature trust beyond strip/corrupt probes: the SP must use the
**same** assertion node it cryptographically verified. Map deployment first with
`saml-sso-basics`.

## Use When

| Situation | Direction |
| --- | --- |
| Lab/CTF/authorized SP; focus is **signature wrapping / XSW** | **This skill** |
| SP verifies a signature yet session identity matches an **unsigned** sibling | **This skill** |
| Need XSW variants after basic strip-signature fails | **This skill** |
| General SAML audience/ACS/signing (no wrap hypothesis) | `saml-sso-basics` |
| Post-ACS JWT without XML issues | `api-auth-and-jwt-abuse` |
| OAuth/OIDC only / third-party IdP prod outside scope | Other skill / **out of scope** |

Keywords: SAML signature wrapping, XSW, signed vs parsed node, duplicate
Assertion, Reference URI / Id mismatch, enveloped signature.

## Scope And Authorization

- **Authorized labs, CTFs, owned SPs, or written scope** naming the SP (and any
  IdP/tenant exercised). Prefer test IdP or vendor staging.
- Do **not** attack commercial IdP production beyond SP mistakes and IdP apps
  **explicitly** in scope. Dual NameID V vs A only; never wrap workforce assertions.
- Redact signatures, certs, cookies, raw Base64; store captures offline.
- Lab acceptance logic and reproducible payloads — not unpublished zero-days on
  third-party products. Cap ACS spam; one wrap proof beats mass mutation.

## Workflow

### 1. Preconditions

From `saml-sso-basics`: EntityIDs, ACS, what is signed (Response/Assertion/both),
cert pin, NameID used for session. Decode ACS `SAMLResponse` offline. Baseline
SSO as V. If unsigned messages already succeed, document that first — wrapping
is secondary when verification never runs.

### 2. Verify-vs-parse model

```text
SP: (1) verify digest+sig on Reference node
    (2) pick Assertion/Subject for session
Bug: (1) ≠ (2) → wrap succeeds
```

**Good proof:** Session principal matches **unverified** node (A) while signed
node still verifies as V (or reverse), dual canaries.  
**Bad proof:** Nested XML only; total reject; or strip-sig alone with no second
identity node.

### 3. Controlled wrapping ladder (lab)

Work on **copies**. Re-sign only if **you control** IdP keys; prefer lab fixtures.

| Variant | Idea | Secure SP |
| --- | --- | --- |
| Sibling unsigned Assertion | Signed V + unsigned A; SP loads A | Parse = verified node |
| Nested / Id / Reference tricks | XPath or `#id` ≠ signed node | Same node; reject dup Ids |
| Response signed, Assertion swapped | Outer sig ok; body replaced | Require Assertion sig + pin |
| Wrong subtree / EncryptedAssertion | Sig elsewhere; decrypt unbound | Verify correct element |

### 4. Per-probe execution

1. Keep signed benign V that verifies under a strict tool.
2. Place attacker A only **outside** signed bytes.
3. POST in-scope ACS; isolate Audience/ACS with `saml-sso-basics` if needed.
4. Compare session canary V vs A.
5. **Confirmed** only if identity = unverified node **and** signed node would
   still verify (or SP reports valid signature).

Evidence: original + wrapped Response (redacted), ACS status, session identity,
signed vs used Id/XPath.

### 5. Do not mislabel

| Observation | Classify |
| --- | --- |
| No signature required | Missing validation → `saml-sso-basics` |
| Trusts attacker `KeyInfo` | Cert pin → `saml-sso-basics` |
| Wrong Audience/ACS | → `saml-sso-basics` |
| Verify node ≠ session node | **This skill (XSW)** |
| Pre-ACS session fixed | `session-fixation-management` |
| JWT after ACS forged | `api-auth-and-jwt-abuse` |

### 6. Remediation

- Maintained SAML libraries with wrapping fixes; pin IdP certs from trusted
  metadata; ignore untrusted `KeyInfo`.
- Consume **only** the validated Reference node; reject sibling/duplicate
  Assertions and ambiguous Ids.
- Enforce Audience, Destination/Recipient, times, one-time Assertion IDs.
- XXE-safe parse; implement with `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Full SAML map: audience, ACS, strip-sig, replay | `saml-sso-basics` |
| XSW / verify≠parse | **This skill** |
| JWT/API auth after SAML | `api-auth-and-jwt-abuse` |
| MFA after SSO | `mfa-bypass-methodology` / `mfa-enrollment-flaws` |
| ATO including SAML | `account-takeover-methodology` |
| XXE via SAML XML | `xxe-xml-external-entity` |
| SP session fixation at ACS | `session-fixation-management` |
| Secure SP code | `code-quality-standards` |

## Checklist

- [ ] Auth covers SP and any IdP/tenant used
- [ ] Baseline signed SSO as V; signing policy noted
- [ ] Hypothesis: verified node vs session node
- [ ] Sibling/nested/Id-ambiguity probe on lab copies
- [ ] Dual NameID canaries on resulting session
- [ ] Confirmed only with unverified-identity evidence pack
- [ ] Distinguished from no-sig / any-KeyInfo; Audience/ACS via basics skill
- [ ] Post-ACS JWT/session skills if needed; pin certs + bind parse remediation
- [ ] Secrets redacted; no third-party IdP abuse

## Rules

- Authorized lab/SP only; dual identities. No wrap claim without unverified principal accepted.
- Prefer fixtures; general SAML → `saml-sso-basics`; JWT → `api-auth-and-jwt-abuse`.
- Redact live SAMLResponse; negative strict verify+parse is valuable.

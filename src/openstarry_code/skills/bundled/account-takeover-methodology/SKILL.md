---
name: account-takeover-methodology
description: >-
  Authorized account-takeover (ATO) methodology that chains password-reset,
  session fixation, IDOR/BOLA, JWT/API tokens, and OAuth/OIDC failures into
  end-to-end impact paths. Use when planning or executing multi-vector ATO
  assessment with owned test accounts only — not single-class deep dives alone.
---

# Account Takeover Methodology (Authorized)

Orchestrates multi-step **account takeover** testing: map identity surfaces, prioritize high-yield vectors, chain class findings into a coherent ATO narrative, and hand off depth work to specialized skills.

## Use When

| Situation | Direction |
| --- | --- |
| Engagement goal is **account takeover**, identity takeover, or “login as another user” impact | **This skill** (primary orchestrator) |
| Multiple auth surfaces exist (reset, SSO, API tokens, sessions, object IDs) and you need a **test order** | **This skill** |
| You already have a single-class hit (reset poison, IDOR, JWT) and need **impact chaining / ATO framing** | **This skill** + class skill for depth |
| Only password-reset Host/token poisoning | `password-reset-poisoning` primary |
| Only SID not regenerated on login | `session-fixation-management` primary |
| Only OAuth/OIDC redirect/state/token issues | `oauth-oidc-misconfiguration` primary |
| Only JWT/API authN | `api-auth-and-jwt-abuse` primary |
| Only object-level access (no auth boundary break) | `idor-broken-object-authorization` primary |
| SAML enterprise SSO specifically | `saml-sso-basics` |
| No authorization / no test accounts | **Do not use** |

Keywords: ATO, account takeover, identity takeover, session hijack chain, reset → login, token theft, horizontal privilege escalation to full account.

## Scope And Authorization

- **Authorized applications only**: written pentest SOW, bug-bounty in-scope assets, owned apps, or lab/CTF targets. Do not infer permission from “looks like a sandbox.”
- Prove ATO **only with accounts you control** (attacker + victim test users, or program-provided mailboxes). Never reset, fixate, or access real third-party users.
- Prefer non-destructive proofs: read a victim-test canary field, change a non-critical preference, or demonstrate session binding — not mass password resets or production lockouts.
- Treat reset links, session cookies, JWTs, OAuth codes, and SAML assertions as **credentials**: redact in tickets; store raw captures offline; rotate after production demos.
- Rate-limit auth endpoints. Stop on account lockout risk, mail flood, or payment/destructive side effects outside the test plan.
- Phishing real humans, SIM-swap, malware delivery, and credential stuffing against production users are **out of scope** for this skill unless a program **explicitly** allows a named, non-destructive class (rare).

## Core Model

```text
Identity entry points
  → Weak link (reset | session | token | SSO | object authZ)
  → Attacker obtains usable session / credential for victim-test principal
  → Optional chain (IDOR after session, privilege step-up, linked accounts)
  → ATO impact: act as victim on in-scope app
```

| Vector family | What “win” looks like | Deep skill |
| --- | --- | --- |
| **Password / magic-link reset** | Attacker-controlled host or redirect receives reset token; or weak token reused | `password-reset-poisoning` |
| **Session fixation / lifecycle** | Pre-auth SID becomes victim session; no rotate on login/reset/MFA | `session-fixation-management` |
| **OAuth / OIDC** | Code/token to attacker redirect; state/nonce fail; account linking confusion | `oauth-oidc-misconfiguration` |
| **SAML SSO** | Unsigned/weak assertion accepted; bad audience/ACS; signature wrap (high-level) | `saml-sso-basics` |
| **JWT / API authN** | Forged/confused token accepted as victim identity | `api-auth-and-jwt-abuse` |
| **IDOR / BOLA** | Authenticated as A, read/write B’s account objects (email, tokens, password-change) | `idor-broken-object-authorization` |
| **Token leakage** | Token in logs, Referer, XSS, cache, open redirect | matching skill + this for ATO story |

**Good ATO proof:** Dual test accounts; attacker client ends with **victim-test** principal’s authenticated canary (profile email, user id, private resource) via a documented chain.  
**Bad ATO proof:** Theoretical “could phish”; scanner noise without session/credential; IDOR that only reads public fields with no identity boundary story.

## Workflow

### 1. Authorization lock and account matrix

1. Confirm scope text: hosts, apps, SSO tenants, mobile backends, and excluded third-party IdPs.
2. Provision fixtures:

   | Role | Purpose |
   | --- | --- |
   | Victim-test V | Target identity for ATO proof |
   | Attacker-test A | Receives poisoned links, holds fixated SID, swaps IDs |
   | Optional low/high priv | Vertical step-up after foothold |
   | Optional second tenant | Cross-tenant ATO / linking |

3. Capture how each identity authenticates: password, magic link, OAuth, SAML, API key, refresh token, “remember me.”
4. Open a living **ATO surface map** (next step). Keep secrets out of shared notes.

### 2. Map identity and recovery surfaces

From proxy history, docs, and UI (`api-recon-and-docs` / `recon-and-methodology` as needed):

| Surface | Examples to record |
| --- | --- |
| Login | Cookie session, JWT, multi-step MFA |
| Registration / invite | Tokenized invite URLs, auto-login |
| Password reset / magic link | Request + consume endpoints; email link shape |
| Email / phone change | Verification codes; binding to session |
| OAuth / OIDC | `client_id`, redirect URIs, callback |
| SAML | ACS URL, EntityID, IdP metadata (in-scope) |
| Account link / unlink | Social login attach |
| API tokens | Personal access tokens, refresh, device codes |
| Object IDs on “me” | `/users/{id}`, export, recovery codes, sessions list |

Tag each surface: **authN**, **recovery**, **session lifecycle**, **authZ object**, **federation**.

### 3. Prioritize vectors (impact × ease × chain potential)

Default order for ATO-focused authorized tests (adjust to stack):

| Priority | Theme | Why first | Hand off |
| ---: | --- | --- | --- |
| P0 | Password-reset / magic-link poisoning | Direct credential recovery | `password-reset-poisoning` |
| P0 | OAuth/OIDC redirect, code theft, linking | Federated login as victim | `oauth-oidc-misconfiguration` |
| P0 | SAML signature / audience / ACS (if SSO in scope) | Enterprise IdP → SP session | `saml-sso-basics` |
| P0 | JWT/API authN break | Mint or confuse victim identity | `api-auth-and-jwt-abuse` |
| P1 | Session fixation / no regenerate | Pre-auth SID → victim session | `session-fixation-management` |
| P1 | IDOR on account, email, recovery, sessions, tokens | Steal identity artifacts while authed as A | `idor-broken-object-authorization` |
| P1 | Account binding / email change without re-auth | Takeover via profile mutation | IDOR + logic + CSRF skills |
| P2 | Open redirect + token in query/Referer | Secondary theft path | `open-redirect` + reset/OAuth skills |
| P2 | Host header / cache aiding reset or Set-Cookie | Delivery amplifiers | `http-host-header-attacks` |
| P2 | XSS / CSRF on session or email change | Browser-bound completion | `xss-*`, `csrf-*` |
| P3 | Weak rate limit / enumeration alone | Supporting finding unless chained | note; rarely full ATO alone |

Do **not** deep-dive every class equally. Run P0 federation/recovery first when present; use IDOR early if dual accounts already authenticated.

### 4. Execute class deep-dives (one primary skill at a time)

For each selected vector:

1. Switch **primary** to the matching skill; keep this skill as orchestrator for impact narrative.
2. Use only V and A (and allowed mailboxes/canary domains).
3. Stop at the **first clean proof** per sink class; avoid flooding mail or auth APIs.
4. Record: preconditions, single changed variable, response that shows V’s canary under A’s control.

Minimum evidence per successful vector:

```text
[Vector] e.g. reset Host poison
[Accounts] A=..., V=...
[Request delta] one header/param/id change
[Artifact] token/session/code obtained (redacted)
[Session proof] request as A that returns V canary fields
[Chain next?] e.g. use V session → IDOR admin object
```

### 5. Chain patterns (compose findings into ATO)

Use chaining only when each hop is evidenced:

| Chain | Typical path | Skills |
| --- | --- | --- |
| **Reset → session** | Poisoned reset sets password + issues session without rotate | `password-reset-poisoning` → `session-fixation-management` |
| **OAuth code → RP session** | Bad `redirect_uri` / state → attacker redeems or victim browser binds wrong identity | `oauth-oidc-misconfiguration` → session skill |
| **JWT forge → API as V** | `none`/kid/jwks confusion → call `/me` and state-changing APIs | `api-auth-and-jwt-abuse` |
| **IDOR → recovery material** | As A, read V’s reset token, backup codes, or session list revoke/reuse | `idor-broken-object-authorization` |
| **IDOR email change** | Change V’s email to A-controlled inbox → reset legitimately | IDOR + `password-reset-poisoning` |
| **Fixation + login CSRF** | Force SID then induce login (or inverse login CSRF) | `session-fixation-management`, `csrf-cross-site-request-forgery` |
| **Token leak → API** | Referer/log/XSS leak refresh token → long-lived ATO | open-redirect / XSS / JWT skills |
| **Host → Set-Cookie / reset URL** | Authority confusion delivers cookie or email link | `http-host-header-attacks` + reset/session |

Document chains as **numbered hops**. Do not claim multi-hop ATO if intermediate hops were only theoretical.

### 6. Post-foothold identity impact (optional, authorized)

Once you hold V’s session or credential (test accounts only):

1. List sessions / devices; attempt revoke of A’s fake device vs keep attacker session.
2. Change email/password/MFA with and without step-up — residual takeover durability.
3. Export personal data, OAuth grants, API tokens — severity narrative (minimize data).
4. Vertical: IDOR or mass-assignment to admin if still in scope.
5. Logout/invalidate: confirm attacker session dies on password change when claiming full remediation guidance.

### 7. Negative testing and dead ends

Record explicitly:

- Edge rejects unknown `Host` / XFH for reset.
- Session ID rotates on login and password change.
- OAuth exact-match `redirect_uri`; `state` bound server-side.
- JWT verifies `iss`/`aud`/alg; no cross-API audience accept.
- Object IDs on account resources return 403/404 for A→V.

Dead ends prevent duplicate work and strengthen residual-risk notes.

### 8. Report framing for ATO

1. **Title:** identity impact first — `[ATO] Password-reset Host poison steals token for victim-test user`.
2. **Summary:** entry vector → artifact stolen → session as V → optional chain.
3. **Account diagram:** A vs V; never real customer identities.
4. **Reproduction:** clean numbered steps; one variable per hop.
5. **Impact:** confidentiality of V’s data; integrity (password/email change); persistence (refresh token, unrevoked sessions).
6. **Remediation themes:** canonical reset base URL; regenerate session on auth and recovery; exact OAuth redirect allowlist; server-side object ACL; JWT claim binding; invalidate sessions on password/email change. Pair code fixes with `code-quality-standards`.
7. **Severity:** base on realistic attacker capabilities **within policy** (no assumed mass phishing unless program includes it).

## Routing

| Need | Skill |
| --- | --- |
| ATO plan, prioritization, multi-vector chaining, impact narrative | **This skill** |
| Password-reset / magic-link Host or token poisoning | `password-reset-poisoning` |
| Session fixation / SID not rotated on login or recovery | `session-fixation-management` |
| OAuth / OIDC redirect, state, nonce, code, mix-up | `oauth-oidc-misconfiguration` |
| JWT / Bearer / API authentication flaws | `api-auth-and-jwt-abuse` |
| Object-level access to other users’ account resources | `idor-broken-object-authorization` |
| SAML SSO assertion / signature / audience / ACS | `saml-sso-basics` |
| Generic Host / cache (not email ATO primary) | `http-host-header-attacks` |
| Open redirect as token leak hop | `open-redirect` |
| CSRF on email/password change or login | `csrf-cross-site-request-forgery` |
| XSS completing browser-bound theft | `xss-cross-site-scripting` |
| API / auth surface inventory | `api-recon-and-docs` |
| Engagement planning / recon order | `recon-and-methodology` |
| Bug bounty policy / report quality | `bug-bounty-methodology` |
| Secure implementation of fixes | `code-quality-standards` |

**Selection rule:** If the user asks only about one sink, use that class skill as **primary**. If the user asks for ATO methodology, full identity review, or chaining, use **this skill** as primary and load helpers for execution.

## Checklist

- [ ] Written authorization / in-scope assets confirmed; third-party IdPs handled per policy
- [ ] Dual (or multi) test accounts provisioned; no real-user resets or fixation
- [ ] Identity surface map: login, reset, SSO, tokens, account objects, session lifecycle
- [ ] Priority order chosen (reset / OAuth / SAML / JWT / session / IDOR) for this stack
- [ ] Each pursued vector executed under its deep skill with redacted evidence
- [ ] At least one end-to-end path (or explicit residual: no ATO found) documented
- [ ] Chains listed hop-by-hop only when evidenced
- [ ] Session durability after password/email change tested if foothold obtained
- [ ] Dead ends recorded (controls that worked)
- [ ] Report: ATO narrative, account diagram, remediation, redaction complete
- [ ] Tokens/cookies/reset links rotated or invalidated after production tests

## Rules

- **Authorized only.** No SOW, program, ownership, or lab charter → stop.
- ATO proofs use **your** victim-test identity only — never third-party mailboxes or sessions.
- This skill **orchestrates**; it does not replace deep methodology in reset, session, OAuth, JWT, IDOR, or SAML skills.
- Do not equate “email enumeration” or “missing MFA” alone with full ATO without a usable session/credential path.
- Do not label post-login cookie theft as fixation; do not label pure IDOR without identity impact as ATO without explanation.
- One clean dual-account proof beats bulk automation against auth endpoints.
- Redact credentials in all shared artifacts; keep originals immutable and separate from reports.
- Gate destructive password changes, MFA removal, and global session revoke on explicit approval when accounts are shared with the client.
---

# Note

Primary entry for **multi-vector account takeover** on authorized targets. Hand off each technical sink to the specialized skills in Routing; return here to prioritize, chain, and report identity impact.

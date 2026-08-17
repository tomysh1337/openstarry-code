---
name: session-fixation-management
description: >-
  Detect and prevent session fixation: pre-auth session IDs that remain valid
  after login, URL/cookie injection of attacker-chosen SIDs, and missing
  regenerate-on-auth. Use when assessing cookie, header, or URL-based session
  mechanisms under authorization and login does not mint a fresh session;
  keywords session fixation, session regenerate, SID.
---

# Session Fixation — Detection And Prevention

## Scope And Authorization

- Authorized applications, labs, CTFs, and owned systems only. Prove fixation only with **accounts you control** (attacker + victim test users).
- Do not fixate real-user sessions, plant SIDs in production shared links, or phish third parties.
- Prefer disposable browsers / clean profiles. Redact full session cookies and tokens from tickets; store raw captures offline per program policy.
- Destructive logout/rotation of shared accounts requires explicit approval.

## When To Use

- Login, SSO callback, MFA step-up, password change, or “remember me” leaves the **same** session identifier that existed before authentication.
- Session ID appears in URL (`?PHPSESSID=`, `;jsessionid=`), form field, or is acceptably set from a request parameter/header.
- Cookie session without `HttpOnly` / with broad `Domain=` plus a delivery path that lets an attacker set or force a known SID.
- Engagement language: “session fixation”, “session not regenerated”, “login CSRF + fixed SID”, “URL session ID”.
- After `api-auth-and-jwt-abuse` when the issue is **server-side session store reuse**, not JWT crypto.

## Core Model

```
Attacker obtains SID S (or forces victim browser to use S)
  → Victim authenticates while still bound to S
  → Server upgrades S to authenticated principal (no regenerate)
  → Attacker reuses S → acts as victim
```

| Variant | Delivery of S | What fails |
| --- | --- | --- |
| **Classic cookie fixation** | Attacker sets cookie (`Set-Cookie` via vuln, subdomain, or meta) | No regenerate on login |
| **URL / path SID** | Link `https://app/?SID=attacker` or path param | Server trusts client-supplied SID |
| **Login without rotate** | Victim already has anonymous S from site visit | Auth binds identity to pre-login S |
| **Secondary step-up** | MFA / password-change keeps old S | Privilege change without new SID |
| **Token + session hybrid** | JWT mint OK but cookie SID fixed | Cookie path still fixable |

**Good proof:** Attacker-chosen or pre-login SID becomes authenticated for the victim; attacker presents that SID and receives victim-only data.  
**Bad proof:** Attacker steals SID after login (that is session **theft**, not fixation); or JWT forgery without a fixed pre-auth ID (`api-auth-and-jwt-abuse`).

## Workflow

1. **Map the session mechanism**  
   From proxy history and login flow, record:

   | Item | Capture |
   | --- | --- |
   | SID name | `session`, `PHPSESSID`, `JSESSIONID`, `connect.sid`, custom |
   | Transport | Cookie / URL / body / header |
   | Cookie flags | `Secure`, `HttpOnly`, `SameSite`, `Domain`, `Path`, `Max-Age` |
   | When issued | First hit, login only, both |
   | Server store | Opaque ID vs signed cookie (Rails, Flask itsdangerous, JWT-in-cookie) |

   Decode signed cookies only to understand structure; fixation still applies if the **server accepts a client-supplied id** without rotation after auth.

2. **Baseline: pre-login vs post-login SID**  
   Clean browser or cookie jar:

   1. Visit a public page → note anonymous SID `S0` (if any).
   2. Log in as test user A → note SID `S1` and any `Set-Cookie` rotation.
   3. Compare `S0` and `S1` **byte-for-byte**.

   | Result | Interpretation |
   | --- | --- |
   | `S1` ≠ `S0` (new value) | Rotation present for this path — still retest MFA/password-change |
   | `S1` == `S0` | Strong fixation candidate |
   | No pre-login cookie; first SID only after login | Classic URL/cookie **injection** variants still matter |

   ```http
   GET /login HTTP/1.1
   Host: target.example
   Cookie: session=<S0>

   POST /login HTTP/1.1
   Host: target.example
   Cookie: session=<S0>
   Content-Type: application/x-www-form-urlencoded

   user=alice&pass=...
   ```

   Success signal: response is 200/302 to app **and** subsequent requests with `Cookie: session=S0` show alice’s data **without** a new SID.

3. **Attacker-controlled SID acceptance**  
   Generate or obtain an SID the server will accept (visit app as attacker, copy SID `S_att`, or try predictable patterns only within scope).

   In a **victim** browser profile that does **not** yet hold a privileged session:

   ```http
   GET / HTTP/1.1
   Host: target.example
   Cookie: session=<S_att>
   ```

   Then complete login as victim test user B with that cookie forced (Burp Match/Replace, browser extension, or `document.cookie` only if non-HttpOnly and same-site script is in scope).

   From **attacker** client:

   ```http
   GET /account HTTP/1.1
   Host: target.example
   Cookie: session=<S_att>
   ```

   **Confirmed** if body contains B’s canary (email, user id). Use dual accounts; never real victims.

4. **URL and parameter SID injection**  
   When the app or framework historically supports SID in URL:

   | Probe | Example |
   | --- | --- |
   | Query | `/login?PHPSESSID=S_att`, `?sessionid=S_att` |
   | Path | `/app/;jsessionid=S_att` |
   | Body | hidden `sessionid` on login form |
   | Header | `X-Session-Id`, `Cookie` override vs custom header preference |

   Check whether a response `Set-Cookie` **overwrites** your value (mitigation) or **echoes** it (bad). Also test open-redirect / login `return` links that embed SID — chain with `open-redirect` if navigation is the delivery vehicle.

5. **Login CSRF as delivery (related, not the same bug)**  
   If the app accepts cross-site login POST (no CSRF on login) **and** does not rotate SID, an attacker can sometimes bind the **victim’s browser** to an attacker account (login CSRF) — inverse of fixation. Document separately:

   | Class | Who ends up authenticated as whom |
   | --- | --- |
   | Session fixation | Attacker reuses SID → **victim** identity |
   | Login CSRF | Victim browser → **attacker** identity |

   Use `csrf-cross-site-request-forgery` for login CSRF methodology; keep this skill primary when the SID is attacker-chosen and later becomes victim-auth’d.

6. **Privilege and lifecycle rotations**  
   Retest regenerate requirements at:

   - Password change / reset completion  
   - MFA enrollment or step-up  
   - Role switch / “impersonate” end  
   - Logout (SID must invalidate server-side, not only clear cookie)

   ```http
   POST /account/password HTTP/1.1
   Cookie: session=<S_before>
   ...
   ```

   If `S_after` == `S_before` after password change, residual fixation/session-reuse risk remains (stolen SID still works).

7. **Cookie scope and subdomain fixation**  
   - `Domain=.example.com` cookies set from a weaker sibling host can fixate the apex app if login does not rotate.  
   - XSS on a sibling that can `document.cookie` non-HttpOnly SIDs → fixation **or** theft; classify by whether SID was known pre-auth.  
   - Host-header / cache tricks that inject `Set-Cookie` → pair with `http-host-header-attacks` / `crlf-injection` for the injection sink; impact proof stays here.

8. **JWT and API sessions**  
   - Opaque server sessions: this skill.  
   - Pure `Authorization: Bearer` JWT with no server session: fixation rare unless the app also sets a fixable cookie SID or accepts client-chosen `jti` without rebind — deep JWT issues → `api-auth-and-jwt-abuse`.  
   - OAuth/OIDC `state` / session binding failures at IdP callback → `oauth-oidc-misconfiguration` primary; use this skill when the **RP session cookie** is not rotated after code exchange.

9. **Remediation guidance (for reports and code fixes)**  
   Apply with `code-quality-standards` when implementing:

   - **Regenerate** session ID on every authentication and privilege change; invalidate the old server record.  
   - Prefer server-generated cryptographically random SIDs; never accept SID from query/body as authoritative if avoidable.  
   - Cookie: `HttpOnly; Secure; SameSite=Lax` or `Strict`; tight `Path`; avoid parent `Domain` unless required.  
   - On logout: destroy server session; clear cookie with matching flags.  
   - Framework knobs (examples — verify version docs): PHP `session_regenerate_id(true)`; Java `HttpServletRequest.changeSessionId()` / invalidate+new; ASP.NET Core `Session.Clear` + new cookie auth ticket; Express regenerate; Rails `reset_session`.

## Routing

| Need | Skill |
| --- | --- |
| JWT alg/kid/claim forgery, Bearer auth | `api-auth-and-jwt-abuse` |
| Login CSRF / cookie state-change CSRF | `csrf-cross-site-request-forgery` |
| Host/`Set-Cookie` injection delivery | `http-host-header-attacks`, `crlf-injection` |
| Redirect link carries SID or post-login next= | `open-redirect` |
| OAuth callback session binding | `oauth-oidc-misconfiguration` |
| Password-reset link host/token theft | `password-reset-poisoning` |
| IDOR after solid session | `idor-broken-object-authorization` |
| Implement regenerate / cookie flags | `code-quality-standards` |

## Output Checklist

- [ ] SID name, transport, cookie flags, issue timing
- [ ] Pre-login vs post-login SID comparison (values redacted or hashed in public notes)
- [ ] Attacker-SID acceptance test with dual test accounts
- [ ] URL/parameter/header injection attempts and outcomes
- [ ] Privilege-change and logout invalidation results
- [ ] Delivery path (cookie only / URL / subdomain / CSRF-related)
- [ ] Impact: attacker can use S after victim login (evidence snippet)
- [ ] Remediation: regenerate-on-auth, invalidate old, cookie flags, no URL SID

## Rules

- Fixation requires a **pre-auth or attacker-supplied** identifier that becomes privileged — do not relabel post-login cookie theft as fixation.
- Always dual-account: one supplies SID, one authenticates, first reuses SID.
- Do not plant SIDs in public channels or third-party cookies outside scope.
- HttpOnly blocks pure JS cookie set from XSS but **not** server-accepted URL SIDs or response-splitting `Set-Cookie`.
- One solid authenticated canary response beats a long list of theoretical cookie flag notes.
- Authorized testing only; rotate test sessions after demos if accounts are shared with the client.

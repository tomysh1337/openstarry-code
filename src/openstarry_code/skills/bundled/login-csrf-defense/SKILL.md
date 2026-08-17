---
name: login-csrf-defense
description: >-
  Detect, prove, and remediate login CSRF: cross-site login that binds the
  victim browser to an attacker-controlled identity, silent account switch,
  and post-login action chaining. Use when login, SSO password-form, or
  magic-link consume endpoints lack anti-CSRF controls, or when assessing
  “login CSRF”, “forced login”, or session bind-on-auth under authorization.
---

# Login CSRF Defense

## When To Use

- Cookie/session login (`POST` or GET-equivalent), password form before SSO, “switch user”, or magic-link consume lacks a bound CSRF token, custom header, or equivalent anti-forgery check.
- Engagement language: “login CSRF”, “forced login”, “cross-site login”, “victim logged into attacker account”, “account linking via login CSRF”.
- Impact hinges on **post-login sinks**: OAuth linking, payments, uploads to “my” storage, notifications, or actions that trust the ambient session.
- SameSite=Lax alone may not block all paths (GET login, method override, missing token, `SameSite=None`/absent cookies).
- Primary for login/auth-bind forgery. Hand general authenticated state-change CSRF to `csrf-cross-site-request-forgery`. Hand attacker-chosen SID that becomes the **victim** principal to `session-fixation-management`.

## Scope And Authorization

- Authorized apps, labs, CTFs, and owned systems only. Prove only with **accounts you control** (attacker + victim).
- Do not force-login real users, plant credentials off-scope, or phish outside the program.
- Prefer dual clean browser profiles or cookie jars. Redact passwords, session cookies, and tokens; store raw captures offline per policy.
- Avoid destructive linking, fund moves, or admin binds unless approved. Prefer canary data (unique email, harmless note).

## Workflow

1. **Model the risk** — Login CSRF is not password theft:

   ```
   Attacker auto-POSTs /login with attacker credentials into victim browser
     → Session cookie = authenticated as attacker
     → Victim later links OAuth, uploads, adds payment, accepts invite
     → Attacker reopens own account → harvests victim-attached artifacts
   ```

   | Class | Browser ends as | Attacker goal |
   | --- | --- | --- |
   | **Login CSRF** | Attacker identity | Harvest victim actions into attacker account |
   | **Session fixation** | Victim identity (known SID) | Act as victim after they log in |
   | **Generic CSRF** | Already-victim session | Change victim settings while logged in |

2. **Inventory login surfaces** — Map cookie-auth entry points: `POST /login`/`/session`/`/auth/sign-in`; JSON login that still sets a session cookie; MFA second step; magic-link consume; SSO password front-door; “login as” / switch user. Record Content-Type, cookie flags (`SameSite`, `Secure`, `HttpOnly`), pre-login session presence, and any form CSRF token.

3. **Map defenses on the authenticate request**

   | Control | Capture |
   | --- | --- |
   | CSRF / anti-forgery token | Present? Bound to pre-login session? Validated fail-closed? |
   | Custom header | `X-Requested-With` / app header (non-simple request) |
   | Origin / Referer | Allowlist? Fail open on missing Referer? |
   | SameSite on session | Strict / Lax / None / missing |
   | Method | POST-only vs GET login / method override |
   | Body format | form vs JSON; form-encoded fallback accepted? |

4. **Baseline forge** — Victim profile logged out (or not on a high-value account). Attacker credentials known only to you. Host authorized PoC:

   ```html
   <form id="f" method="POST" action="https://target.example/login">
     <input name="username" value="attacker@test.example">
     <input name="password" value="REDACTED">
   </form>
   <script>document.getElementById("f").submit();</script>
   ```

   Load as “victim”; confirm UI/session is **attacker**. Also try: omit/empty/foreign token; GET login; form body when UI uses JSON; method-override where relevant.

   **Confirmed:** cross-site request establishes attacker-authenticated session in the victim browser without a secret the attacker could not supply.

5. **Impact canary** — After forced login, perform one authorized action from the victim profile:

   | Canary | Why |
   | --- | --- |
   | Link OAuth / social | Attacker inherits or controls link |
   | Upload file / unique note | Attacker retrieves from own account |
   | Add shipping / notify email | Data lands on attacker profile |
   | Accept org invite / device trust | Privilege binds to wrong principal |

   Document attacker-side recovery without the victim password. If no valuable sink exists, still note missing login anti-CSRF as defense-in-depth when the program cares; do not overstate severity.

6. **Differentiate fixation** — If pre-login SID survives and becomes the **victim** principal after victim credentials, primary skill is `session-fixation-management`. Forced switch to attacker identity stays here. Both can coexist (no login CSRF token **and** no regenerate).

7. **Defense and remediation** — Implement with `code-quality-standards`:

   - Synchronizer token (or signed double-submit) on login, bound to pre-auth session or short-lived cookie; fail-closed on missing/invalid.
   - Session cookie: `Secure; HttpOnly; SameSite=Lax` or `Strict`; avoid `SameSite=None` without strong token + HTTPS.
   - POST-only login; disable method override on auth routes; magic-link session only via unguessable one-time token capability.
   - `Origin`/`Referer` checks as defense-in-depth only (Referer may be stripped).
   - On success: **regenerate** session id; invalidate anonymous pre-session as needed.
   - Step-up / re-auth for account linking, email add, payment add—limits impact if login is forged.
   - Pure Bearer-in-memory APIs avoid classic login CSRF; still protect if a session cookie is also set.
   - Logout CSRF is usually lower severity; avoid unauthenticated GET logout if UX abuse matters.

8. **Regression (authorized)** — Login without token → 403/400; valid pre-session token → success; e2e cross-origin form POST blocked; post-login SID ≠ pre-login SID.

## Routing

| Need | Skill |
| --- | --- |
| Authenticated state-change CSRF after a session already exists | `csrf-cross-site-request-forgery` |
| Pre-auth SID survives and becomes **victim** identity | `session-fixation-management` |
| Implement tokens, cookie flags, regenerate, tests | `code-quality-standards` |

## Output Checklist

- [ ] Login endpoint(s), method, Content-Type, cookie names/flags
- [ ] Anti-forgery present/absent; strip/empty/foreign token results
- [ ] PoC: victim browser principal = attacker test account
- [ ] Post-login canary + attacker-side recovery (or no sink noted)
- [ ] Fixation: pre vs post SID (redacted); route if victim-principal reuse
- [ ] SameSite / Origin / method-override notes
- [ ] Remediation: login CSRF token fail-closed; POST-only; regenerate-on-auth; step-up for linking; cookie flags
- [ ] Dual test accounts only; secrets redacted

## Rules

- Outcome is **attacker identity in victim browser**, not password theft and not fixation-as-victim unless proven separately.
- Severity needs a credible post-login sink or program-accepted hardening finding—not “cookie was set” alone.
- Proof needs a victim browser context; raw curl is not login CSRF.
- No third-party credentials or real-user force-login. One solid dual-account chain beats unvalidated HTML dumps.

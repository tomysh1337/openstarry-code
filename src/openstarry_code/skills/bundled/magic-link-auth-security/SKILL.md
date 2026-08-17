---
name: magic-link-auth-security
description: >-
  Authorized assessment and hardening of passwordless magic-link authentication:
  token lifecycle, single-use/TTL, email binding, consume races, open-redirect
  after verify, prefetch/scanner consumption, and post-login session hygiene.
  Use when login, sign-in, or passwordless verify flows email a one-click link
  or code that establishes a session without a password.
---

# Magic Link Auth Security

## When To Use

- App offers passwordless login, “email me a sign-in link”, OTP-in-link, or device-confirm via absolute email URL.
- Token or `code` appears in query/fragment (`?token=`, `?link=`, `/auth/verify/:id`) and consume mints a session or JWT.
- Engagement language: “magic link”, “passwordless email”, “login link ATO”, “sign-in token reuse”, “email link race”.
- Primary when the **auth product** is the magic-link flow end-to-end. Hand pure Host/`X-Forwarded-Host` email URL poisoning to `password-reset-poisoning`. Hand SID not rotated after consume to `session-fixation-management`.

## Scope And Authorization

- Authorized apps, labs, CTFs, and program-scoped mailboxes only. Trigger links **only for accounts you own** (or vendor-provided test inboxes). Never request magic links for third-party users.
- Cap resend and consume attempts; avoid lockouts and inbox flooding on shared production identities.
- Prefer canary domains and disposable browsers. Redact full tokens, links, and session cookies in tickets; keep raw captures offline per policy.
- Do not mass-email real users or poison shared caches unless the program explicitly allows controlled cache tests.

## Workflow

1. **Inventory magic-link surfaces**  
   Map request vs consume:

   | Phase | Typical endpoints |
   | --- | --- |
   | Request link | `POST /auth/magic`, `/login/email`, `/api/auth/link` |
   | Consume / verify | `GET/POST /auth/verify`, `/login/callback`, `/magic/consume` |
   | Optional code entry | UI that accepts emailed code without full URL |

   Note CSRF on request, email enumeration (different status/timing), rate limits, Content-Type, and whether SPA uses a different base URL than MVC. Use `api-recon-and-docs` if routes are unclear.

2. **Baseline honest flow**  
   Clean browser, your inbox:

   1. Request link for test user A; save raw email (headers + body).
   2. Extract scheme, host, path, token param names, any `next`/`returnUrl`/`redirect`.
   3. Consume once; capture `Set-Cookie`, redirects, and privileged canary (`/api/me`).
   4. Record: single-use?, TTL?, session vs Bearer issued?, pre-auth cookie reused?

3. **Token properties (core checks)**  

   | Check | Action | Fail signal |
   | --- | --- | --- |
   | Entropy | Compare several tokens (length, charset) — no mass brute on prod | Short/sequential/guessable |
   | Single-use | Replay same token after success | Second consume still auths |
   | TTL | Wait past stated expiry; retry once | Expired token still works |
   | Binding | Token from A on consume path with B’s email/session context | Cross-user upgrade |
   | Purpose | Magic-login token on password-reset or invite endpoint | Cross-purpose accept |
   | Method | GET-only consume vs state-changing POST | CSRF-able session mint via GET image/prefetch |

4. **Request-side abuse (without third-party mail)**  
   - Enumeration: same/different responses for registered vs unknown emails.  
   - Resend storms: per-IP and per-account caps.  
   - Unauthenticated request that always returns `200` with token in JSON (token should leave only via email channel you control in tests).  
   - Host/XFH influence on **absolute** email URL → stop and apply `password-reset-poisoning` as primary for that sink; keep this skill for lifecycle after a trusted host.

5. **Consume-side chains**  
   - **Open redirect:** trusted host validates token then lands on `next=https://attacker.tld` with token still in `Referer` or residual query — document theft path; detail payload ladder with `open-redirect` if needed.  
   - **Prefetch / link scanners:** some mail clients GET the URL once; if GET is one-shot consume, legitimate user fails or attacker races second hit. Prefer POST + user gesture or intermediate interstitial that does not invalidate until confirm.  
   - **Race double-consume:** parallel requests with same token → `race-condition` helper if non-atomic invalidate.  
   - **Fragment vs query:** tokens only in `#` may avoid some Referer leaks but still hit JS/logs; document actual placement.

6. **Session and authz after success**  
   Compare SID (or session binding) **before** request and **after** consume:

   | Observation | Route |
   | --- | --- |
   | Pre-auth SID becomes privileged without regenerate | `session-fixation-management` |
   | Old sessions remain valid after new magic login | lifecycle note + fixation skill |
   | Pure Bearer mint, no cookie SID | `api-auth-and-jwt-abuse` for token claims/TTL if relevant |

   Also test: logout invalidates server session; magic-link account-merge/email-change edges do not attach attacker inbox without proof of ownership.

7. **Remediation (implement with `code-quality-standards`)**  
   - High-entropy single-purpose tokens; store only hashes server-side; short TTL (minutes).  
   - Atomic single-use on consume; bind to `user_id` + purpose + optional request nonce.  
   - Canonical `APP_URL` / `PUBLIC_URL` for email links — never raw `Host` / client `X-Forwarded-Host` (`password-reset-poisoning` detail).  
   - Prefer POST consume or two-step “click → confirm on page”; mitigate mail-scanner prefetch.  
   - After success: regenerate session id, invalidate or limit concurrent sessions per policy, optional notify.  
   - Rate-limit request and consume per IP + account; constant-time compare; no token in client logs.  
   - Avoid long-lived tokens in URLs that redirect off-site; strip sensitive query on landing.

## Routing

| Need | Skill |
| --- | --- |
| Host / XFH / base-URL poisoning of email absolute links | `password-reset-poisoning` |
| SID not rotated on magic-link login or privilege change | `session-fixation-management` |
| Secure token store, consume, session mint implementation | `code-quality-standards` |
| `next=` / return URL after verify | `open-redirect` |
| Parallel double-consume / non-atomic invalidate | `race-condition` |
| JWT claims after passwordless mint | `api-auth-and-jwt-abuse` |
| Multi-vector ATO chaining | `account-takeover-methodology` |

## Output Checklist

- [ ] Request and consume endpoints; token location (query/fragment/body)
- [ ] Baseline email link shape (host/path redacted); single-use, TTL, binding results
- [ ] Replay, cross-user, cross-purpose, and method (GET prefetch) outcomes
- [ ] Host/authority poisoning deferred or proved (`password-reset-poisoning`)
- [ ] Post-consume session: SID change, old session validity (`session-fixation-management`)
- [ ] Redirect/Referer or race notes if any
- [ ] Impact with **owned** inbox only; remediation list (canonical URL, hash+TTL, rotate session)

## Rules

- Owned mailboxes and dual test accounts only; no third-party magic-link requests.
- Distinguish **token lifecycle bugs** (this skill) from **poisoned link host** (`password-reset-poisoning`) and **fixation** (`session-fixation-management`).
- Prefetch/scanner behavior is a real product risk — prove with controlled double-GET, not speculation alone.
- Never paste live magic tokens into public issues; redact (`token=REDACTED_len_N`).
- Authorized assessment only; stop if rate limits or mail systems risk other users.

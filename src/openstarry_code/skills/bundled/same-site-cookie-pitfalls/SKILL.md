---
name: same-site-cookie-pitfalls
description: >-
  SameSite cookie attribute pitfalls for Lax, Strict, and None; browser defaults,
  top-level navigation exceptions, cross-site POST gaps, and CSRF interactions.
  Use when session cookies lack or mis-set SameSite, CSRF defenses depend only on
  browser cookie attachment, OAuth/login sets cookies cross-site, or remediation
  reviews claim SameSite alone blocks forgery. Authorized assessments only.
---

# SameSite Cookie Pitfalls

## Scope And Authorization

- Authorized applications, labs, and owned test accounts only. Do not phish real users or host drive-by PoCs outside program rules.
- Prefer demonstrating state change or cookie attachment on **your** session. Avoid irreversible admin or payment actions unless explicitly approved.
- SameSite behavior is **browser-dependent**; document browser, version, and third-party cookie settings. Do not assume one engine equals all clients.
- Redact full session cookies in reports; rotate shared lab sessions after demos when needed.

## When To Use

- `Set-Cookie` shows `SameSite=Lax`, `Strict`, `None`, or **missing** SameSite on auth/session cookies.
- CSRF testing needs a precise matrix of when cookies attach (top-level GET vs cross-site POST vs iframe).
- Claims that "SameSite fixes CSRF" without tokens, Origin checks, or custom headers.
- Cross-site login, OAuth callback, SSO, or payment return flows set or refresh session cookies.
- Chrome/Safari third-party cookie changes, CHIPS/`Partitioned`, or embedded widgets break or weaken assumptions.
- Not primary for pure CORS **reads** → `cors-cross-origin-misconfiguration`; for full CSRF token/method workflow → `csrf-cross-site-request-forgery`.

## Workflow

1. **Inventory cookies that carry auth**  
   From proxy/DevTools, list cookies used for identity (session, JWT-in-cookie, CSRF double-submit partners). Record for each:

   | Field | Capture |
   | --- | --- |
   | Name / Domain / Path | Scope of attachment |
   | SameSite | Strict / Lax / None / absent |
   | Secure / HttpOnly | Cross-scheme and JS exposure |
   | Partitioned / host-only | Embedded context notes |

2. **Establish browser baseline**  
   Modern Chromium often treats **missing** SameSite as **Lax** for most cookies; legacy clients may send cookies more freely. Test with the victim profile the program cares about (desktop Chrome, Safari ITP, embedded WebView). Note if third-party cookies are blocked entirely — that changes None impact.

3. **SameSite=Strict pitfalls**  
   - Cookies **not** sent on any cross-site request, including top-level GET from another site.  
   - Users arriving via external link (email, ads, OAuth return to wrong path) may appear logged out until a same-site navigation.  
   - **Bypass class for CSRF:** Strict does not stop same-site attackers (XSS, open redirect on target origin, subdomain takeover if cookie Domain is parent). Route those to matching skills.  
   - Subdomain siblings: `Domain=.example.com` + Strict still attaches for `a.example.com` → `b.example.com` if considered same-site (schemeful same-site rules matter).

4. **SameSite=Lax pitfalls (most common)**  
   - Cookies **sent** on top-level GET navigations (links, `window.location`, some redirects).  
   - Cookies **not** sent on cross-site POST forms, most XHR/fetch from other origins, or iframe subrequests (typical).  
   - **CSRF-relevant gaps:**
     - State-changing **GET** (or POST coerced to GET).  
     - Method override: top-level GET with `_method=POST` / `X-HTTP-Method-Override` while Lax still attaches.  
     - **Lax-allowing** window: some browsers delayed full Lax enforcement on new cookies (document if still relevant to target clients); re-test current engines rather than citing old writeups alone.  
   - Login/session fixation style issues: attacker may still influence login CSRF if tokens absent — note separately under CSRF skill.

5. **SameSite=None pitfalls**  
   - Requires `Secure`; without Secure, browsers should reject.  
   - Cookie sent on cross-site requests when third-party cookies allowed → **full CSRF surface** unless synchronizer/double-submit tokens, Origin binding, or non-cookie auth.  
   - Embedded checkout, iframes, and partner widgets often force None; treat as high priority for token review.  
   - Partitioned cookies (CHIPS) limit cross-site sharing to the top-level partition — verify whether the app actually sets `Partitioned` or only documents it.

6. **Cross-check CSRF defenses (do not stop at SameSite)**  
   For each sensitive mutation, record whether:

   - CSRF token is required on all methods that can change state.  
   - Origin/Referer is validated (not sole defense).  
   - Auth is Bearer header only (browser cannot set from pure HTML form) vs ambient cookie.  
   Route detailed token mutation and PoC delivery to `csrf-cross-site-request-forgery`.

7. **Prove attachment behavior**  
   Authorized dual-browser or lab:

   - Attacker page: form POST to state-change URL vs top-level GET navigation.  
   - Observe whether session cookie is present on the request (proxy from victim browser).  
   - Confirm side effect only when cookie attached **and** other defenses fail.  
   Document: browser, SameSite value, request type, cookie present Y/N, outcome.

8. **Remediation guidance (implementation)**  
   Prefer defense-in-depth: SameSite=Lax or Strict **plus** CSRF tokens on cookie-auth mutations; `Secure` + `HttpOnly`; avoid `None` unless embedding requires it, then mandate tokens and tight Origin checks. Hand code review to `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Full CSRF token / method / Referer testing | `csrf-cross-site-request-forgery` |
| Cross-origin **read** of credentialed JSON | `cors-cross-origin-misconfiguration` |
| Open redirect gadget enabling same-site hop | `open-redirect` |
| XSS on target expanding same-site power | `xss-cross-site-scripting` / `injection-checking` |
| Cookie flags and secure session implementation | `code-quality-standards` |
| OAuth/SSO cookie issuance context | `oauth-oidc-misconfiguration` / `saml-sso-basics` |

## Output Checklist

- [ ] Cookie table: name, Domain/Path, SameSite, Secure, HttpOnly, Partitioned
- [ ] Browser/engine under test and third-party cookie policy
- [ ] Matrix: top-level GET / cross-site POST / iframe / fetch — cookie attached?
- [ ] CSRF interaction: which actions remain forgeable under observed SameSite
- [ ] Working authorized PoC note (URL or form) tied to attachment evidence
- [ ] Remediation: token + SameSite + avoid unnecessary None; retest plan

## Rules

- SameSite is **not** a complete CSRF control. Never close a finding only because Lax is set if GET or method-override paths exist.
- Schemeful same-site: `http://` vs `https://` siblings may differ; record scheme.
- Mobile WebViews and in-app browsers may diverge from desktop defaults — call out when in scope.
- Do not confuse "site" (registrable domain + scheme) with "origin" (scheme+host+port).
- Prefer one reproducible attachment matrix over a laundry list of historical browser bugs.

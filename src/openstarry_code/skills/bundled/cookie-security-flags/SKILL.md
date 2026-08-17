---
name: cookie-security-flags
description: >-
  Assess and harden HTTP cookie flags: Secure, HttpOnly, SameSite, Domain,
  Path, Prefixes (__Host-/__Secure-), and Max-Age/Expires. Use when reviewing
  session or auth cookies for missing flags, overly broad scope, CSRF exposure,
  or XSS cookie theft risk on authorized applications.
---

# Cookie Security Flags — Assessment And Hardening

## Scope And Authorization

- Authorized apps, labs, CTFs, and owned systems only. Use **test accounts** you control.
- Never publish full session values; report name + flags + length/hash. Prefer clean browser profiles.
- CSRF/XSS proofs that depend on flag gaps stay within program rules; PoCs only on allowed hosts.

## When To Use

- Login, SSO callback, remember-me, CSRF double-submit, or cookie-based API auth is in scope.
- Review asks for cookie hardening, SameSite matrix, or `Set-Cookie` audit.
- Suspect XSS theft (no `HttpOnly`), cleartext/MITM (no `Secure`), cross-site CSRF (`SameSite=None`/absent), or subdomain fixation (broad `Domain=`).
- After `session-fixation-management` or `csrf-cross-site-request-forgery` when the root issue is flag/scope misconfiguration.
- Implementing cookie auth middleware — pair with `code-quality-standards`.

## Core Model

```
Set-Cookie flags → storage scope (Domain/Path/Secure/lifetime)
  → attachment (SameSite × request kind) → script access (HttpOnly)
```

| Attribute | Intent | Typical failure |
| --- | --- | --- |
| **Secure** | HTTPS-only | Theft on HTTP / mixed content |
| **HttpOnly** | Block `document.cookie` | XSS → session theft |
| **SameSite** | Cross-site attach policy | CSRF if None/absent + weak token |
| **Domain** | Host scope | Sibling subdomain set/read |
| **Path** | Path scope | Attach on sibling apps |
| **Max-Age/Expires** | Lifetime | Long-lived stolen sessions |
| **__Host-** | Secure + Path=/ + no Domain | Tight host binding |
| **__Secure-** | Requires Secure | Weaker than __Host- |

**Good proof:** Cookie attaches or is script-readable under a condition the flag should block.  
**Bad proof:** Flag laundry list with no browser scenario or related control considered.

## Workflow

1. **Inventory cookies** at login, refresh, logout, SSO callback:

   | Field | Capture |
   | --- | --- |
   | Name / purpose | session, refresh, CSRF, preference |
   | Secure / HttpOnly | yes/no |
   | SameSite | Strict / Lax / None / **absent** |
   | Domain / Path | host-only vs `.parent`; `/` vs prefix |
   | Lifetime / prefix | session vs Max-Age; `__Host-` / `__Secure-` |

   ```http
   Set-Cookie: session=REDACTED; Path=/; HttpOnly; Secure; SameSite=Lax
   Set-Cookie: csrf=REDACTED; Path=/; Secure; SameSite=Strict
   ```

   Note cookies set on subdomains, CDN hosts, or OAuth redirects separately.

2. **Browser defaults** — Missing `SameSite` defaults toward Lax on modern Chrome; other engines differ. Record test browser. `SameSite=None` without `Secure` is dropped in modern browsers — confirm jar contents, not headers alone.

3. **Secure** — Auth cookies without `Secure` on HTTPS sites are cleartext/MITM risks. If HTTP remains in scope, verify the cookie is sent on `http://`. HSTS does not replace `Secure` on first visit.

4. **HttpOnly** — Session without `HttpOnly`: on authorized same-origin script context, confirm name appears in `document.cookie` (value redacted). CSRF cookies may omit HttpOnly intentionally if JS double-submit is designed (`csrf-cross-site-request-forgery`). HttpOnly does not stop network attachment or URL SID fixation (`session-fixation-management`).

5. **SameSite matrix**

   | Value | Cross-site behavior | Test focus |
   | --- | --- | --- |
   | **Strict** | Not sent cross-site | On-site gadgets (open redirect, XSS) |
   | **Lax** | Top-level GET yes; cross-site POST no | State-changing GET / method override |
   | **None; Secure** | Sent including POST | Token defenses must hold |
   | **Absent** | Browser-dependent | Victim browser profile |

   ```html
   <script>location = "https://target.example/account";</script>
   <form action="https://target.example/email/change" method="POST">
     <input name="email" value="attacker@test.example">
   </form>
   <script>document.forms[0].submit();</script>
   ```

   In proxy, check whether `Cookie:` included the session. Full CSRF methodology → `csrf-cross-site-request-forgery`.

6. **Domain and Path** — Prefer host-only (omit `Domain`) for sessions. `Domain=.example.com` exposes sibling hosts; weaker sibling XSS/set-cookie enables fixation or theft depending on HttpOnly. Over-broad `Path=/` may attach admin sessions to less trusted apps — note boundaries; test siblings only if in scope.

7. **Prefixes** — `__Host-name=...; Secure; Path=/` without `Domain` is strongest common pattern (browsers reject bad `__Host-` combos). `__Secure-` only requires `Secure`. Recommend prefixes for new session cookies.

8. **Lifetime and logout** — Long `Max-Age` widens theft window; remember-me should be a separate revocable token. Logout clear must match Domain/Path/Secure/SameSite. Flags alone do not fix missing regenerate-on-login → `session-fixation-management`.

9. **Chains** — Open redirect + Lax session as GET CSRF gadget → `open-redirect` / `open-redirect-advanced`. OAuth callback briefly setting `SameSite=None` — retest after login settles. Weak double-submit CSRF cookie → CSRF skill.

10. **Remediation** (with `code-quality-standards`)

    ```
    Set-Cookie: __Host-session=<id>; Path=/; Secure; HttpOnly; SameSite=Lax
    # CSRF double-submit: Secure; SameSite=Strict; omit HttpOnly only if JS must read
    # Avoid parent Domain= unless required; document sibling risk
    ```

    Check framework knobs: Express cookie/session; ASP.NET `CookieSecurePolicy`/`SameSite`; Spring `CookieSerializer`; Django `SESSION_COOKIE_*`; Rails `same_site`.

## Routing

| Need | Skill |
| --- | --- |
| CSRF exploitation / token bypass | `csrf-cross-site-request-forgery` |
| Pre-auth SID accepted after login | `session-fixation-management` |
| Redirect gadgets / token leak | `open-redirect`, `open-redirect-advanced` |
| OAuth callback session binding | `oauth-oidc-misconfiguration` |
| XSS reading non-HttpOnly cookies | `xss-cross-site-scripting` |
| Implement cookie options / middleware | `code-quality-standards` |

## Output Checklist

- [ ] Cookie inventory (name, purpose, flags, Domain, Path, lifetime, prefix)
- [ ] Browser(s) and SameSite-default notes for absent attributes
- [ ] Secure / HttpOnly / SameSite evidence (attach or script access)
- [ ] Domain/Path breadth and sibling risk
- [ ] Logout clear effectiveness
- [ ] CSRF / fixation / OAuth / redirect interactions
- [ ] Target `Set-Cookie` profile + regenerate-on-login reminder
- [ ] Redaction of full session values

## Rules

- Verify jar and request `Cookie` headers — do not trust docs alone.
- HttpOnly ≠ “session safe”; still need regenerate, CSRF defenses, tight Domain.
- `SameSite=None` without a CSRF design is a finding.
- Prefer host-only + `__Host-` for new session cookies when compatible.
- One evidenced cross-site attach or JS read beats a generic missing-flags list.
- Authorized testing only; rotate shared test sessions after demos.

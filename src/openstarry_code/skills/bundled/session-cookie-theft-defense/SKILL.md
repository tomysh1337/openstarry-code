---
name: session-cookie-theft-defense
description: >-
  Defend against session cookie theft with secure cookie flags, session binding,
  rotation and invalidation, short lifetimes, and theft-window reduction. Use when
  hardening cookie-based sessions, designing session middleware, responding to XSS
  or network theft risk, or reviewing session lifecycle after auth events.
---

# Session Cookie Theft Defense

## When To Use

- Designing or reviewing **cookie-based sessions** (opaque SID or signed session cookie).
- Reducing impact of **XSS cookie exfil**, **MITM / cleartext leak**, **subdomain Set-Cookie**, or **long-lived stolen SIDs**.
- Implementing login, logout, MFA step-up, password change, or refresh paths that must **rotate or rebind** sessions.
- Threat model or remediation asks for session theft hardening, cookie binding, session rotation, or stolen-cookie window.
- Not primary for pure **fixation** or **flag-only audits** — route those to helpers; keep this skill for **theft-resistance as a system**.

## Scope And Authorization

- Authorized applications, owned systems, labs, and CTFs only.
- Use **test accounts** you control. Do not exfiltrate or reuse real-user sessions.
- Redact full cookie values; report name, flags, lifetime, and hash/length only.
- Active theft simulation (XSS, MITM lab) stays within program rules; prefer non-production.
- Pair implementation with `code-quality-standards` (tests, no secrets in logs).

## Workflow

1. **Threat-model the theft surface**

   | Vector | Typical cause | Primary mitigations |
   | --- | --- | --- |
   | Script read | Missing `HttpOnly`, XSS | HttpOnly + XSS fix + short TTL |
   | Network | Missing `Secure`, HTTP | Secure + HSTS + TLS only |
   | Subdomain / Path | Broad `Domain=` / shared Path | Host-only + `__Host-` + tight Path |
   | Malware / extension | Client compromise | Binding + step-up + revoke |
   | Logs / Referer | SID in URL or verbose logs | No URL SID; redact logs |
   | Long idle reuse | No absolute/idle timeout | Rotate + server revoke |

   **Theft** = post-auth SID stolen. **Fixation** = pre-auth SID forced → `session-fixation-management`.

2. **Inventory session cookies** at login, refresh, SSO callback, logout: name/role, Secure/HttpOnly/SameSite, Domain/Path, prefix (`__Host-` / `__Secure-`), Max-Age vs session, opaque server store vs signed blob. Deep attribute audit → `cookie-security-flags`.

3. **Hardening baseline (flags + scope)**

   ```http
   Set-Cookie: __Host-session=<opaque>; Path=/; Secure; HttpOnly; SameSite=Lax
   ```

   - Prefer host-only (omit `Domain`); avoid parent `Domain=.example.com` unless required.
   - Prefer `__Host-` when compatible. Always `HttpOnly` + `Secure` on HTTPS apps.
   - `SameSite=Lax` or `Strict`; `None; Secure` only with a deliberate CSRF design.
   - Separate **remember-me** / refresh: revocable server-side, rotated, not immortal session clones.
   - Logout: clear cookie with **matching** attributes and **destroy** the server record.

4. **Rotation and invalidation (shrink the theft window)**  
   Regenerate SID and invalidate the previous server record on: login/SSO success, MFA enroll/step-up, password or email change, logout, admin/user “revoke all sessions”.

   - Set **idle** and **absolute** lifetimes (e.g. idle 30m, absolute 8–24h for high risk).
   - Bound concurrent sessions when product allows.
   - On suspected theft: revoke all subject sessions; force re-auth; optional notify.
   - Never put SID in URLs, fragments, or cross-origin `postMessage`.
   - Knobs (verify docs): PHP `session_regenerate_id(true)`; Express `req.session.regenerate`; ASP.NET re-issue ticket; Java `changeSessionId()`; Rails `reset_session`.

5. **Session binding (raise cost of replay elsewhere)**

   | Binding | Guidance |
   | --- | --- |
   | Network / TLS | Soft-bind IP prefix/ASN if needed; step-up on hard change (mobile/CGNAT) |
   | UA / device | Hash stable client hints; mismatch → challenge |
   | Refresh family | Refresh rotation with reuse detection → kill family |
   | amr / ACR | High-risk actions need recent MFA, not cookie alone |
   | Integrity | Opaque random SID; signed cookies reject tampering; rotate signing secrets |

   Prefer **step-up** over hard kill when confidence is medium. Avoid brittle over-binding that locks legit users.

6. **Complementary controls**  
   Fix XSS/CSP; keep CSRF tokens even with SameSite; enable HSTS (still set `Secure`); re-auth for money move / API-key mint / email change; monitor geo/IP diversity or refresh reuse → revoke; log **SID hash** only.

7. **Verify defenses** (test accounts)  
   (1) Flags in jar and request `Cookie` headers. (2) Copy SID to second client → fail, step-up, or documented soft-bind behavior. (3) Login and password change mint new SIDs; old SID dead. (4) Logout rejects old SID server-side. (5) Remember-me revoke works without waiting for Max-Age.

8. **Implement with `code-quality-standards`**  
   Centralize cookie options; unit-test `Set-Cookie` attributes; store delete-on-rotate with TTL = absolute timeout; regression tests for regenerate, logout invalidation, no SID in URLs.

## Routing

| Need | Skill |
| --- | --- |
| Set-Cookie flag / Domain / SameSite / prefix audit | `cookie-security-flags` |
| Pre-auth SID kept after login; attacker-chosen SID | `session-fixation-management` |
| Session middleware, tests, secure defaults | `code-quality-standards` |
| XSS as theft vector | `xss-cross-site-scripting` |
| CSRF when SameSite=None or state-changing GET | `csrf-cross-site-request-forgery` |
| JWT/refresh theft and rotation families | `jwt-refresh-token-patterns`, `api-auth-and-jwt-abuse` |
| Multi-vector ATO chaining | `account-takeover-methodology` |

**Primary vs helper:** This skill = **defense architecture** (flags + binding + rotation + revoke). `cookie-security-flags` = attribute assessment. `session-fixation-management` = missing regenerate / attacker-controlled pre-auth SID.

## Output Checklist

- [ ] Cookie inventory (names, roles, flags, Domain/Path, lifetime, prefix)
- [ ] Theft vectors considered (XSS, network, subdomain, logs, long TTL, malware)
- [ ] Target Set-Cookie profile (`__Host-` / host-only / Secure / HttpOnly / SameSite)
- [ ] Rotation events (login, MFA, password, logout, admin revoke)
- [ ] Idle + absolute timeout; concurrent-session policy
- [ ] Binding and step-up rules (re-auth vs hard revoke)
- [ ] Server invalidation proven (copy SID / post-logout / post-rotate)
- [ ] Logging redaction; remember-me/refresh revoke design
- [ ] Helpers: `cookie-security-flags`, `session-fixation-management`, `code-quality-standards`
- [ ] Residual risk: HttpOnly ≠ network-safe; binding is probabilistic

## Rules

- Flags reduce likelihood; **rotation + server revoke** reduce impact of successful theft.
- HttpOnly blocks `document.cookie`, not wire attachment or malware.
- Do not relabel fixation as theft, or post-login cookie copy as fixation.
- Prefer opaque server SIDs; treat refresh/remember tokens as equally sensitive.
- Authorized hardening only; rotate shared test sessions after demos.

---
name: django-csrf-middleware-tuning
description: >
  Tune and review Django CsrfViewMiddleware and CSRF-related settings:
  CSRF_TRUSTED_ORIGINS, cookie flags, header names, exemptions, and middleware
  order for cookie-authenticated browser apps. Use when Django CSRF 403s after
  deploy, SPA/API Origin mismatches, CSRF_COOKIE_* / CSRF_TRUSTED_ORIGINS
  hardening, @csrf_exempt audit, or DRF session-auth CSRF wiring on owned apps.
---

# Django CSRF Middleware Tuning

Hardening and diagnostics for **Django CSRF** (`CsrfViewMiddleware` + settings)
on systems you own or are authorized to review. Prefer correct Origin/cookie
design over blanket exemptions.

## Scope And Authorization

- **In scope:** org-owned Django settings, staging/prod under engagement, labs/CTFs
  with Django config, authorized hardening PRs.
- **Out of scope:** forging CSRF on third-party sites without permission; mass
  probing of public admin; disabling CSRF in prod without a compensating control
  and owner sign-off.
- Prefer settings/middleware review and controlled requests with **test accounts**.
  Redact `csrftoken`/session values; store raw captures offline.
- Active browser CSRF PoCs → `csrf-cross-site-request-forgery` under the same rules.

## When To Use

- Cookie/session auth hits `403 CSRF verification failed` after domain, HTTPS, or SPA origin changes
- Reviewing `CSRF_TRUSTED_ORIGINS`, `CSRF_COOKIE_*`, `CSRF_HEADER_NAME`,
  `CSRF_USE_SESSIONS`, or `CsrfViewMiddleware` placement
- Auditing `@csrf_exempt` / `csrf_protect` / `ensure_csrf_cookie`, or DRF
  `SessionAuthentication` CSRF expectations
- Subdomain, reverse-proxy, or multi-front-end Origin mismatches
- Mentions: Django CSRF, `CsrfViewMiddleware`, trusted origins, csrf cookie

Do **not** use as primary for: broad Django `SECURE_*` / `DEBUG` / `SECRET_KEY`
(`django-security-settings`); cookie flag matrix (`cookie-security-flags`); full
cross-site exploit methodology (`csrf-cross-site-request-forgery`); Bearer-only
APIs with no cookie session (CSRF often N/A — `api-auth-and-jwt-abuse`).

## Repo Config First

Repo conventions **outrank** defaults below.

1. **Settings modules:** `base` / `local` / `prod` (or env-driven single module)
2. **`MIDDLEWARE` order:** `SessionMiddleware` before `CsrfViewMiddleware`
3. **Deploy topology:** public hostnames, SPA origins, admin host, TLS terminator
4. **Proxy:** `SECURE_PROXY_SSL_HEADER` / `USE_X_FORWARDED_HOST` only if trusted
5. **Frontends:** templates vs SPA (cookie + header) vs pure Bearer clients
6. **DRF / allauth / custom auth** already setting CSRF or exemptions
7. **CI:** `manage.py check --deploy`, settings tests, `@csrf_exempt` lint

**Precedence:** Follow the repo. Flag global CSRF disable, empty
`CSRF_TRUSTED_ORIGINS` with cross-site frontends, or `CSRF_COOKIE_SECURE=False`
on HTTPS prod.

## Workflow

1. **Inventory** — Prod settings module; every `CSRF_*` key; confirm
   `django.middleware.csrf.CsrfViewMiddleware` is present once.

2. **Middleware order** — Required pattern:

   ```text
   SecurityMiddleware → SessionMiddleware → CommonMiddleware →
   CsrfViewMiddleware → AuthenticationMiddleware → …
   ```

   Missing session middleware breaks cookie/session CSRF; wrong order → flaky 403s.

3. **Trusted origins (Django 4+)** — Cross-site/port mutating frontends need
   scheme+host (no bare hosts, no `*`):

   ```python
   CSRF_TRUSTED_ORIGINS = [
       "https://app.example.com",
       "https://admin.example.com",
       "https://localhost:5173",  # local SPA ports as needed
   ]
   ```

4. **Cookie controls**

   | Setting | Hardened direction |
   | --- | --- |
   | `CSRF_COOKIE_SECURE` | `True` on HTTPS |
   | `CSRF_COOKIE_HTTPONLY` | `False` if JS must read for `X-CSRFToken`; else True |
   | `CSRF_COOKIE_SAMESITE` | `Lax` default; `Strict` if UX allows; avoid bare `None` |
   | `CSRF_COOKIE_DOMAIN` | Prefer host-only (unset); parent domain widens exposure |
   | `CSRF_COOKIE_PATH` / `NAME` / `AGE` | Match layout; document renames |
   | `CSRF_USE_SESSIONS` | `True` stores token in session (no CSRF cookie) |

   Align `SESSION_COOKIE_SECURE` / `SESSION_COOKIE_SAMESITE`. Deep flags →
   `cookie-security-flags`.

5. **Header / body token** — SPA double-submit: cookie `csrftoken` + header
   `X-CSRFToken` (`CSRF_HEADER_NAME` → `HTTP_X_CSRFTOKEN`). Templates:
   `{% csrf_token %}`. Masked tokens are normal.

6. **Exemptions** — Audit `@csrf_exempt` / `csrf_exempt(view)`. Accept only for
   non-cookie auth (signed webhooks, pure Bearer) with documented controls.
   Re-apply `@csrf_protect` on cookie-auth paths.

7. **DRF** — `SessionAuthentication` enforces Django CSRF on unsafe methods.
   JWT/Token auth does not replace CSRF on session-cookie routes.

8. **Proxy / HTTPS** — Trusted `SECURE_PROXY_SSL_HEADER` so Django sees HTTPS;
   keeps Secure cookies and Origin checks aligned after TLS termination.

9. **Verify** — Tokened POST OK; strip/wrong token → 403; SPA only for listed
   origins; `check --deploy` reviewed; `code-quality-standards` on edits.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Django CSRF middleware/settings, trusted origins, exemptions | **This skill** | — |
| Broad Django `SECURE_*`, DEBUG, SECRET_KEY, HSTS | `django-security-settings` | this for CSRF slice |
| Cookie flag inventory | `cookie-security-flags` | this for Django knobs |
| Browser CSRF exploit / PoC | `csrf-cross-site-request-forgery` | this for config |
| Session not rotated on login | `session-fixation-management` | — |
| CORS ACAO/credentials | `cors-cross-origin-misconfiguration` | this when Origin+CSRF |
| Settings/view implementation quality | `code-quality-standards` | **always** on code changes |

Keep **this skill primary** for Django CSRF configuration. Hand attack proofs to
`csrf-cross-site-request-forgery`; broad deploy checklist to `django-security-settings`.

## Output Checklist

- [ ] Scope recorded; only owned or engaged targets
- [ ] Effective settings module + full `CSRF_*` inventory
- [ ] `CsrfViewMiddleware` present; order after `SessionMiddleware`
- [ ] `CSRF_TRUSTED_ORIGINS` scheme+host matches frontends (no `*`)
- [ ] CSRF cookie Secure/SameSite/Domain/HttpOnly fit HTTPS and SPA
- [ ] `CSRF_USE_SESSIONS` / header name documented if non-default
- [ ] `@csrf_exempt` paths listed with compensating controls or removed
- [ ] DRF session routes CSRF-protected; Bearer-only routes labeled
- [ ] Proxy HTTPS/host trust consistent with Secure cookies and Origin
- [ ] Evidence: allowed POST vs token-stripped 403 (redacted tokens)
- [ ] Residual risks noted; `code-quality-standards` applied on edits

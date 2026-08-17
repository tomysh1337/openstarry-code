---
name: django-security-settings
description: >
  Django settings security checklist for org-owned projects: DEBUG, SECRET_KEY,
  ALLOWED_HOSTS, CSRF/CORS/cookies, SSL redirect, HSTS, XSS/clickjacking
  middleware, and safe production settings modules. Use when Django security
  settings, django settings hardening, SECRET_KEY, ALLOWED_HOSTS, CSRF_COOKIE,
  or SECURE_* flags review.
---

# Django Security Settings

Harden **Django** project settings and security middleware for systems you own
or are authorized to review. Focus on **deployment flags**, **host/cookie trust**,
and **safe defaults** — not exploiting third-party Django sites.

## Use When

- Reviewing `settings.py`, split settings packages, or env-driven Django config
- Prod may run `DEBUG=True`, weak/hard-coded `SECRET_KEY`, or open `ALLOWED_HOSTS`
- CSRF, session cookies, HTTPS redirect, or HSTS need confirmation
- CORS, admin exposure, or middleware order is unclear
- Mentions: Django security settings, `SECURE_*`, `SECRET_KEY`, `ALLOWED_HOSTS`,
  CSRF cookie, Django production checklist

Do **not** use as primary for: vault/rotation (`secrets-management-hygiene`),
form/API allowlists (`input-validation-patterns`), template XSS encoding detail
(`output-encoding-patterns`), code baseline (`code-quality-standards`),
full XSS methodology (`xss-cross-site-scripting`).

## Repo Config First

Repo conventions **outrank** defaults below.

1. **Settings layout:** single module vs `base` / `local` / `prod`
2. **Env loader:** `django-environ`, pydantic-settings, or custom `os.environ`
3. **Proxy topology:** TLS terminator; whether `SECURE_PROXY_SSL_HEADER` applies
4. **Middleware + apps:** CORS, allauth, DRF already configured
5. **Deploy:** `DJANGO_SETTINGS_MODULE`, Docker/K8s/PaaS env injection
6. **CI:** `manage.py check --deploy`, secret scan, settings tests
7. **Admin / static / media** hosting already documented

**Precedence:** Follow the repo. Flag prod `DEBUG`, committed `SECRET_KEY`, or
global CSRF disable “for the SPA” without a replacement control.

## Workflow

1. **Inventory** — which settings module loads in prod; env keys; secret injection
   (`secrets-management-hygiene`).
2. **Core flags** — `DEBUG=False` in prod; strong unique `SECRET_KEY` from env/vault
   (never git); explicit `ALLOWED_HOSTS` (no `*` in prod).
3. **HTTPS / proxy** — `SECURE_SSL_REDIRECT` and HSTS only when HTTPS is real;
   set `SECURE_PROXY_SSL_HEADER` only if a **trusted** proxy overwrites proto.
4. **Cookies / CSRF** — `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, suitable
   `SameSite`; explicit `CSRF_TRUSTED_ORIGINS`; no blanket `@csrf_exempt` on
   cookie-authenticated POSTs without alternate anti-CSRF.
5. **Middleware / headers** — keep SecurityMiddleware and clickjacking middleware;
   set `X_FRAME_OPTIONS` / CSP as needed; `SECURE_CONTENT_TYPE_NOSNIFF`.
6. **Output** — autoescape on; no user-controlled `mark_safe`
   (`output-encoding-patterns`).
7. **Input** — forms/serializers/uploads use allowlists and size caps
   (`input-validation-patterns`).
8. **Verify** — `python manage.py check --deploy`; confirm env-only secrets;
   staging HTTPS/cookie checks; `code-quality-standards` on loader changes.

## Good / Bad

**Good — prod sketch (env-injected)**

```python
DEBUG = env.bool("DJANGO_DEBUG", default=False)
SECRET_KEY = env.str("DJANGO_SECRET_KEY")  # required; no default
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = ["https://app.example.com"]
```

**Bad:** `DEBUG=True`, `SECRET_KEY="django-insecure-…"`, `ALLOWED_HOSTS=["*"]`,
`CORS_ALLOW_ALL_ORIGINS=True` with credentialed cookies.

**Good:** `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` only
behind a proxy that **overwrites** the header.

**Bad:** trusting client-supplied `X-Forwarded-Proto` on a public app port;
`@csrf_exempt` on session-cookie APIs without replacement controls.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Django settings, `SECURE_*`, hosts, cookies, CSRF | **This skill** | — |
| Settings/middleware implementation | `code-quality-standards` | **always** on code changes |
| Forms/serializers/upload validation | `input-validation-patterns` | this for Django placement |
| Templates / `mark_safe` / HTML sinks | `output-encoding-patterns` | this for autoescape defaults |
| `SECRET_KEY`, DB passwords, vault, rotation | `secrets-management-hygiene` | this for Django env wiring |

### Required helpers

- **`code-quality-standards`:** settings modules, middleware, deploy checks.
- **`input-validation-patterns`:** forms, DRF serializers, admin actions.
- **`output-encoding-patterns`:** sinks beyond autoescape; unsafe `mark_safe`.
- **`secrets-management-hygiene`:** secret storage/rotation; this skill keeps them out of source.

## Checklist

- [ ] Prod settings module + env injection documented
- [ ] `DEBUG=False`; no public debug toolbar
- [ ] `SECRET_KEY` from vault/env; not in VCS (`secrets-management-hygiene`)
- [ ] Explicit `ALLOWED_HOSTS`; no prod `*`
- [ ] SSL redirect + HSTS only with correct TLS termination
- [ ] `SECURE_PROXY_SSL_HEADER` only with trusted proxy
- [ ] Secure session/CSRF cookies; correct `CSRF_TRUSTED_ORIGINS`
- [ ] Security/clickjacking middleware on; nosniff / frame policy set
- [ ] Autoescape on; inputs allowlisted (`output-encoding-patterns` / `input-validation-patterns`)
- [ ] `check --deploy` clean or owned exceptions; CORS not `*` + credentials
- [ ] `code-quality-standards` on settings code; residual risks recorded

## Rules

- Never hard-code prod `SECRET_KEY` or ship `DEBUG=True` publicly.
- Fail startup when required secrets are missing; env-split settings preferred.
- CSRF/secure cookies default-on for browser session apps; document exempt paths.
- Repo layout wins; defense and **authorized** hardening only.
---

# Note

Owns **Django deployment security settings**. Pair with `code-quality-standards`,
`input-validation-patterns`, `output-encoding-patterns`, and
`secrets-management-hygiene`.

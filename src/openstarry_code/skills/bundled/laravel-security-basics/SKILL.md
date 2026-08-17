---
name: laravel-security-basics
description: >-
  Laravel security basics: APP_KEY, session/cookies, CSRF, mass assignment,
  policies, validation, rate limits, files, Sanctum/Passport. Use when reviewing
  Laravel config, $fillable/$guarded, Blade XSS, or hardening org-owned PHP apps
  — authorized only.
---

# Laravel Security Basics

Defensive baselines for **Laravel** (9/10/11-style). Prefer the project’s auth
stack (Breeze, Jetstream, Fortify, Sanctum, Passport) and env/config layout.

## Use When

- Reviewing or hardening Laravel web/API apps you own or may assess
- `APP_DEBUG=true`, weak `APP_KEY`, or secrets committed in `.env`
- CSRF/`VerifyCsrfToken` exceptions too broad; SPA cookie auth unclear
- Mass assignment (`$fillable`/`$guarded`), missing policies, IDOR-ish routes
- File uploads to public disk; unvalidated `Storage::` paths
- Mentions: Laravel security, Sanctum, Passport, `$fillable`, Blade, throttle, policy

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Deep JWT/token crypto abuse | `api-auth-and-jwt-abuse` |
| Browser CSRF PoC methodology | `csrf-cross-site-request-forgery` |
| Code quality, tests, structure | `code-quality-standards` |

## Repo Config First

Repo and Laravel version config **outrank** samples below.

1. Laravel version; Breeze/Jetstream/Fortify/UI
2. Auth: session, Sanctum (SPA cookie or token), Passport, Socialite
3. Config: `auth.php`, `session.php`, `cors.php`, `sanctum.php`, `filesystems.php`
4. Middleware: `bootstrap/app.php` or `Http/Kernel.php` (web vs api)
5. CSRF: `VerifyCsrfToken` `$except`; `SANCTUM_STATEFUL_DOMAINS`
6. Session driver; cookie `http_only`, `same_site`, `secure`
7. Models: `$fillable`/`$guarded`; `$hidden` for secrets
8. Policies, gates, FormRequest `authorize()`
9. Validation style; `$request->all()` call sites
10. Deploy: `APP_DEBUG`, trusted proxies, HTTPS termination

**Precedence:** Follow existing middleware/policy patterns. Surface global CSRF
disable, `$guarded = []` with user input, or debug mode in production.

## Workflow

1. **Inventory:** `web.php`/`api.php`/Livewire-Inertia; auth middleware; upload,
   reset, webhook routes; `.env` not web-served.
2. **Secrets / posture:** unique `APP_KEY` per env; `APP_DEBUG=false` in prod;
   `.env` out of git; framework password hasher only. Leaks → rotate first.
3. **Session / CSRF:** keep `VerifyCsrfToken` for cookie apps; audit `$except`;
   exact Sanctum stateful domains; regenerate session on login; invalidate on
   logout/password change. CSRF PoCs → `csrf-cross-site-request-forgery`.
4. **AuthZ / mass assignment:** policies over scattered `is_admin`; never
   `Model::create($request->all())` without tight `$fillable`; avoid
   `$guarded = []`; FormRequest auth+rules; authorize model instances (IDOR).
5. **Output / files / limits:** Blade `{{ }}`; audit `{!! !!}`; validate uploads;
   private disk + authorized download; no raw user paths into `Storage`/`file()`;
   throttle login/reset/costly APIs; bind SQL (audit `whereRaw`).
6. **Tokens:** Sanctum/Passport least privilege; revoke on password change; never
   log full tokens. Token crypto → `api-auth-and-jwt-abuse`.
7. **Verify:** guest/user/admin tests; CSRF 419; policy 403; prod debug off.

## Good / Bad Examples

**Good — policy + fillable**

```php
public function authorize(): bool
{
    return $this->user()->can('update', $this->route('post'));
}
// protected $fillable = ['title', 'body']; // not is_admin, user_id
```

**Bad**

```php
Post::create($request->all()); // protected $guarded = [];
```

**Good — CSRF for web; Bearer API separate**

```text
web: session + VerifyCsrfToken
api: auth:sanctum Bearer; no session-cookie auth for mutations
```

**Bad** — `protected $except = ['*'];` on `VerifyCsrfToken`.  
**Good** — `{{ $comment->body }}`  
**Bad** — `{!! $comment->body !!}` for untrusted HTML.  
**Good** — `Limit::perMinute(5)` on login by email+IP.  
**Bad** — unlimited login/forgot-password; debug public in prod.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Laravel config, CSRF, mass assignment, policies | **This skill** | — |
| Implementing fixes / tests | `code-quality-standards` | this skill |
| Sanctum/Passport/JWT token abuse | `api-auth-and-jwt-abuse` | this skill for wiring |
| Browser CSRF proofs | `csrf-cross-site-request-forgery` | this skill for SPA/CSRF |
| Session fixation on login | `session-fixation-management` | this skill |
| Password-reset host/token issues | `password-reset-poisoning` | this skill |
| `.env` / key rotation process | `secrets-management-hygiene` | this skill for APP_KEY |

Always apply **`code-quality-standards`** when changing app code. Use
**`api-auth-and-jwt-abuse`** for token/JWT assessment and
**`csrf-cross-site-request-forgery`** for cookie CSRF methodology.

## Checklist

- [ ] `APP_DEBUG=false` in prod; unique `APP_KEY`; `.env` not in VCS/web root
- [ ] Session cookies Secure/HttpOnly/SameSite fit deployment
- [ ] CSRF on for cookie mutations; `$except` justified
- [ ] Sanctum stateful domains / CORS not wildcard+credentials
- [ ] Tight `$fillable`; no `$request->all()` into create/update
- [ ] Policies/gates on sensitive actions; 403 tested
- [ ] FormRequest validation on mutating routes
- [ ] Blade/Inertia escaped; `{!! !!}` audited
- [ ] Uploads validated; private disk + authorized download
- [ ] Rate limits on auth and costly endpoints
- [ ] Tokens least-privilege; revoked on credential change
- [ ] Trusted proxies/HTTPS match the edge
- [ ] `code-quality-standards` + routed JWT/CSRF skills when needed

## Rules

- Authorized assessment and hardening only.
- Most issues are misconfig, broad `$except`, and mass assignment.
- Do not disable CSRF for “the API” if session cookies still authenticate.
- `APP_KEY` compromise implies cookie/session forgery — rotate and invalidate.
- Redact `.env`, tokens, and session cookies from reports.

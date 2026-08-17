---
name: angular-security-basics
description: >
  Angular client security: template encoding defaults, DomSanitizer,
  bypassSecurityTrust* review, HttpClient XSRF/CSRF, and auth interceptors.
  Use when reviewing Angular XSS sinks, innerHTML bindings, DomSanitizer
  bypass, HttpClient withCredentials, XSRF-TOKEN, HTTP interceptors for
  Bearer/cookie auth, or hardening org-owned Angular SPAs — authorized only.
---

# Angular Security Basics

Defensive baselines for **Angular** (Ivy / modern standalone or NgModule apps)
you own or are authorized to review. Prefer framework defaults (template
escaping, HttpClient XSRF) over custom HTML sinks and ad-hoc token plumbing.

## When To Use

- Reviewing Angular templates, `[innerHTML]`, SVG/URL/style bindings, or rich text
- `DomSanitizer` / `bypassSecurityTrustHtml|Url|Script|Style|ResourceUrl` usage
- HttpClient cookie auth, `withCredentials`, or `HttpClientXsrfModule` / XSRF headers
- Auth via `HttpInterceptor` / `HttpInterceptorFn` (Bearer attach, 401 refresh)
- Mentions: Angular security, DomSanitizer, bypassSecurityTrust, Angular CSRF/XSRF,
  interceptor auth, template encoding, Angular XSS

Do **not** use as primary for: full XSS methodology (`xss-cross-site-scripting`);
browser CSRF PoCs (`csrf-cross-site-request-forgery`); JWT crypto/claims abuse
(`api-auth-and-jwt-abuse`); CSP deep bypass (`content-security-policy-bypass`);
code reliability baseline (`code-quality-standards`); server/API hardening
(Express/FastAPI/Django skills).

## Repo Config First

Repo Angular version and existing security wiring **outrank** samples below.

1. Angular major version; standalone vs NgModule; zone vs zoneless
2. `HttpClient` providers: `provideHttpClient(withInterceptors(...), withXsrfConfiguration(...))`
3. Cookie vs Bearer auth; BFF/same-site vs cross-origin API base URL
4. Existing interceptors: auth, error, logging — order and registration
5. XSRF cookie/header names if customized; backend CSRF expectations
6. Sanitizer helpers or shared “safe HTML” pipes/components already in the monorepo
7. CSP / Trusted Types meta and deploy headers (nginx, CDN, Firebase, etc.)
8. Environment files: never commit live tokens; API origins per env

**Precedence:** Extend project interceptor and sanitizer patterns. Surface
global `bypassSecurityTrust*` helpers, disabled XSRF on cookie sessions, and
tokens in `localStorage` without threat-model review.

## Workflow

1. **Inventory sinks** — search templates and TS for `[innerHTML]`, `[outerHTML]`,
   `bypassSecurityTrust*`, `DomSanitizer`, dynamic `script`/`iframe`/`object`,
   `document.write`, direct `ElementRef.nativeElement` HTML assignment, and
   untrusted URL bindings (`[href]`, `[src]`, `routerLink` with external URLs).
2. **Trust template defaults** — interpolation `{{ }}` and property bindings encode
   for HTML context by default. Prefer text bindings over HTML. For intentional
   rich text: sanitize **server-side or with a vetted library**, then bind only
   the cleaned result — do not treat `bypassSecurityTrustHtml` as a sanitizer.
3. **Audit every bypass** — each `bypassSecurityTrustHtml|Url|Script|Style|ResourceUrl`
   needs: (a) proven trusted source or post-sanitize pipeline, (b) narrow helper
   (not a global “trust anything” pipe), (c) no user/query/storage input wired
   straight into bypass. Prefer `ResourceUrl` only for known embed allowlists.
4. **HttpClient CSRF/XSRF** — for cookie-authenticated mutating APIs on Angular’s
   default XSRF scheme, ensure the client reads the cookie and sends the header
   (`X-XSRF-TOKEN` / project names via `withXsrfConfiguration`). Confirm
   `withCredentials` (or equivalent) when cookies must cross the XHR boundary.
   Bearer-only APIs without cookie session auth do not replace server CSRF design
   for cookie routes — see `csrf-cross-site-request-forgery` for browser proofs.
5. **Interceptor auth** — attach `Authorization` only to intended API origins;
   never log tokens; on 401, single-flight refresh or re-login without loops;
   avoid storing long-lived access tokens in XSS-readable storage without a
   documented trade-off (prefer httpOnly cookies + BFF when the threat model
   prioritizes XSS). Deep JWT issues → `api-auth-and-jwt-abuse`.
6. **Defense in depth** — set a strict CSP for the SPA shell; avoid
   `unsafe-inline` where Trusted Types / nonces are feasible; keep
   `innerHTML` paths out of third-party script gadgets.
7. **Verify** — unit-test sanitizer helpers reject payloads; e2e check XSRF header
   on POST/PUT/PATCH/DELETE; interceptor tests for missing token and origin
   allowlist; manual review of any remaining bypass call sites.
8. **Implement** — apply `code-quality-standards` on interceptor and sanitizer code;
   keep secrets out of `environment*.ts` committed defaults
   (`secrets-management-hygiene`).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Angular templates, DomSanitizer, bypass*, HttpClient XSRF, auth interceptors | **This skill** | — |
| General XSS payloads / DOM sinks methodology | `xss-cross-site-scripting` | this skill for Angular wiring |
| Cookie CSRF proofs / SameSite methodology | `csrf-cross-site-request-forgery` | this skill for HttpClient XSRF |
| JWT alg/claims, refresh abuse | `api-auth-and-jwt-abuse` | this skill for interceptor attach |
| CSP policy / bypass research | `content-security-policy-bypass` | this skill for SPA sinks |
| Implementation quality, tests, errors | `code-quality-standards` | **always** on code changes |
| Token/secret storage process | `secrets-management-hygiene` | this skill for client placement |

Keep **this skill primary** for Angular client hardening. Always apply
**`code-quality-standards`** when changing app code. Hand deep XSS/CSRF/JWT
methodology to the skills above; do not re-derive them here.

## Output Checklist

- [ ] Scope is org-owned or explicitly authorized Angular app
- [ ] Template encoding relied on; unnecessary `[innerHTML]` removed or justified
- [ ] Every `bypassSecurityTrust*` call site listed with trust rationale
- [ ] No user/query/fragment/storage data piped raw into bypass helpers
- [ ] Rich HTML uses real sanitization before bind (not bypass-as-sanitizer)
- [ ] Cookie-session APIs: XSRF cookie/header wired; mutating verbs covered
- [ ] `withCredentials` / cookie policy matches API origin design
- [ ] Auth interceptor: origin allowlist, no token logs, sane 401/refresh
- [ ] Token storage choice documented (httpOnly/BFF vs accessible storage)
- [ ] CSP (and Trusted Types if used) aligned with remaining sinks
- [ ] Tests cover sanitizer rejects, XSRF header, interceptor auth failures
- [ ] `code-quality-standards` (+ XSS/CSRF/JWT helpers) applied where relevant
- [ ] Residual risks have owner and review date; secrets redacted in notes

## Rules

- Authorized review and hardening only — not attacks on third-party Angular sites.
- `bypassSecurityTrust*` means “skip Angular’s defenses”; treat each use as a
  security exception, not a convenience API.
- Framework template encoding is the default control; do not disable it globally.
- Client XSRF headers only work if the server validates them — verify both ends.
- Redact tokens, cookies, and PII from reports and examples.
---

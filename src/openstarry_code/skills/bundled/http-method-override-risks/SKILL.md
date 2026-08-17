---
name: http-method-override-risks
description: >
  Assess HTTP method override / method spoofing risks: X-HTTP-Method-Override,
  X-HTTP-Method, X-Method-Override, body/query _method, and framework tunnels that
  change the effective verb after WAF or auth middleware. Use when authorized tests
  show ACL or CSRF controls that gate only on the wire method (GET/POST) while the
  app honors overrides, or when 401/403/WAF rules look verb-bound.
---

# HTTP Method Override Risks (Authorized)

## When To Use

- State-changing routes accept `POST` with `_method=PUT|PATCH|DELETE` (Rails, Laravel,
  Symfony, Spring, Express middleware, ASP.NET overload).
- Clients or docs mention `X-HTTP-Method-Override`, `X-HTTP-Method`, or `X-Method-Override`.
- Edge/WAF/API gateway allows `GET`/`POST` but blocks `PUT`/`PATCH`/`DELETE`/`TRACE`.
- AuthZ or CSRF validation appears **method-dependent** (token on POST only; ACL on DELETE only).
- SameSite=Lax cookie CSRF research where GET + override may still mutate state.
- Not primary for pure path/IP 403 tricks — use `401-403-bypass-techniques`; use this
  skill when the **verb** is the control being spoofed.

## Workflow

1. **Baseline the real verbs**  
   For each sensitive route, record allowed methods without override: `OPTIONS`/`Allow`,
   and responses for `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`. Capture status,
   length, body hash, and auth context (anonymous / low-priv / admin).

2. **Inventory override surfaces** (one channel per trial):

   | Channel | Examples |
   | --- | --- |
   | Headers | `X-HTTP-Method-Override`, `X-HTTP-Method`, `X-Method-Override` |
   | Query | `?_method=DELETE`, `?method=PUT` |
   | Body (form) | `_method=PATCH` with `application/x-www-form-urlencoded` |
   | Body (JSON) | `{"_method":"DELETE"}` only if stack documents it |
   | Nested | Override header **and** `_method` with conflicting verbs |

   Prefer values: `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, and invalid tokens
   (`FOO`, empty, lowercase `delete`) to map parse rules.

3. **Spoof past wire-method gates**  
   Send an **allowed** outer method the edge permits, with override toward a privileged
   action the edge would block if sent natively:

   ```http
   POST /api/users/123 HTTP/1.1
   Host: target.example
   Content-Type: application/x-www-form-urlencoded
   X-HTTP-Method-Override: DELETE

   _method=DELETE
   ```

   Also try outer `GET` with `?_method=POST` or override header (CSRF / SameSite path):

   ```http
   GET /account/email?email=attacker@evil.test&_method=POST HTTP/1.1
   Host: target.example
   ```

   **Success** = privileged side effect or body matching the blocked native verb, not
   only a different error page.

4. **WAF / gateway vs origin split**  
   Compare native `DELETE` (often 403/405 at edge) vs `POST` + override (200/204 at
   origin). Log which hop denied (`Server`, `Via`, WAF headers). Edge-only fool without
   origin executing the verb is a config gap; full impact needs origin applying override
   after authz that trusted the outer method.

5. **Auth middleware ordering**  
   Hypothesis: middleware enforces “POST-only CSRF” or “no DELETE for role X” on the
   **request-line method**; router later rewrites to DELETE/PUT. Tests:
   - Low-priv session: outer POST (allowed) + override DELETE on admin resource.
   - CSRF token present/absent only on outer POST while effective verb is DELETE.
   - PUT requires auth natively, but `POST` + `_method=PUT` succeeds under weaker policy.

   Prove with two accounts or a canary you own; avoid mass deletes.

6. **CSRF implications**  
   If cookies authenticate and override turns navigable `GET` into a state change,
   build an authorized PoC (test victim only):

   ```html
   <script>
   location = "https://target.example/settings?email=pwned@evil.test&_method=POST";
   </script>
   ```

   Cross-check SameSite, Referer, and tokens under `csrf-cross-site-request-forgery`.
   Bearer-only APIs without cookies are usually CSRF-N/A — still note override for
   BOLA/ACL if middleware is verb-bound.

7. **Framework notes (measure, do not assume)**  
   Rails/Laravel: `_method` on POST forms. Some Java filters honor
   `X-HTTP-Method-Override` only for POST. ASP.NET may use `X-HTTP-Method-Override` or
   `X-Method-Override`. Field names vary (`_method`, `method`, `_METHOD`). Confirm with
   response differentials, not blog claims.

8. **Remediation**  
   Authorize on the **effective** method after one canonical parse; disable override on
   sensitive APIs; if needed for HTML forms, allowlist POST→PUT/PATCH/DELETE only, ignore
   overrides on GET, apply CSRF/authz to the effective verb; align WAF; add role-matrix tests.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Method override / verb spoof | **This skill** | — |
| Broad 401/403 path/IP tricks | `401-403-bypass-techniques` | this skill for verb channel |
| Cookie CSRF + `_method` / override | `csrf-cross-site-request-forgery` | this skill for override matrix |
| Object access after verb change | `idor-broken-object-authorization` | this skill |
| JWT/Bearer auth flaws | `api-auth-and-jwt-abuse` | — |
| H1/H2 desync changing method | `request-smuggling` / `http2-specific-attacks` | — |
| Secure middleware order / tests | `code-quality-standards` | this skill for cases |

## Output Checklist

- [ ] Scope, accounts, and non-destructive canary resources
- [ ] Baseline Allow / native verb matrix per endpoint
- [ ] Override channels tested (header / query / body) and winner on conflict
- [ ] Edge vs origin differential (status, body, side effect)
- [ ] AuthZ/CSRF behavior on outer vs effective method
- [ ] Redacted request/response pairs and reproduction steps
- [ ] Impact: privileged action, data change, or CSRF PoC (authorized host only)
- [ ] Remediation: canonical effective method, disable or allowlist override, align WAF

## Scope And Authorization

- Authorized apps, staging, labs, bug bounty, and CTFs only. Do not spoof methods against
  third-party infrastructure outside written scope.
- Prefer reversible proofs (toggle a test flag, soft-delete your own object). Avoid bulk
  `DELETE`, payments, or production admin wipes unless explicitly approved.
- Host HTML PoCs only on allowed exploit servers; use program-provided victim accounts.
- Redact cookies, tokens, and PII. Stop if testing risks lockouts or availability; throttle
  automated verb matrices.
- A different 405/HTML error alone is not a finding — require a security decision or state
  change tied to the effective method.

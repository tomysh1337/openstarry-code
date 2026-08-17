---
name: fetch-metadata-sec-headers
description: >
  Assess and implement Fetch Metadata request headers (Sec-Fetch-Site,
  Sec-Fetch-Mode, Sec-Fetch-Dest, Sec-Fetch-User) for CSRF mitigation and
  Resource Isolation Policy (RIP). Use when hardening or auditing same-origin
  vs same-site vs cross-site browser request isolation, missing Sec-Fetch
  checks on cookie-authenticated endpoints, top-level navigation allowlists,
  or server-side reject-cross-site policies on owned apps and authorized
  assessments.
---

# Fetch Metadata Sec-Fetch Headers (CSRF / Resource Isolation)

Use browser-sent **Fetch Metadata** headers to enforce **Resource Isolation
Policy (RIP)** and defense-in-depth against cross-site request forgery and
cross-site resource abuse. Owns **server policy on `Sec-Fetch-*`**. Classic
token/SameSite CSRF proofs → `csrf-cross-site-request-forgery`. Login-bind
forgery → `login-csrf-defense`.

## Scope And Authorization

- **In scope:** Owned apps, labs, CTFs, written-scope review of middleware that
  reads `Sec-Fetch-Site` / `Mode` / `Dest` / `User`, cookie-auth mutations,
  sensitive JSON or HTML document endpoints.
- **Out of scope:** Unauthenticated mass scanning; forging headers against
  third-party sites without permission; phishing real users.
- Headers are **browser-set and non-writable from page JS** in supporting
  browsers; treat non-browser clients (missing headers) as an explicit policy.
- Prefer dual test accounts and canary state changes. Redact cookies, tokens,
  and PII. Keep captures under derived paths.

## When To Use

- Implementing or reviewing **Resource Isolation Policy** / reject-cross-site
  middleware (Google-style RIP or org variants).
- Cookie/session endpoints lack CSRF tokens and rely (or claim to rely) on
  Fetch Metadata alone — verify completeness.
- Keywords: `Sec-Fetch-Site`, `Sec-Fetch-Mode`, `Sec-Fetch-Dest`,
  `Sec-Fetch-User`, same-origin vs same-site vs cross-site isolation.
- Hardening APIs that should refuse cross-site `no-cors` / embed loads while
  allowing top-level navigations and first-party XHR/fetch.
- After CORS or CSRF findings when the fix path is server-side Sec-Fetch gates.

**Not primary:** full CSRF token/SameSite methodology →
`csrf-cross-site-request-forgery`; forced login → `login-csrf-defense`;
credentialed CORS reads → `cors-credentialed-requests`; cookie flag audit →
`cookie-security-flags`.

## Workflow

### 1. Map header semantics

| Header | Common values | Security use |
| --- | --- | --- |
| `Sec-Fetch-Site` | `same-origin`, `same-site`, `cross-site`, `none` | Initiator relationship |
| `Sec-Fetch-Mode` | `navigate`, `cors`, `no-cors`, `same-origin`, `websocket` | Nav vs embed vs XHR |
| `Sec-Fetch-Dest` | `document`, `empty`, `image`, `script`, `style`, … | Consumer destination |
| `Sec-Fetch-User` | `?1` when user-activated | User gesture on navigation |

`none` ≈ typed URL/bookmark entry. `same-site` ≠ `same-origin` (eTLD+1 vs full origin).

### 2. Inventory protected surfaces

1. List cookie-auth **state changes** and sensitive **reads** (HTML docs, JSON
   “me”, exports, admin UI).
2. Per route: method, Content-Type, cookie `SameSite`, existing CSRF token /
   Origin checks, any Sec-Fetch middleware.
3. Note SPA same-origin fetches vs cross-site form POSTs and image/script embeds.

### 3. Baseline Resource Isolation Policy (RIP)

```text
Allow if Sec-Fetch-Site is absent → non-browser/old-client policy (step 5)
Allow if Sec-Fetch-Site in {same-origin, same-site, none}
Allow if Mode == navigate AND Dest == document
  (optional: Sec-Fetch-User == ?1 for sensitive GET navigations)
Else reject (403/400) cross-site non-navigation / embed / no-cors abuse
```

**Goal:** Block cross-site simple POSTs and sensitive `no-cors` embeds while
keeping first-party pages and top-level navigations working.

### 4. Authorized verification matrix

| Scenario | Expect headers (approx.) | Expect policy |
| --- | --- | --- |
| First-party `fetch`/XHR | `Site: same-origin`, Mode cors/same-origin | Allow |
| Top-level link/nav | `Mode: navigate`, `Dest: document` | Allow (nav exception) |
| Cross-site form POST CSRF | `Site: cross-site` | **Reject** if not public |
| Cross-site `<img>`/embed of sensitive | `Site: cross-site`, Mode `no-cors` | **Reject** |
| Subdomain same-site call | `Site: same-site` | Allow only if all hosts trusted |

Use an authorized exploit host; capture real browser headers via proxy/devtools.

### 5. Missing headers and layering

1. **Absent `Sec-Fetch-*`:** curl, old UAs. **Fail-open** (allow) for legacy
   clients, or **fail-closed** for browser-only APIs — document the choice.
2. Page JS cannot set these headers in supporting browsers; still do not treat
   absence alone as “safe.”
3. Defense-in-depth only: same-site evil subdomains need tighter `same-origin`
   rules; high-value actions still need tokens/SameSite →
   `csrf-cross-site-request-forgery`; login bind → `login-csrf-defense`.
4. Remediate with `code-quality-standards`: central middleware; tests for
   cross-site POST/`no-cors` vs same-origin fetch; log rejects.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Sec-Fetch / RIP / reject-cross-site middleware | **This skill** | — |
| CSRF tokens, SameSite proofs, method override | `csrf-cross-site-request-forgery` | this for Sec-Fetch gates |
| Login CSRF / forced attacker session | `login-csrf-defense` | this if login lacks Sec-Fetch |
| Cookie flag audit | `cookie-security-flags` | this for request isolation |
| Credentialed CORS data theft | `cors-credentialed-requests` | not a substitute for ACAO |
| Edge **response** header inventory | `nginx-security-headers` | this for **request** policy |
| Implementing middleware/tests | `code-quality-standards` | **always** on code |

**Handoff:** authenticated state-change CSRF → `csrf-cross-site-request-forgery`.
Login-bind forgery → `login-csrf-defense`. Keep this skill for **Sec-Fetch
semantics, RIP rules, and isolation tests**.

## Output Checklist

- [ ] Scope/authorization; test accounts; browser/UA versions
- [ ] Routes protected (mutations + sensitive reads) inventoried
- [ ] Policy: allow same-origin/same-site/none; nav+document; reject matrix
- [ ] Evidence: cross-site POST / no-cors embed rejected; first-party allowed
- [ ] Missing-header policy (fail-open vs fail-closed) documented
- [ ] same-site vs same-origin trust boundary (subdomain risk) noted
- [ ] Layering: tokens/SameSite still required where appropriate
- [ ] Handoffs: `csrf-cross-site-request-forgery`, `login-csrf-defense` as needed
- [ ] Remediation + regression tests; CQS if code changed
- [ ] Redacted cookies/tokens in reports

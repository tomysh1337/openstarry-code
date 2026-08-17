---
name: hsts-preload-checklist
description: >
  Prepare, verify, and operate HTTP Strict Transport Security (HSTS) for Chromium
  preload eligibility and long-lived HTTPS enforcement. Use when auditing or
  enabling Strict-Transport-Security with preload, includeSubDomains, max-age
  policy, apex/www dual hosts, subdomain HTTPS readiness, preload list submit
  or removal, or first-visit MITM residual risk on owned apps and authorized
  assessments.
---

# HSTS Preload Checklist

Own **HSTS policy correctness and preload readiness**: header syntax, max-age,
`includeSubDomains`, `preload`, HTTP→HTTPS redirects, full-tree HTTPS, and
submit/ops risk. Edge header inventory → `nginx-security-headers`. Certs →
`cert-manager-basics`. Cookie `Secure` → `cookie-security-flags`.

## Scope And Authorization

- **In scope:** Org-owned hostnames, staging mirrors of prod policy, labs/CTFs
  with edge/header review, written-scope HSTS/preload assessment.
- **Out of scope:** Submitting third-party domains without owner approval;
  forcing `preload` on shared parents you do not control; mass Internet scans.
- Preload is **hard to reverse** (browser list lag). Treat `preload` +
  `includeSubDomains` as multi-team commitment, not a scanner checkbox.
- Capture only in-scope hosts; redact cookies, tokens, internal SANs, and
  customer hostnames. Keep original header dumps immutable; notes under
  derived paths.

## When To Use

- Planning or reviewing `Strict-Transport-Security` with **`preload`**.
- Pre-submit checklist vs Chromium/hstspreload-style requirements.
- Short `max-age`, missing `includeSubDomains`, or `preload` before every
  covered subdomain is HTTPS-ready.
- Apex vs `www` (or dual hosts) must both satisfy redirect + HSTS rules.
- Residual **first-visit** cleartext risk (not yet preloaded) on cookie domains.
- Considering **removal**/rollback after a bad HTTP or subdomain dependency.

**Not primary:** full nginx TLS/header matrix → `nginx-security-headers`; ACME
only → `cert-manager-basics`; framework knobs alone →
`django-security-settings` (use this for preload gates); cookies →
`cookie-security-flags`.

## Workflow

### 1. Confirm product commitment

1. List **every hostname** under the registrable domain that `includeSubDomains`
   will cover once preloaded.
2. Confirm no long-lived **HTTP-only** dependency (legacy devices, intranet
   CNAMEs, partner callbacks, HTTP email landers).
3. Document owner and that preload is **opt-in, permanent-ish**.
4. Prefer a **long max-age without preload** burn-in; add `preload` only after
   zero HTTP exceptions.

### 2. Preload gate requirements

Verify current public-list criteria before submit; typical baseline:

| Requirement | Expectation | Common failure |
| --- | --- | --- |
| HTTPS | Valid cert on apex and required hosts | Expired/mismatched SAN |
| HTTP → HTTPS | Redirect to HTTPS on same host (no HTTP content) | Soft upgrade only |
| HSTS on HTTPS base | Present on preload base domain HTTPS | Header only on `/login` |
| `max-age` | **≥ 31536000** (1 year) for eligibility | Trial 5–30d left in place |
| `includeSubDomains` | Required with preload | Apex-only HSTS |
| `preload` | Last token after criteria stable | Added before subdomains ready |
| Extra hosts | Often `www` must redirect/HSTS consistently | Apex OK, `www` bare HTTP |

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

Emit HSTS **only on HTTPS**. Prefer `always` (or equivalent) so 3xx/4xx carry it.

### 3. Subdomain inventory

1. Enumerate DNS: prod/staging patterns, `api`/`cdn`/`static`, admin, vanity hosts.
2. Every public name under the parent: HTTPS works; no HTTP-only subdomain left.
3. Wildcard certs do not replace response HSTS; each edge must emit policy (or
   browser inherits parent preload).
4. Internal names still break if public DNS + preload forces HTTPS without cert.

### 4. Verify before submit (authorized)

```bash
# In-scope hosts only
curl -sI http://example.com/ https://example.com/
curl -sI http://www.example.com/ https://www.example.com/
curl -sI https://api.example.com/
```

Per host: HTTP redirects to HTTPS; HTTPS STS has full directives; CDN and origin
do not emit conflicting shorter max-age. Optional lab proof via browser HSTS
view after visit — not a substitute for list criteria.

### 5. Submit, operate, remove

1. Submit **only owned** domains via the official process; store receipt in change tickets.
2. Browser enforcement follows **release cadence** — not instant worldwide.
3. **Removal** is slow and incomplete across clients; fix HTTPS first; plan
   incidents as if preload remains.
4. Monitor cert expiry and CDN dual-header drift after acceptance.
5. With `code-quality-standards`: centralize STS; test min max-age + required
   tokens on apex/`www`/errors; never default `preload` in shared-parent dev configs.

### 6. Residual risk

- Missing HSTS → first-visit MITM/SSL-strip residual (severityity via cookies →
  `cookie-security-flags`).
- Premature preload → **self-DoS** of HTTP-only subdomains.
- Preload does not replace `Secure` cookies, cert hygiene, or app HTTPS redirects.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| HSTS preload readiness, max-age, includeSubDomains, submit/remove | **This skill** | — |
| Broad nginx/edge header + TLS inventory | `nginx-security-headers` | this for preload gate |
| ACME/cert issuance and renew | `cert-manager-basics` | this after certs stable |
| Django/framework SECURE_HSTS_* knobs | `django-security-settings` | this for preload criteria |
| Cookie Secure/HttpOnly/SameSite | `cookie-security-flags` | this for transport pin |
| Host/redirect canonicalization abuse | `http-host-header-attacks` | this if HSTS host wrong |
| Implementing header middleware/tests | `code-quality-standards` | **always** on code |

**Handoff:** edge matrix → `nginx-security-headers`. Issuance →
`cert-manager-basics`. Cookies → `cookie-security-flags`. Keep this skill for
**preload eligibility, subdomain commitment, STS directive correctness**.

## Output Checklist

- [ ] Authorization/scope; only owned hosts exercised or submitted
- [ ] Full subdomain/HTTP dependency inventory under includeSubDomains
- [ ] HTTP→HTTPS proven for apex and required aliases (`www`)
- [ ] HTTPS STS: max-age ≥ 31536000; includeSubDomains; preload only when ready
- [ ] Header on representative 200/3xx/4xx; CDN/origin agree
- [ ] Burn-in without preload documented (or explicit risk accept)
- [ ] Submit/remove decision, owner, first-visit residual risk recorded
- [ ] Handoffs: nginx / cert-manager / cookies / CQS as applicable
- [ ] Redacted header captures; originals immutable; derived notes separate

---
name: csp-report-only-rollout
description: >
  Roll out Content-Security-Policy-Report-Only safely: report-uri/report-to,
  owned collectors, violation triage, noise filtering, gradual directive
  tightening, canary then enforce. Use when staging CSP without blocking
  production, cutting report floods, migrating report-only to
  Content-Security-Policy, or planning dual-header CSP rollouts — hand DOM XSS
  proof to xss-cross-site-scripting and Trusted Types adopt to
  trusted-types-adoption; CSP bypass research to content-security-policy-bypass.
---

# CSP Report-Only Rollout

Deploy **Content-Security-Policy-Report-Only** first, measure violations, filter
noise, tighten directives, then flip to enforcing **Content-Security-Policy**
with rollback. Owned apps, staging, labs, and authorized assessments only.

## When To Use

- Adding or migrating CSP via **Report-Only** before enforce.
- Wiring **report-uri** / **report-to** (Reporting API) to an owned collector.
- Flooded CSP reports, extension noise, or third-party widget violations.
- Gradual tighten of `script-src`, `style-src`, `connect-src`, `img-src`, etc.
- Dual-header canaries (enforce on slice, report-only on main) until clean.
- Keywords: CSP-RO, `Content-Security-Policy-Report-Only`, `report-uri`,
  `report-to`, Reporting-Endpoints, CSP rollout.

Do **not** use as primary for XSS PoCs (`xss-cross-site-scripting`), Trusted
Types (`trusted-types-adoption`), CSP bypass (`content-security-policy-bypass`),
or edge header lists alone (`nginx-security-headers`).

## Scope And Authorization

- **In scope:** org-owned frontends/edges you may change; staging/prod under
  written engagement; labs/CTFs with CSP report endpoints.
- **Out of scope:** report sinks you do not own; collector DoS; mass crawl.
- Prefer header review + controlled browser traffic. Redact cookies, tokens,
  PII. Keep original headers and sample reports immutable.

## Workflow

### 1. Baseline delivery and assets

1. Capture CSP and CSP-RO on document, error, and CDN paths.
2. Inventory first- vs third-party scripts, styles, fonts, frames, fetch/XHR,
   workers, inline handlers (templates, tag managers, SPAs).
3. Note nonces/hashes, `'strict-dynamic'`, `'unsafe-inline'`/`'unsafe-eval'`,
   and any `require-trusted-types-for` (→ `trusted-types-adoption`).
4. Edge vs app emission: avoid conflicting dual CSPs (`nginx-security-headers`).

### 2. Owned reporting path

Prefer Reporting API (`Reporting-Endpoints` + CSP `report-to`) with legacy
`report-uri` fallback. Collector must be first-party/org-owned HTTPS; rate-limit
and drop floods; strip cookies/Authorization; controlled retention.

```http
Reporting-Endpoints: csp-endpoint="https://reports.example/csp"
Content-Security-Policy-Report-Only: default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; report-to csp-endpoint
```

Verify browser POSTs succeed (not only `curl`). Document expected status codes.

### 3. Start loose-but-measurable Report-Only

1. Ship **Report-Only** (or dual with a known-safe enforce baseline).
2. Cover login, checkout, admin, SPA shell; sample desktop + mobile browsers.
3. Group by `effective-directive`, blocked host, document path, source line, UA.
4. Do **not** enforce until residual true positives are owned or accepted.

### 4. Noise filtering

| Noise class | Action |
| --- | --- |
| Browser extensions | Filter known schemes/hosts; never permanent enforce allowlist |
| Prefetch / bots / scanners | Sample; do not overfit policy to crawlers |
| Obsolete browsers | Track share; metrics only, not forever-weak CSP |
| Third-party tags | Ticket owner: HTTPS, narrow host, or sandboxed iframe |
| Mixed content residuals | `mixed-content-hardening` — not endless `http:` allowlists |
| Duplicates | Fingerprint: directive + blocked + document template |

Alert on **new** fingerprints and rate spikes, not raw volume alone.

### 5. Gradual tighten

1. `object-src 'none'`, `base-uri 'self'`, `frame-ancestors` as product needs.
2. `script-src`: nonces/hashes → `'strict-dynamic'`; drop `'unsafe-inline'` and
   host wildcards only after stacks are clean.
3. Then `style-src`, `img-src`, `font-src`, `connect-src`, `worker-src`, `form-action`.
4. Narrow third parties to exact origins; drop `https:` catch-alls.
5. Re-sample after each step; canary enforce on staff or % traffic.

Keep Report-Only one step **stricter** than enforce so the next flip is measured.

### 6. Enforce and verify

1. Flip canaries to `Content-Security-Policy`; optional RO twin for next tighten.
2. Smoke: auth, payments, uploads, embeds, consent/analytics paths.
3. XSS retest under enforce (`xss-cross-site-scripting`); posture/bypass
   (`content-security-policy-bypass`); DOM sinks → `trusted-types-adoption`.
4. Document rollback (flag, edge toggle, prior policy). Code → `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CSP-RO rollout, report-to/uri, noise, tighten → enforce | **This skill** | — |
| Prove/find XSS impact | `xss-cross-site-scripting` | this for CSP timing |
| Trusted Types / require-trusted-types-for | `trusted-types-adoption` | this for RO→enforce |
| CSP parse, nonce/hash, bypass research | `content-security-policy-bypass` | this for safe rollout |
| nginx/edge header delivery | `nginx-security-headers` | this for CSP-RO plan |
| Mixed content / UIR residuals | `mixed-content-hardening` | this for reports |
| SRI for third-party tags | `subresource-integrity-sri` | this if CSP + SRI |
| Implement collectors/templates | `code-quality-standards` | always on code changes |

**This skill** owns Report-Only measurement, reporting plumbing, noise control,
and graduated enforce. Hand XSS to `xss-cross-site-scripting` and Trusted Types
to `trusted-types-adoption`.

## Output Checklist

- [ ] Scope/authorization; hosts and paths covered
- [ ] Baseline CSP and CSP-RO headers quoted (per critical path)
- [ ] Owned collector: endpoint, `report-to`/`report-uri`, retention, redaction
- [ ] Asset inventory; violation groups + noise class; filter rules
- [ ] Tighten sequence, canary plan, dual-header state if used
- [ ] Enforce smoke + security retest; rollback path
- [ ] Hand-offs: XSS, TT, bypass posture, edge delivery
- [ ] Residuals (RO-only prod, unsupported browsers, third parties)

## Rules

- Measure with Report-Only; enforce only after true positives fixed or accepted.
- Collectors must be **owned**; never dump sessions into public sinks.
- Filter noise; do not permanently weaken `script-src` for extension spam.
- CSP is not a substitute for encoding, HttpOnly cookies, or Trusted Types.
- Authorized defensive rollout only; evidence redacted and reproducible.

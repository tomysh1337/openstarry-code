---
name: ssrf-filter-bypass-catalog
description: >-
  Systematic SSRF filter and URL-parser bypass catalog for authorized assessments:
  IP encoding, DNS/TOCTOU, redirect and scheme tricks, allowlist confusion, and
  cloud metadata edge cases. Use when a server-side fetch is confirmed but
  deny-lists, allowlists, or parsers block naive loopback/metadata URLs and you
  need structured bypass methodology. Not for unsolicited scanning. Pair with
  ssrf-server-side-request-forgery for end-to-end SSRF workflow.
---

# SSRF Filter Bypass Catalog (Authorized Only)

## Scope And Authorization

- **Authorized targets only** (owned apps, written pentest/bug-bounty scope, CTF/lab). Do not run bypass catalogs against third-party infrastructure without permission.
- Prefer **out-of-band collaborator** and benign canaries over credential harvest. Cloud IMDS and internal ports need explicit owner approval.
- No free-form internal network sweeps. Use scoped hosts/ports from the engagement diagram.
- If metadata credentials appear: stop escalation, redact, store evidence securely, notify owner for rotation. Do not use keys against other cloud APIs unless SOW allows.
- Redact secrets, internal hostnames beyond need-to-know, and personal data in reports.

## When To Use

- SSRF already **proven** externally (DNS/HTTP OOB) but internal/metadata URLs are filtered.
- Filters appear to be string deny-lists (`localhost`, `127.0.0.1`, `169.254.169.254`) or weak host allowlists.
- Multiple URL parsers in play (app vs library vs redirect follower vs proxy).
- Primary full-feature SSRF triage is done or in parallel via `ssrf-server-side-request-forgery`.
- Not for client-only open redirect without server fetch; not for pure DNS rebinding product research without lab control of DNS.

## Workflow

### 1. Baseline before bypass spam

1. Confirm server-side fetch with unique OOB URL; capture User-Agent, timing (sync/async), in-band vs blind.
2. Record **which layer** rejects candidates: app validation error, connection failure, empty body, WAF, or no OOB hit.
3. Identify library hints (error strings, headers, known stack) — parser quirks differ (Java URL, Go net/url, Python requests/urllib3, curl, browserless).
4. One change per test; unique OOB subdomain per payload class so hits map cleanly.

### 2. Catalog — IP and host literals

Test **scoped** loopback/metadata/internal targets only. Log pass/fail per class:

| Class | Examples (illustrative) | Note |
| --- | --- | --- |
| Dotted decimal alternatives | Octal/hex/decimal integer forms of 127.0.0.1 if accepted | Many filters match strings only |
| IPv6 / mapped | `[::1]`, `[::ffff:127.0.0.1]`, compressed forms | Bracket rules vary |
| Short / malformed IP | `127.1`, `0`, vendor-specific | Verify real connect via OOB or in-band |
| DNS to fixed IP | `localtest.me`, nip.io, customer DNS → internal | You must control or scope the name |
| Trailing / case | `Localhost.`, mixed-case host | Normalization gaps |
| Userinfo confusion | `http://allowed@127.0.0.1/`, `http://127.0.0.1#@allowed` | Check **actual** request host with OOB |

### 3. Catalog — scheme, path, and encoding

1. **Schemes:** if only `https://` allowed, try redirect from allowed HTTPS to `http://169.254.169.254/`; probe `file://`, `gopher://`, `dict://`, `ftp://` only if client library plausibly supports them and SOW permits.
2. **Encoding:** single/double URL-encoding of `.` `/` `@` `:`; Unicode dots/homoglyphs when app decodes inconsistently.
3. **Slash tricks:** backslash vs slash, extra slashes, path-only allowlist bypass (`http://evil/http://internal` style) — always verify with instrumentation, not theory.
4. **Port and path:** metadata paths with extra prefixes; alternate IMDS ports only if documented in scope.

### 4. Catalog — redirects and multi-hop

1. Collaborator returns `302/307/308` to scoped internal or metadata URL.
2. Note whether each hop re-validates host/IP or only the first URL.
3. Mixed-scheme and cross-host chains; limit depth to avoid noisy loops.
4. Open-redirect on an **allowlisted** host used as trampoline — document chain clearly.

### 5. Catalog — allowlist and partial-match failures

1. Suffix/prefix mistakes: `target.example.evil.test`, `evil-target.example`.
2. Substring allow: host contains `trusted.com` via `nottrusted.com.evil`.
3. Fragment/query smuggling depending on parser (`#`, `?`, `;` parameters).
4. DNS rebinding **lab-only:** short TTL name resolves allowlisted then internal; requires controlled DNS and scoped victim service. Mitigations to recommend: resolve → classify IP → connect to pinned address; re-check after redirects.

### 6. Catalog — cloud metadata specifics (approved)

| Provider | Filter-oriented notes |
| --- | --- |
| AWS | IMDSv1 vs v2 (token PUT); link-local `169.254.169.254`; container hops |
| GCP | Host `metadata.google.internal`; required `Metadata-Flavor: Google` |
| Azure | `Metadata: true` header; API version query |

Prove **reachability** (headers/status) before any identity document content. Prefer existence proofs.

### 7. Score and stop conditions

- Mark each class: blocked / partial (DNS only) / full HTTP hit / in-band body.
- Stop expanding internal surface once impact class is demonstrated per SOW.
- Feed successful classes into remediation: deny by **resolved IP class**, not string equality; pin connections; disable unused schemes; egress allowlist.

### 8. Implementation review handoff

When fixing or reviewing fetchers, apply `code-quality-standards`: no user-controlled URL to raw clients without allowlist + IP classification; timeouts; size limits; no raw body reflection.

## Routing

| Need | Skill |
| --- | --- |
| End-to-end SSRF feature triage, OOB, impact classes | `ssrf-server-side-request-forgery` |
| Injection class unclear before SSRF confirmed | `injection-checking` |
| DNS rebinding deep dive / browser sticky | `dns-rebinding-attacks` |
| Controlled risky tooling | `security-sandbox` |
| Secure fetch/allowlist implementation | `code-quality-standards` |
| CSRF/cookie issues (unrelated to server fetch) | `csrf-cross-site-request-forgery` / `same-site-cookie-pitfalls` |

## Output Checklist

- [ ] Baseline OOB proof and filter failure mode for naive internal URL
- [ ] Table of bypass **classes** tried with pass/fail and unique OOB IDs
- [ ] Parser/stack notes if known
- [ ] Redirect or rebinding chain diagram when used
- [ ] Scoped internal/metadata evidence only; secrets redacted
- [ ] Remediation: IP classification at connect time, redirect re-validation, scheme lockdown, egress proxy
- [ ] Retest plan after fix

## Rules

- Catalog entries are **assessment patterns**, not a free attack kit for out-of-scope hosts.
- Theory without OOB/in-band confirmation is a hypothesis, not a finding.
- Avoid write protocols against Redis/internal admin; connection proof is enough.
- Rate-limit timing/port probes; mark timing-only results low confidence.
- Prefer the smallest successful bypass class that proves the control failure.

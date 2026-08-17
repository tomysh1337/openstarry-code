---
name: ssrf-allowlist-design
description: >
  Design SSRF defenses for server-side URL fetchers: hostname allowlists, scheme
  allowlists, metadata and private-IP blocks, DNS-rebinding-safe resolve-then-
  connect checks, and URL parser pitfalls. Use when hardening webhooks, previews,
  importers, unfurl, PDF/HTML renderers, or any user-influenced server fetch —
  owned apps only. Hand offensive SSRF testing to ssrf-server-side-request-forgery.
---

# SSRF Allowlist Design

Design **application-layer SSRF defenses** for features that open outbound
connections from user-influenced URLs. Prefer **exact allowlists** and
**connect-time IP checks** over denylist-only filters. Platform IMDS hop limits
and egress policy remain defense-in-depth; this skill owns **fetcher policy**.

## Scope And Authorization

- Design/implement/review on systems you **own** or are contracted to harden.
  Staging/lab first when changing production fetch behavior.
- Do not probe third-party internals/metadata. Residual offensive proofs →
  `ssrf-server-side-request-forgery` under explicit authorization.
- Redact credentials, tokens, and IMDS material. On accidental exposure: stop,
  secure evidence, rotate (`secrets-management-hygiene`).

## When To Use

- Building or reviewing URL allowlists for webhooks, previews, import-from-URL,
  link unfurl, avatar/media fetch, SSO metadata URL, or proxy-style APIs
- Blocking loopback, RFC1918, link-local, and cloud metadata destinations
- Fixing DNS rebinding / TOCTOU (check host, then resolve to private IP)
- Restricting schemes (`https` only); disabling `file`/`gopher`/`dict`/`ftp`
- Hardening URL parser confusion (userinfo, encoding, redirects)
- Mentions: SSRF allowlist, URL fetch harden, block 169.254.169.254, scheme
  allowlist, DNS rebinding defense, webhook SSRF, 出站白名单

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized offensive SSRF / bypass catalog | `ssrf-server-side-request-forgery` |
| Cloud IMDS platform config (IMDSv2, hop limit) | `cloud-metadata-ssrf-defenses` |
| DNS rebinding as browser/attack focus | `dns-rebinding-attacks` |
| Generic request field validation | `input-validation-patterns` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

### 1. Inventory fetch surfaces

1. List every server-side path that builds a URL/host from user/admin input
   (sync handlers, workers, renderers, server-followed redirects).
2. Note HTTP client, redirect policy, DNS resolver, and whether response bodies
   return to the client (in-band vs fire-and-forget).
3. Prefer **no arbitrary URL fetch**: fixed partner endpoints, signed webhook
   targets, or server-side resource IDs over free-form URLs.

### 2. Scheme allowlist (first gate)

1. Allow only schemes the product needs — default **`https` only**.
2. Explicitly reject `file`, `gopher`, `dict`, `ftp`, `jar`, `data`, and other
   schemes the client library might honor.
3. Reject missing/empty scheme; do not default to `http`.
4. Cap URL length, redirect hops, timeouts, and response body size.

### 3. Host allowlist (preferred over denylist)

1. Prefer **exact hostname** (or fixed ID → URL map) over substring/suffix regex.
2. If suffix rules are required (e.g. `*.partners.example`), lowercase DNS
   labels, reject IP literals unless approved, ban userinfo before match.
3. Never treat “hostname contains allowlisted string” as safe.
4. Customer-configured webhook bases still use resolve-and-classify (step 4).

### 4. Resolve, classify IP, then connect

1. Resolve DNS; **classify every A/AAAA** before connect.
2. Deny by default: loopback (`127.0.0.0/8`, `::1`), RFC1918, link-local
   (`169.254.0.0/16`, `fe80::/10`), CGNAT `100.64.0.0/10` if in policy,
   metadata hostnames, and IPv4-mapped IPv6 forms of the above.
3. Connect only to a classified-safe address; **pin** it (no separate check then
   client re-resolve).
4. **Re-run the full check on every redirect** (scheme, host, resolve, IP).
5. DNS rebinding: short-TTL flip after name allowlist fails if you never re-check
   IPs — always classify resolved addresses at connect time.

### 5. URL parse pitfalls (normalize before policy)

| Pitfall | Defense |
| --- | --- |
| Userinfo `https://allowed.com@evil/` | Reject userinfo; one URL parser |
| Decimal/hex/octal IP literals | Classify binary IP, not string form |
| Trailing dots, mixed case, IDN | Canonicalize host; fixed IDN policy |
| Backslash / odd slash (parser split) | Single well-tested URL parser |
| Double encoding / Unicode dots | Decode once to canonical form, then check |
| Open redirect chain to metadata | Re-validate each hop; cap redirects |
| Host allowlist only | Still require IP classification for non-fixed hosts |

### 6. Response and egress depth

1. Avoid reflecting raw remote bodies/headers to untrusted clients.
2. Pair app policy with egress proxy/allowlist for fetch workers when possible.
3. IMDS platform hardening → `cloud-metadata-ssrf-defenses`.
4. Regression tests: metadata IPs, private ranges, userinfo, redirects, bad
   schemes (`code-quality-standards`). Residual attack →
   `ssrf-server-side-request-forgery` (authorized).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Design/review SSRF allowlist, scheme, IP block, parse safety | **This skill** | — |
| Authorized offensive SSRF testing / bypass proof | `ssrf-server-side-request-forgery` | this for remediation |
| AWS/GCP/Azure IMDS config and role blast radius | `cloud-metadata-ssrf-defenses` | this for app URL policy |
| DNS rebinding mechanism deep-dive | `dns-rebinding-attacks` | this for connect-time pin |
| Generic field/schema validation | `input-validation-patterns` | this for URL fetch sinks |
| Implement fetcher, redirects, tests, logs | `code-quality-standards` | **always** on code |

- **`ssrf-server-side-request-forgery`:** find/prove SSRF; fix allowlist design here.
- **`cloud-metadata-ssrf-defenses`:** IMDSv2 / hop limit / network deny to metadata.
- **`code-quality-standards`:** single parser, fail-closed errors, tests, no secret logs.

## Output Checklist

- [ ] All user-driven server fetch paths inventoried (sync + async + redirects)
- [ ] Scheme allowlist documented; unsafe schemes rejected
- [ ] Host policy is exact allowlist or fixed ID→URL map (weak regex = debt)
- [ ] Resolve → classify IP → connect pin; private/link-local/metadata denied
- [ ] Every redirect hop re-validated (scheme, host, IP)
- [ ] Userinfo, IP literal forms, encoding, and parser-split cases covered
- [ ] Timeouts, size, and redirect hop caps set
- [ ] Response reflection policy decided; egress proxy noted if present
- [ ] Platform IMDS/egress paired via `cloud-metadata-ssrf-defenses` when cloud-hosted
- [ ] Regression tests for allow/deny cases; no live secrets in fixtures
- [ ] Residual surface → `ssrf-server-side-request-forgery` when in scope
- [ ] `code-quality-standards` applied on implementation changes

## Rules

- Allowlists and connect-time IP checks beat denylist-only hostname filters.
- One URL parser, one classification path, pin address — no TOCTOU re-resolve.
- Prefer fixed destinations over free-form URL fetch.
- Defense in depth: app policy **and** network egress **and** IMDS/IAM hardening.
- Authorized hardening only; never probe foreign internals via “test fetch.”

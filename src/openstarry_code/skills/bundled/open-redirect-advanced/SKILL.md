---
name: open-redirect-advanced
description: >-
  Advanced open-redirect testing: multi-parser gaps, allowlist failures,
  encoding and scheme tricks, and chains into OAuth/OIDC redirect_uri and
  token theft. Use when basic next/return checks exist but Location still
  leaves the trusted host, or when post-login/SSO exits need deep bypass work.
---

# Open Redirect — Advanced Parser And OAuth Chains

## Scope And Authorization

- Authorized apps, labs, CTFs, and owned systems only. Redirect only to **domains you control** (collaborator/OAST). Do not phish real users.
- Prefer non-destructive proofs: one hop to your canary. Capture raw `Location` with auto-follow off.
- OAuth chains may expose `code` / tokens — use test clients and accounts only. Redact secrets in tickets.

## When To Use

- Basic `open-redirect` ladder failed (`//evil` blocked) but residual bypasses are suspected.
- Login, logout, SSO callback, email exit, or deep-link bridge uses a return URL with partial allowlisting.
- Validators use `contains`, `startsWith`, regex, or dual stacks (gateway + app + JS) that disagree on host/scheme.
- OAuth/OIDC `redirect_uri` or RP `return_to` reuses the same weak parser as site redirects.
- Keywords: open redirect bypass, allowlist bypass, parser discrepancy, OAuth redirect chain.

## Core Model

```
User-controlled return → filter layer(s) → Location / window.location
  → browser final authority → phishing / token leak / OAuth code theft
```

| Gap class | Failure |
| --- | --- |
| String allowlist | Substring `trusted.com` ≠ real host |
| Dual parser | Server accepts; browser leaves site (or reverse) |
| Normalize-late | Decode after validation |
| Relative confuse | Path-looking values become scheme-relative |
| OAuth chain | RP open redirect lands code/token on attacker |

**Good proof:** Browser-resolved host is attacker-controlled; for OAuth, test `code`/token hits canary.  
**Bad proof:** HTML reflection without navigation; same-host path-only change claimed as full open redirect.

## Workflow

1. **Inventory sinks** — Query (`next`, `return`, `returnUrl`, `redirect`, `continue`, `goto`, `RelayState`), nested/base64 `return_to`, client JS/meta, OAuth `redirect_uri` / `post_logout_redirect_uri`. Note 302/303/307 and client-only checks.

2. **Classify control** — Baseline allowed internal path vs blocked `https://canary.example`.

   | Control | Signal |
   | --- | --- |
   | None | External accepted |
   | Blocklist | Only known bad strings rejected |
   | Prefix/contains | Trusted substring required |
   | Parse-host | Host extracted then compared |
   | Key map | Opaque keys → fixed paths (strong) |

3. **Advanced payload ladder** (adapt canary; after basics fail)

   | Class | Examples | Why |
   | --- | --- | --- |
   | Userinfo | `https://trusted.com@canary.example/` | Filter sees trusted string |
   | Scheme-relative | `//canary.example`, `/\canary.example` | Path vs authority |
   | Backslash | `https://canary.example\.trusted.com` | Legacy `\` as `/` |
   | Encoding | `%2f%2fcanary.example`, `%252f%252f` | Validate raw; sink decodes |
   | Dot / eTLD | `https://trusted.com.canary.example` | Contains vs DNS host |
   | Port / scheme | `https://trusted.com:443@canary.example`, `https:canary.example` | Parser split |
   | Data / JS | `javascript:...`, `data:text/html,...` | Browser navigation sinks |
   | Nested | `https://trusted.com/logout?next=//canary.example` | Double hop |
   | CRLF | `%0d%0aLocation:%20https://canary.example` | → `crlf-injection` if split |

   Capture raw `Location`, then confirm final host in a real browser (Chrome + one other if engine-specific).

4. **Multi-parser disagreement** — Same bytes through app library (`urllib` / `URI` / `net/url` / WHATWG), edge WAF, and browser bar. Finding class is **parser discrepancy** when the chain exits the allowlist only in combination.

5. **Allowlist failure patterns**

   ```
   # BAD: if "trusted.com" in url  → try trusted.com.canary / userinfo
   # BAD: startswith("https://trusted.com") → trusted.com.canary / %00 tricks
   # BAD: strip scheme then prefix → ////canary , /\\canary
   # GOOD: parse once → https only → exact host → reject userinfo → compare after one unquote
   ```

   Prefer server-side **redirect keys** over raw URLs when remediating (`code-quality-standards`).

6. **OAuth / OIDC chain**  
   - Test IdP `redirect_uri` strictness: path prefix, query append, slash, `@` userinfo (in-scope clients only).  
   - If IdP is strict but RP open-redirects after code exchange:

     ```
     Auth with redirect_uri=https://rp.example/callback
     → victim logs in → RP 302 via ?next= to canary
     → code/token in query, fragment, or Referer
     ```

   - Deep IdP misconfig → `oauth-oidc-misconfiguration`; keep **this skill** primary when the pivot is advanced open redirect on the RP/shared helper.

7. **Side channels** — Reset/magic `next=` → `password-reset-poisoning` / `open-redirect`. SID in return URL → `session-fixation-management`. Lax top-level GET via redirect as CSRF gadget → `csrf-cross-site-request-forgery`. Server **fetches** URL → `ssrf-server-side-request-forgery`.

8. **Severity** — Unauth exit phishing &lt; post-login trusted exit &lt; email first hop &lt; OAuth code/token on canary. Do not claim ATO without the concrete token/session step. Confirm legitimate internal returns still work.

## Routing

| Need | Skill |
| --- | --- |
| First-pass inventory / simple payloads | `open-redirect` |
| OAuth/OIDC client, state, PKCE | `oauth-oidc-misconfiguration` |
| CSRF gadget via top-level navigation | `csrf-cross-site-request-forgery` |
| SID in return URL / no regenerate | `session-fixation-management` |
| Reset link Host vs redirect token leak | `password-reset-poisoning` |
| Server-side fetch of target | `ssrf-server-side-request-forgery` |
| CRLF into Location | `crlf-injection` |
| Secure allowlist / redirect-key code | `code-quality-standards` |

## Output Checklist

- [ ] Sinks (param, client vs server, status)
- [ ] Control class and working advanced payload(s)
- [ ] Raw `Location` / JS sink + browser final host
- [ ] Parser disagreement evidence if claimed
- [ ] Auth context: anonymous, post-login, email, OAuth
- [ ] OAuth chain steps; secrets on canary (redacted)
- [ ] Remediation: single parser, scheme+exact host, no userinfo, redirect keys

## Rules

- Record raw redirects; auto-follow hides bugs. Canary domains only.
- Parser-gap needs dual evidence (filter decision + browser host).
- OAuth impact only with test clients/accounts — no production phishing.
- One solid off-site navigation with context beats an unvalidated payload dump.
- Authorized testing only.

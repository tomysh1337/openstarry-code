---
name: waf-rule-tuning-basics
description: >
  Authorized WAF rule tuning basics: false-positive triage, detect-then-block
  rollout, exception design, managed vs custom rules, and evidence from WAF
  logs. Use when reducing noisy blocks on owned apps, staging a new managed
  ruleset, designing path/IP/parameter exceptions, scoring thresholds, or
  documenting residual risk after WAF changes — not for third-party evasion.
---

# WAF Rule Tuning Basics

Tune **Web Application Firewall** policy for systems you own or are explicitly
authorized to operate: cut false positives, keep true-positive coverage, and
change rules through staged, reversible rollout with log evidence.

## Scope And Authorization

- **In scope:** org-owned WAF policies (cloud WAF, ModSecurity/CRS, API-gateway
  or CDN WAF), staging/prod under change control, labs, CTF edges you administer.
- **Out of scope:** evasion against third-party sites; DoS via rule floods;
  disabling prod block mode without ownership and rollback; scanning WAFs you
  do not operate.
- Prefer **log and config review** before live probes. Probe only approved
  hostnames, accounts, and volumes. Redact tokens, cookies, PII bodies, and
  internal rule secrets. Prod **block-mode** or ruleset swaps need a change
  window, detect/canary first, and rollback via prior policy snapshot.

## When To Use

- Legitimate traffic is **blocked or challenged** after ruleset enable, CRS
  upgrade, or a new custom rule
- High **false-positive** rate on a path, parameter, content-type, or client
  class (CMS admin, upload, GraphQL, mobile API)
- Moving from **detect/count** to **block**, or raising anomaly scores /
  paranoia levels, with controlled exceptions
- Designing **allowlists/exceptions** by path, method, IP/VPN, header, or body
  field without opening whole hosts
- Keywords: WAF tuning, ModSecurity CRS, AWS/Azure/Cloudflare/Fastly WAF, rule
  exception, anomaly score, false positive, paranoia level

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Network SG / host firewall ACLs | `firewall-rule-review` |
| App injection testing (authorized) | class skill / `injection-checking` |
| Rate-limit keying / quota research | `rate-limit-bypass-testing` |
| nginx headers / TLS edge (not WAF rules) | `nginx-security-headers` |
| CAPTCHA / bot-challenge controls | `captcha-bypass-research` |
| Safe config/code change practice | `code-quality-standards` |

## Workflow

### 1. Baseline policy and traffic

1. Record owner, env, WAF product, policy ID/version, mode (detect vs block),
   linked origins/hostnames.
2. Export rulesets, custom rules, IP sets, and exceptions as immutable evidence.
3. Define metrics: FP rate, block rate, critical-path availability, residual
   coverage for SQLi/XSS/RCE-class signals the WAF should catch.
4. Map **critical legitimate flows** (login, search, upload, webhooks, admin,
   GraphQL, mobile API) and body encodings / unusual methods.

### 2. Triage false positives from logs

Sample blocked/flagged events. Cluster by **rule × path × parameter**:

| Field | Capture |
| --- | --- |
| Rule ID / name / ruleset | Managed vs custom |
| Matched variable | URI, arg, header, body, cookie |
| Sample URI + method | Redact secrets |
| Client class | Browser, bot, partner IP, CI |
| Count / share of blocks | Noise severity |
| Confirmed legitimate? | Reproduce with test account |

### 3. Choose the least-privilege fix

Prefer, in order: (1) **App fix** — stop attack-like patterns in legitimate
fields; (2) **Narrow exception** — path + method + parameter for one rule ID,
time-boxed with owner/ticket; (3) **Rule tune** — threshold/score for that rule
or location only; (4) **Paranoia/sensitivity drop** — last resort, document lost
coverage; (5) **Disable whole rule/ruleset** — written risk acceptance only.

Never exception `/*` or entire rulesets without residual-risk notes. Prefer
**positive security** (known-good schemas) for stable APIs when supported.

### 4. Stage detect → canary → block

1. Ship in **count/detect** (or shadow) where available.
2. Re-check noisy clusters and lab true-positive samples on non-prod.
3. Canary block on subset of hosts/routes or percentage traffic.
4. Full block only after FP budget is met; keep prior policy export for rollback.
5. Policy-as-code edits → pair with `code-quality-standards` (reviewable diffs).

### 5. Validate and operate

On non-prod/approved synthetic traffic: exercise critical-path **benign**
requests and labeled attack samples; confirm exceptions do not open adjacent
paths (e.g. `/api/search` must not cover `/api/admin`). Owner + ticket + expiry
on every exception; alert on disablements and FP/TP shifts; stage managed-ruleset
upgrades before prod. Bot challenges / rate limits → `captcha-bypass-research` /
`rate-limit-bypass-testing`; this skill owns **signature/score rule** tuning.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| WAF FP triage, exceptions, detect→block, managed ruleset tuning | **This skill** | — |
| Host/cloud network allow rules | `firewall-rule-review` | — |
| nginx headers / TLS termination | `nginx-security-headers` | this skill if co-located WAF |
| Rate limit / anti-automation | `rate-limit-bypass-testing` | this skill for WAF rate rules |
| CAPTCHA / bot challenges | `captcha-bypass-research` | this skill for signature noise |
| Authorized injection past the edge | class skill / `injection-checking` | this skill for log interaction |
| Policy-as-code or app input fixes | `code-quality-standards` | this skill for WAF semantics |

## Output Checklist

- [ ] Authorization, env, WAF product/policy version, mode recorded
- [ ] Pre-change policy export stored as evidence
- [ ] Critical legitimate flows and encodings listed
- [ ] Top FP clusters: rule ID × path × variable (redacted samples)
- [ ] Fix choice justified (app vs narrow exception vs score vs disable)
- [ ] Exceptions least-privilege, owned, ticketed, expiry when temporary
- [ ] Detect/canary results and FP budget before full block
- [ ] Residual coverage / intentional gaps documented
- [ ] Rollback verified; monitoring for disablements and rate shifts
- [ ] Follow-ups routed (app fix, rate limit, headers, CQS for policy code)

## Rules

- **Owned or written-authorization only** — defensive ops/assessment; never
  present third-party WAF evasion as “tuning.”
- Prefer log-driven, minimal exceptions over global allowlists.
- Staging first for ruleset upgrades and paranoia increases.
- Redact secrets/PII from shared reports; full exports stay in secured ops stores.

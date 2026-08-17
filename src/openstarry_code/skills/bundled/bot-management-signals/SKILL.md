---
name: bot-management-signals
description: >
  Design bot-management signal pipelines: signal taxonomy, collection points,
  risk scoring, action thresholds (allow / challenge / throttle / block),
  feedback loops, privacy, and false-positive controls. Use when bot score
  design, device or TLS fingerprints as risk signals, bot management rules,
  challenge step-up policy, or anti-automation signal architecture for owned
  applications and authorized assessments.
---

# Bot Management Signals Design

Design **how signals become decisions** for bot and abuse management: which
inputs to collect, how to score them, which actions fire at which thresholds,
and how humans recover from false positives. Prefer the platform’s existing
CDN/WAF/bot product and app middleware over inventing a parallel opaque scorer.

## Scope And Authorization

- Design/implement on systems you **own** or are contracted to harden.
- Control-gap measurement (UI-only challenges, bypassable scores) is **not**
  fraud enablement — hand CAPTCHA/rate probes to `captcha-bypass-research` /
  `rate-limit-bypass-testing` under clear scope only.
- Minimize data collection; redact fingerprints, cookies, and device IDs in docs.
- Tune thresholds in staging/synthetic traffic; no production floods against
  shared users or challenge providers.
- Do not hard-block accessibility users, privacy browsers, or whole regions
  without documented product risk acceptance.

## When To Use

- Defining **signal inventory** (network, TLS, browser, behavioral, reputation)
- Building/reviewing a **risk score** and action ladder (allow → challenge →
  soft throttle → hard block)
- Placing collection (edge CDN, app, mobile SDK) with **server-side** enforce
- Tuning false positives, allowlists, step-up on login/signup/checkout abuse
- Keywords: bot management, bot score, device fingerprint, JA3/JA4, TLS
  fingerprint, headless signals, challenge step-up, anti-automation policy,
  人机验证策略, risk-based bot rules

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Soft API quotas / `429` budgets alone | `api-rate-limit-design` |
| Authorized CAPTCHA/token enforcement gaps | `captcha-bypass-research` |
| Authorized rate-limit keying bypass | `rate-limit-bypass-testing` |
| Auth lockout after password/OTP fails | `account-lockout-design` |
| Edge WAF signature rule syntax only | `waf-rule-tuning-basics` |
| Implementation hygiene baseline | `code-quality-standards` |

## Workflow

### 1. Inventory surfaces and abuse goals

| Surface | Typical abuse | Signal priority |
| --- | --- | --- |
| Login / OTP / reset | Stuffing, spray, SMS flood | Strict; dual rate + challenge |
| Signup / invite | Account factory | Device + reputation + challenge |
| Search / scrape-prone read | Bulk extraction | Rate + behavior + IP rep |
| Checkout / vote / promo | Integrity fraud | Session integrity + velocity |
| Public API / partner | Quota theft, scripts | API key + plan + edge score |

Document decisions that must be **server-side** (never trust client `botScore`).

### 2. Signal taxonomy (collect only what you use)

| Class | Examples | Notes |
| --- | --- | --- |
| **Network** | Trusted IP, ASN, geo, VPN/DC | IP from edge overwrite only |
| **Transport** | JA3/JA4, H2 settings, ALPN | High cardinality; version carefully |
| **Client** | UA consistency, automation flags | Spoofable alone; low solo weight |
| **Behavioral** | Velocity, path entropy, session age | Prefer server-observable events |
| **Reputation** | IP lists, prior abuse, good bots | Separate verified-bot allow path |
| **Challenge** | CAPTCHA/Turnstile, PoW, MFA step-up | Server bind; single-use TTL |
| **Identity** | User/org, API key tier | Post-auth vs anonymous differ |

Every signal needs **source of truth**, **TTL**, and **missing-data** fail-open/closed.

### 3. Score and action ladder

1. Normalize contributions; one spoofable bit must not equal hard block alone.
2. Internal **risk bands** (low/med/high/critical) — do not leak exact weights in errors.
3. Map bands: **low** allow+sample log; **med** soft rate / passive challenge; **high**
   interactive challenge or MFA on sensitive acts; **critical** block/quarantine + alert.
4. Login, pay, reset may force challenge even at medium.
5. Verified automation (crawlers, monitors, partners): explicit allowlist/API-key path.

### 4. Placement, feedback, and ops

- Edge: coarse IP/TLS/reputation. App: identity velocity, business events, challenge verify.
- One authoritative decision per class; shared support reason codes; normalize route aliases
  into shared velocity buckets (`api-rate-limit-design` for keying).
- Log reason codes + hashed IDs, not full fingerprints; short retention for high-cardinality
  signals; track challenge rate, FP tickets, good-bot miss.
- Document vendor/store outage fail-open vs closed (auth often stricter).
- Accessibility: alternate challenge paths; never pointer-only sole UX.
- Validate: missing signal, spoofed headers, omit/replay challenge. Authorized gaps →
  CAPTCHA/rate-limit skills. Code with `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Signal taxonomy, score bands, action ladder, FP controls | **This skill** | — |
| Soft QPS / 429 / budget windows | `api-rate-limit-design` | this for bot-triggered tighten |
| CAPTCHA/token binding research (authorized) | `captcha-bypass-research` | this for when to challenge |
| Rate key split / XFF bypass testing | `rate-limit-bypass-testing` | this for intended policy |
| Auth hard lockout after secret fails | `account-lockout-design` | this for pre-auth bot step-up |
| WAF rule/signature tuning | `waf-rule-tuning-basics` | this for score→action design |
| Code, tests, logging, config | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for multi-signal bot **policy design**. Switch for pure
quota math, pure CAPTCHA verify gaps, or pure WAF rule syntax.

## Output Checklist

- [ ] Surfaces and abuse goals listed; server-side enforcement required
- [ ] Signal classes with source, TTL, missing-data behavior
- [ ] Trusted IP path documented; client-supplied scores rejected
- [ ] Risk bands mapped to allow / challenge / throttle / block
- [ ] Sensitive routes and verified-bot paths separated
- [ ] Challenge outcomes bound and single-use (CAPTCHA skill if needed)
- [ ] FP/allowlist/support codes and accessibility path documented
- [ ] Outage fail-open/closed decided per surface
- [ ] Privacy/retention for fingerprints and device IDs set
- [ ] Metrics: challenge/block rate, FP tickets, good-bot miss
- [ ] Adversarial validation via CAPTCHA/rate-limit skills when in scope
- [ ] `code-quality-standards` applied for implementation and tests

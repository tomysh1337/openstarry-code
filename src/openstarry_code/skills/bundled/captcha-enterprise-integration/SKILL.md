---
name: captcha-enterprise-integration
description: >
  Design and implement enterprise CAPTCHA / bot-challenge integration for owned
  applications: provider selection, sitekey and secret lifecycle, server-side
  token verification, action and hostname binding, score thresholds, fail-closed
  behavior, multi-client parity, accessibility, and step-up with rate limits.
  Use when reCAPTCHA Enterprise, hCaptcha Enterprise, Turnstile Enterprise,
  enterprise CAPTCHA rollout, siteverify integration, bot score threshold design,
  challenge step-up on login/signup/reset, or hardening CAPTCHA for production.
---

# Enterprise CAPTCHA Integration (Defense)

Build **defense-in-depth bot challenges** on systems you own: widgets and
invisible/score modes that are **always verified server-side**, bound to action
and session, consistent across clients, and paired with rate limits—not UI-only theater.

## Scope And Authorization

- **In scope:** Integrate or harden CAPTCHA on apps/APIs/gateways you **own** or
  are contracted to change (staging preferred; prod under change control).
- **Out of scope:** CAPTCHA farms, fraud, stuffing, or third-party bypass work.
  Control-gap research → `captcha-bypass-research` (authorized only).
- Prefer provider **test keys** and synthetic traffic in non-prod; never ship
  always-pass test secrets to production.
- Redact site secrets, full tokens, and customer IDs. Public sitekeys may live in
  clients; **secrets stay server-side only**.
- CAPTCHA is not a substitute for dual-key rate limits or account lockout on auth.

## When To Use

- Rolling out or reviewing **enterprise** CAPTCHA (reCAPTCHA / hCaptcha /
  Turnstile Enterprise or equivalent)
- Wiring **server-side siteverify**/assessment APIs, action names, hostname
  allowlists, score thresholds, single-use consume
- Protecting login, register, password reset, checkout, vote, or scrape-prone APIs
- Mentions: enterprise CAPTCHA, siteverify, bot score, challenge step-up,
  invisible CAPTCHA integration

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized CAPTCHA control-gap / bypass research | `captcha-bypass-research` |
| Soft API quotas / `429` budgets | `api-rate-limit-design` |
| Auth hard lockout thresholds | `account-lockout-design` |
| Adversarial rate-limit keying tests | `rate-limit-bypass-testing` |
| Secret storage / rotation of provider keys | `secrets-management-hygiene` |
| Implementation reliability baseline | `code-quality-standards` |

## Workflow

1. **Threat and surface inventory.** List abuse goals (account factory, spray,
   SMS burn, spam, checkout fraud). Map web, mobile, GraphQL, legacy `/v1`,
   partner embeds. Choose **always-on** vs **step-up after N fails** per surface;
   document residual risk for exemptions.

2. **Provider and mode.** Prefer org enterprise contracts (audit, SSO admin, SLA).
   Pick checkbox, invisible, or score mode from UX and risk. Require **server
   assessment**, **action labels**, and **hostname binding**. CDN managed
   challenges complement—do **not** replace app verify on sensitive POSTs.

3. **Keys and envs.** Public sitekey client-side; secret/API key only via
   `secrets-management-hygiene`. Separate keys per env. Block test keys from prod
   (config lint/flags). Rotate on exit or leak; dual-run if provider allows.

4. **Client integration.** Challenge on the **same action** the server authorizes.
   Pass stable action names (`login`, `register`, `password_reset`). Never trust
   `captchaPassed: true`. CSP: only required provider origins. Mobile: official
   SDKs; send token on the API the backend verifies.

5. **Server-side verification (mandatory)** before side effects, after path normalize:

   | Check | Requirement |
   | --- | --- |
   | Provider verify/assessment call | Fail **closed** on auth if API/network error |
   | Success / valid assessment | Reject false/failed |
   | Hostname / package name | Match deployment allowlist |
   | Action / purpose | Match intended operation |
   | Score (score mode) | Min threshold **server-side**; no JS-only gate |
   | Freshness + single use | Enforce TTL; consume so replay fails |
   | Optional binding | Session and/or trusted client IP when warranted |

   One authoritative enforcer per action class—not widget-on-form + open GraphQL twin.

6. **Step-up + limits.** Pair with `api-rate-limit-design` and
   `account-lockout-design`: progressive delay → CAPTCHA → hard lock. Score soft
   friction for low risk; challenge after failures or high risk. Never CAPTCHA alone
   for OTP length or password spray.

7. **Client parity.** Web, mobile, legacy, GraphQL share the same gate for the same
   abuse goal. Partner/admin paths may use mTLS or signed service identity—document
   the compensating control.

8. **A11y and overrides.** Accessible/audio paths per policy. Support/QA overrides
   audited, time-boxed, env-scoped—not global disable. Stable error codes; no
   CAPTCHA-based user-enumeration oracles.

9. **Observe and test.** Metrics: verify latency, fail reasons, step-up rate,
   provider errors; alert on missing-token spikes or sudden 100% pass. Contract
   tests reject omit/empty/garbage/expired/replay; accept one valid lab token.
   Authorized adversarial review → `captcha-bypass-research`. Code →
   `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Enterprise CAPTCHA design, siteverify, scores, multi-client parity | **This skill** | — |
| Prove UI-only / replay / skip gaps (authorized) | `captcha-bypass-research` | this for intended policy |
| Attempt budgets, `429`, route quotas | `api-rate-limit-design` | this for step-up placement |
| Auth hard lock after N fails | `account-lockout-design` | this for CAPTCHA step-up |
| Provider secret storage and rotation | `secrets-management-hygiene` | this for key roles |
| Map endpoints before rollout | `api-recon-and-docs` | this for which need challenge |
| Code, tests, logging hygiene | `code-quality-standards` | **always** on implementation |

Keep **this skill primary** for build/harden. Switch to `captcha-bypass-research`
only under authorization; feed findings into verify, bind, and parity.
`code-quality-standards`: atomic consume, fail-closed on provider outage for auth,
no secrets in logs, tests for omit/replay/action mismatch.

## Output Checklist

- [ ] Abuse surfaces and entrypoints inventoried (web/mobile/API/GraphQL/legacy)
- [ ] Provider/mode chosen; edge challenge vs app verify roles documented
- [ ] Sitekey public / secret server-only; env-separated; no prod test keys
- [ ] Server siteverify: success, hostname, action, score, TTL, single-use
- [ ] Optional session/IP binding; fail-closed on provider errors for auth
- [ ] Step-up combined with rate limits and lockout—not CAPTCHA alone
- [ ] All clients share the gate; exemptions have compensating controls
- [ ] Accessibility / support overrides audited and time-boxed
- [ ] Metrics, alerts, and reject-path contract tests in place
- [ ] Secrets redacted; `secrets-management-hygiene` + `code-quality-standards` applied
- [ ] Residual risk recorded if any high-risk surface lacks challenge

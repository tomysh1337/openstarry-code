---
name: captcha-bypass-research
description: >
  Authorized CAPTCHA and bot-challenge control research: when challenges bind,
  client-trust gaps, reusable tokens, logic skips, accessibility/alternate paths,
  and rate-limit interplay. Use for labs, CTFs, and scoped assessments measuring
  control effectiveness — not fraud, credential stuffing, ticket scalping, or
  CAPTCHA-farm abuse.
---

# CAPTCHA Bypass Research (Authorized Labs)

## Scope And Authorization

- **Authorized only**: owned apps, vendor labs, CTFs, bug bounty / pentest programs that allow bot-mitigation testing.
- Purpose is **control quality measurement** — show that automation or account abuse windows remain open despite CAPTCHA — **not** to enable fraud, spam, scalping, bulk account creation, or third-party CAPTCHA-solving services against production.
- Prefer **test accounts**, staging, and vendor test keys. Do not attack CAPTCHA providers’ infrastructure; do not purchase or integrate CAPTCHA-solving farms for out-of-scope abuse.
- Cap attempt volume. CAPTCHA and challenge endpoints often front SMS/email/login — coordinate cost and lockout risk; stop before shared users are impacted.
- Redact sitekeys, full tokens, cookies, and solver API secrets from public writeups.
- Missing CAPTCHA alone is usually **informational** unless paired with a concrete abuse path (unlimited OTP guess, free signup factory, password spray window) — bind findings to impact via `rate-limit-bypass-testing` and auth skills.

## When To Use

- Login, register, password reset, checkout, vote, or scrape-prone APIs show CAPTCHA, Turnstile/hCaptcha/reCAPTCHA widgets, or interstitial bot challenges.
- Engagement language: “CAPTCHA bypass”, “bot protection skip”, “token reuse”, “challenge not enforced server-side”.
- You observe the widget in the browser but the **API accepts requests without a valid server-side verification**.
- Alternate clients (mobile API, legacy endpoint, GraphQL) lack the challenge the web UI shows.
- **Do not use** this skill to operationalize fraud, mass credential stuffing, or solving challenges for third-party sites without authorization.

## Core Model

```
User action → challenge issued (widget / interstitial / proof-of-work)
  → client obtains token or passes check
  → server MUST verify token with shared secret / provider API / session binding
  → then perform sensitive action
```

Weakness classes (research taxonomy):

| Class | Failure mode | Research signal |
| --- | --- | --- |
| **Not enforced** | UI-only CAPTCHA | API success with empty/omitted token field |
| **Wrong step** | Challenge on GET form, not on POST action | Direct POST skips check |
| **Token not bound** | Token reusable, transferable, or not tied to action/IP/session | Replay same token N times or on other account |
| **Provider result ignored** | `success:false` still accepted; hostname unchecked | Mutated token or wrong hostname still passes app |
| **Alternate surface** | Mobile / v1 / partner API unprotected | Same abuse without token |
| **Logic skip** | Step token / feature flag / “dev” param disables check | Parameter or path variant |
| **Race / TOCTOU** | Check then act without atomic consume | Parallel use of one single-use token |
| **Rate-limit only** | CAPTCHA after N, but N is large or bypassable | Pair with rate-limit skill |

**Good proof:** Sensitive action completes for a **test** identity without solving a fresh challenge (or with a deliberately invalid token), with request evidence and server verification gap explained.  
**Bad proof:** “We used a paid solver against production login” as the only narrative; or DoS against the challenge endpoint.

## Workflow

### 1. Inventory challenge surfaces

From proxy history and UI:

| Surface | What to record |
| --- | --- |
| Pages with widgets | Provider (reCAPTCHA v2/v3, hCaptcha, Turnstile, custom, image CAPTCHA) |
| Sitekey / siteparams | Public sitekey only; never exfiltrate provider secrets |
| Token parameter names | `g-recaptcha-response`, `h-captcha-response`, `cf-turnstile-response`, custom |
| Actions protected | login, register, reset, comment, checkout, vote |
| Score-based vs checkbox | v3/score thresholds if visible in JS |
| Interstitial / JS challenge | CDN bot fight mode vs app-level CAPTCHA |

Map **browser path** vs **raw API path** for the same action.

### 2. Establish honest baseline

1. Complete the flow **once** legitimately (solve CAPTCHA as a normal user in lab).
2. Capture the verify request: token length/shape, extra fields (`remoteip`, action name), response cookies.
3. Confirm failure mode with empty token, `null`, omitted field, and garbage string — statuses and error codes.
4. Note whether rate limits or lockouts appear (`429`, temporary ban). Document for `rate-limit-bypass-testing` handoff.

### 3. Server-enforcement matrix (primary research)

Change **one** variable per trial against the sensitive **API** (not only the HTML form):

| Probe | Request change | Pass means |
| --- | --- | --- |
| Omit token | Remove CAPTCHA field | Not enforced |
| Empty token | `""` or whitespace | Weak validation |
| Garbage token | Random base64 | No provider verify |
| Expired token | Old captured token | No TTL / no single-use |
| Replay | Same valid token twice | Not consumed / not bound |
| Cross-account | Token from account A on action for B | Missing session binding |
| Cross-action | Login token on register (or reverse) | Missing action binding |
| Wrong sitekey token | Token minted for another **lab** site you own | Hostname/sitekey not checked by app |

Use only tokens from **your** solves or **your** lab sites. Do not harvest tokens from other users.

### 4. Client-trust and logic skips

1. Search JS and mobile clients for `skipCaptcha`, `bypass`, `debug`, `captcha=false`, feature flags, or hardcoded “always valid” stubs — authorized code review / local builds only for third-party apps.
2. Replay API bodies while stripping browser-only headers; confirm server does not trust `X-Requested-With` or similar as a substitute for CAPTCHA.
3. Multi-step wizards: obtain challenge on step 1, skip to final POST with step tokens only — classic business-logic adjacency (`business-logic-vuln`).
4. GraphQL: mutation without captcha field vs REST twin that requires it (`graphql-and-hidden-parameters` for discovery).

### 5. Alternate entrypoints and clients

| Entry | Why it matters |
| --- | --- |
| Mobile API host | Often weaker bot rules |
| Legacy `/api/v1` | CAPTCHA added only to v2 web |
| Partner / embed SSO | Different WAF profile |
| Password reset vs login | One protected, one not |
| Bulk or admin import | No CAPTCHA by design — document residual risk |

Same abuse goal, different route: if any in-scope route skips CAPTCHA **and** lacks compensating rate limits / MFA, report the **control gap** with impact.

### 6. Token lifecycle and races

1. **Single-use:** After one successful verify, replay should fail; if not, document reuse window.
2. **Parallel:** Two concurrent requests with one token (Turbo Intruder / parallel Repeater) — if both succeed, note TOCTOU; helper `race-condition`.
3. **TTL:** Age tokens (1m / 10m / 1h) within lab policy; do not stress provider APIs.
4. **Binding claims:** If JWT-like challenge tokens appear, inspect claims only on tokens issued to you; alg confusion belongs under `api-auth-and-jwt-abuse`.

### 7. Score-based and passive challenges (v3 / bot scores)

1. Record score-related parameters if the app echoes them (rare) or if server behavior changes with headless vs normal browser **on your lab account**.
2. Research whether the **application** enforces a minimum score server-side or only styles the button in JS.
3. Headless detection gaps are residual risk notes — do not productize stealth-browser kits for fraud. Prefer reporting: “sensitive action accepts requests with failed/missing risk signal.”

### 8. Interaction with rate limits and WAF

1. If CAPTCHA appears only after N failures, measure N and whether N resets via IP headers or path aliases → primary may become `rate-limit-bypass-testing`.
2. If edge challenge (JS VM, managed challenge) blocks tools, document fingerprint; do not run volumetric challenge-bypass floods. WAF signature work → `waf-bypass-techniques`.
3. CAPTCHA that is always present but API unlimited still fails open if token not verified — keep CAPTCHA skill primary for the verify gap.

### 9. Accessibility and legitimate alternate paths

1. Audio CAPTCHA, support override, and allowlisted QA keys are **legitimate** product paths — test only if in scope.
2. Misconfigured **always-pass test keys** left in production are high-value findings (provider test secrets).
3. Do not harass human support channels to social-engineer CAPTCHA removal.

### 10. Impact binding and remediation

Bind every report to an abuse story:

| Gap | Impact narrative (authorized test identity) |
| --- | --- |
| Register without CAPTCHA | Account factory if no other throttles |
| Login without CAPTCHA | Password spray window if rate limit weak |
| Reset without CAPTCHA | Email/SMS cost or token grind |
| Vote/comment without CAPTCHA | Spam / integrity |

Remediation (implement with `code-quality-standards`):

- Verify tokens **server-side** with provider API or signed secret; reject `success:false`.
- Bind token to **action**, **session**, **site hostname**, and **single use** with short TTL.
- Enforce on **all** clients (web, mobile, API) after routing normalization.
- Combine with **account- and IP-keyed** rate limits (`rate-limit-bypass-testing` guidance).
- Never trust client assertions (`captchaPassed: true`); do not leave test keys in production.
- Log verify failures; alert on spike of missing-token attempts.
- For score-based modes, enforce threshold server-side and fail closed on provider errors.

## Concrete Techniques Cheatsheet

| Goal | Technique |
| --- | --- |
| Prove UI-only CAPTCHA | Burp: drop token field on API twin of form POST |
| Prove no provider check | Submit random token; compare to empty-token errors |
| Prove replay | Capture one valid lab solve; resubmit N times |
| Prove cross-endpoint skip | Mobile/legacy host same body without token |
| Prove step skip | Jump to final mutation without challenge step |
| Prove race | Parallel dual submit one single-use token |
| Prove test-key leak | Known provider test sitekey/secret patterns in config (code review) |
| Measure residual | CAPTCHA OK but rate limit weak → rate-limit skill |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CAPTCHA / bot-challenge control gaps | **This skill** | — |
| Unlimited attempts / quota keying / XFF | `rate-limit-bypass-testing` | this skill if challenge is the control under test |
| Unknown injection while testing forms | `injection-checking` | this skill only for challenge fields if relevant |
| HTTP desync to skip edge challenge | `request-smuggling` / `http2-specific-attacks` | this skill for app-level CAPTCHA after reachability |
| Business workflow skip around challenge | `business-logic-vuln` | this skill |
| Login/MFA/OTP beyond CAPTCHA | `api-auth-and-jwt-abuse` / MFA skills if present | `rate-limit-bypass-testing` |
| WAF/JS interstitial only | `waf-bypass-techniques` | this skill for app tokens |
| Implement verify + limits correctly | `code-quality-standards` | this skill for test evidence |
| Map all clients/endpoints | `api-recon-and-docs` | this skill |

## Output Checklist

- [ ] Authorization and environment (lab/staging/scoped prod)
- [ ] Surfaces: provider type, actions protected, web vs API
- [ ] Baseline: legitimate solve + failure modes (omit/empty/garbage)
- [ ] Enforcement matrix results (which probes passed)
- [ ] Token lifecycle: TTL, replay, binding, race notes
- [ ] Alternate entrypoints tried
- [ ] Rate-limit / WAF interaction notes
- [ ] Impact: abuse window with test identity (not fraud metrics)
- [ ] Remediation: server-side verify, bind, single-use, all clients, rate limits
- [ ] Explicit statement: no CAPTCHA-farm / fraud operationalization

## Rules

- Authorized labs and scoped assessments only — **not fraud**.
- Do not integrate commercial CAPTCHA-solving services to abuse third-party sites.
- Do not attack CAPTCHA vendor infrastructure or shared challenge CDNs beyond normal app traffic.
- Prefer demonstrating **missing server-side verification** over stealth automation kits.
- One variable per probe; minimal PoC; low volume.
- Pair CAPTCHA gaps with rate-limit and auth impact; avoid inflated severity for “no captcha on marketing form” without abuse path.
- Redact tokens and secrets; restore test fixtures when done.

---
name: permission-policy-headers
description: >-
  Assess and harden the Permissions-Policy (formerly Feature-Policy) HTTP
  response header: powerful browser features, allowlists, iframe delegation,
  and missing or over-permissive policies. Use when reviewing camera/mic/geo
  geolocation payment USB sensors fullscreen autoplay document-domain policy
  gaps, Feature-Policy legacy names, or edge/app header configs on owned apps
  and authorized assessments — not for attacking third-party sites.
---

# Permissions-Policy Headers

Own **Permissions-Policy** (legacy **Feature-Policy**): which powerful browser
features a document and nested contexts may use, and origin allowlists. Full
edge header suites → `nginx-security-headers`.

## Scope And Authorization

- **In scope:** org-owned apps, written-engagement staging/prod, labs, CTFs;
  config and live response review for `Permissions-Policy` / `Feature-Policy`.
- **Out of scope:** mass scanning; production policy changes without rollback;
  coercing users to grant device permissions.
- Prefer header inventory plus browser feature probes on authorized hosts.
- Redact tokens, cookies, device IDs, internal hostnames. Stage/canary before
  deny-all — third-party embeds may break.

## When To Use

- Responses omit `Permissions-Policy`, or only ship deprecated `Feature-Policy`.
- Sensitive UI could use camera, microphone, geolocation, payment, USB,
  sensors, clipboard, or display-capture without an explicit deny/allowlist.
- Nested iframes receive feature grants that should stay top-level only.
- Keywords: Permissions-Policy, Feature-Policy, `camera=()`, `geolocation`,
  `microphone`, `payment`, `fullscreen`, `autoplay`, `display-capture`,
  `document-domain`, browsing-topics / interest-cohort.
- Edge/app header hardening — pair code with `code-quality-standards`.

**Not primary:** CSP/XSS → `content-security-policy-bypass` /
`xss-cross-site-scripting`; clickjacking → `clickjacking` /
`clickjacking-frame-busting`; cookies → `cookie-security-flags`.

## Workflow

### 1. Inventory

```bash
# Authorized host only
curl -sI https://app.example/ https://app.example/login https://app.example/no-such
```

Record both headers; note CDN/edge vs origin conflicts. Map pages that need
powerful features (calls, maps, payments) vs static shells; include errors.

### 2. Syntax

```http
Permissions-Policy: geolocation=(), microphone=(), camera=(self),
  payment=(self "https://checkout.example"), fullscreen=(self)
```

| Construct | Meaning |
| --- | --- |
| `feature=()` | Disabled here and in nested contexts |
| `feature=(self)` | Same-origin (plus controlled embeds) |
| `feature=*` | Any origin — usually too broad |
| `feature=("https://a.example")` | Explicit origin allowlist |
| Missing feature | Browser default (often allow-until-prompt) — not deny |

Legacy Feature-Policy used `'none'` / `'self'`. Prefer Permissions-Policy list
syntax; Feature-Policy-only is incomplete modernization.

### 3. High-value features

Disable unused features with `=()` unless product requires them. Confirm token
names against current MDN/spec for target browsers.

| Feature (examples) | Why restrict |
| --- | --- |
| `camera`, `microphone`, `display-capture` | Device / screen capture |
| `geolocation` | Location privacy |
| `payment` | Payment Request scope |
| `usb`, `serial`, `hid`, `bluetooth` | Local device access |
| `fullscreen`, `autoplay` | UI redress / unexpected media |
| `clipboard-read` / `clipboard-write` | Paste/exfil (UA-dependent) |
| `accelerometer`, `gyroscope`, `magnetometer` | Sensor fingerprinting |
| `browsing-topics`, `document-domain` | Tracking / relaxed same-origin |

### 4. iframes and misconfigs

Header deny can be undermined by iframe `allow="camera *"` on untrusted embeds —
review markup and header together. Grant widgets only required features/origins.
Framing impact → `clickjacking` skills.

| Pattern | Action |
| --- | --- |
| Header absent | Baseline deny-unused |
| `feature=*` on sensitive APIs | Tighten to `self` or origin list |
| Policy only on 200 | Cover errors/redirects (`always` / middleware) |
| Nested nginx `add_header` drops PP | Re-include (`nginx-security-headers`) |
| Edge vs app conflict / only Feature-Policy | Single owner; migrate to PP |

### 5. Verify and remediate

1. DevTools: header on HTML navigations; after deny, camera/geo fail or no prompt.
2. Owned child iframe cannot use denied features; product paths still work.
3. Implement with `code-quality-standards`: central middleware, presence tests, canary.

```http
Permissions-Policy: accelerometer=(), camera=(), display-capture=(),
  fullscreen=(self), geolocation=(), gyroscope=(), microphone=(), payment=(),
  usb=(), document-domain=()
```

Re-enable only product-needed features as `(self)` or partner origins — avoid
`*` without written exception.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Permissions-Policy / Feature-Policy audit | **This skill** | — |
| Full edge header suite (HSTS, CSP, XFO) | `nginx-security-headers` | this for PP detail |
| CSP bypass / XSS | `content-security-policy-bypass`, `xss-cross-site-scripting` | this if co-emitted |
| Clickjacking / frame-ancestors | `clickjacking`, `clickjacking-frame-busting` | this for feature grants |
| Cookie / CSRF / Sec-Fetch | related session/CSRF skills | not PP substitutes |
| Header middleware/tests | `code-quality-standards` | **always** on code |

**Handoff:** feature allowlists, iframe `allow`, PP syntax. Multi-header
baselines → `nginx-security-headers`. Framing → clickjacking.

## Output Checklist

- [ ] Scope/authorization and paths exercised
- [ ] PP / Feature-Policy inventory (incl. errors); edge vs origin ownership
- [ ] Unused features denied or risk-accepted; needed features `self`/origins
- [ ] No unjustified `*`; iframe `allow` over-delegation reviewed
- [ ] Browser verify deny/allow; product regression (media/maps/pay)
- [ ] Remediation + CQS if config/code changed; secrets/PII redacted
- [ ] Handoffs: `nginx-security-headers`, clickjacking, CSP as needed

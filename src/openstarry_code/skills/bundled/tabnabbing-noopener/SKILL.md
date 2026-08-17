---
name: tabnabbing-noopener
description: >
  Reverse tabnabbing and window.opener hardening for target=_blank links and
  window.open popups: rel=noopener noreferrer, Cross-Origin-Opener-Policy,
  and audits of user-generated or untrusted outbound links. Use when pages
  open third-party or UGC URLs in new tabs without isolating opener, when
  window.opener is non-null after navigation, or when reviewing link
  sanitizers, markdown/HTML renderers, or phishing-adjacent tabnab risks.
---

# Reverse Tabnabbing And noopener

## When To Use

- Markup or templates emit `target="_blank"` (or equivalent new-tab navigation) without `rel="noopener noreferrer"`.
- Client code calls `window.open(url, '_blank')` / `window.open(url)` for untrusted or third-party URLs and does not set `noopener` / `noreferrer` features.
- User-generated content (comments, bios, markdown, rich text, chat) renders outbound links that open in a new tab.
- Browser DevTools shows `window.opener` still pointing at the origin after a cross-origin open.
- Hardening reviews ask for COOP, referrer leakage on outbound links, or phishing risk from tab replacement.
- Not primary for open redirect sinks (`open-redirect`), pure XSS in link HTML (`xss-cross-site-scripting` / `markdown-xss-sanitization`), or postMessage between windows (`postmessage-security`). Combine when those channels amplify impact.

## Scope And Authorization

- Authorized applications, owned staging, labs, and CTFs only. Do not host phishing pages that target real users outside the engagement.
- Prefer lab proofs: opener-controlled navigation of a test account tab to a controlled canary URL or `about:blank` with a clear banner — not credential harvesting of third parties.
- Redact session tokens, cookies, personal data, and full referrer URLs that embed secrets from reports and screenshots.
- Document browser name/version: modern defaults for `target=_blank` differ from legacy engines and embedded WebViews.
- Treat findings as **client isolation** issues; severity depends on trust of the opened origin and presence of sensitive UI in the opener tab.

## Workflow

### 1. Inventory new-tab and popup sinks

1. Search templates, SSR HTML, and client bundles for:
   - `target="_blank"` / `target='_blank'`
   - `window.open(`
   - framework link props (`target: '_blank'`, Next.js/`Link`, React Router external links)
   - markdown/HTML sanitizer config for `a[target]` / `a[rel]`
2. Classify each sink by **URL trust**:
   - First-party fixed URL (docs, help)
   - Allowlisted partner
   - Fully user-controlled or weakly validated external URL (highest priority)
3. Note whether `rel` is static, partially set (`nofollow` only), or absent; note `window.open` feature strings (`noopener=yes`, `noreferrer=yes`).

### 2. Understand reverse tabnabbing

When page A opens page B and B retains a reference to A via `window.opener`:

1. B may script `window.opener.location = attackerURL` (or navigate opener to a lookalike login).
2. The victim returns to the original tab and interacts with attacker content under the expectation it is still A.
3. Impact is **UI phishing / session confusion** in the opener tab, not direct SOP bypass to read A’s DOM (cross-origin opener access is limited). Same-origin B can do more if A opens a same-origin path attacker can influence.

Primary mitigations historically: `rel="noopener"` (severs `opener`), `rel="noreferrer"` (implies noopener in browsers and strips referrer), and `window.open(url, '_blank', 'noopener,noreferrer')`.

### 3. Modern browser defaults (do not skip measurement)

Defaults change by engine and version — **always verify on the engagement’s target browsers and any in-scope WebView**:

| Context | Typical modern desktop browser behavior | Residual risk |
| --- | --- | --- |
| `<a target="_blank">` without `rel` | Often treated as `noopener` by default in current Chromium/Firefox/Safari | Older browsers, some WebViews, non-standard embeds; policy still wants explicit `rel` |
| `window.open` without features | May still expose `opener` depending on browser | Explicit `noopener` required for defense-in-depth |
| `rel="noopener"` | `window.opener` is null in B | Prefer also `noreferrer` or Referrer-Policy when URL secrecy matters |
| `rel="noreferrer"` | No referrer + noopener semantics in major browsers | May break analytics that rely on referrer |
| COOP on A (`same-origin` / `same-origin-allow-popups`) | Cross-origin openers isolated at process/browsing-context group level | Complements link `rel`; does not replace careful `window.open` |

Record actual `window.opener === null` vs object in the **opened** page, not assumptions from blog posts alone.

### 4. Authorized proof technique

1. Deploy a controlled page B (lab domain) that logs `!!window.opener` and, if non-null, offers a button: `opener.location = 'https://canary.example/tabnab-demo'`.
2. From the target app, trigger the sink that opens B (UGC link, “Open resource”, OAuth-style external help link, etc.).
3. In B’s console/UI, record opener presence, origin of `document.referrer`, and success of opener navigation.
4. If opener navigation works, capture before/after screenshots of tab A under test account only.
5. Repeat with fixes applied in a local patch or staging: `rel="noopener noreferrer"`, then `window.open(..., 'noopener,noreferrer')`, then optional COOP header — note which control closed the issue.

### 5. Audit user-generated and sanitized links

1. Submit links with `target=_blank` if the app preserves attacker-supplied `target`/`rel` (HTML injection into anchors).
2. If the app forces `target=_blank` on all external URLs, confirm it also forces safe `rel` (and does not strip only `nofollow`).
3. Markdown renderers: check whether autolinks and `[text](url)` get `noopener`/`noreferrer` by default (many need explicit option).
4. Reject or rewrite `javascript:` / `data:` URLs in the same pass (`markdown-xss-sanitization`, `xss-cross-site-scripting` when HTML is free-form).
5. Prefer server-side canonicalization: external → always `rel="noopener noreferrer"` (plus `nofollow ugc` when appropriate); internal → no need for blank+noopener unless product requires new tab.

### 6. Defense checklist (implementation review)

- Every `target="_blank"` includes `rel="noopener noreferrer"` (or app-wide post-processor).
- Every `window.open` to untrusted URL uses feature `noopener,noreferrer` (or assigns `opened.opener = null` only as legacy fallback — prefer feature string).
- Referrer-Policy (`no-referrer` or strict-origin-when-cross-origin) on sensitive pages if path/query must not leak.
- Optional: `Cross-Origin-Opener-Policy` on authenticated app origins.
- CSP and HTML sanitizers cannot be bypassed to drop `rel` while keeping `target`.
- Third-party widgets that open windows reviewed with the same rules.

### 7. Severity guidance

| Scenario | Typical severity signal |
| --- | --- |
| UGC opens attacker origin with live `opener` on browsers in-scope | Medium (phishing UX); higher if high-value session UI sits in opener |
| Only first-party help links; modern browsers null opener by default | Low / informational — still fix for policy consistency and WebViews |
| `opener` null but full URL referrer leaks tokens | Treat as referrer/info leak, not classic tabnabbing |
| Same-origin open to attacker-controlled path (stored XSS / open redirect chain) | Escalate with XSS / open-redirect skills |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| `target=_blank` / `window.open` / opener tabnab | **This skill** | — |
| Redirect parameter sends victim off-site | `open-redirect` | this skill if new tab + opener |
| Stored/reflected HTML in anchors | `xss-cross-site-scripting` | this skill for `rel`/`target` |
| Markdown/HTML sanitizer link policy | `markdown-xss-sanitization` | this skill |
| postMessage between opener and popup | `postmessage-security` | this skill for opener nulling |
| Framing / UI redress (not tab replace) | `clickjacking` | — |
| Secure defaults in code review | `code-quality-standards` | this skill |

## Output Checklist

- [ ] Sink list: markup vs `window.open` vs UGC renderer; URL trust level
- [ ] Observed `rel` / feature strings and any sanitizer rewrites
- [ ] Browser/WebView versions tested; `window.opener` null or not
- [ ] Referrer behavior if relevant
- [ ] Authorized PoC steps and canary navigation evidence (redacted)
- [ ] COOP / Referrer-Policy headers if present or recommended
- [ ] Remediation: explicit `noopener noreferrer`, safe `window.open`, UGC defaults
- [ ] Residual risk on legacy clients called out honestly

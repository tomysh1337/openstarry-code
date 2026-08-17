---
name: postmessage-security
description: >
  Authorized window.postMessage security review: origin validation on
  message handlers, targetOrigin misuse, untrusted data into DOM/code sinks,
  and XSS or token theft via postMessage. Use when apps use iframes, openers,
  webviews, or cross-window messaging, or when DOM XSS sources include
  event.data from message listeners.
---

# postMessage Security (Authorized)

## When To Use

- Application JS registers `window.addEventListener('message', …)` or `onmessage`.
- Flows use `iframe`, `window.open`, OAuth/popups, embedded widgets, chat UIs, or mobile webviews that bridge via `postMessage`.
- Suspected DOM XSS where the source is `event.data` rather than `location` or server HTML.
- Hardening review of cross-origin embeds (payment widgets, maps, SSO).
- Not primary for CORS header misconfiguration alone — use `cors-cross-origin-misconfiguration`. Not primary for pure server-reflected XSS — use `xss-cross-site-scripting`. Combine when postMessage delivers the payload into an XSS sink.

## Scope And Authorization

- Authorized web apps, staging, labs, CTFs, and in-scope production only.
- Host attacker parent/opener pages only on approved exploit origins or local files under program rules — do not phish real users.
- Prefer proofs with test accounts: unique canary strings, benign `postMessage` payloads, or self-account state — not bulk token harvesting.
- Redact tokens, session identifiers, personal data, and full `event.data` dumps that contain secrets.
- postMessage issues are **browser / client** issues: document origin of sender page, target window, and handler code path with reproducible steps.

## Workflow

### 1. Inventory messaging surfaces

1. In DevTools Sources or bundled JS (pretty-print), search for:
   - `addEventListener('message'`
   - `onmessage`
   - `.postMessage(`
2. Map each **sender** call site:
   - `targetWindow.postMessage(data, targetOrigin)`
   - `targetOrigin` value: concrete origin vs `"*"`
3. Map each **receiver** handler:
   - Origin checks (`event.origin`, `event.source`)
   - How `event.data` is parsed (string, JSON, structured clone)
   - Downstream sinks (DOM, storage, navigation, `eval`, app state)
4. Note multi-frame graphs: top ↔ iframe, opener ↔ popup, nested third-party widgets.

### 2. Origin and source validation review

For every handler, classify the origin gate:

| Pattern | Risk |
| --- | --- |
| No `event.origin` check | Any origin can send messages the handler accepts |
| `event.origin !== expected` missing else-return | Partial check bugs; fall-through |
| Allowlist via `indexOf` / `endsWith` / regex on origin | Prefix/suffix bypasses (`https://evil.example.com` vs `https://example.com`) |
| Protocol or port ignored | `http://` vs `https://`, non-default ports |
| Only checks `event.data.type` / token, not origin | Attacker forges shape if they can target the window |
| Checks `event.source === expectedWindow` only | Still verify origin; source alone can be subtle in multi-iframe apps |
| `targetOrigin: '*'` on send | Eavesdropping by embedded malicious frames if data is sensitive |

Secure baseline (conceptual):

- Receiver: allowlist exact origins (`https://app.example` — scheme + host + port).
- Sender: set `targetOrigin` to the exact expected receiver origin, not `*`, when data is sensitive.
- Prefer explicit message schema + origin check **before** any sink.

### 3. Probe with an authorized sender page

From an approved attacker origin, obtain a reference to the target window (iframe `contentWindow`, `window.open` result, or `window.opener` if the target opens you — only within test design).

```html
<script>
  // Authorized lab PoC skeleton — replace origins and payloads per engagement
  const target = document.getElementById('victim').contentWindow;
  const payload = { type: 'user', html: '<img src=x onerror=console.log("pmXss")>' };
  target.postMessage(payload, 'https://target.example'); // or '*' only if testing wildcard acceptance
</script>
<iframe id="victim" src="https://target.example/embed"></iframe>
```

Vary:

1. **Origin**: send from allowed vs disallowed attacker origins (different ports/schemes).
2. **Shape**: expected `type` / `action` fields, extra fields, prototype-like keys if objects are merged unsafely (route deep merge issues also to `prototype-pollution` when relevant).
3. **Types**: string vs object (handlers that `JSON.parse(event.data)` vs structured clone).
4. **Source window**: message from unexpected iframe vs opener.

Record whether the handler ran side effects (network, DOM, navigation, storage).

### 4. Sink analysis → XSS and data theft

Treat `event.data` as an untrusted **source** (same rigor as `location.hash`).

| If data reaches… | Impact class |
| --- | --- |
| `innerHTML` / `document.write` / angular-like `{{ }}` / rich text | DOM XSS — prove with `xss-cross-site-scripting` methodology |
| `eval` / `new Function` / `setTimeout(string)` | Direct code execution |
| `location` / `location.href` / `open(...)` | Open redirect / javascript URL navigation |
| `localStorage` / `sessionStorage` / cookies via JS | Persistence / later XSS |
| Auth token handlers / `postMessage` of secrets to `*` | Token theft if malicious embed can listen |
| `fetch`/XHR URL or body built from data | CSRF-like client calls; combine with cookie rules |

CSP may block some XSS proofs — continue with `content-security-policy-bypass` for policy-constrained execution, but still report unsafe handlers.

### 5. Sender-side issues (sensitive data broadcast)

1. App sends tokens, PII, or DOM snapshots via `postMessage(..., '*')`.
2. Embed attacker-controlled iframe (or compromised widget origin) and listen:

   ```javascript
   window.addEventListener('message', (e) => {
     if (e.data /* matches secret shape */) {
       console.log('captured', e.origin, e.data); // lab evidence only
     }
   });
   ```

3. Document who can embed the sender page (`frame-ancestors` / XFO) — weak framing + wildcard postMessage compounds impact (`clickjacking` for frame policy).

### 6. Common product patterns

- **OAuth / SSO popups:** `postMessage` of auth codes or tokens to opener — verify origin allowlist and exact message types.
- **Payment / chat / help widgets:** parent↔child protocol; fuzz message `type` for privileged actions (account switch, address change) without UI.
- **Mobile webview bridges:** host apps may inject JS; still validate origins when web content is multi-tenant.
- **Multi-tenant embeds:** `https://tenant.example` vs attacker registration of similar tenants on shared parents.

### 7. Relationship to CORS and SOP

- `postMessage` is an **intentional** SOP relaxation channel; fixing CORS does not fix a bad message handler.
- Credentialed API reads from a malicious origin remain CORS issues — `cors-cross-origin-misconfiguration`.
- If the handler’s only bug is reflecting into HTML, primary exploit writeup may live under XSS with postMessage as the source.

### 8. Remediation verification

1. Origin allowlist: exact string match (or `URL` parse + equality on `origin`), fail closed.
2. Validate message schema (type, version, required fields); reject unknown actions.
3. Send with explicit `targetOrigin`; never `*` for secrets.
4. Do not pass `event.data` into HTML/code sinks; use `textContent`, safe APIs, or sanitizers if rich content is required.
5. Avoid privileged actions solely from postMessage without secondary auth when risk is high.
6. Retest with attacker origin PoC; add unit tests for the origin guard (`code-quality-standards`).

## Routing

| Need | Skill |
| --- | --- |
| DOM/HTML/script sink exploitation detail | `xss-cross-site-scripting` |
| Injection class unclear | `injection-checking` |
| Cross-origin XHR/fetch **read** with ACAO | `cors-cross-origin-misconfiguration` |
| CSP blocks proof payload | `content-security-policy-bypass` |
| Unsafe object merge from message data | `prototype-pollution` |
| Framing policy for embeddable sender | `clickjacking` |
| Secure handler / origin-check implementation | `code-quality-standards` |

## Output Checklist

- [ ] Handler locations (file/bundle + listener registration)
- [ ] Origin check logic: none / broken allowlist / exact allowlist
- [ ] Sender `targetOrigin` values (`*` vs concrete)
- [ ] Message schema and privileged `type`/`action` values
- [ ] Source → sink path for `event.data` (XSS, navigation, storage, auth)
- [ ] Authorized PoC: attacker origin page, payload, observed effect
- [ ] Browser/version; iframe vs opener topology
- [ ] CSP / cookie flags affecting impact
- [ ] Remediation and retest status
- [ ] Redacted evidence (no live tokens)

## Rules

- Always prove with a concrete sender origin and observable sink effect.
- Do not report “postMessage used” alone — require missing/broken origin checks or sensitive data to `*` or a dangerous sink.
- Label self-impact (attacker must already control a same-origin window) vs cross-origin embed/opener impact honestly.
- Keep payloads minimal; avoid destructive stored actions on shared production data.
- Authorized targets only; no real-user phishing popups or drive-by token stealers.
- Prefer exact-origin allowlists in remediation over substring checks.

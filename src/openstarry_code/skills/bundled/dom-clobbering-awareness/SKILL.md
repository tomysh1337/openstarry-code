---
name: dom-clobbering-awareness
description: >
  Authorized DOM clobbering awareness: named HTML elements (id/name) shadowing
  window and document properties, form/collection multi-level clobbering, and
  client config or sink confusion without a script injection. Use when markup
  accepts attacker-controlled id/name attributes, JS reads bare globals or
  document.* as config, or reviews mix DOM clobbering with XSS or prototype
  pollution during authorized web assessments.
---

# DOM Clobbering Awareness (Authorized)

## When To Use

- Untrusted HTML (or partial markup) can set `id` / `name` on elements, forms, anchors, or embeds.
- Client JS reads bare identifiers (`config`, `defaultSettings`, `isAdmin`) or `document.x` without hard guarantees they are plain objects or primitives.
- Libraries or gadgets check `if (window.foo)` / `window.foo.bar` and treat truthy DOM nodes as configuration.
- Bug bounty, lab, CTF, or hardening review mentions DOM clobbering, named-property shadowing, or “HTML-only” client takeover.
- Not primary for script/HTML injection sinks — use `xss-cross-site-scripting`. Not primary for `__proto__` / merge pollution — use `prototype-pollution`. Combine when clobbering feeds an XSS sink or merges with untrusted objects.

## Scope And Authorization

- Owned apps, staging, labs, CTFs, and explicitly in-scope production only.
- Prefer non-destructive proofs: unique canary element ids/names, benign `console` markers, self-account markup — not session theft against real users.
- Host exploit HTML only on approved origins or local PoCs under program rules.
- Document browser and version; named-property behavior differs across engines and over time.
- Redact tokens, cookies, PII, and live session markup from reports.
- “Clobbering” means a **working** shadow of a JS-readable property with observable wrong branch or sink input — not a theoretical list of every global.

## Workflow

### 1. Inventory untrusted markup and JS assumptions

1. Find where attacker-controlled HTML is rendered: profiles, comments, markdown/HTML sanitizers, CMS fields, email-like templates, SVG, rich editors, error pages that echo markup.
2. Note sanitizer policy: are `id`, `name`, `form`, nested controls, `<a name>`, `<embed>`, `<object>`, `<img>`, `<iframe>` stripped or preserved?
3. Grep client bundles for patterns that trust globals or `document` named properties:
   - Bare `config`, `options`, `params` used without `const`/`let` local binding
   - `window.APP_CONFIG`, `document.currentScript`, `document.querySelector` fallbacks that first check `window.x`
   - `if (x)` / `x || default` where `x` may resolve to a DOM node
   - Code that does `JSON.parse`-like logic on values that could be elements (`.value`, `.href`, `.src`)
4. Map **which names** matter (config keys, feature flags, CDN base URLs, callback names).

### 2. Single-level clobbering (id / name → window or document)

Core idea: in browsers, certain elements with `id` or `name` become reachable as `window[name]` or via `document[name]` collections.

| Injected shape (lab) | Typical JS read | Risk if untrusted markup allowed |
| --- | --- | --- |
| `<a id="config">` | `window.config` truthy; not a plain object | Branch taken; property access may yield unexpected types |
| `<img name="isEnabled">` | `isEnabled` / `window.isEnabled` | Feature-flag style checks pass incorrectly |
| `<form name="settings">` | `document.settings` / `window.settings` | Later `.action` / field access follows form semantics |
| Named `<form>` fields | `form.fieldName` | Nested-looking access without real objects |

Proof pattern (authorized):

1. Inject one canary element with a **unique** id matching a sensitive global the app reads.
2. In DevTools, evaluate `window.canaryName` / `document.canaryName` and record node type.
3. Trigger the app path that reads that name; record wrong default, network URL, or UI branch.

### 3. Multi-level and form-collection clobbering

Some gadgets need `window.a.b` style access. Forms and nested named controls can approximate that:

1. `<form id="a"><input id="b" value="…">` style structures so `a.b` resolves toward a control (engine-dependent details — **measure**, do not assume).
2. Anchors with `name`/`id` and `href` when code reads `.href` / toString-like coercion of elements.
3. Multiple elements sharing names → `HTMLCollection` / `RadioNodeList`: `.length`, indexing, or `.value` may surprise strict object expectations.
4. Clobbering **methods or known document APIs** is often constrained by browsers; prefer app-specific names over claiming universal `getElementById` replacement without proof.

Always validate the exact chain in the target browser before reporting multi-level impact.

### 4. Source → effect classification

| If clobbered name influences… | Treat as |
| --- | --- |
| Script URL, `import()`, loader base, `src` assignment | High impact client RCE-class when script executes — pair with `xss-cross-site-scripting` |
| `innerHTML` / HTML builders using clobbered strings | DOM XSS pipeline — XSS skill for sinks |
| Feature flags / client authz defaults | Integrity / business-logic client bypass (document honestly as client-only unless server trusts it) |
| API base URL / analytics endpoint | Data exfil or wrong-origin calls if network follows client |
| Object merge of clobbered value | May combine with `prototype-pollution` only if real object merge exists — do not conflate |

DOM clobbering is **not** prototype pollution: it shadows bindings via the DOM namespace, not `Object.prototype`.

### 5. Sanitizer and Trusted Types notes

1. HTML sanitizers that allow `id`/`name` but strip `on*` and `script` still leave clobbering surface.
2. Allowlisting tags without attribute filtering is insufficient; filter or namespace `id`/`name` (prefixes), or strip them on untrusted HTML.
3. Trusted Types help DOM XSS sinks; they do **not** stop named properties from existing on `window`/`document`.
4. CSP may block script gadgets after clobbering a script URL — note CSP in impact; continue with `content-security-policy-bypass` only if policy-constrained execution is in scope.

### 6. Remediation verification

1. Prefer explicit module-scoped config: `const config = …` from JSON endpoint or inline boot payload, not ambient globals.
2. Do not use bare identifiers for security or control flow; use `window.APP.config` only after validating `typeof` / `Object.prototype.toString` / schema parse on a real object.
3. For dictionaries, avoid relying on ambient names; use `Map` or validated plain objects from `JSON.parse`.
4. Sanitize untrusted HTML: strip or rewrite `id`/`name` (and dangerous URL attrs) per policy; test with canary ids after fix.
5. Add regression tests that render markup with attacker ids matching former global names (`code-quality-standards`).
6. Retest original PoC in the same browser; confirm `window[name]` no longer drives the branch or is unreachable from untrusted HTML.

## Routing

| Need | Skill |
| --- | --- |
| HTML/script sink, DOM XSS, encoding | `xss-cross-site-scripting` |
| `__proto__` / deep merge / query parser pollution | `prototype-pollution` |
| Secure config loading, sanitizer tests, typing | `code-quality-standards` |
| Injection class unclear | `injection-checking` |
| CSP blocks clobber-driven script URL | `content-security-policy-bypass` |
| `postMessage` trusts bad data shape | `postmessage-security` |

This skill is primary for **named-property / markup clobbering awareness**. Hand pure XSS or pure prototype pollution to those skills; keep this as helper when clobbering is the source.

## Output Checklist

- [ ] Untrusted markup surface and sanitizer behavior for `id`/`name`
- [ ] JS reads that assume plain config/globals (file/bundle + symbol names)
- [ ] Minimal HTML PoC and browser/version
- [ ] Observed binding: `window.*` / `document.*` / form field chain
- [ ] Observable effect (branch, URL, sink input) — evidence-backed
- [ ] Impact class: client flag, network, XSS assist, none
- [ ] Distinction from prototype pollution stated if both discussed
- [ ] Remediation and retest status
- [ ] Redacted evidence (no live tokens/PII)

## Rules

- Authorized targets only; no real-user drive-by pages.
- Prove with one canary name and one code path; avoid encyclopedia lists of globals as “findings.”
- Measure multi-level chains in the actual browser; label engine-specific behavior.
- Do not call DOM clobbering “prototype pollution” or plain “XSS” without the matching sink/prototype evidence.
- Prefer client-integrity and hardening language when the server does not trust the clobbered value.
- Keep originals immutable; store PoC HTML separately from production content.

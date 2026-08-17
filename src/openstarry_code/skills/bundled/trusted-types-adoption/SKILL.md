---
name: trusted-types-adoption
description: >
  Adopt browser Trusted Types for DOM XSS mitigation: require-trusted-types-for,
  trusted-types, createPolicy, default policy risks, sink migration (innerHTML,
  outerHTML, insertAdjacentHTML, document.write, script src/text, eval),
  report-only rollout, browser support. Use when enabling Trusted Types on owned
  or authorized web apps, fixing TypeError on DOM sink assignment, reviewing
  createPolicy or default policies, or pairing CSP with DOM XSS defenses — hand
  pure XSS to xss-cross-site-scripting and CSP bypass to
  content-security-policy-bypass.
---

# Trusted Types Adoption

Defensive adoption of Trusted Types and CSP so string assignment to DOM XSS sinks
fails closed unless values pass an explicit policy. Owned apps, staging, labs,
and authorized assessments only.

## When To Use

- Enabling `require-trusted-types-for 'script'` and/or `trusted-types` (enforce
  or report-only) on a document or SPA shell.
- TT violations / `TypeError` on `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
  `document.write`, `eval`/`Function`, or script `src`/text fed plain strings.
- Designing `createPolicy` or reviewing a **default** policy; migrating
  jQuery/templates/CMS/Markdown HTML paths; progressive enforce planning.

Do **not** use as primary for general XSS (`xss-cross-site-scripting`), CSP bypass
(`content-security-policy-bypass`), Markdown-only sanitization
(`markdown-xss-sanitization`), or nginx headers (`nginx-security-headers`).

## Scope And Authorization

- **In scope:** org-owned frontends, staging, labs, CTFs, production under written
  engagement; config and client code you may change or review.
- **Out of scope:** weaponizing TT gaps on third parties; real-user session theft
  as proof. Prefer report-only + canaries before enforce; keep header rollback.
- Redact tokens, cookies, nonces, PII. Evidence: full CSP, violations, browser, sinks.

## Workflow

### 1. Baseline sinks and CSP

1. Inventory sinks: `innerHTML`/`outerHTML`/`insertAdjacentHTML`,
   `document.write`/`writeln`, `DOMParser` inserts, `Range.createContextualFragment`,
   string `setTimeout`/`setInterval`, `eval`/`new Function`, script `src`/`text`,
   framework APIs (`dangerouslySetInnerHTML`, `v-html`, `|safe`).
2. Capture CSP enforce and report-only; note `script-src`, nonces/hashes, any TT
   directives (posture → `content-security-policy-bypass`). List third-party
   widgets that mutate the DOM (often need named policies).

### 2. Browser support and delivery

Chromium: primary enforce + report. Firefox/Safari: verify **current** versions;
do not assume full parity. WebViews: often older Chromium — pin min version and
test the real shell. Node SSR: no browser TT — sanitize at render; TT guards
client sinks after hydrate. Prefer HTTP headers; report-only first, then enforce.

### 3. CSP directives

1. **`require-trusted-types-for 'script'`** — require Trusted Types for
   script-adjacent DOM XSS sinks (main enforcement switch).
2. **`trusted-types PolicyA PolicyB ...`** — allowlist `createPolicy` names;
   keep minimal. `'allow-duplicates'` only with a documented dual-load case.
3. Pair with strong `script-src` (nonces/hashes; avoid `'unsafe-eval'` when
   possible). TT does **not** replace CSP script control or server encoding.
4. Dual-header rollout: enforce on canaries; report-only on main until clean.

### 4. createPolicy and default policy

1. Create policies **once** at bootstrap; export `createHTML` / `createScript` /
   `createScriptURL` only. Prefer **named policies per subsystem** and official
   framework TT hooks.
2. **createHTML:** maintained sanitizer (e.g. DOMPurify Trusted Type return) or
   strict builders — never identity-return untrusted input.
3. **createScript / createScriptURL:** app constants, SRI catalog, or validated
   URLs only; deny open concat from user/query/storage.
4. **Default policy** runs on raw-string sink assignment without an explicit type
   (migration crutch, not a goal).

| Pattern | Risk |
| --- | --- |
| Identity `createHTML: (s) => s` | Disables TT for that sink class |
| Log-then-wrap unsanitized HTML | Same as off if data becomes TrustedHTML |
| Weak regex “sanitize” in default | Bypass-prone; real sanitizer or throw |
| Forever-on default in production | Hides non-migrated sinks |

Prefer **no default** after migration. Temporary default must sanitize or reject,
emit metrics, and have a removal ticket. Never re-enable attacker-controlled `eval`.

### 5. Migration sequence

1. **Measure:** report-only + violations grouped by sink and stack.
2. **Fix:** prefer `textContent` / safe DOM APIs; else `policy.createHTML(sanitized)`.
   Upgrade/shim libraries or sandbox third-party HTML in iframes.
3. Register named policies; list in `trusted-types`; remove default; enforce
   `require-trusted-types-for 'script'` on documents that host sinks.
4. Tests: raw untrusted strings rejected; policy values accepted
   (`code-quality-standards`). Retest XSS under enforce
   (`xss-cross-site-scripting` for PoC method).

TT alone does **not** fix server-reflected HTML without client sinks, DOM
clobbering (`dom-clobbering-awareness`), unsafe `postMessage`
(`postmessage-security`), weak CSP allowlists (`content-security-policy-bypass`),
or non-HTML contexts (`output-encoding-patterns`).

## Routing table

| Situation | Primary | Helper |
| --- | --- | --- |
| TT adoption, createPolicy, default, sink migration | **This skill** | — |
| Find/prove XSS or DOM sink impact | `xss-cross-site-scripting` | this for TT gaps |
| CSP parse, nonce/hash/strict-dynamic, bypass | `content-security-policy-bypass` | this for TT directives |
| Injection class unknown | `injection-checking` | XSS / this after DOM sink |
| Markdown → HTML sanitization | `markdown-xss-sanitization` | this if client uses TT |
| Edge CSP (nginx) / context encoding | `nginx-security-headers` / `output-encoding-patterns` | this for TT / HTML sinks |
| Policy modules, tests / DOM clobbering | `code-quality-standards` / `dom-clobbering-awareness` | always / if clobber → HTML |

**This skill** owns Trusted Types rollout and policy design. Hand XSS proof to
`xss-cross-site-scripting` and broader CSP attack surface to
`content-security-policy-bypass`.

## Output Checklist

- [ ] Scope recorded; sink inventory with code locations
- [ ] CSP (enforce + report-only) and TT directives quoted
- [ ] Browser/version matrix; enforce vs report-only plan
- [ ] Policy catalog; default absent or temporary fail-closed + removal plan
- [ ] No identity/passthrough on untrusted input; redacted violations; adapters
- [ ] Enforce live; XSS retest under TT; CSP posture; tests + CQS
- [ ] Residual risks (unsupported browsers, report-only only, sandboxes)

## Rules

- TT reduces DOM XSS from string-to-sink bugs; not a CSP/HttpOnly/encoding substitute.
- Fail closed: sanitize or reject — never identity-default untrusted HTML/script.
- Prefer safe DOM APIs over HTML strings; policies only when markup is required.
- Measure with report-only; enforce after stacks are clean; keep rollback.
- Authorized defensive work only; minimal canary proofs, not drive-by exploits.

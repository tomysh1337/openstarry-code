---
name: clickjacking-frame-busting
description: >-
  Defense-first clickjacking and frame-busting controls: X-Frame-Options,
  CSP frame-ancestors, SameSite cookie interaction, and authorized UI-redress
  validation. Use when hardening framable UI, reviewing anti-framing headers,
  replacing client-side frame-busters, or verifying framing defenses on owned
  or in-scope apps — not for general XSS or unauthenticated mass framing.
---

# Clickjacking Defenses And Frame-Busting

Harden pages against UI redress by enforcing **who may embed** the document,
documenting **cookie attachment in frames**, and proving residual risk only
with authorized, self-account checks. Primary controls are server headers;
client-side “frame-buster” scripts are not sufficient alone.

## When To Use

- Missing, weak, or conflicting `X-Frame-Options` (XFO) and CSP `frame-ancestors`.
- Replacing or auditing `if (top !== self)` / `top.location` frame-buster JS.
- Sensitive UI (settings, delete, OAuth approve, payments confirm) must not load
  in untrusted iframes; defense review or post-fix retest is required.
- SameSite / third-party cookie policy may block classic jacking — need residual
  risk notes without claiming universal immunity.
- Edge/CDN/app disagree on framing headers (path, host, 200 vs error vs redirect).

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full attack PoC / multi-step UI redress | `clickjacking`, `clickjacking-ui-redress-deep` |
| Script injection / DOM XSS | `xss-cross-site-scripting`, `injection-checking` |
| CSP script-src bypass research | `content-security-policy-bypass` |
| Cross-site state change without framing | `csrf-cross-site-request-forgery` |
| Cookie flag audit (broader than framing) | `cookie-security-flags` |
| nginx edge header delivery only | `nginx-security-headers` |

## Workflow

1. **Inventory sensitive documents**  
   List authenticated HTML (or SPA shells) where one click or short sequence
   changes state. Note URL, host variants (`www` / mobile), and whether the
   control lives on the initial document or a later client-routed view.

2. **Measure framing policy on the UI document**  
   Inspect response headers for every sensitive path (and 3xx/4xx if users can
   land there). Prefer evidence from the **document that paints the control**.

   | Control | Strong | Weak / avoid |
   | --- | --- | --- |
   | CSP `frame-ancestors` | `'none'` or explicit origin allowlist | Missing, `*`, bare `https:` |
   | `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Absent; obsolete `ALLOW-FROM` |
   | Both present | Modern browsers honor CSP when both set | Relying on XFO alone |
   | Delivery | Header on HTML document (and errors if needed) | Only on JSON/API or CDN static assets |

   Prefer **`frame-ancestors` as primary**; keep XFO as defense-in-depth for
   older clients. Values must match product needs (e.g. trusted admin embedders).

3. **Authorized framing smoke test**  
   From an **approved** attacker-origin page or local PoC host, load a minimal
   iframe of each candidate URL. Record: loads vs blocked, console XFO/CSP
   errors, path/host differences. Do not drive-by real users.

   ```html
   <iframe src="https://target.example/settings/danger" width="800" height="600"></iframe>
   ```

4. **SameSite and session attachment (not a substitute for frame block)**  
   - `SameSite=Lax` / `Strict`: cross-site iframes often lack session cookies in
     modern Chromium → classic authenticated jack may fail; document profile.
   - `SameSite=None; Secure` (or legacy missing SameSite) may still attach when
     third-party cookies are allowed.
   - Treat SameSite as **partial mitigation**, not a framing control. Unauth or
     public sensitive UI can still be jacked. Full cookie matrix →
     `cookie-security-flags`.

5. **Reject JS-only frame-busting as the sole control**  
   Historical bypasses include sandbox, double-frame, CSP on the parent, and
   race/navigation tricks. If only client busting exists: recommend server
   `frame-ancestors` (+ XFO). Optional layered UX: re-auth / WebAuthn for
   high-risk actions so one opaque click cannot complete the change.

6. **Edge, cache, and SPA consistency**  
   Check CDN/origin dual headers, nested nginx `add_header` drops, headers only
   on HTTPS or only on `/app/*`, and SPA shells that set CSP late or only on
   the API. Align allowlists with intentional embed partners only.

7. **Remediation and retest**  
   Ship CSP `frame-ancestors 'none'` or a tight allowlist; add XFO DENY/SAMEORIGIN
   as depth. Avoid sensitive state-changing GET. Retest iframe smoke + console
   after deploy. Implementation hygiene → `code-quality-standards`. Deep exploit
   chains beyond defense verify → `clickjacking` / `clickjacking-ui-redress-deep`.

## Routing

| Need | Skill |
| --- | --- |
| Defense headers, frame-buster replacement, framing retest | **This skill** |
| Baseline or advanced UI-redress PoC | `clickjacking`, `clickjacking-ui-redress-deep` |
| CSRF without framing | `csrf-cross-site-request-forgery` |
| Cookie SameSite/Secure/HttpOnly audit | `cookie-security-flags` |
| OAuth consent framed as protocol issue | `oauth-oidc-misconfiguration` |
| XSS / script-src CSP | `xss-cross-site-scripting`, `content-security-policy-bypass` |
| Edge header delivery (nginx) | `nginx-security-headers` |
| Safe config/app change practice | `code-quality-standards` |

## Output Checklist

- [ ] Authorization/scope and approved PoC hosting noted
- [ ] Sensitive URLs and host/path variants inventoried
- [ ] XFO and CSP `frame-ancestors` values on the **UI document** (and error/redirect gaps)
- [ ] Intentional embed allowlist documented (or `'none'`)
- [ ] Authorized iframe smoke: blocked vs load; browser/version
- [ ] SameSite / third-party cookie notes (residual risk, not sole control)
- [ ] Client frame-buster present? Marked insufficient alone if no server policy
- [ ] SPA/CDN/edge consistency checked
- [ ] Remediation: `frame-ancestors` + optional XFO; re-auth for high risk; no sensitive GET
- [ ] Retest evidence after fix; cookies/PII redacted

## Scope And Authorization

- **In scope:** owned apps, labs, CTFs, and written engagements that allow framing
  and header review. Prefer **test accounts** and self-impact actions.
- **Out of scope:** drive-by framing of real users; irreversible money movement or
  mass admin actions without explicit approval; treating this skill as general XSS.
- Host PoC HTML only on approved exploit servers or local files under program rules.
- Redact session cookies, tokens, and PII from screenshots and reports.
- Missing headers alone are incomplete without a **sensitive** framable control
  or a clear defense-gap finding on high-value UI under engagement rules.
- Evidence over assumptions: record effective browser behavior; do not claim all
  modern browsers are immune because of SameSite defaults alone.

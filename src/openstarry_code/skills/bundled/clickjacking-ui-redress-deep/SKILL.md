---
name: clickjacking-ui-redress-deep
description: >-
  Advanced authorized clickjacking and UI redress: multi-step overlays,
  drag-drop and cursor-jack chains, SameSite/third-party cookie limits,
  nested-frame and CSP frame-ancestors bypasses, and high-impact framed
  actions. Use when basic framing checks are done and a deeper PoC or
  defense review is required on owned or in-scope applications.
---

# Clickjacking / UI Redress (Deep)

## Scope And Authorization

- Authorized targets, labs, CTFs, and owned apps only. Host PoC HTML on an approved exploit server or local file under program rules — never drive-by real users.
- Prefer self-account impact (settings, delete own object, OAuth approve on test client). Avoid irreversible money movement, mass admin actions, or lockouts unless explicitly approved.
- Clickjacking is a **browser + UI** class: missing headers alone are incomplete without a framed sensitive control and a reproducible overlay path.
- Redact session cookies, tokens, and PII from screenshots; crop to the framed region needed for evidence.
- Respect program bans on deceptive phishing wording — use labeled “test bait” when required.

## Use When

- Basic XFO / `frame-ancestors` triage is done (or trivial) and the task needs **multi-step**, drag-drop, nested-frame, or SPA-shell advanced proof.
- Sensitive UI is framable in some browsers/profiles but SameSite, CHIPS, or third-party cookie policy blocks classic single-click — need documented limits and residual risk.
- Engagement language: advanced clickjacking, UI redress, double-click jack, cursorjack, drag-and-drop jack, framed OAuth consent.
- Not primary for pure CSRF without framing (`csrf-cross-site-request-forgery`), pure CORS reads (`cors-cross-origin-misconfiguration`), or generic header-only inventory (start with `clickjacking`).

## Workflow

1. **Confirm baseline framing (short path)**  
   Reuse or run the standard ladder from `clickjacking`: inventory sensitive UI, check `X-Frame-Options` and CSP `frame-ancestors` on the **document that holds the control**, load an authorized attacker iframe, note cookie attachment (`SameSite`, third-party cookie mode).

   | Control | Strong | Weak |
   | --- | --- | --- |
   | `X-Frame-Options` | `DENY` / `SAMEORIGIN` | Absent, obsolete `ALLOW-FROM` |
   | `frame-ancestors` | `'none'` or tight allowlist | Missing, `*`, broad `https:` |
   | Cookie in cross-site frame | N/A (defense is frame block) | `None; Secure` + third-party allowed |

2. **Map click surface geometry**  
   For each candidate action, record:

   | Item | Capture |
   | --- | --- |
   | URL and method | GET nav vs form/XHR after click |
   | Control type | button, checkbox, drag target, file input |
   | Layout | offsets, scroll, sticky headers, responsive breakpoints |
   | Dialog steps | open → confirm → optional re-auth |
   | Token in page | CSRF hidden field already in framed DOM |

   Prefer DevTools element measures over guesswork. Note mobile vs desktop layout differences.

3. **Single-click overlay (quality bar)**  
   Transparent iframe over bait; align bait over real control. Prefer near-zero `opacity` on the iframe; avoid `pointer-events` mistakes that steal the click from the frame.

   ```html
   <style>
     iframe.victim { position: absolute; opacity: 0.01; z-index: 2; border: 0; }
     .bait { position: absolute; z-index: 1; }
   </style>
   <button class="bait">Continue</button>
   <iframe class="victim" src="https://target.example/settings/danger"></iframe>
   ```

   Document viewport assumptions, opacity, and measured top/left. Prove state change on the **test** account.

4. **Multi-step and dialog chains**  
   - Step 1 click opens modal; step 2 confirms — reposition iframe/bait between events or use staged overlays.  
   - Time delays and CSS animations that move the real button under a fixed bait.  
   - “Are you sure?” flows where only the second click is state-changing — report the full scripted path.  
   - Re-auth / WebAuthn gates: if a single framed gesture cannot complete, document residual framing risk vs actual exploitability.

5. **Drag-drop, file, and cursor variants**  
   - Drag bait source over framed drop zone (upload tray, share target, kanban).  
   - File-picker / attach flows if program accepts UI-redress impact.  
   - Fake cursor / oversized hit regions only when in scope; label as UX deception layered on framing.  
   - Nested iframes: attacker page → intermediate → target; test whether `frame-ancestors` allows an unexpected ancestor chain.

6. **Bypass and environment edges**  
   - SPA shell lacks CSP while later route paints sensitive UI (or reverse).  
   - Path/host split: `/app/*` protected, `/legacy/*` or mobile subdomain not.  
   - CDN/cache serves old HTML without `frame-ancestors`.  
   - `frame-ancestors` only on error JSON, not the HTML document.  
   - Sandbox attribute on parent frames; `allow-scripts` / `allow-forms` interactions.  
   - Browser matrix: Chromium third-party cookie phaseout vs Firefox/Safari; document profile used.

7. **Impact chains**  
   - Framed UI already embeds CSRF token → classic anti-CSRF may not block the click.  
   - OAuth/OIDC consent or account-link screens → detail with `oauth-oidc-misconfiguration` when protocol is the core issue.  
   - XSS inside framed origin is script-as-target (`xss-cross-site-scripting`), not pure redress.  
   - PostMessage from framed app → `postmessage-security` if messaging is the sink.

8. **Remediation and retest**  
   Prefer CSP `frame-ancestors 'none'` or explicit allowlist; keep XFO as defense-in-depth. High-risk actions: re-auth, WebAuthn, or interaction that cannot be satisfied by one opaque click. Frame-busting JS is **not** sufficient alone. Implementation review → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Baseline framing / intro clickjack | `clickjacking` (primary for simple cases) |
| Cross-site state change without UI alignment | `csrf-cross-site-request-forgery` |
| Cross-origin data read | `cors-cross-origin-misconfiguration` |
| OAuth consent / redirect_uri framed | `oauth-oidc-misconfiguration` |
| XSS in framed document | `xss-cross-site-scripting` |
| postMessage from frame | `postmessage-security` |
| Secure CSP/header implementation | `code-quality-standards` |

## Checklist

- [ ] Authorization and approved PoC hosting confirmed
- [ ] Sensitive URL, action, and cookie/SameSite context documented
- [ ] Framing headers on the **UI document** (XFO + `frame-ancestors`)
- [ ] Browser/version and third-party cookie / CHIPS notes
- [ ] Working PoC: single- and/or multi-step with alignment notes
- [ ] Drag-drop or nested-frame variants tested if relevant
- [ ] State-change evidence on test account (redacted)
- [ ] Paths that still frame vs blocked; SPA/CDN edge cases
- [ ] Impact class and any CSRF/OAuth/XSS chain labeled correctly
- [ ] Remediation: `frame-ancestors`, optional XFO, re-auth for high risk; no reliance on frame-busters alone

## Rules

- Header absence is a finding only with a **sensitive**, realistic framed action under engagement rules.
- Document actual browser cookie and framing behavior — do not claim universal modern-browser immunity.
- Prefer one solid authenticated multi-step proof over many low-value public-page frames.
- Never host PoCs that auto-attack arbitrary visitors outside the authorized cohort.
- Keep bait professional; follow program social-engineering limits.
- Client-side frame-busters are historically bypassable; server CSP/XFO are the controls under test.

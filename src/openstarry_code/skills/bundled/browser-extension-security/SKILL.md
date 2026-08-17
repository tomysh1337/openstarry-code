---
name: browser-extension-security
description: >
  Authorized browser extension security review: manifest permissions, content
  scripts, background/service workers, messaging, web_accessible_resources,
  update and store packaging risks. Use when assessing Chrome/Firefox/Edge
  extensions you own or are scoped to review, MV2/MV3 manifests, or extension
  XSS and privilege-escalation patterns in lab or engagement work.
---

# Browser Extension Security (Authorized)

## Use When

- Reviewing **Chrome, Edge, Firefox, or Chromium** extensions (Manifest V2 or V3).
- Manifest requests broad host access, sensitive APIs, or remote code surfaces.
- Content scripts inject into web pages; DOM XSS or page→extension bridge risks matter.
- Messaging (`runtime` / `tabs` / external) may accept untrusted origins or data.
- Store package, update URL, or CI-built extension zip needs a security pass.
- Not primary for pure website XSS without an extension — use `xss-cross-site-scripting`.
- Not primary for desktop Electron shells — use `electron-app-security`.

## Scope And Authorization

- **In scope:** Extensions you own, org-internal tools, staging builds, CTF/lab packs, and targets with **written** assessment authorization.
- **Out of scope:** Unauthorized store scraping, mass-install malware research against third parties, or weaponizing extensions against real users outside test accounts.
- Prefer **local unpacked** or lab builds; do not ship drive-by malicious extensions to public stores.
- Treat extension storage, cookies, and tokens as sensitive — redact in reports (`secrets-management-hygiene`).
- Keep originals immutable; store notes, unpacked diffs, and PoCs separately.
- Prove issues with **minimal** canaries (unique console markers, test-account state), not credential theft against production users.

## Workflow

### 1. Inventory package and trust boundary

1. Unpack the extension (`.crx` / `.xpi` / zip / source). Record version, id, update URL.
2. Read `manifest.json` (or `.json` + browser-specific keys). Note MV2 vs MV3.
3. List entry points: background/service worker, content scripts, popup/options/side panel, devtools pages, sandboxed pages.
4. Draw trust zones: **web page** → content script → extension process → native messaging / network.

### 2. Manifest permission review

| Area | What to check |
| --- | --- |
| `permissions` / `optional_permissions` | Least privilege; avoid unused `tabs`, `webRequest`, `cookies`, `debugger`, `nativeMessaging`, `proxy` |
| `host_permissions` / `matches` | Prefer exact origins over `<all_urls>` / `*://*/*` |
| `content_scripts` | Matches too broad; `run_at`, `all_frames`, `world` (isolated vs main) |
| `web_accessible_resources` | Over-exposure of scripts/HTML to any site (extension XSS / fingerprint gadgets) |
| `externally_connectable` | Who may `runtime.connect` / `sendMessage` from the web |
| `content_security_policy` | Extension pages CSP; remote script / `unsafe-eval` on extension origins |
| `update_url` / store metadata | Unexpected update endpoints; side-loaded update trust |
| MV3 `host_permissions` + activeTab | Prefer user-gesture scoped access over permanent broad hosts |

Flag **permission→API** pairs that enable data exfil (cookies + broad hosts, `webRequest` + logging, clipboard, history).

### 3. Content script and DOM XSS

1. Trace untrusted data: page DOM, `postMessage`, URL/query, `storage`, network responses rendered into extension UI.
2. Search sinks: `innerHTML`, `document.write`, `insertAdjacentHTML`, jQuery `.html()`, `eval`, dynamic `script` injection, `setTimeout(string)`.
3. Page-controlled input into extension chrome UI is often **high impact** (extension origin privilege).
4. For DOM/HTML proof methodology and context encoding, follow `xss-cross-site-scripting`.
5. Check whether content scripts run in the **page world** (can be patched by page JS) vs isolated world.

### 4. Messaging and external entry

1. Enumerate `runtime.onMessage`, `onMessageExternal`, `onConnect`, `onConnectExternal`, ports to native hosts.
2. Require **sender** validation: `sender.id`, `sender.url` / origin allowlists, and message schema — fail closed.
3. Reject privileged actions (cookie read, arbitrary fetch as extension, eval, navigate all tabs) from unauthenticated external messages.
4. Treat message bodies as untrusted sources into sinks (XSS, open navigation, SSRF-like extension fetches).
5. Review long-lived ports and broadcast patterns that leak tokens to any listener.

### 5. Network, storage, and secrets

1. Find API keys, OAuth client secrets, or tokens in source, `_locales`, or remote config — route remediation to `secrets-management-hygiene`.
2. Prefer backend-held secrets; never ship long-lived privileged keys in the extension package.
3. Review `storage.local` / `sync` / `session` for tokens without encryption expectations; note multi-profile and backup exposure.
4. Check TLS to first-party APIs; pin only with a maintained strategy (document breakage risk).
5. Remote-hosted code (`script` tags, eval of fetched strings, dynamic import from CDN) is a **supply-chain and policy** red flag — especially under store rules.

### 6. Update, build, and supply chain

1. Verify build reproducibility: lockfiles, CI signing, who can push store releases.
2. Scan package for unexpected binaries, minified remote loaders, or hidden content scripts.
3. Review dependency XSS in popup/options React/Vue apps with `code-quality-standards` + XSS skill.
4. Confirm uninstall/data deletion expectations and enterprise policy force-install scope if relevant.

### 7. Remediation verification

1. Reduce host and API permissions; use `optional_permissions` / `activeTab` where product allows.
2. Tighten `web_accessible_resources` and `externally_connectable` allowlists.
3. Encode/sanitize all untrusted data in extension pages; avoid HTML sinks.
4. Validate every external message; least-privilege handlers.
5. Remove secrets from package; rotate any that shipped (`secrets-management-hygiene`).
6. Retest PoCs on the fixed build; add regression tests where practical (`code-quality-standards`).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Extension security review (this surface) | **This skill** | — |
| DOM/HTML/script injection in pages or extension UI | `xss-cross-site-scripting` | this skill for privilege context |
| Keys/tokens in package, storage, or remote config | `secrets-management-hygiene` | this skill for extension paths |
| Implementation fixes, tests, safe messaging code | `code-quality-standards` | **always** on code changes |
| Electron / `BrowserWindow` desktop shell | `electron-app-security` | — |
| Pure website postMessage without extension | `postmessage-security` | — |
| CSP on web app (not extension page) | `content-security-policy-bypass` | XSS skill |

### Routing notes (required helpers)

- **`xss-cross-site-scripting`:** source→sink proofs, context encoding, CSP notes for injected UI.
- **`code-quality-standards`:** baseline when fixing handlers, UI, and build scripts.
- **`secrets-management-hygiene`:** lifecycle for keys found in manifests, bundles, or storage.

## Checklist

- [ ] Manifest version, id, update path, and entry points documented
- [ ] Permissions and host access justified or flagged as over-broad
- [ ] Content script matches, world isolation, and DOM sinks reviewed
- [ ] `web_accessible_resources` / `externally_connectable` minimized
- [ ] Messaging handlers validate sender and schema; no privileged external RPC
- [ ] XSS paths proven or closed with context-correct encoding (`xss-cross-site-scripting`)
- [ ] No long-lived secrets in package; rotation if leaked (`secrets-management-hygiene`)
- [ ] Storage and cookie access least privilege; redacted evidence
- [ ] No remote code eval / unexpected dynamic script load
- [ ] Fixes meet `code-quality-standards`; PoCs retested on new build
- [ ] Authorization and browser versions recorded; residual risk listed

## Rules

- Authorized extensions and test accounts only — no drive-by store malware.
- Extension-origin XSS is not “just XSS”; document elevated API impact honestly.
- Minimal canary proofs beat full session-stealing writeups against real users.
- Do not claim “critical” from unused permissions alone — tie to a reachable abuse path when possible.
- Redact tokens, cookie values, and PII from all artifacts.
- Prefer least privilege and explicit origin allowlists in every remediation.

---
name: cordova-webview-risks
description: >
  Authorized Cordova/PhoneGap hybrid app security review: config.xml navigation
  allowlists, file:// origin and content access, JS↔native bridge injection,
  and outdated/vulnerable plugins. Use when assessing Cordova, PhoneGap, Ionic
  Cordova, or cordova-android/ios WebView shells you own or are scoped to harden
  — not unauthorized third-party store apps.
---

# Cordova / PhoneGap WebView Risks (Authorized)

Assess **Cordova/PhoneGap** hybrid shells: `config.xml` policy, `file://` origin,
plugin bridges, and stale stacks that turn XSS into native privilege.

## When To Use

- App is **Cordova, PhoneGap, Ionic (Cordova)**, or embeds `cordova.js` / plugins.
- Reviewing `config.xml` for navigation, intent, cleartext, and content `src`.
- Hybrid UI loads remote HTML/JS or deep-linked URLs into the Cordova WebView.
- Concern is **bridge injection** (XSS or attacker page → `cordova.exec` / plugins).
- Plugins are old, unmaintained, or grant broad file/camera/geo/intent power.
- Not primary for pure native Android `WebView` — use `android-webview-security`.
- Not primary for Capacitor-only unless a Cordova compatibility layer is present.

## Scope And Authorization

- **In scope:** owned apps, org hybrid clients, staging/debug builds, CTF/lab
  APKs/IPAs, targets under **written** authorization.
- **Out of scope:** unauthorized store apps, mass malware packaging, phishing real
  users, or production fleets without SOW.
- Record app id, Cordova/platform versions, plugins, build hash. Keep originals
  immutable; store decompile trees and PoCs under `derived/`.
- Attacker HTML, deep links, and bridge canaries only on **lab** devices and
  approved origins. Redact tokens, cookies, device ids, and PII.
- Gate Frida / remote WebView debug on ownership and engagement rules.

## Workflow

### 1. Confirm Cordova surface and inventory

1. Unpack APK/IPA or use source. Confirm `cordova.js`, `cordova_plugins.js`, `www/`,
   and platform packages (`cordova-android`, `cordova-ios`).
2. Read **`config.xml`** (and platform overrides): `id`, content `src`, preferences,
   feature/plugin entries, hooks.
3. List plugins from `package.json` / `plugins/` / `cordova_plugins.js` with versions.
4. Trust zones: **remote or XSS page** → WebView JS → `cordova.exec` → native plugin
   → OS (files, intents, sensors, network).

### 2. Navigation and scheme policy

| Control | What to check |
| --- | --- |
| `<allow-navigation href>` | Over-broad `*` / `http://*` / extra hosts — attacker pages keep the bridge |
| `<allow-intent href>` | Open `tel:`, `sms:`, `geo:`, custom schemes, or `*` without need |
| `<access origin>` | Legacy network whitelist; still document on old platforms |
| Content `src` | Remote `https://` start vs local `index.html`; hybrid cold-start risk |
| Deep links / custom schemes | Attacker query into WebView navigation or JS |

Fail closed: allowlist exact `https://` app origins only. Open navigation plus live
plugins is an **XSS→native** enabler.

### 3. `file://`, local origin, and content access

1. Default Cordova UI often runs from **`file://`** (or app-local origin). XSS in
   local HTML is same-origin with the shell — high impact.
2. Check prefs/native flags that widen file/content access (hand deep Android flag
   analysis to `android-webview-security`): file access, file-from-file, universal
   access from file URLs, `content://` via plugins.
3. Remote pages must not inherit unrestricted `file://` reads; verify InAppBrowser
   vs main WebView. User paths into File/File-Transfer plugins are arbitrary-read
   candidates (`path-traversal-lfi` / `file-access-vuln` when relevant).

### 4. Bridge injection and plugin surface

1. Enumerate `cordova.exec` services and plugin APIs visible to page JS.
2. Any script in the Cordova WebView (XSS, open nav, bad CDN, debug console) can call
   plugins — no separate browser-vs-native barrier unless you isolate (InAppBrowser
   without bridge, or strict navigation allowlist).
3. High-risk plugins: filesystem R/W, contacts, SMS, clipboard, camera roll, geo,
   intent/URL launchers, raw SQLite, bridges that return tokens to JS.
4. Custom plugins: validate args; block intent/command/SQL/path sinks; prefer
   capability-limited APIs.
5. Page sink methodology: `xss-cross-site-scripting`.

### 5. Outdated plugins and platform stack

1. Compare Cordova platforms, WebView engine, and each plugin to maintained releases
   and known advisories.
2. Flag abandoned plugins, mis-set whitelist prefs on old majors, deprecated
   File-Transfer, and stacks that predate modern WebView defaults.
3. Rebuild on supported Cordova/platform; remove unused plugins; pin versions in CI.
4. Secrets in `www/`, prefs, or plugin config → `secrets-management-hygiene`.

### 6. Lab proof and remediation

1. Lab-only canary JS (remote debug or controlled XSS) calling a sensitive plugin;
   demonstrate navigation escape if `allow-navigation` is wildcarded.
2. Remediate: tighten `allow-navigation` / `allow-intent`; fixed local or HTTPS start
   URL; drop unused plugins; validate plugin args natively; load untrusted remote
   content in **InAppBrowser** (or system browser) **without** bridge.
3. Harden Android WebView engine settings via `android-webview-security`.
4. Fixes/tests: `code-quality-standards`. Retest on a fresh signed build.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Cordova config, plugins, bridge, allow-navigation | **This skill** | — |
| Android WebView flags, `addJavascriptInterface`, SSL handlers | `android-webview-security` | this skill for Cordova layer |
| Exports / deep links into hybrid UI | `android-exported-components` | this skill |
| Full Android lab methodology | `android-pentesting-tricks` | this skill |
| Page DOM XSS detail | `xss-cross-site-scripting` | this skill for native impact |
| Secrets in www/config/plugins | `secrets-management-hygiene` | this skill |
| Custom plugin code and CI pins | `code-quality-standards` | **always** on fixes |

### Required hand-offs

- **`android-webview-security`:** native WebView settings, non-Cordova JS bridges,
  `file://` universal-access flags, mixed content, `onReceivedSslError`.
- **`android-pentesting-tricks`:** APK acquire, device baseline, broader mobile flow.
- **`code-quality-standards`:** plugin hardening, validation, regression tests.

## Output Checklist

- [ ] Scope, app id, Cordova/platform versions, plugins, build hash
- [ ] `config.xml`: content src, `allow-navigation`, `allow-intent`, access origins
- [ ] `file://` / start-URL model and remote content boundaries documented
- [ ] Plugin bridge surface listed; high-risk native capabilities flagged
- [ ] Outdated plugins/platform called out with upgrade path
- [ ] Lab PoC (nav and/or bridge canary) on owned device; evidence redacted
- [ ] Hand-off notes for `android-webview-security` (flags/SSL)
- [ ] Remediation: allowlists, plugin removal, InAppBrowser isolation, pins
- [ ] Fixes follow `code-quality-standards`; residual risk stated

## Rules

- Owned/authorized hybrid apps and lab devices only. Severity needs a **reachable**
  path (open nav, XSS, or untrusted content + plugin), not “Cordova present” alone.
  Minimal canaries; no real-user exfil; redact secrets/PII; prefer allowlists.

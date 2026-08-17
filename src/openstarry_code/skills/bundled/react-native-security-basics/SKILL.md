---
name: react-native-security-basics
description: >
  Authorized React Native mobile app security basics: expo-secure-store /
  react-native-keychain storage, certificate pinning notes, deep-link and
  universal-link handling, JS bundle tampering awareness, and WebView risks.
  Use when hardening or reviewing owned RN / Expo apps, lab builds, or CTF
  targets — not for unauthorized third-party App Store apps.
---

# React Native Security Basics (Authorized)

Assess **React Native (RN) / Expo** client security on apps you own or are
explicitly authorized to test. Cover secret storage, TLS pinning intent,
deep links, JS bundle integrity awareness, and hybrid WebView surfaces.

## When To Use

- Reviewing **React Native** or **Expo** apps (iOS/Android) for storage, links, TLS posture, WebViews.
- Tokens/credentials may live in AsyncStorage, SecureStore, Keychain/Keystore wrappers, or MMKV.
- Custom schemes, App Links, or Universal Links feed navigation or auth.
- Release/debug JS bundles (`index.android.bundle`, Hermes bytecode, Metro) may embed secrets or be swapped.
- `react-native-webview` or platform WebViews bridge JS to native capabilities.
- Pinning libraries (`react-native-ssl-pinning`, TrustKit/OkHttp pins, custom fetch) need a **design note** — bypass belongs elsewhere.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SSL pin **bypass** / traffic intercept (authorized only) | `mobile-ssl-pinning-bypass` (after `tls-plaintext-acquisition`) |
| Broader Android export / Intent surface | `android-exported-components`, `android-pentesting-tricks` |
| Native Android WebView bridges only | `android-webview-security` |
| iOS Keychain attribute deep-dive | `ios-keychain-hygiene` |
| Org vault / server secret lifecycle | `secrets-management-hygiene` |
| Implementation quality of fixes | `code-quality-standards` |

## Scope And Authorization

- **In scope:** owned RN/Expo apps, enterprise/lab builds, CTF targets, written mobile assessments.
- **Out of scope:** unauthorized third-party apps; shipping malware; attacking users or stores outside SOW.
- Prefer debug/staging builds, lab devices, and test accounts. Keep production signing keys out of tickets.
- Record platform, OS version, app id/version, RN/Expo version, Hermes on/off, and build type (debug/release).
- Redact tokens, cookies, device IDs, and PII from logs, screenshots, and bundle excerpts.
- Gate Frida, repackaging, pin bypass, and live intercept behind clear **ownership or written authorization**.
- Hand active pinning bypass exclusively to `mobile-ssl-pinning-bypass` (authorized only).

## Workflow

### 1. Map app model and trust zones

1. Identify RN version, Expo vs bare, Hermes, and native modules from `package.json` / lockfile / native projects.
2. List auth entry points: login, refresh, biometric unlock, deep-link callbacks, WebView SSO.
3. Trust zones: **remote content / deep-link params** → JS → native modules → OS Keychain/Keystore / network.
4. Inventory third-party SDKs that hold tokens or open WebViews.

### 2. Secret storage (SecureStore / Keychain / Keystore)

1. Prefer **hardware-backed** stores: `expo-secure-store`, `react-native-keychain`, or platform Keychain/Keystore — not AsyncStorage, MMKV, or plain files for long-lived tokens.
2. Check accessibility / when-unlocked policies (iOS Keychain classes; Android Keystore auth-bound keys when product requires biometrics).
3. Flag secrets in JS source, `.env` baked into bundles, remote config without integrity, or debug logs (`console.log` of tokens).
4. Session design: short access tokens; refresh in SecureStore/Keychain; clear on logout; no tokens in deep-link query strings that hit logs/history.
5. Pair storage policy detail with `ios-keychain-hygiene` / platform skills when native flags matter; use `secrets-management-hygiene` for org rotation.

### 3. Certificate pinning notes (design, not bypass)

1. Document **whether** the app pins (custom native module, OkHttp `CertificatePinner`, TrustKit, `react-native-ssl-pinning`, Expo config plugins).
2. Prefer SPKI/public-key pins with **backup pins** and a rotation runbook; pure leaf-cert pins break on renewals.
3. Note debug builds that disable pins vs release — avoid shipping pin-off flags in production.
4. Pinning is **defense-in-depth**, not a substitute for secure storage or auth design.
5. For authorized MITM/plaintext capture when pins block testing: route to `tls-plaintext-acquisition` → **`mobile-ssl-pinning-bypass` only when authorized**.

### 4. Deep links and app links

1. Inventory schemes (`myapp://`), Android App Links, iOS Universal Links, and associated domains / assetlinks.
2. Treat all deep-link path/query/body as **untrusted input** — validate before navigation, token exchange, or payment actions.
3. Auth callbacks: prefer one-time codes / PKCE over long-lived tokens in URLs; strip fragments from logs.
4. Reject open redirects into WebViews or in-app browsers with attacker-controlled hosts.
5. On Android, relate exported Activities/intent filters to `android-exported-components` when the entry is native.

### 5. JS bundle tampering awareness

1. Release clients are reverse-engineerable: assume attackers read Hermes/Metro bundles and native bridges.
2. Never rely on “obscure JS” for license or auth; enforce authorization on the **server**.
3. Awareness checks (owned builds): unsigned/debug bundles, sideload of modified APK/IPA, missing Play Integrity / App Attest where product requires it.
4. Integrity APIs raise the bar; they do not stop determined lab reverse engineering — report residual risk honestly.
5. Hunt hardcoded API keys and private endpoints in bundles; rotate anything found (`secrets-management-hygiene`).

### 6. WebView risks (RN)

1. Audit `react-native-webview` (and native WebViews): `originWhitelist`, `onShouldStartLoadWithRequest`, JS enabled, file access, mixed content.
2. `injectedJavaScript` / message bridges (`onMessage` / `postMessage`): treat page JS as untrusted; never expose raw native token dumps or file APIs without allowlists.
3. Do not load untrusted HTTP/HTML with privileged bridges; prefer system browser / Custom Tabs / SFSafariViewController for third-party IdPs when bridges are unnecessary.
4. For pure Android WebView settings/bridges, deepen with `android-webview-security`; XSS class detail → `xss-cross-site-scripting`.
5. Remediate with least privilege, HTTPS allowlists, and tests under `code-quality-standards`.

### 7. Remediation and verify

1. Move secrets to SecureStore/Keychain; remove bundle-embedded credentials; fix deep-link validation.
2. Document pin inventory and rotation; enable pins only with backup keys and monitoring.
3. Harden WebView navigation and bridges; retest deep-link and WebView canaries on **lab** builds.
4. Re-scan release artifacts for leaked secrets; apply `code-quality-standards` to native modules and TS/JS fixes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| RN/Expo storage, deep links, bundle awareness, WebView basics | **This skill** | — |
| Authorized SSL pin bypass / HTTPS MITM | `mobile-ssl-pinning-bypass` | `tls-plaintext-acquisition` first |
| Android exported components / Intent filters | `android-exported-components` | this skill for RN navigation |
| Android WebView bridge deep-dive | `android-webview-security` | this skill for RN wrapper |
| iOS Keychain accessibility / ACL flags | `ios-keychain-hygiene` | this skill for RN wrappers |
| Client/server secret sprawl and rotation | `secrets-management-hygiene` | this skill for device paths |
| Secure coding of fixes and tests | `code-quality-standards` | **always** on implementation |

### Routing notes

- **`mobile-ssl-pinning-bypass`:** authorized pin defeat only — never as a default “how to break apps” path; this skill stops at pinning **notes**.
- **`tls-plaintext-acquisition`:** choose how to obtain plaintext before tool-specific bypass.
- **`code-quality-standards`:** baseline for SecureStore helpers, link parsers, WebView props, and tests.
- **`android-webview-security` / platform pentest skills:** when findings leave the RN layer into native OS surfaces.

## Output Checklist

- [ ] Authorization, app id/version, RN/Expo/Hermes, platform/OS, build type recorded
- [ ] Secret map: SecureStore/Keychain vs AsyncStorage/files/logs/bundle
- [ ] Pinning inventory and rotation notes (no unauthorized bypass steps in report body)
- [ ] Deep-link schemes/App Links/Universal Links validated as untrusted input
- [ ] Bundle/secret leakage reviewed; server-side auth not assumed client-only
- [ ] WebView whitelist, JS bridge, and navigation risks assessed
- [ ] Findings state attacker model (stock device vs lab root/repack)
- [ ] Evidence redacted; hand-offs listed (`mobile-ssl-pinning-bypass` only if authorized)
- [ ] Remediation + retest notes; code changes follow `code-quality-standards`

---
name: flutter-security-basics
description: >
  Authorized Flutter app security basics: flutter_secure_storage and secret
  placement, MethodChannel/EventChannel trust boundaries, Dart obfuscation
  limits, deep-link / App Links validation, and certificate-pinning packages.
  Use when reviewing or hardening owned Flutter (Android/iOS/desktop) clients,
  lab builds, or CTF APKs/IPAs — not unauthorized third-party mobile apps.
---

# Flutter Security Basics (Authorized)

Assess **Flutter client security** for owned or authorized apps: secret placement,
platform-channel trust, obfuscation limits, deep links, and TLS pinning packages.

## When To Use

- Flutter client stores tokens/API keys/PII; uses `flutter_secure_storage`, prefs, Hive, SQLite, or files
- Custom `MethodChannel` / `EventChannel` / `BasicMessageChannel` bridges
- Release builds rely on `--obfuscate` / `--split-debug-info` for “security”
- Deep links, App Links, Universal Links, or `go_router` / `uni_links` / `app_links` handle untrusted URLs
- Pinning via `SecurityContext`, custom `HttpClient`, or certificate-pinning packages
- Hardening checklist before store release for an **owned** product

| Need instead | Skill |
| --- | --- |
| Full Android / iOS methodology | `android-pentesting-tricks` / `ios-pentesting-tricks` |
| Keychain attribute deep-dive | `ios-keychain-hygiene` |
| Authorized pin bypass / TLS plaintext | `mobile-ssl-pinning-bypass`, `tls-plaintext-acquisition` |
| Export / intent-filter inventory | `android-exported-components` |
| Android WebView JS bridges | `android-webview-security` |
| Vault / secret lifecycle; code quality | `secrets-management-hygiene`; `code-quality-standards` |

## Scope And Authorization

- **In scope:** owned Flutter apps, org clients, staging builds, labs, CTF packages under written RoE.
- **Out of scope:** unauthorized third-party store apps; malware; real-user devices/accounts outside agreed tests.
- Prefer source + lab builds. Keep signing keys and customer tokens out of tickets (`secrets-management-hygiene`).
- Dynamic work (Frida, proxies, deep-link injection) only on owned devices/emulators and approved package names.
- Redact tokens, device IDs, Keystore/Keychain values, PII. Record Flutter/Dart SDK, package/bundle ID, flavor, OS version.
- State **stock device** vs **rooted/jailbroken lab** per finding — Dart is never a server trust boundary.

## Workflow

### 1. Inventory Flutter surface

1. Read `pubspec.yaml` for HTTP, storage, auth, deep-link, and pinning packages.
2. Map `main.dart`, flavors, channel names, native `MainActivity` / `AppDelegate` plugins.
3. Note `--obfuscate`, `--split-debug-info`, Android R8, iOS strip as applicable.
4. List clients (`http`, `dio`, `HttpClient`) and whether pinning is configured.

### 2. Secure storage and secret placement

| Store | Security note |
| --- | --- |
| `flutter_secure_storage` | Keystore/Keychain-backed; review platform options/accessibility |
| `shared_preferences` | Flags only — **not** refresh tokens or passwords |
| Hive / SQLite / files | No hard-coded encryption keys in Dart |
| Assets / source constants | Extractable; treat API keys as public |

1. Sessions → secure storage (or short-lived memory + OS store), not prefs/logs.
2. Secrets must not depend on Dart obfuscation alone.
3. Align iOS Keychain accessibility with threat model (`ios-keychain-hygiene`).
4. No tokens in `debugPrint`/crash reporters; vault rotation → `secrets-management-hygiene`.

### 3. Platform channel trust

Treat channels as **IPC with an untrusted peer**:

1. Enumerate channel names/methods and who initiates (Dart vs native).
2. Never authorize only in Dart — sensitive actions need **server-side** checks.
3. Native handlers: validate types/ranges; allowlist paths/URLs/SQL; no privileged concat from Dart strings.
4. Do not return Keystore material, cookies, or PII to release debug UI.
5. Third-party plugins with broad FS/intent access get the same review; use `code-quality-standards` for handlers.

### 4. Obfuscation limits

- `--obfuscate --split-debug-info=…` renames symbols; **not** encryption; does not stop RE, Frida, or traffic analysis.
- Keep symbol maps offline for crashes; never ship maps in the bundle.
- Pair with server authz, pinning (defense-in-depth), secure storage — do not claim “cannot be reverse engineered.”
- R8/iOS strip are separate native layers; report residual risk honestly.

### 5. Deep links and navigation

1. Inventory Android intent-filters/App Links and iOS associated domains/custom schemes.
2. Trace `app_links` / `uni_links` / `go_router`: path/query/fragment are attacker-controlled when exported or user-visible.
3. Reject open redirects, arbitrary `http` WebView loads, and unbound token-in-query login links.
4. OAuth/reset/pay links need server `state`/one-time binding — not client route match alone.
5. Exported activities forwarding URIs → `android-exported-components`.

### 6. Certificate pinning packages

1. Prefer SPKI/public-key pins with rotation/backup pins over brittle leaf-only pins.
2. **All** API stacks must pin (`dio`, `HttpClient`, SDK-owned clients often bypass app pins).
3. Proxy overrides only via compile-time/flavor flags — never a release “disable pin” switch.
4. Authorized intercept: `tls-plaintext-acquisition` → `mobile-ssl-pinning-bypass` (Flutter/BoringSSL).
5. Pinning is defense-in-depth, not a substitute for authn/authz.

### 7. Remediate and verify

Move secrets to secure storage; harden channels and deep-link allowlists; add malicious-URI tests; document obfuscation as friction only; retest release lab builds; list residual risk (root, plugin SDKs).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Flutter storage / channels / obfuscation / deep links / pin packages | **This skill** | — |
| Broad Android or iOS lab methodology | `android-pentesting-tricks` / `ios-pentesting-tricks` | this skill; `ios-keychain-hygiene` |
| Export / intent-filter inventory | `android-exported-components` | this skill for Flutter routes |
| HTTPS plaintext / pin bypass (authorized) | `tls-plaintext-acquisition` → `mobile-ssl-pinning-bypass` | this skill for package config |
| Secrets lifecycle; implementation fixes | `secrets-management-hygiene`; `code-quality-standards` | this skill for on-device placement |

**Helpers:** `code-quality-standards` (handlers/tests); `secrets-management-hygiene` (keys/rotation); pin/TLS skills for intercept; platform pentest skills beyond the Flutter layer.

## Output Checklist

- [ ] Authorization, package/bundle ID, Flutter/Dart version, platform, flavor recorded
- [ ] Storage map: each secret → store; no tokens in prefs/assets/logs
- [ ] `flutter_secure_storage` (or equivalent) options reviewed per platform
- [ ] Platform channels inventoried; native validation; least data returned
- [ ] Obfuscation flags noted; symbol maps not shipped; limits stated
- [ ] Deep links/schemes: allowlist, token handling, no open redirect into WebView
- [ ] Pinning covers all HTTP clients; backup/rotation; no release kill-switch
- [ ] Attacker model (stock vs lab-root); redacted evidence; residual risk listed
- [ ] Fixes via `code-quality-standards`; exposed secrets rotated (`secrets-management-hygiene`)

## Rules

- Owned, lab, CTF, or written-authorization targets only.
- Do not equate Dart obfuscation or client checks with server security.
- Prefer code/config evidence; retest release-mode lab builds; redact identifiers.

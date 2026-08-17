---
name: android-exported-components
description: >
  Authorized Android exported-component security review: Activities, Services,
  BroadcastReceivers, ContentProviders, deep links, and intent-filter surface.
  Use when assessing android:exported, unprotected IPC, path permissions, or
  privilege escalation via exported components on owned apps, labs, or CTF APKs.
---

# Android Exported Components Security Review

Review **exported Android components** and IPC for apps you own or are
explicitly authorized to test. Focus on export flags, intent filters,
permission guards, and untrusted intent/URI impact.

## Scope And Authorization

- **In scope:** owned apps, written assessments, labs, CTF APKs, lab devices.
- **Out of scope:** unauthorized third-party apps; mass Play scanning; other
  users’ accounts or device fleets.
- Record package, versionCode/versionName, targetSdk, APK hash. Invoke
  components only on **lab installs**. Redact tokens, cookies, device IDs, PII.

## Use When

- `android:exported="true"` or implicit export via `intent-filter`
- Component attack-surface table (Activity / Service / Receiver / Provider)
- Deep links / App Links reach privileged UI or skip auth
- ContentProviders lack permissions or weak path rules
- Unprotected receivers/services accept crafted extras (leak/bypass/privesc)

| Need instead | Skill |
| --- | --- |
| Full Android methodology (storage, Frida, patch) | `android-pentesting-tricks` |
| WebView JS bridge / file:// | `android-webview-security` |
| SSL pinning bypass only | `mobile-ssl-pinning-bypass` |

## Workflow

### 1. Acquire and decode

```bash
adb shell pm path com.example.app
adb pull /data/app/.../base.apk derived/base.apk
jadx -d derived/jadx derived/base.apk
apktool d derived/base.apk -o derived/apktool
```

### 2. Inventory export surface

Per component: class, `exported`, permissions, intent-filters (actions, schemes,
hosts, paths), `grantUriPermissions` / `path-permission`, launchMode notes.

```bash
rg -n 'android:exported|intent-filter|android:permission|path-permission|grantUriPermissions|android:authorities' derived/apktool/AndroidManifest.xml
```

targetSdk 31+ needs explicit `exported`; still review all `true` and custom
permission `protectionLevel` (`normal`/`dangerous` often weak vs `signature`).

### 3. Protection and static handlers

| Guard | Strength |
| --- | --- |
| No permission + exported | High — any app can send intents |
| Custom `normal` / `dangerous` | Weak if attacker app can request |
| `signature` / `signatureOrSystem` | Stronger if key not shared |

- **Activities:** extras, URI/query, auth skip via deep link.
- **Services:** start/bind without caller checks.
- **Receivers:** implicit actions, sticky data.
- **Providers:** SQL concat, `openFile` traversal, `UriMatcher` gaps.

```bash
rg -n 'getIntent\(|getStringExtra|getData\(|openFile|rawQuery' derived/jadx
```

### 4. Dynamic lab invocation

```bash
adb shell am start -n com.example.app/.ExportedActivity --es token 'lab-canary'
adb shell am start -a android.intent.action.VIEW -d 'myapp://path?id=1'
adb shell am startservice -n com.example.app/.ExportedService --es cmd dump
adb shell am broadcast -a com.example.app.ACTION --es extra value
adb shell content query --uri content://com.example.app.provider/table
adb logcat | rg -i 'com.example.app|SecurityException|AndroidRuntime'
```

Vary missing extras, type confusion, path traversal, login-gated actions.
Use canaries, not real secrets.

### 5. Impact and remediation

| Outcome | Class |
| --- | --- |
| Read tokens/PII via provider/activity | Confidentiality |
| Bypass login via deep link | AuthZ / session |
| Privileged service action or provider write | Integrity |

Remediate: `exported="false"` when unused; `signature` perms for sensitive IPC;
validate extras/URIs; safe SQL/`openFile`; auth before deep-link privileged UI.
Retest after changes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Exported components, deep links, provider IPC | **This skill** | — |
| Full APK surface, storage, Frida, resign | `android-pentesting-tricks` | this skill |
| WebView after export launches it | `android-webview-security` | this skill |
| Pinning blocks post-component API traffic | `mobile-ssl-pinning-bypass` | android-pentesting |
| Ship fixes/tests for handlers/manifest | `code-quality-standards` | this skill |

### Required helpers (when applicable)

- **`android-pentesting-tricks`:** APK acquire, lab baseline, storage, broader workflow.
- **`mobile-ssl-pinning-bypass`:** impact proof needs lab HTTPS despite pins.
- **`code-quality-standards`:** remediations and regression tests.

## Checklist

- [ ] Scope, package/version/APK hash recorded
- [ ] Inventory: exported, permissions, intent-filters, deep links
- [ ] Custom permission protectionLevel reviewed
- [ ] Handlers: untrusted extras/URI; provider SQL/`openFile`
- [ ] Lab `am`/`content` repros with redacted evidence
- [ ] Impact model: any-app IPC vs deep-link vs signature suite
- [ ] Remediation + retest; hand-off WebView / pinning / CQS

## Rules

- Owned/authorized apps and labs only.
- Evidence over speculation; do not rate root-only reads as remote export bugs.
- Keep originals immutable; derived apktool/jadx separate.
---

# Note

Owns **exported-component / IPC** review. Pair with `android-pentesting-tricks`,
`android-webview-security`, `mobile-ssl-pinning-bypass`, `code-quality-standards`.

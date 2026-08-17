---
name: ios-keychain-hygiene
description: >
  Authorized iOS Keychain access-control assessment: SecItem attributes,
  kSecAttrAccessible classes, access-control flags (biometry, device passcode,
  ThisDeviceOnly), access groups, and common storage mistakes. Use when reviewing
  how an owned or lab iOS app stores tokens, credentials, or keys in the Keychain —
  not for dumping third-party App Store apps without written permission.
---

# iOS Keychain Hygiene

Assess **how an iOS app stores and protects secrets in the Keychain** on devices
and builds you own or are explicitly authorized to test. Focus on accessibility
classes, access-control constraints, sharing scope, and app-side misuse — not
on claiming “Keychain is broken.”

## Scope And Authorization

- **In scope:** owned apps, enterprise/lab IPAs, deliberately vulnerable iOS labs,
  CTF targets, written mobile assessments that allow Keychain review.
- **Out of scope:** unauthorized Keychain dumps of third-party App Store apps;
  publishing full dumps with live tokens; abusing devices or Apple IDs you do not control.
- Prefer **jailbroken lab devices**, debuggable/enterprise builds, or simulator
  only where Keychain parity is acceptable for the finding class.
- Document device model, iOS version, jailbreak status, `CFBundleIdentifier`, and
  app version. Redact tokens, Keychain values, UDIDs, and PII.
- Distinguish **stock-device attacker** (no jailbreak) vs **lab-root** evidence
  in every finding.

## Use When

- Reviewing `SecItemAdd` / `SecItemUpdate` / `SecItemCopyMatching` usage
- Checking `kSecAttrAccessible*`, `kSecAccessControl`, LocalAuthentication gates
- App stores session/refresh tokens, API keys, certs, or private keys in Keychain
- Entitlements show Keychain access groups that may over-share
- Hardening checklist for “secrets not in UserDefaults/plist”
- Follow-on after broad iOS map in `ios-pentesting-tricks`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full iOS attack surface (static + dynamic) | `ios-pentesting-tricks` |
| TLS pinning / HTTPS intercept | `tls-plaintext-acquisition`, `mobile-ssl-pinning-bypass` |
| Android Keystore / APK integrity | `android-pentesting-tricks`, `apk-signing-and-integrity` |
| Org vault / server secret lifecycle | `secrets-management-hygiene` |
| Implementing storage helpers in code | `code-quality-standards` (+ this skill for Keychain rules) |

## Core Controls

| Control | Secure direction | Weak outcome |
| --- | --- | --- |
| Accessibility | Tightest class that meets UX (prefer `*WhenUnlockedThisDeviceOnly` for high-value secrets) | `kSecAttrAccessibleAlways` / unlock-independent access |
| ThisDeviceOnly | On for credentials that must not restore to another device | Items migrate via backup unexpectedly |
| Access control | `SecAccessControl` with biometry/passcode when policy requires | Readable whenever process can call SecItem |
| Access groups | Least-privilege team/app group entitlements | Over-broad Keychain sharing across apps |
| Sync / iCloud | Explicit decision; avoid for high-sensitivity sessions unless required | Secrets sync to unintended devices |
| App-side store | Keychain + OS ACL over home-rolled “encryption” in plist | Tokens in `NSUserDefaults`, files, logs |

Non-jailbroken: OS isolation is strong. Jailbroken lab dumps prove *storage choice and
flags* — report both and state the realistic attacker model.

## Workflow

### 1. Baseline app and entitlements

Record bundle ID, version, team ID, build type. Inspect Keychain access groups,
app groups, `get-task-allow`. Static-search Keychain APIs and wrappers.

```bash
plutil -p Payload/*.app/Info.plist
codesign -d --entitlements :- Payload/*.app 2>/dev/null
strings Payload/*.app/<Binary> | rg -i 'SecItem|kSecAttr|Keychain|accessGroup|kSecClass'
```

### 2. Map secrets and assess flags

Build a table: purpose → account/service attrs → class → accessibility → access
control → shared group? Sources: source/decompile, Frida/Objection on lab, or
vendor config. Names only in tickets; values only in redacted evidence.

1. Flag `Always` / `AlwaysThisDeviceOnly` for long-lived credentials.
2. Check AfterFirstUnlock is justified (background refresh) vs overused.
3. Verify biometry/passcode for step-up secrets (payments, export keys).
4. Confirm `ThisDeviceOnly` where backup extraction is in the threat model.
5. Note missing `kSecAttrAccessControl` when product claims biometric protection.

### 3. Lab validation (authorized only)

```bash
objection -g com.example.app explore
# ios keychain dump   # redacted output only
```

Hook themes: `SecItemAdd` / `SecItemUpdate` / `SecItemCopyMatching` — log
**attribute dictionaries** (accessibility, access group), not production secret
values in shared chat. Confirm locked-device readability, backup expectations,
and whether a sibling app in the same access group can read.

### 4. Non-Keychain sprawl and remediate

Also check tokens in UserDefaults, plists, SQLite, cookies, pasteboard, logs.
Prefer OS Keychain with least accessibility + ACL; shrink access groups; rotate
any token dumped or logged in cleartext. Re-run static + lab checks. Apply
`code-quality-standards` to wrappers (error handling, no secret logs).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Keychain accessibility / ACL / access-group hygiene | **This skill** | — |
| Broader iOS pentest (IPA, runtime, ATS, components) | `ios-pentesting-tricks` | this skill for Keychain deep-dive |
| Implementing or reviewing Keychain helper code | `code-quality-standards` | this skill for attribute policy |
| Android storage / package testing | `android-pentesting-tricks` | — |
| APK signing / v1–v3 / tamper checks | `apk-signing-and-integrity` | `android-pentesting-tricks` |
| TLS pin blocking traffic | `tls-plaintext-acquisition` → `mobile-ssl-pinning-bypass` | `ios-pentesting-tricks` |

### Required helpers

- **`ios-pentesting-tricks`:** device baseline, IPA acquire, Frida/Objection, non-Keychain storage/network.
- **`code-quality-standards`:** implementation baseline for wrappers, tests, secure logging.
- **`android-pentesting-tricks`:** switch platform when the target is Android (not this skill).

## Checklist

- [ ] Authorization, device, iOS version, jailbreak/sim, bundle ID + version recorded
- [ ] Entitlements: Keychain access groups and app groups inventoried
- [ ] High-value secrets mapped (Keychain vs elsewhere)
- [ ] Accessibility class per item; `Always*` justified or flagged
- [ ] `ThisDeviceOnly` and backup/restore expectations reviewed
- [ ] Access-control (biometry/passcode) matches product claims
- [ ] Access-group sharing least-privilege
- [ ] No long-lived tokens in UserDefaults/files/logs
- [ ] Lab dumps redacted; stock vs jailbreak model stated; exposed secrets rotated
- [ ] Code changes follow `code-quality-standards`; broader iOS via `ios-pentesting-tricks`

## Rules

- Authorized lab/owned apps only; never publish raw Keychain dumps.
- Blame **app attribute choices**, not the Keychain service itself.
- Separate configuration findings from root-only extraction severity.
- Prefer attribute evidence over speculation; rotate before wide discussion of live tokens.

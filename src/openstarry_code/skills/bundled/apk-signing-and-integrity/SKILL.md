---
name: apk-signing-and-integrity
description: >
  Authorized APK signing-scheme and integrity assessment: APK Signature Scheme
  v1/v2/v3/v4, cert lineage, apksigner verification, split/AAB notes, and app-side
  integrity or repack detection patterns. Use when reviewing how an owned or lab
  Android package is signed, re-signed, or self-checks integrity — not for
  distributing pirated or fraudulently re-signed third-party apps.
---

# APK Signing And Integrity

Assess **Android package signing schemes, certificate identity, and integrity
controls** for APKs/AABs you own or are explicitly authorized to test (v1–v4,
apksigner, lab re-sign, app-side anti-tamper) — not piracy or malware re-signing.

## Scope And Authorization

- **In scope:** owned apps, lab/CTF APKs, enterprise builds, written assessments
  that allow package integrity and signing review.
- **Out of scope:** re-signing/redistributing third-party Play apps for fraud;
  unauthorized Play Protect/license bypass; trojanized updates outside scope.
- Prefer **test keystores**. Never reuse production upload keys in chat or CI logs.
- Record package, version, APK/cert SHA-256; redact keystore secrets. Lab re-sign is for authorized instrumentation only.

## Use When

- Verifying which **signature schemes** an APK uses (v1 JAR, v2/v3 whole-file, v4)
- Checking cert identity, debug vs release keys, multiple signers, or rotation lineage
- Preparing or reviewing **re-sign** after apktool/smali patches in a lab
- App implements signature checks, Play Integrity/SafetyNet, or checksum anti-tamper
- Supply-chain questions: “was this artifact signed by our release key?”
- Follow-on after package acquire in `android-pentesting-tricks`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full Android surface (manifest, storage, Frida) | `android-pentesting-tricks` |
| TLS pinning after re-sign | `mobile-ssl-pinning-bypass`, `tls-plaintext-acquisition` |
| iOS codesign / Keychain | `ios-pentesting-tricks`, `ios-keychain-hygiene` |
| Keystore password lifecycle | `secrets-management-hygiene` |
| CI verify jobs / signing config code | `code-quality-standards` |

## Signing Schemes

| Scheme | What is signed | Notes |
| --- | --- | --- |
| **v1** (JAR) | ZIP entries via `META-INF` | Weak alone on modern targets; strip/re-add risks if only v1 |
| **v2** | APK Signing Block; whole-file | Preferred baseline on modern Android |
| **v3** | v2-style + **key rotation** lineage | Cert change without breaking updates |
| **v4** | Separate `.idsig` for incremental install paths | Often alongside v2/v3 |

**Hygiene:** ship **v2+v3** (add v4 when the pipeline needs it); keep v1 only for
documented legacy `minSdk`. Never ship production on a debug keystore.

## Workflow

### 1. Inventory and verify

```bash
sha256sum app-release.apk
aapt dump badging app-release.apk | rg 'package:|sdkVersion|version'
apksigner verify --verbose --print-certs app-release.apk
# jarsigner -verify is v1-oriented — not sufficient alone
```

Note splits, `.aab`, and Play App Signing (upload cert vs distribution cert may differ).
Record schemes present, signer DN / SHA-256, debug vs release, unexpected co-signers,
and v3 lineage when the cert rotated.

### 2. Assess scheme and key hygiene

1. **v1-only** on a modern app → finding.
2. **Debug cert** on a production channel → high severity process finding.
3. **Key rotation:** confirm v3 lineage; document upload vs app-signing key holders.
4. **Keystore protection:** no `*.jks` / passwords in git → `secrets-management-hygiene`.
5. **CI:** fail release if `apksigner verify` fails.

### 3. Lab re-sign (authorized patches only)

```bash
zipalign -p -f 4 app-unsigned.apk app-aligned.apk
apksigner sign --ks lab.keystore --ks-key-alias lab \
  --out app-lab-signed.apk app-aligned.apk
apksigner verify --verbose app-lab-signed.apk
adb install -r app-lab-signed.apk
```

Use a **lab-only** keystore. Apps that pin their signing cert should refuse to run —
document that as intended integrity. Re-sign all splits consistently when needed.

### 4. App-side integrity and remediate

Pair with `android-pentesting-tricks` for static/dynamic location:

| Pattern | Note |
| --- | --- |
| `PackageManager` / `GET_SIGNING_CERTIFICATES` | Pins running signer |
| Play Integrity / SafetyNet | Server must validate tokens; client-only is weak |
| DEX/native CRC self-checks | Brittle; often hookable in lab |
| Installer package checks | e.g. expect Play Store |

**Good:** server-side attestation. **Weak:** client-only cert hash / toast “tamper.”
Play App Signing: upload cert may differ from distribution cert — pin what users trust.
Report schemes/certs; enable modern Gradle signing; rotate on leak; re-verify.
Code/CI → `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| APK/AAB schemes, cert verify, re-sign lab, integrity checks | **This skill** | — |
| Broader Android pentest | `android-pentesting-tricks` | this skill for signing deep-dive |
| Gradle/CI signing config and tests | `code-quality-standards` | this skill for scheme policy |
| iOS Keychain / iOS testing | `ios-keychain-hygiene`, `ios-pentesting-tricks` | — |
| Pinning / traffic after lab re-sign | `tls-plaintext-acquisition`, `mobile-ssl-pinning-bypass` | `android-pentesting-tricks` |
| Keystore secret leakage | `secrets-management-hygiene` | this skill for signing impact |

### Required helpers

- **`android-pentesting-tricks`:** acquire APK, apktool/jadx, install/runtime context.
- **`code-quality-standards`:** Gradle/CI signing config, verification scripts, tests.
- **`ios-pentesting-tricks` / `ios-keychain-hygiene`:** when engagement spans iOS.

## Checklist

- [ ] Authorization and artifact identity (package, version, SHA-256) recorded
- [ ] `apksigner verify --verbose --print-certs` captured; schemes documented
- [ ] Signer cert vs expected release/upload/Play cert; debug-on-prod flagged
- [ ] Key rotation / v3 lineage considered; lab re-sign uses disposable keystore
- [ ] App integrity checks mapped; server-side attestation noted when missing
- [ ] Split/AAB vs distribution signing differences noted
- [ ] Keystore secrets via `secrets-management-hygiene`
- [ ] Broader app → `android-pentesting-tricks`; code → `code-quality-standards`

## Rules

- Authorized packages and lab re-signs only — no trojanized third-party redistrib.
- Production signing keys are high-tier secrets; rotate on exposure.
- Prefer `apksigner` evidence over guessing schemes from `META-INF` alone.
- Client-side signature checks are **signals**, not complete trust roots.
- Distinguish upload key, app-signing key, and debug key in every report.

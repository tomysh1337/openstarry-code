---
name: frida-hooking-playbook
description: >
  Frida attach/spawn playbook for owned apps and CTF labs: frida-server setup,
  process attach vs spawn, common Java/ObjC/native Interceptor hooks, script
  patterns, and troubleshooting. Use when instrumenting authorized Android/iOS
  apps or native lab binaries at runtime — not for third-party apps without
  written authorization.
---

# Frida Hooking Playbook

## When To Use

- Need runtime visibility into an **owned**, lab, CTF, or explicitly authorized app/binary.
- Want to log or temporarily alter function args/returns (crypto, auth, storage, network validation).
- Prefer reversible instrumentation over permanent APK/IPA repack when attach is possible.
- Debugging lab anti-root/anti-emulator/debug checks that block testing.

**Do not use as primary skill when:**

| Situation | Prefer instead |
| --- | --- |
| Only SSL pinning blocks a proxy | `tls-plaintext-acquisition` → `mobile-ssl-pinning-bypass` |
| Full Android surface map (manifest, storage, components) | `android-pentesting-tricks` |
| Deep native reverse (disasm, decompile, full RE report) | `binary-re` (+ nested phases) |
| Unknown sample needs isolation first | `security-sandbox` |

This skill is the **Frida attach/spawn + script pattern** playbook. Pinning recipes live in `mobile-ssl-pinning-bypass`; mobile methodology lives in `android-pentesting-tricks` / `ios-pentesting-tricks`.

## Scope And Authorization

- **In scope:** apps and binaries you own; written authorized assessments; deliberately vulnerable labs (e.g. DVIA-style); CTF packages; internal test builds on lab devices/emulators.
- **Out of scope:** instrumenting third-party production apps without authorization; shipping universal bypass kits for unowned targets; bypassing protections on end-user devices outside engagement scope.
- Match `frida-tools` host version to on-device `frida-server` (or Gadget) major.minor when possible.
- Prefer lab devices, emulators, and debuggable builds. Document package name, version, device model, and Frida versions.
- Redact tokens, cookies, device IDs, PII, and key material in notes and shared scripts.
- Keep originals immutable; store scripts and logs under a `derived/` workspace.

## Prerequisites

| Component | Role |
| --- | --- |
| `frida-tools` (host) | CLI: `frida`, `frida-ps`, `frida-trace` |
| `frida-server` (device, root/jailbreak lab) | Injects into processes over USB/network |
| USB debugging / jailbreak or Gadget | Access path to target process |
| `adb` (Android) | Push server, port forward, package install |
| Optional: Objection | Higher-level explore REPL on top of Frida |

```bash
# Host
pip install -U frida-tools
frida --version

# Android lab: push matching frida-server architecture (arm64 common)
adb push frida-server /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
# or: adb shell "su -c 'killall frida-server; /data/local/tmp/frida-server -D &'"

frida-ps -U
```

Version mismatch symptoms: empty process list, immediate disconnect, or “unable to connect to remote frida-server”. Fix by aligning host tools and device server builds from the same Frida release.

## Workflow

### 1. Confirm target and lab path

```bash
# USB device present
frida-ps -Uai                    # apps with identifiers
frida-ps -U | rg -i 'example|target'

# Android package path / pid
adb shell pm path com.example.app
adb shell pidof com.example.app
```

Decide:

| Mode | When | Frida flag pattern |
| --- | --- | --- |
| **Attach** | Process already running; preserve current state | `frida -U <name|pid> -l hook.js` |
| **Spawn** | Need early hooks (init, SSL setup, anti-debug at start) | `frida -U -f com.example.app -l hook.js` |
| **Gadget** | No root; repackaged app loads `frida-gadget` | Local listen / script config in gadget config |
| **Remote** | Network frida-server | `frida -H host:port ...` |

Spawn starts a fresh process; attach does not. Prefer spawn for “fires only at startup” checks.

### 2. Attach vs spawn — concrete commands

```bash
# Attach by name (USB)
frida -U "App Name" -l derived/hooks/log_crypto.js
frida -U -n com.example.app -l derived/hooks/log_crypto.js
frida -U -p 12345 -l derived/hooks/log_crypto.js

# Spawn package (Android identifier)
# Older CLI used --no-pause; modern Frida resumes by default after script load
frida -U -f com.example.app -l derived/hooks/early.js
# If process stays paused in your version:
frida -U -f com.example.app -l derived/hooks/early.js --no-pause

# Load multiple scripts
frida -U -f com.example.app -l base.js -l crypto.js

# Interactive REPL without file
frida -U -f com.example.app
# then paste JS or %load path

# Trace exports quickly (generated stubs)
frida-trace -U -i "open*" -i "connect" com.example.app
frida-trace -U -j '*!*Certificate*!*' -f com.example.app   # Java patterns when supported
```

Windows / local native lab binary (same architecture as host):

```bash
frida -f ./lab_binary -l derived/hooks/hook_connect.js
frida -p $(pidof lab_binary) -l derived/hooks/hook_connect.js
```

**Constraint:** Frida does **not** attach to QEMU-user cross-arch targets. Use on-device `frida-server`, native-arch execution, or fall back to GDB/QEMU under `binary-re/dynamic-analysis`.

### 3. Script skeleton (safe lab defaults)

```javascript
// derived/hooks/skeleton.js
'use strict';

function log(msg) {
  console.log('[hook] ' + msg);
}

// Delay Java hooks until VM is ready (Android)
function whenJava(cb) {
  if (Java.available) {
    Java.perform(cb);
  } else {
    log('Java not available');
  }
}

// Enumerate modules once for orientation
Process.enumerateModules().slice(0, 20).forEach(function (m) {
  log(m.name + ' @ ' + m.base);
});

whenJava(function () {
  log('Java.perform ready');
});
```

Run:

```bash
frida -U -f com.example.app -l derived/hooks/skeleton.js
```

### 4. Common hook patterns

#### 4.1 Android Java — SharedPreferences / tokens

```javascript
// derived/hooks/prefs.js
Java.perform(function () {
  var SP = Java.use('android.app.SharedPreferencesImpl');
  SP.getString.overload('java.lang.String', 'java.lang.String').implementation = function (k, def) {
    var v = this.getString(k, def);
    console.log('[prefs get] ' + k + ' => ' + v);
    return v;
  };
  SP.putString.overload('java.lang.String', 'java.lang.String').implementation = function (k, v) {
    console.log('[prefs put] ' + k + ' => ' + v);
    return this.putString(k, v);
  };
});
```

#### 4.2 Android Java — crypto (lab logging only)

```javascript
// derived/hooks/javax_crypto.js
Java.perform(function () {
  var Cipher = Java.use('javax.crypto.Cipher');
  Cipher.doFinal.overload('[B').implementation = function (input) {
    var out = this.doFinal(input);
    try {
      console.log('[Cipher.doFinal] in=' + input.length + ' out=' + out.length +
        ' algo=' + this.getAlgorithm());
    } catch (e) {}
    return out;
  };
});
```

Log algorithms and lengths first; dump full key material only when engagement rules allow and notes are redacted for sharing.

#### 4.3 Android Java — root/debug check return flip (authorized lab)

```javascript
// derived/hooks/root_stub.js — example only; class names are app-specific
Java.perform(function () {
  try {
    var Root = Java.use('com.example.app.security.RootCheck');
    Root.isRooted.implementation = function () {
      console.log('[RootCheck.isRooted] forced false');
      return false;
    };
  } catch (e) {
    console.log('[RootCheck] class not found: ' + e);
  }
});
```

Find real class names via Objection or:

```javascript
Java.perform(function () {
  Java.enumerateLoadedClasses({
    onMatch: function (name) {
      if (name.toLowerCase().indexOf('root') !== -1 ||
          name.toLowerCase().indexOf('emulator') !== -1) {
        console.log(name);
      }
    },
    onComplete: function () {}
  });
});
```

#### 4.4 Native Interceptor — libc `connect` / `open`

```javascript
// derived/hooks/native_connect.js
function htons(n) { return ((n & 0xff) << 8) | ((n >> 8) & 0xff); }

var connectPtr = Module.findExportByName(null, 'connect');
if (connectPtr) {
  Interceptor.attach(connectPtr, {
    onEnter: function (args) {
      var sa = args[1];
      var family = sa.readU16();
      if (family === 2) { // AF_INET
        var port = htons(sa.add(2).readU16());
        var b = new Uint8Array(sa.add(4).readByteArray(4));
        console.log('[connect] ' + b.join('.') + ':' + port);
      }
    }
  });
}

var openPtr = Module.findExportByName(null, 'open');
if (openPtr) {
  Interceptor.attach(openPtr, {
    onEnter: function (args) {
      try { console.log('[open] ' + args[0].readCString()); } catch (e) {}
    }
  });
}
```

#### 4.5 iOS ObjC — method hook sketch

```javascript
// derived/hooks/ios_objc.js — jailbroken lab / authorized IPA only
if (ObjC.available) {
  var cls = ObjC.classes.NSURLCredential;
  // Enumerate interesting classes first; then:
  // Interceptor.attach(ObjC.classes.SomeClass['- methodName:'].implementation, { ... });
  console.log('[objc] runtime available, classes sample:');
  var names = Object.keys(ObjC.classes).filter(function (n) {
    return n.indexOf('Pinning') !== -1 || n.indexOf('Trust') !== -1;
  }).slice(0, 30);
  names.forEach(function (n) { console.log('  ' + n); });
} else {
  console.log('ObjC not available');
}
```

SSL pin-specific SecTrust / CertificatePinner recipes → **`mobile-ssl-pinning-bypass`**, not duplicated here.

#### 4.6 Replace return value / call original

```javascript
// Force boolean true (lab)
Interceptor.attach(Module.findExportByName('libapp.so', 'is_licensed'), {
  onLeave: function (retval) {
    console.log('[is_licensed] was ' + retval);
    retval.replace(ptr(1));
  }
});

// Java: call original then modify
Java.perform(function () {
  var Cls = Java.use('com.example.app.Auth');
  Cls.getToken.implementation = function () {
    var t = this.getToken();
    console.log('[getToken] ' + t);
    return t;
  };
});
```

### 5. Objection quick path (when installed)

```bash
objection -g com.example.app explore
# android hooking list classes
# android hooking search classes Root
# android hooking list class_methods com.example.app.security.RootCheck
# android hooking watch class_method com.example.app.security.RootCheck.isRooted --dump-args --dump-return
# android sslpinning disable    # delegates to pinning workflows
# android root disable
```

Use Objection for discovery; promote stable hooks into version-controlled Frida scripts under `derived/hooks/`.

### 6. Gadget (no-root / non-jailbreak lab)

1. Unpack APK (`apktool`) or use a gadget injection helper on a **lab** build only.
2. Add `frida-gadget` `.so` + config (listen or script path).
3. Repackage, resign, install — see patch cycle in `android-pentesting-tricks`.
4. Connect:

```bash
frida -U Gadget -l derived/hooks/early.js
# or host:port from gadget config
```

Coordinate packaging steps with `android-pentesting-tricks`; keep Frida script logic in this skill.

### 7. Anti-instrumentation and stability notes

| Symptom | Likely cause | Mitigation (lab) |
| --- | --- | --- |
| Instant crash on spawn | Early integrity / Frida detection | Spawn + very early native hooks; patch detection with `binary-re`; test on debuggable build |
| Hooks never fire | Wrong overload / class not loaded yet | `Java.perform` + classloader enumerate; hook after activity start; use `Java.choose` |
| Empty `frida-ps -U` | Server not running / version skew | Restart server; match versions |
| Only works once | Process died | Spawn again; catch exceptions inside hooks |
| Cross-arch fail | QEMU-user target | On-device server or native arch only |

```bash
# Verbose host side
frida -U -f com.example.app -l hook.js --runtime=v8
# Confirm server arch
adb shell "file /data/local/tmp/frida-server"
```

### 8. Evidence hygiene

```bash
mkdir -p derived/hooks derived/logs
frida -U -f com.example.app -l derived/hooks/prefs.js 2>&1 | tee derived/logs/prefs-$(date +%Y%m%d-%H%M%S).log
```

Record: package/version, device build, Frida host/server versions, script names, and redacted excerpts of hits.

## Routing

| Observation / need | Next skill |
| --- | --- |
| SSL/TLS pinning, TrustManager, OkHttp pin, SecTrust | `mobile-ssl-pinning-bypass` (after `tls-plaintext-acquisition` method choice) |
| Manifest, APK pull, storage, components, resign cycle | `android-pentesting-tricks` |
| iOS lab packaging / non-Frida iOS surface | `ios-pentesting-tricks` |
| Native `.so` / ELF deep RE, symbols, decompile | `binary-re` → `binary-re/static-analysis` or `binary-re/dynamic-analysis` |
| Frida tools missing / general RE toolchain | `binary-re/tool-setup` |
| Untrusted sample; need VM snapshot / isolation | `security-sandbox` |
| After plaintext: Protobuf / WS binary | `protobuf-grpc-reverse-engineering` / `websocket-binary-reverse-engineering` |

**Primary vs helper:** For “hook this lab app with Frida,” this skill is primary. Add `android-pentesting-tricks` for static/mobile surface, `mobile-ssl-pinning-bypass` for pin-only goals, `binary-re` for serious native analysis, `security-sandbox` before executing unknown extracted code.

## Output Checklist

- [ ] Authorization / lab scope stated (package, owner, engagement)
- [ ] Device/emulator id, Android/iOS version, root/jailbreak/Gadget path
- [ ] Frida host version and frida-server (or Gadget) version match noted
- [ ] Attach vs spawn decision and exact CLI used
- [ ] Script paths under `derived/hooks/` and what each hooks
- [ ] Key runtime observations (redacted): function, args summary, return
- [ ] Failures and anti-Frida signals (if any)
- [ ] Hand-off: pinning skill, android skill, or binary-re as needed

## Rules

- Authorized targets only; do not treat “public APK” as authorization.
- Prefer logging over destructive memory corruption; keep hooks exception-safe (`try/catch`) so one bad hook does not kill the process mid-test.
- Do not paste production secrets into public writeups.
- Do not claim a bypass works without showing script + log evidence on the stated build.
- Native RE and full dynamic RE methodology stay under `binary-re`; this skill does not replace sandbox policy — use `security-sandbox` for untrusted binaries.
- Pinning-specific scripts: implement or extend under `mobile-ssl-pinning-bypass` for consistency with TLS capture routing.

---
name: electron-app-security
description: >
  Authorized Electron desktop app security review: nodeIntegration,
  contextIsolation, sandbox, preload bridges, shell.openExternal, navigation
  and webview risks, and renderer XSS to OS/code execution. Use when assessing
  Electron, Spectron-era, or Chromium-embedded desktop apps you own or are
  scoped to harden, or when BrowserWindow / WebPreferences need a security pass.
---

# Electron App Security (Authorized)

## Use When

- Reviewing **Electron** (or Electron-like) desktop apps: main process, preload, renderer.
- `BrowserWindow` / `webPreferences` may enable `nodeIntegration`, disable `contextIsolation`, or weaken `sandbox`.
- Renderer loads remote or user-influenced content; XSS may become RCE.
- Preload exposes broad IPC or raw Node primitives to page JavaScript.
- `shell.openExternal`, custom protocols, auto-updaters, or `webview` tags need review.
- Not primary for pure browser extensions — use `browser-extension-security`.
- Not primary for generic website XSS without an Electron shell — use `xss-cross-site-scripting`.

## Scope And Authorization

- **In scope:** Apps you own, org desktop clients, staging builds, CTF/lab binaries, and targets under **written** authorization.
- **Out of scope:** Shipping malware, bypassing third-party app licensing, or attacking users outside agreed test builds/accounts.
- Prefer local builds and test fixtures; keep production signing keys and update credentials out of reports (`secrets-management-hygiene`).
- Prove impact with **lab** payloads (calc/canary file write, unique dialog) only on owned machines — no destructive wipes.
- Redact tokens, license keys, device ids, and customer data from logs and screenshots.
- Gate dynamic instrumentation (Frida, debug builds) on ownership and SOW.

## Workflow

### 1. Map process model and entry points

1. Identify Electron version (`package.json`, `process.versions.electron`) — older majors lag Chromium security fixes.
2. List main-process entry, all `BrowserWindow` / `BrowserView` / `webview` creations, preload paths, and custom `protocol.register*`.
3. Note what each window loads: `file://` app UI, `https://` remote SPA, hybrid, or user-selected files.
4. Trust zones: **remote/user content** → renderer → preload bridge → main → OS (Node, shell, filesystem).

### 2. WebPreferences baseline (critical)

For every window and webview, record and assess:

| Preference | Secure default / expectation |
| --- | --- |
| `contextIsolation` | **`true`** — isolate preload from page world |
| `nodeIntegration` | **`false`** — no `require` in page |
| `nodeIntegrationInWorker` | **`false`** unless strongly justified |
| `nodeIntegrationInSubFrames` | **`false`** |
| `sandbox` | **`true`** when compatible with the app model |
| `webviewTag` | **`false`** unless required; then isolate and restrict |
| `allowRunningInsecureContent` | **`false`** |
| `experimentalFeatures` / `navigateOnDragDrop` | off unless required |

**Anti-pattern:** `nodeIntegration: true` + `contextIsolation: false` on untrusted HTML/JS → **XSS→RCE**. Prefer explicit IPC over legacy `remote` / `enableRemoteModule`.

### 3. Preload and IPC bridge review

1. Open every `preload.js` / `.ts`. Ensure it runs only with isolation and exposes a **minimal** API via `contextBridge.exposeInMainWorld`.
2. Ban exposing: `require`, `process`, `child_process`, raw `ipcRenderer` / `ipcMain`, `Buffer`, filesystem, or universal `invoke(channel, …)` proxies.
3. Main-process handlers (`ipcMain.handle` / `on`):
   - Allowlist **channel names** and **sender** frame URL / partition when relevant.
   - Validate argument schema; never pass renderer strings into `exec`, `spawn`, `eval`, or unchecked file paths.
4. Prefer capability-style methods (`saveExport(pathValidated)`) over generic “run command” bridges.
5. Apply `code-quality-standards` when hardening handlers and shared validation.

### 4. Navigation, new windows, and openExternal

1. Attach `will-navigate`, `will-redirect`, `setWindowOpenHandler` — deny unexpected origins; allowlist app origins.
2. Disable or tightly control `createWindow` for arbitrary URLs.
3. `shell.openExternal(url)`: allowlist schemes (`https:`) and hosts; block `file:`, `javascript:`, unsanitized attacker URLs (classic RCE/phishing chain).
4. Custom protocol handlers: prevent path traversal to sensitive files; do not map user input to arbitrary FS reads.
5. `webview`: guest partitions, `preload` for guests, and IPC from guest treated as untrusted.

### 5. Renderer XSS and untrusted content

1. If the renderer renders remote HTML, markdown, or user notes, map sources→sinks with `xss-cross-site-scripting`.
2. Prefer `textContent`, safe UI frameworks, or hardened sanitizers; avoid `dangerouslySetInnerHTML` / `innerHTML` for untrusted data.
3. With secure `webPreferences`, XSS stays **in renderer** — still report for data theft via exposed bridge APIs.
4. With insecure preferences, escalate proof: XSS → bridge/Node → canary command or file write on a **lab** account.
5. CSP on loadURL content helps defense-in-depth; not a substitute for isolation and no-node in page.

### 6. Secrets, updates, and packaging

1. Hunt API keys, signing secrets, and tokens in asar/source/env samples — `secrets-management-hygiene`.
2. Auto-updater: TLS, signature verification, feed URL integrity; no HTTP unauthenticated updates.
3. asar integrity / fuses (Electron fuses: e.g. disable `nodeIntegration` override, cookie encryption) when version supports them — document enablement.
4. Native Node addons and helper binaries: least privilege, no world-writable update dirs.
5. Crash reports and logs must not ship session tokens or local file contents.

### 7. Remediation verification

1. Set `contextIsolation: true`, `nodeIntegration: false`, enable `sandbox` where feasible for all untrusted windows.
2. Shrink preload API; validate IPC; remove `remote`.
3. Lock navigation and `openExternal` allowlists.
4. Fix renderer sinks (`xss-cross-site-scripting`); remove secrets from client packages.
5. Bump Electron to a supported release; retest PoCs on the signed build.
6. Add automated checks for webPreferences regressions (`code-quality-standards`).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Electron `webPreferences` / preload / IPC / openExternal | **This skill** | — |
| Renderer HTML/JS injection detail | `xss-cross-site-scripting` | this skill for RCE escalation path |
| Keys in asar, updater, or config | `secrets-management-hygiene` | this skill for desktop paths |
| Secure coding of main/preload/IPC | `code-quality-standards` | **always** on implementation |
| Browser extension (MV2/MV3), not Electron | `browser-extension-security` | — |
| Deep binary RE of native helpers | `binary-re` | this skill for Electron shell |

### Routing notes (required helpers)

- **`xss-cross-site-scripting`:** prove renderer injection; this skill covers preference and bridge impact.
- **`code-quality-standards`:** baseline for main/preload fixes, validation, and tests.
- **`secrets-management-hygiene`:** client secret inventory, rotation, and update-feed credentials.

## Checklist

- [ ] Electron version and all window/webview creation sites inventoried
- [ ] `contextIsolation`, `nodeIntegration`, `sandbox`, `webviewTag` recorded per window
- [ ] Preload uses `contextBridge` only; no raw Node/IPC leak to page
- [ ] IPC channels allowlisted; args validated; no shell/exec from renderer strings
- [ ] Navigation and `setWindowOpenHandler` deny unexpected origins
- [ ] `shell.openExternal` scheme/host allowlist enforced
- [ ] Renderer XSS assessed (`xss-cross-site-scripting`); RCE only claimed with working lab proof
- [ ] No secrets in asar/repo; updater authenticity reviewed (`secrets-management-hygiene`)
- [ ] Custom protocols and file access fail closed on traversal
- [ ] Fixes and regression checks follow `code-quality-standards`
- [ ] Authorization, OS, and app version in report; residual risk listed

## Rules

- Authorized/owned apps and lab payloads only — no destructive demos on production endpoints.
- Never disable isolation “for convenience” without documenting RCE risk; severity follows Node/OS reachability.
- Redact secrets, license material, and customer paths; prefer origin/channel/scheme allowlists.
- Keep Electron/Chromium on supported releases; unsupported stacks are standing risk.

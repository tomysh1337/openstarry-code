---
name: application-build
description: "Build, validate, and release OpenStarry Code desktop applications. Use for Electron packaging, Windows EXE/MSI installers, bundled runtimes, artifact verification, and GitHub Release publication."
description_zh: "用于 OpenStarry Code 应用构建与发布：Electron 打包、Windows EXE/MSI 安装包、内置运行时、产物校验和 GitHub Release。"
triggers:
  - "应用构建"
  - "打包成 exe"
  - "用 msi 打包"
  - "Windows 安装包"
  - "Electron release"
  - "desktop build"
provenance:
  origin: openstarry-code
  license: Apache-2.0
  maintained_by: OpenStarry Code contributors
metadata:
  {
    "openstarry-code":
      {
        "emoji": "build",
        "requires": { "anyBins": ["node", "npm"] },
        "capabilities": ["filesystem-write", "process-control", "network-read", "github-release"]
      }
  }
---

# Application Build

Use this skill for reproducible desktop builds and release artifacts. The
Electron package lives in `desktop/electron`; the generated artifacts are kept
under `dist/desktop-electron/` and are never committed to source control.

## Windows EXE and MSI

From the repository root, run the following in PowerShell:

```powershell
Set-Location desktop/electron
npm.cmd ci
$env:NODE_OPTIONS = '--use-system-ca'
npm.cmd run fetch:runtimes
npm.cmd run build:gateway
npm.cmd run dist:windows
```

`dist:windows` builds the TypeScript main process and invokes electron-builder
for both targets:

- NSIS: interactive `.exe` installer
- WiX MSI: per-user `.msi` installer with desktop and Start Menu shortcuts

The command finishes with `verify:package`, which checks the icon contract,
packaged file layout, and bundled gateway metadata. Expected files are named
`OpenStarry-Code-<version>-win-x64.exe` and
`OpenStarry-Code-<version>-win-x64.msi`.

## Runtime and Tooling Checks

Before a release, confirm that `desktop/electron/runtime/runtime-manifest.json`
has all six platform targets and that the local `tar` implementation supports
the arguments selected by `fetch-bundled-runtimes.mjs`. GNU tar may use
`--force-local`; bsdtar uses the portable `-xf <archive> -C <destination>` form.

If a runtime download fails during certificate validation, keep
`NODE_OPTIONS=--use-system-ca` in the current shell and retry. Do not publish a
partial `runtime/` directory or an installer built without the gateway.

## Release Checklist

1. Run `npm.cmd run verify:package` from `desktop/electron`.
2. Inspect both installer files and create a SHA-256 manifest:

   ```powershell
   Get-FileHash ..\..\dist\desktop-electron\OpenStarry-Code-*.exe -Algorithm SHA256
   Get-FileHash ..\..\dist\desktop-electron\OpenStarry-Code-*.msi -Algorithm SHA256
   ```

3. Commit source and packaging metadata with a focused message.
4. Create or update the matching Git tag and publish the installers only after
   the build and verification logs are complete:

   ```powershell
   gh release create v<version> `
     dist/desktop-electron/OpenStarry-Code-<version>-win-x64.exe `
     dist/desktop-electron/OpenStarry-Code-<version>-win-x64.msi `
     --title "OpenStarry Code v<version>" --generate-notes
   ```

Never overwrite an existing release asset with bytes from a different build.
Keep the source archive, installer artifacts, and `SHA256SUMS` in the same
release when they are produced together.

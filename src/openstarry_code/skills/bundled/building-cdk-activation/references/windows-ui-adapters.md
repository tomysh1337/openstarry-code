# Windows UI Adapter Patterns

## Shared interface

Expose services rather than cryptographic primitives:

```text
ActivationService.activate(cdk) -> ActivationResult
ActivationService.refresh() -> ActivationResult
UpdateService.check() -> UpdateResult
UpdateService.download(progress, cancellation) -> UpdateResult
UpdateService.install() -> never returns on success
```

Run network, hashing, signature verification, and installer launch off the UI thread. Marshal immutable state snapshots back to the UI. Prevent duplicate activation/check/download/install commands while the matching state is busy.

## Qt/QML + Python or C++

- Put licensing and update logic in Python core modules.
- Expose narrow `QObject` bridge properties/signals/slots for state, message, version, progress, and commands.
- Use `QThread`/worker objects or asynchronous networking; never block QML event handlers.
- QML binds visibility/enabled state to bridge state and contains no key parsing, hashing, download, or process-launch logic.
- Test core services directly, bridge transitions with signal observation, and QML flow with runtime UI tests where possible.
- For C++, keep verification/update services in non-visual classes and expose a narrow `QObject` bridge through `Q_PROPERTY`, signals, and `Q_INVOKABLE` commands. Never expose filesystem paths, arbitrary URLs, or installer arguments to QML.
- Use worker `QObject`s moved to `QThread`, Qt Concurrent, or an application-owned async layer. With `QNetworkAccessManager`, disable implicit trust in redirects: inspect every redirected URL, enforce HTTPS/allowlisted host/hop limits, and keep replies owned and deleted on the correct thread.

## WPF/WinUI + .NET

- Define `IActivationService` and `IUpdateService`; inject them into a ViewModel.
- ViewModel owns observable state and `ICommand`/async command enablement; code-behind stays presentation-only.
- Use cancellation tokens for checks/downloads. Configure the update `HttpClientHandler` with `AllowAutoRedirect = false`, validate each `Location`, and follow only allowlisted HTTPS redirects with a bounded hop count.
- Verify with a maintained Ed25519 implementation, `SHA256`, and Windows signature APIs/PowerShell Authenticode semantics.
- Test service contracts, ViewModel transitions, cancellation, dispatcher marshalling, and installer handoff separately.

## Electron

- Main process owns CDK verification, cache, network, package verification, and installer launch.
- Preload exposes a narrow typed API through `contextBridge`; Renderer only submits commands and displays immutable state.
- Require `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true` where supported.
- Validate IPC sender/frame and reject arbitrary URLs, filesystem paths, shell arguments, and installer arguments from Renderer.
- Use atomic writes in Main and do not expose public-key helpers that can be repurposed into arbitrary file-verification or process-launch oracles.
- Test Main services, IPC authorization, preload API shape, Renderer state transitions, and compromised-renderer negative cases.

## UI behavior

- Activation: masked input with reveal/copy controls as product policy permits; disable submit when empty or validating; show specific recoverable state without leaking token data.
- Update: automatic background check plus manual retry; present version and release notes; require confirmation before download/install; show progress, cancel, retry, and ready-to-install states.
- Narrow windows must stack actions and preserve error/progress text. Keyboard focus, screen-reader names, and high-contrast states must remain usable.

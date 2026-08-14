# OpenStarry Code

OpenStarry Code is a Python agent runtime with MCP-native tools, durable sessions,
local memory, multi-channel messaging, and a local web control UI.

The package is published as part of an OpenStarry Code release zip. Install from the
release bundle rather than from a source checkout so the wheel, dependency
wheelhouse, install scripts, and third-party notices stay together.
The wheel already contains the built Web UI, so installing this release bundle
does not require Node.js or npm. Those tools are needed only when building from
a Git checkout.

## Requirements

- Python 3.12 or newer.
- A configured model provider for live model calls.
- Optional channel credentials only for the channel integrations you enable.

## After Install

Run the onboarding command before starting the gateway:

```sh
openstarry-code onboard --if-needed
```

Then start the local gateway:

```sh
openstarry-code gateway run
```

## Project Links

Repository, license, release, and third-party notice information are included in
the release bundle and in the public OpenStarry Code repository.

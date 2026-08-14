import assert from 'node:assert/strict'

import { buildCliInvocation } from '../dist/cli-invocation.js'

// --- bundled posix: env pair + quoted binary, spaces survive quoting ---
{
  const result = buildCliInvocation({
    platform: 'darwin',
    mode: 'bundled',
    binaryPath: '/Applications/OpenStarry Code.app/Contents/Resources/runtime/gateway/openstarry-code-gateway/openstarry-code-gateway',
    // OPENSTARRY_CODE_STATE_DIR is the OpenStarry Code home root; runtime databases
    // remain under the config-pinned <home>/state directory.
    stateDir: '/opt/OpenStarry Code Data',
    configPath: '/opt/OpenStarry Code Data/config.toml',
  })
  assert.equal(result.mode, 'bundled')
  assert.equal(
    result.prefix,
    "OPENSTARRY_CODE_STATE_DIR='/opt/OpenStarry Code Data' "
      + "OPENSTARRY_CODE_GATEWAY_CONFIG_PATH='/opt/OpenStarry Code Data/config.toml' "
      + "'/Applications/OpenStarry Code.app/Contents/Resources/runtime/gateway/openstarry-code-gateway/openstarry-code-gateway'",
  )
}

// --- posix: single quotes inside paths get the '\'' escape ---
{
  const result = buildCliInvocation({
    platform: 'linux',
    mode: 'bundled',
    binaryPath: "/opt/o'brien apps/openstarry-code-gateway",
    stateDir: "/opt/o'brien data",
    configPath: "/opt/o'brien data/config.toml",
  })
  assert.ok(result.prefix.includes("'/opt/o'\\''brien apps/openstarry-code-gateway'"))
  assert.ok(result.prefix.includes("OPENSTARRY_CODE_STATE_DIR='/opt/o'\\''brien data'"))
}

// --- windows: PowerShell $env: syntax, '' doubling, & call operator ---
{
  const result = buildCliInvocation({
    platform: 'win32',
    mode: 'bundled',
    binaryPath: 'C:\\Program Files\\OpenStarry Code\\resources\\runtime\\gateway\\openstarry-code-gateway.exe',
    stateDir: "C:\\Users\\o'brien\\AppData\\Roaming\\OpenStarry Code\\openstarry-code",
    configPath: 'C:\\Users\\jo\\AppData\\Roaming\\OpenStarry Code\\openstarry-code\\config.toml',
  })
  assert.ok(result.prefix.startsWith("$env:OPENSTARRY_CODE_STATE_DIR = 'C:\\Users\\o''brien\\AppData"))
  assert.ok(result.prefix.includes("$env:OPENSTARRY_CODE_GATEWAY_CONFIG_PATH = 'C:\\Users\\jo\\AppData"))
  assert.ok(result.prefix.includes("& 'C:\\Program Files\\OpenStarry Code\\resources\\runtime\\gateway\\openstarry-code-gateway.exe'"))
}

// --- windows: unicode smart quotes are single-quote delimiters in PowerShell ---
{
  const result = buildCliInvocation({
    platform: 'win32',
    mode: 'bundled',
    binaryPath: 'C:\\Apps\\OpenStarry Code\\openstarry-code-gateway.exe',
    stateDir: 'C:\\Users\\O’Brien\\AppData\\Roaming\\OpenStarry Code\\openstarry-code',
    configPath: 'C:\\Users\\O’Brien\\AppData\\Roaming\\OpenStarry Code\\openstarry-code\\config.toml',
  })
  assert.ok(result.prefix.includes("$env:OPENSTARRY_CODE_STATE_DIR = 'C:\\Users\\O’’Brien\\AppData"))
  assert.ok(result.prefix.includes("$env:OPENSTARRY_CODE_GATEWAY_CONFIG_PATH = 'C:\\Users\\O’’Brien\\AppData"))
}

// --- windows dev mode: PowerShell env syntax composes with the uv runner ---
{
  const result = buildCliInvocation({
    platform: 'win32',
    mode: 'dev',
    repoRoot: 'C:\\Dev Projects\\openstarry-code',
    stateDir: 'C:\\Users\\jo\\AppData\\Roaming\\OpenStarry Code\\openstarry-code',
    configPath: 'C:\\Users\\jo\\AppData\\Roaming\\OpenStarry Code\\openstarry-code\\config.toml',
  })
  assert.equal(result.mode, 'dev')
  assert.ok(result.prefix.startsWith("$env:OPENSTARRY_CODE_STATE_DIR = 'C:\\Users\\jo\\AppData"))
  assert.ok(result.prefix.endsWith("uv run --directory 'C:\\Dev Projects\\openstarry-code' openstarry-code"))
}

// --- dev mode: uv run with an explicit checkout directory, no cwd dependence ---
{
  const result = buildCliInvocation({
    platform: 'darwin',
    mode: 'dev',
    repoRoot: '/opt/dev projects/openstarry-code',
    stateDir: '/opt/OpenSquilla Data',
    configPath: '/opt/OpenSquilla Data/config.toml',
  })
  assert.equal(result.mode, 'dev')
  assert.ok(result.prefix.endsWith("uv run --directory '/opt/dev projects/openstarry-code' openstarry-code"))
}

console.log('cli-invocation: all assertions passed')

import assert from 'node:assert/strict'

import {
  CODEX_X_ARCHIVE_SHA256,
  CODEX_X_ARCHIVE_URL,
  CODEX_X_EXECUTABLE_SHA256,
  CODEX_X_VERSION,
  currentCodexXTarget,
} from './fetch-codex-x.mjs'

assert.equal(CODEX_X_VERSION, '0.3.12')
assert.equal(CODEX_X_ARCHIVE_SHA256.length, 64)
assert.match(CODEX_X_ARCHIVE_SHA256, /^[0-9a-f]{64}$/)
assert.match(CODEX_X_EXECUTABLE_SHA256, /^[0-9a-f]{64}$/)
assert.match(CODEX_X_ARCHIVE_URL, /Codex-X-0\.3\.12-windows-x64-portable\.zip$/)
assert.equal(currentCodexXTarget('win32', 'x64'), 'windows-x64')
assert.equal(currentCodexXTarget('win32', 'arm64'), null)
assert.equal(currentCodexXTarget('linux', 'x64'), null)

console.log('Codex-X bundle contract tests passed.')

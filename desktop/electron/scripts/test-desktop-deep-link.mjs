import { strict as assert } from 'node:assert'

import {
  desktopDeepLinkArguments,
  parseDesktopDeepLink,
} from '../dist/desktop-deep-link.js'

for (const url of [
  'openstarry-code://open',
  'openstarry-code://open/',
  'OPENSTARRY-CODE://OPEN',
]) {
  assert.equal(parseDesktopDeepLink(url), 'open', url)
}

for (const url of [
  '',
  'not a URL',
  'https://open',
  'tokenrhythm://open',
  'openstarry-code://unknown',
  'openstarry-code://open/anything',
  'openstarry-code://open?command=anything',
  'openstarry-code://open#anything',
  'openstarry-code://user@open',
  'openstarry-code://open:1234',
  'openstarry-code:open',
]) {
  assert.equal(parseDesktopDeepLink(url), null, url)
}

assert.equal(parseDesktopDeepLink(null), null)
assert.equal(parseDesktopDeepLink({}), null)

assert.deepEqual(
  desktopDeepLinkArguments([
    'OpenStarry Code.exe',
    '--flag',
    'openstarry-code://open',
    'https://example.com',
    'openstarry-code://unknown',
  ]),
  ['openstarry-code://open', 'openstarry-code://unknown'],
)
assert.deepEqual(
  desktopDeepLinkArguments(['OpenStarry Code.exe', '--flag']),
  [],
)

console.log('desktop deep-link checks passed')

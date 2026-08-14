import { existsSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(scriptDir, '..')
const packageJsonPath = join(packageRoot, 'package.json')
const macIconPath = join(packageRoot, 'assets', 'icon.icns')
const windowsIconPath = join(packageRoot, 'assets', 'icon.ico')
const portableIconPath = join(packageRoot, 'assets', 'icon.png')

const failures = []

function fail(message) {
  failures.push(message)
}

function expectEqual(actual, expected, label) {
  if (actual !== expected) {
    fail(`${label} must be ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

const pkg = JSON.parse(await readFile(packageJsonPath, 'utf8'))
const build = pkg.build ?? {}

if (!existsSync(macIconPath)) {
  fail(`macOS icon is missing at ${macIconPath}`)
}

if (!existsSync(windowsIconPath)) {
  fail(`Windows icon is missing at ${windowsIconPath}`)
}

if (!existsSync(portableIconPath)) {
  fail(`Portable icon is missing at ${portableIconPath}`)
}

if (existsSync(portableIconPath)) {
  const png = await readFile(portableIconPath)
  const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  if (!png.subarray(0, pngSignature.length).equals(pngSignature)) {
    fail(`Portable icon is not a valid PNG at ${portableIconPath}`)
  }
}

expectEqual(build.mac?.icon, 'assets/icon.icns', 'build.mac.icon')
expectEqual(build.dmg?.icon, 'assets/icon.icns', 'build.dmg.icon')
expectEqual(build.win?.icon, 'assets/icon.ico', 'build.win.icon')
expectEqual(build.nsis?.installerIcon, 'assets/icon.ico', 'build.nsis.installerIcon')
expectEqual(build.nsis?.uninstallerIcon, 'assets/icon.ico', 'build.nsis.uninstallerIcon')

if (failures.length > 0) {
  console.error('OpenStarry Code desktop icon verification failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('OpenStarry Code desktop icon verification passed.')

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  copyFile,
  mkdir,
  readFile,
  rename,
  rm,
  stat,
  writeFile,
} from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import process from 'node:process'
import { fileURLToPath, pathToFileURL } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(scriptDir, '..')

export const CODEX_X_VERSION = '0.3.12'
export const CODEX_X_ARCHIVE_SHA256 = '3641a3cc4434fd8bf237108ccb7177c231606639b4990b32630faccee403978f'
export const CODEX_X_EXECUTABLE_SHA256 = '0f9054e7623de829bfd4962f569e27095637ca73b768392337f3d28b29046af9'
export const CODEX_X_ARCHIVE_URL = `https://github.com/yynxxxxx/Codex-X/releases/download/v${CODEX_X_VERSION}/Codex-X-${CODEX_X_VERSION}-windows-x64-portable.zip`
export const defaultCodexXRoot = join(packageRoot, 'runtime', 'codex-x')
export const defaultCodexXCacheRoot = join(packageRoot, '.runtime-cache', 'codex-x')

const manifestName = 'openstarry-codex-x.json'
const executableName = 'Codex-X.exe'
const portableMarkerName = 'Codex-X.portable'

export function currentCodexXTarget(platform = process.platform, arch = process.arch) {
  if (platform !== 'win32') return null
  return arch === 'x64' || arch === 'amd64' ? 'windows-x64' : null
}

export async function sha256File(path) {
  return createHash('sha256').update(await readFile(path)).digest('hex')
}

async function isFile(path) {
  return (await stat(path).catch(() => null))?.isFile() === true
}

async function downloadVerifiedArchive(url, destination) {
  await mkdir(dirname(destination), { recursive: true })
  if (await isFile(destination) && await sha256File(destination) === CODEX_X_ARCHIVE_SHA256) {
    return destination
  }

  const partial = `${destination}.part-${process.pid}`
  await rm(partial, { force: true })
  try {
    const source = new URL(url)
    if (source.protocol === 'file:') {
      await copyFile(fileURLToPath(source), partial)
    } else {
      try {
        const response = await fetch(source, { redirect: 'follow' })
        if (!response.ok) throw new Error(`Codex-X download failed: HTTP ${response.status}`)
        await writeFile(partial, Buffer.from(await response.arrayBuffer()))
      } catch (error) {
        if (process.platform !== 'win32') throw error
        runChecked('powershell.exe', [
          '-NoLogo',
          '-NoProfile',
          '-NonInteractive',
          '-Command',
          'Invoke-WebRequest -UseBasicParsing -Uri $env:OPENSTARRY_CODE_CODEX_X_URL '
            + '-OutFile $env:OPENSTARRY_CODE_CODEX_X_DOWNLOAD',
        ], {
          env: {
            ...process.env,
            OPENSTARRY_CODE_CODEX_X_URL: source.href,
            OPENSTARRY_CODE_CODEX_X_DOWNLOAD: partial,
          },
        })
      }
    }
    const actual = await sha256File(partial)
    if (actual !== CODEX_X_ARCHIVE_SHA256) {
      throw new Error(
        `Codex-X checksum mismatch; expected ${CODEX_X_ARCHIVE_SHA256}, got ${actual}`,
      )
    }
    await rm(destination, { force: true })
    await rename(partial, destination)
    return destination
  } finally {
    await rm(partial, { force: true })
  }
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: 'utf8',
    windowsHide: true,
    ...options,
  })
  if (result.error) throw result.error
  if (result.status !== 0) {
    throw new Error(
      `${command} ${args.join(' ')} failed with exit ${result.status}\n${result.stderr || result.stdout || ''}`.trim(),
    )
  }
}

function extractZip(archive, destination, platform = process.platform) {
  if (platform === 'win32') {
    runChecked('powershell.exe', [
      '-NoLogo',
      '-NoProfile',
      '-NonInteractive',
      '-Command',
      'Expand-Archive -LiteralPath $env:OPENSTARRY_CODE_CODEX_X_ARCHIVE '
        + '-DestinationPath $env:OPENSTARRY_CODE_CODEX_X_DESTINATION -Force',
    ], {
      env: {
        ...process.env,
        OPENSTARRY_CODE_CODEX_X_ARCHIVE: archive,
        OPENSTARRY_CODE_CODEX_X_DESTINATION: destination,
      },
    })
    return
  }
  runChecked('tar', ['-xf', archive, '-C', destination])
}

export async function assertCodexXReady(root = defaultCodexXRoot) {
  const executable = join(root, executableName)
  const portableMarker = join(root, portableMarkerName)
  const manifestPath = join(root, manifestName)
  for (const path of [executable, portableMarker, manifestPath, join(root, 'LICENSE.txt')]) {
    if (!await isFile(path)) throw new Error(`Bundled Codex-X file is missing: ${path}`)
  }
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
  if (
    manifest.version !== CODEX_X_VERSION
    || manifest.archiveSha256 !== CODEX_X_ARCHIVE_SHA256
    || manifest.executableSha256 !== CODEX_X_EXECUTABLE_SHA256
    || manifest.target !== 'windows-x64'
  ) {
    throw new Error('Bundled Codex-X manifest does not match the pinned release.')
  }
  const executableSha256 = await sha256File(executable)
  if (executableSha256 !== CODEX_X_EXECUTABLE_SHA256) {
    throw new Error(
      `Bundled Codex-X executable checksum mismatch; expected ${CODEX_X_EXECUTABLE_SHA256}, got ${executableSha256}`,
    )
  }
  return { executable, manifest }
}

export async function fetchCodexX({
  target = currentCodexXTarget(),
  destination = defaultCodexXRoot,
  cacheRoot = defaultCodexXCacheRoot,
  url = process.env.OPENSTARRY_CODE_CODEX_X_URL || CODEX_X_ARCHIVE_URL,
} = {}) {
  if (target !== 'windows-x64') {
    return { installed: false, target, reason: 'unsupported-target' }
  }

  try {
    const ready = await assertCodexXReady(destination)
    return { installed: true, target, ...ready }
  } catch {
    // Continue into the verified, atomic refresh path.
  }

  const archive = join(cacheRoot, `Codex-X-${CODEX_X_VERSION}-windows-x64-portable.zip`)
  await downloadVerifiedArchive(url, archive)

  const staging = `${destination}.staging-${process.pid}`
  await rm(staging, { recursive: true, force: true })
  await mkdir(staging, { recursive: true })
  try {
    extractZip(archive, staging)
    if (!await isFile(join(staging, executableName)) || !await isFile(join(staging, portableMarkerName))) {
      throw new Error('The verified Codex-X archive does not contain the portable runtime.')
    }
    await copyFile(join(packageRoot, 'third-party', 'Codex-X.LICENSE'), join(staging, 'LICENSE.txt'))
    await writeFile(join(staging, manifestName), `${JSON.stringify({
      schemaVersion: 1,
      product: 'Codex-X',
      version: CODEX_X_VERSION,
      target,
      upstream: 'https://github.com/yynxxxxx/Codex-X',
      archiveUrl: CODEX_X_ARCHIVE_URL,
      archiveSha256: CODEX_X_ARCHIVE_SHA256,
      executableSha256: CODEX_X_EXECUTABLE_SHA256,
    }, null, 2)}\n`, 'utf8')
    await rm(destination, { recursive: true, force: true })
    await rename(staging, destination)
  } finally {
    await rm(staging, { recursive: true, force: true })
  }

  const ready = await assertCodexXReady(destination)
  return { installed: true, target, ...ready }
}

async function main() {
  const targetIndex = process.argv.indexOf('--target')
  const target = targetIndex >= 0 ? process.argv[targetIndex + 1] : currentCodexXTarget()
  if (targetIndex >= 0 && !target) throw new Error('--target requires a value')
  const result = await fetchCodexX({ target })
  if (!result.installed) {
    console.log(`Codex-X is not bundled for ${target || `${process.platform}-${process.arch}`}.`)
    return
  }
  console.log(`Codex-X v${CODEX_X_VERSION} is ready for ${target}.`)
}

const invokedPath = process.argv[1] ? pathToFileURL(resolve(process.argv[1])).href : ''
if (import.meta.url === invokedPath) await main()

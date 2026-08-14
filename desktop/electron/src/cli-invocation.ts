export interface CliInvocation {
  mode: 'bundled' | 'dev'
  // Paste-ready replacement for the leading `openstarry-code` CLI token in
  // copyable commands surfaced by the Control UI.
  prefix: string
}

export interface CliInvocationInput {
  platform: NodeJS.Platform
  mode: 'bundled' | 'dev'
  binaryPath?: string
  repoRoot?: string
  stateDir: string
  configPath: string
}

function quotePosix(value: string): string {
  return `'${value.replaceAll("'", "'\\''")}'`
}

function quotePowerShell(value: string): string {
  // PowerShell treats the Unicode smart quotes U+2018-U+201B as single-quote
  // delimiters too; doubling is the only escape for every quote-class char.
  return `'${value.replace(/['‘’‚‛]/g, (ch) => ch + ch)}'`
}

// The desktop gateway resolves its config and state roots from environment
// variables rather than CLI flags, so a paste-ready invocation must carry both
// alongside the packaged binary path — a bare binary call would silently
// operate on the default ~/.openstarry-code world instead of the app's.
export function buildCliInvocation(input: CliInvocationInput): CliInvocation {
  const windows = input.platform === 'win32'
  const quote = windows ? quotePowerShell : quotePosix
  const runner = input.mode === 'bundled'
    ? (windows ? `& ${quote(input.binaryPath ?? '')}` : quote(input.binaryPath ?? ''))
    : `uv run --directory ${quote(input.repoRoot ?? '')} openstarry-code`
  const env = windows
    ? `$env:OPENSTARRY_CODE_STATE_DIR = ${quote(input.stateDir)}; `
      + `$env:OPENSTARRY_CODE_GATEWAY_CONFIG_PATH = ${quote(input.configPath)}; `
    : `OPENSTARRY_CODE_STATE_DIR=${quote(input.stateDir)} `
      + `OPENSTARRY_CODE_GATEWAY_CONFIG_PATH=${quote(input.configPath)} `
  return { mode: input.mode, prefix: `${env}${runner}` }
}

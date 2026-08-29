<template>
  <section
    class="terminal-panel"
    :class="{ 'is-collapsed': collapsed, 'is-resizing': resizing }"
    :style="collapsed ? undefined : { height: `${height}px` }"
    data-testid="terminal-panel"
  >
    <!-- Collapsed strip: a slim horizontal bar with an expand button. -->
    <div v-if="collapsed" class="terminal-panel__collapsed-bar">
      <button
        type="button"
        class="terminal-panel__toggle"
        :title="t('terminal.expand')"
        :aria-label="t('terminal.expand')"
        @click="expand"
      >
        <Icon name="chevronDown" :size="14" class="terminal-panel__expand-chevron" />
        <span>{{ title }}</span>
      </button>
    </div>

    <!-- Resizer + header only render while expanded; the terminal body below
         stays mounted across collapse/expand so the xterm instance (and its
         WebSocket session) survives — it is only hidden via CSS, and refit()
         restores the geometry on expand. -->
    <template v-if="!collapsed">
      <!-- Top-edge resizer: dragging up grows the panel. -->
      <div
        class="terminal-panel__resizer"
        role="separator"
        aria-orientation="horizontal"
        :title="t('terminal.resize')"
        @pointerdown="onResizeStart"
        @dblclick="resetHeight"
      />

      <header class="terminal-panel__header">
        <div class="terminal-panel__title">
          <span
            class="terminal-panel__status"
            :class="`is-${status}`"
            :title="statusLabel"
          />
          <span>{{ title }}</span>
        </div>
        <div class="terminal-panel__actions">
          <select
            v-if="!mirrorEnabled"
            v-model="sshHostId"
            class="terminal-panel__ssh"
            :aria-label="t('terminal.ssh.aria')"
            data-testid="terminal-ssh-select"
            @change="onSshChange"
          >
            <option value="">{{ t('terminal.ssh.local') }}</option>
            <option v-for="host in sshHosts" :key="host.id || host.name" :value="host.id || host.name">
              {{ host.name }}
            </option>
          </select>
          <button
            v-if="!mirrorEnabled && status !== 'connected'"
            type="button"
            class="terminal-panel__action"
            :title="t('terminal.reconnect')"
            :aria-label="t('terminal.reconnect')"
            @click="connect"
          >
            <Icon name="refresh" :size="14" />
          </button>
          <button
            type="button"
            class="terminal-panel__mirror"
            :class="{ 'is-active': mirrorEnabled }"
            :title="mirrorEnabled ? t('terminal.mirrorOff') : t('terminal.mirror')"
            :aria-label="mirrorEnabled ? t('terminal.mirrorOff') : t('terminal.mirror')"
            :aria-pressed="mirrorEnabled"
            data-testid="terminal-mirror-toggle"
            @click="toggleMirror"
          >
            <span class="terminal-panel__mirror-dot" aria-hidden="true"></span>
            <span>{{ mirrorEnabled ? t('terminal.mirrorOn') : t('terminal.mirror') }}</span>
          </button>
          <button
            type="button"
            class="terminal-panel__action"
            :title="t('terminal.collapse')"
            :aria-label="t('terminal.collapse')"
            @click="collapse"
          >
            <Icon name="chevronDown" :size="14" />
          </button>
        </div>
      </header>
    </template>

    <div class="terminal-panel__body" :class="{ 'is-hidden': collapsed }">
      <div ref="termRef" class="terminal-panel__term" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import Icon from '../Icon.vue'
import { fetchIdeRoot } from '@/utils/ideApi'
import { fetchSshHosts, type SshHost } from '@/utils/sshApi'
import { normalizeWsUrl } from '@/lib/ws-url'
import { useRpcStore } from '@/stores/rpc'

const { t } = useI18n()

// ---------------------------------------------------------------------------
// Persisted panel state
// ---------------------------------------------------------------------------

const HEIGHT_KEY = 'opensquilla.terminal.height'
const COLLAPSED_KEY = 'opensquilla.terminal.collapsed'
const MIRROR_KEY = 'opensquilla.terminal.mirror'

const DEFAULT_HEIGHT = 240
const MIN_HEIGHT = 120
const MAX_HEIGHT = 480

function readStoredNumber(key: string, fallback: number): number {
  try {
    const parsed = Number.parseInt(localStorage.getItem(key) || '', 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
  } catch {
    return fallback
  }
}

function readStoredBoolean(key: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(key)
    return stored === null ? fallback : stored === '1'
  } catch {
    return fallback
  }
}

const height = ref(Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, readStoredNumber(HEIGHT_KEY, DEFAULT_HEIGHT))))
const collapsed = ref(readStoredBoolean(COLLAPSED_KEY, false))
const mirrorEnabled = ref(readStoredBoolean(MIRROR_KEY, false))
const resizing = ref(false)

function persistHeight() {
  try { localStorage.setItem(HEIGHT_KEY, String(Math.round(height.value))) } catch {}
}
function persistCollapsed() {
  try { localStorage.setItem(COLLAPSED_KEY, collapsed.value ? '1' : '0') } catch {}
}
function persistMirror() {
  try { localStorage.setItem(MIRROR_KEY, mirrorEnabled.value ? '1' : '0') } catch {}
}

function collapse() {
  collapsed.value = true
  persistCollapsed()
}

function expand() {
  collapsed.value = false
  persistCollapsed()
  nextTick(() => refit())
}

// ---------------------------------------------------------------------------
// Resize (top edge)
// ---------------------------------------------------------------------------

function onResizeStart(event: PointerEvent) {
  if (event.button !== 0) return
  resizing.value = true
  const startY = event.clientY
  const startHeight = height.value
  const onMove = (move: PointerEvent) => {
    const delta = startY - move.clientY // moving up grows the panel
    height.value = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, startHeight + delta))
  }
  const onUp = () => {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    resizing.value = false
    persistHeight()
    refit()
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
  event.preventDefault()
}

function resetHeight() {
  height.value = DEFAULT_HEIGHT
  persistHeight()
  refit()
}

// ---------------------------------------------------------------------------
// Shell title (PowerShell on Windows, shell on POSIX; the selected SSH host
// name overrides both while an SSH session is active)
// ---------------------------------------------------------------------------

const shellName = ref('')
const title = computed(() => {
  if (mirrorEnabled.value) return t('terminal.mirrorTitle')
  if (sshHostId.value) {
    const host = sshHosts.value.find(h => (h.id || h.name) === sshHostId.value)
    if (host) return host.name
  }
  if (shellName.value === 'nt') return t('terminal.titlePowershell')
  return t('terminal.titleShell')
})

// ---------------------------------------------------------------------------
// SSH hosts (selector feed; sessions ride the same WebSocket with ssh_host)
// ---------------------------------------------------------------------------

const sshHosts = ref<SshHost[]>([])
const sshHostId = ref('')

async function loadSshHosts(): Promise<void> {
  try {
    const data = await fetchSshHosts()
    sshHosts.value = data.hosts.filter(h => h.enabled)
    // A persisted selection that disappeared (deleted/disabled) falls back to
    // the local shell on the next connection.
    if (sshHostId.value && !sshHosts.value.some(h => (h.id || h.name) === sshHostId.value)) {
      sshHostId.value = ''
    }
  } catch { /* selector stays hidden; local shell remains available */ }
}

// ---------------------------------------------------------------------------
// AI mirror mode: stream the AI's shell commands into this terminal display.
//
// The engine already broadcasts session.event.tool_use_start / tool_result to
// the WebSocket RPC stream, so this panel can mirror exec_command input/output
// without running a second live pty. While mirror mode is active the interactive
// terminal socket is closed and the buffer is used purely as a read-only view.
// ---------------------------------------------------------------------------

const rpcStore = useRpcStore()
let mirrorUnsub: (() => void) | null = null

interface MirrorToolResultPayload {
  tool_name?: string
  tool_use_id?: string
  result?: string
  is_error?: boolean
  arguments?: Record<string, unknown> | null
}

function renderMirrorCommand(command: string, output: string) {
  if (!terminal) return
  // Strip any ANSI escape sequences so foreign control bytes cannot corrupt
  // the mirror view, then normalise newlines for the terminal.
  const clean = output
    .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
    .replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, '')
    .replace(/\x1b[^\x1b]*/g, '')
    .replace(/\r\n/g, '\n')
    .replace(/\n/g, '\r\n')
  terminal.write(`\r\n\x1b[1;36mPS \x1b[0m\x1b[1;33m[AI]\x1b[0m ${command}\r\n`)
  if (clean.trim()) {
    terminal.write(`${clean}\r\n`)
  } else {
    terminal.write(`\x1b[90m[${t('terminal.mirrorNoOutput')}]\x1b[0m\r\n`)
  }
}

function handleMirrorToolResult(payload: unknown) {
  if (!payload || typeof payload !== 'object') return
  const record = payload as MirrorToolResultPayload
  if (record.tool_name !== 'exec_command') return
  const command = typeof record.arguments?.command === 'string' ? record.arguments.command : ''
  const output = typeof record.result === 'string' ? record.result : ''
  renderMirrorCommand(command, output)
}

function enterMirror() {
  closeSocketQuietly()
  status.value = 'disconnected'
  terminal?.reset()
  writeLine(t('terminal.mirrorHint'))
  writeLine('')
  mirrorUnsub = rpcStore.on('session.event.tool_result', handleMirrorToolResult)
}

function exitMirror() {
  if (mirrorUnsub) {
    mirrorUnsub()
    mirrorUnsub = null
  }
  terminal?.reset()
  connect()
}

function toggleMirror() {
  mirrorEnabled.value = !mirrorEnabled.value
  persistMirror()
  if (mirrorEnabled.value) {
    enterMirror()
  } else {
    exitMirror()
  }
  nextTick(() => refit())
}

// ---------------------------------------------------------------------------
// xterm.js + WebSocket
// ---------------------------------------------------------------------------

const status = ref<'connecting' | 'connected' | 'disconnected'>('disconnected')
const termRef = ref<HTMLElement | null>(null)
let terminal: Terminal | null = null
let fitAddon: FitAddon | null = null
let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let resizeObserver: ResizeObserver | null = null

const statusLabel = computed(() => {
  if (status.value === 'connected') return t('terminal.connected')
  if (status.value === 'connecting') return t('terminal.connecting')
  return t('terminal.disconnected')
})

function connectionSettings(): { url: string; token: string } {
  let url = ''
  let token = ''
  try {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    url = normalizeWsUrl(localStorage.getItem('opensquilla.wsUrl') || `${proto}//${location.host}/ws`)
  } catch { /* storage unavailable */ }
  try {
    token = sessionStorage.getItem('opensquilla.wsToken') || ''
  } catch { /* storage unavailable */ }
  return { url, token }
}

function buildSocketUrl(): string {
  const { url, token } = connectionSettings()
  const base = url.replace(/\/+$/, '')
  const params = new URLSearchParams()
  if (token) params.set('token', token)
  if (sshHostId.value) params.set('ssh_host', sshHostId.value)
  const query = params.toString()
  return `${base}/builtin/terminal${query ? `?${query}` : ''}`
}

// Resolve a theme token at runtime. xterm paints its canvas with concrete
// colours, so the theme object needs the RESOLVED value of --bg/--text rather
// than a var() reference (which the canvas renderer cannot parse).
function readCssToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function sendResize() {
  if (!terminal || socket?.readyState !== WebSocket.OPEN) return
  const cols = terminal.cols
  const rows = terminal.rows
  if (cols <= 0 || rows <= 0) return
  socket.send(JSON.stringify({ type: 'resize', cols, rows }))
}

function refit() {
  if (!terminal || !fitAddon || collapsed.value) return
  try {
    fitAddon.fit()
    sendResize()
  } catch { /* container not measurable yet */ }
}

function writeLine(text: string) {
  terminal?.writeln(text)
}

function handleMessage(event: MessageEvent) {
  if (!terminal) return
  let frame: { type?: string; data?: string; code?: number }
  try {
    frame = JSON.parse(String(event.data)) as { type?: string; data?: string; code?: number }
  } catch {
    writeLine(String(event.data))
    return
  }
  if (frame.type === 'output' && typeof frame.data === 'string') {
    terminal.write(frame.data)
  } else if (frame.type === 'exit') {
    status.value = 'disconnected'
    writeLine('')
    writeLine(`[${t('terminal.exited')}: ${frame.code ?? '?'}]`)
    scheduleReconnect()
  }
}

function scheduleReconnect() {
  if (socket) return
  if (reconnectTimer) clearTimeout(reconnectTimer)
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, 1500)
}

/** Tear the current socket down without triggering the auto-reconnect loop. */
function closeSocketQuietly() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  const existing = socket
  socket = null
  if (existing) {
    existing.onclose = null
    existing.onerror = null
    existing.onmessage = null
    try { existing.close() } catch { /* already closed */ }
  }
}

/** Rebuild the WebSocket after the SSH selection changed. */
function onSshChange() {
  closeSocketQuietly()
  status.value = 'disconnected'
  // A new session on a new host should not inherit the previous buffer.
  terminal?.reset()
  connect()
}

function connect() {
  if (socket) return
  status.value = 'connecting'
  try {
    socket = new WebSocket(buildSocketUrl())
  } catch {
    status.value = 'disconnected'
    scheduleReconnect()
    return
  }

  socket.onopen = () => {
    status.value = 'connected'
    sendResize()
  }

  socket.onmessage = handleMessage

  socket.onclose = (event) => {
    socket = null
    // 1008 = policy rejection (bad ssh_host, missing ssh binary). Auto-
    // reconnect would loop forever on a deterministic failure, so surface it
    // and wait for an explicit reconnect or selector change instead.
    if (event.code === 1008) {
      status.value = 'disconnected'
      writeLine(`[${t('terminal.ssh.rejected')}]`)
      return
    }
    if (status.value === 'connected') {
      writeLine(`[${t('terminal.disconnected')}]`)
    }
    status.value = 'disconnected'
    scheduleReconnect()
  }

  socket.onerror = () => {
    writeLine(`[${t('terminal.connectionFailed')}]`)
    try { socket?.close() } catch { /* already closed */ }
  }
}

onMounted(async () => {
  // Cosmetic side data — never block the terminal on either.
  try {
    const root = await fetchIdeRoot()
    shellName.value = root.platform
  } catch { /* fall back to generic label */ }
  void loadSshHosts()

  terminal = new Terminal({
    cursorBlink: true,
    fontSize: 13,
    fontFamily: "var(--font-mono, ui-monospace, 'Cascadia Code', Consolas, monospace)",
    scrollback: 5000,
    allowProposedApi: false,
    theme: {
      background: readCssToken('--bg'),
      foreground: readCssToken('--text'),
    },
  })
  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)

  if (termRef.value) {
    terminal.open(termRef.value)
  }

  terminal.onData(data => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'input', data }))
    }
  })

  // Keep the terminal sized to its container and tell the server.
  if (termRef.value) {
    resizeObserver = new ResizeObserver(() => refit())
    resizeObserver.observe(termRef.value)
  }
  refit()
  if (mirrorEnabled.value) {
    enterMirror()
  } else {
    connect()
  }
})

onBeforeUnmount(() => {
  if (mirrorUnsub) {
    mirrorUnsub()
    mirrorUnsub = null
  }
  resizeObserver?.disconnect()
  resizeObserver = null
  if (reconnectTimer) clearTimeout(reconnectTimer)
  reconnectTimer = null
  try { socket?.close() } catch { /* already closed */ }
  socket = null
  terminal?.dispose()
  terminal = null
  fitAddon = null
})
</script>

<style scoped>
.terminal-panel {
  --terminal-panel-border: color-mix(in srgb, var(--border) 70%, transparent);
  position: relative;
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg);
  border-top: 1px solid var(--terminal-panel-border);
  overflow: hidden;
}

.terminal-panel.is-resizing {
  cursor: row-resize;
  user-select: none;
}

/* Collapsed bar */
.terminal-panel__collapsed-bar {
  display: flex;
  align-items: center;
  height: 26px;
  padding: 0 var(--sp-2);
  border-top: 1px solid var(--terminal-panel-border);
  background: var(--bg);
}

.terminal-panel__toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  border: 0;
  background: transparent;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  padding: 2px var(--sp-2);
  border-radius: var(--radius-sm);
}
.terminal-panel__toggle:hover {
  background: var(--bg-hover);
  color: var(--text);
}

.terminal-panel__expand-chevron {
  transform: rotate(180deg);
}

/* Top resizer */
.terminal-panel__resizer {
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 5px;
  cursor: row-resize;
  z-index: 2;
  background: transparent;
  transition: background var(--dur-fast) var(--ease-standard);
}
.terminal-panel__resizer:hover,
.terminal-panel.is-resizing .terminal-panel__resizer {
  background: var(--accent);
}

/* Header */
.terminal-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  height: 28px;
  padding: 0 var(--sp-3);
  border-bottom: 1px solid var(--terminal-panel-border);
}

.terminal-panel__title {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

.terminal-panel__status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-dim);
}
.terminal-panel__status.is-connected {
  background: var(--ok);
}
.terminal-panel__status.is-connecting {
  background: var(--warn);
}
.terminal-panel__status.is-disconnected {
  background: var(--danger);
}

.terminal-panel__actions {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
}

.terminal-panel__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
}
.terminal-panel__action:hover {
  background: var(--bg-hover);
  color: var(--text);
}

/* AI mirror toggle: compact chip that lights up while mirror mode is active. */
.terminal-panel__mirror {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  height: 22px;
  padding: 0 var(--sp-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  transition: border-color var(--dur-fast) var(--ease-standard),
              background var(--dur-fast) var(--ease-standard),
              color var(--dur-fast) var(--ease-standard);
}
.terminal-panel__mirror:hover,
.terminal-panel__mirror:focus-visible {
  background: var(--bg-hover);
  border-color: var(--border-strong);
  color: var(--text);
  outline: none;
}
.terminal-panel__mirror.is-active {
  border-color: var(--accent);
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, var(--bg));
}
.terminal-panel__mirror-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.45;
}
.terminal-panel__mirror.is-active .terminal-panel__mirror-dot {
  opacity: 1;
  animation: terminal-mirror-pulse 1.6s var(--ease-standard) infinite;
}
@keyframes terminal-mirror-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* SSH host selector: compact toolbar chip that matches the 22px action row. */
.terminal-panel__ssh {
  max-width: 150px;
  height: 22px;
  padding: 0 var(--sp-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: border-color var(--dur-fast) var(--ease-standard),
              background var(--dur-fast) var(--ease-standard);
}
.terminal-panel__ssh:hover,
.terminal-panel__ssh:focus-visible {
  background: var(--bg-hover);
  border-color: var(--border-strong);
  outline: none;
}

/* Terminal body */
.terminal-panel__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  padding: 0 var(--sp-1) var(--sp-1);
}

.terminal-panel__body.is-hidden {
  height: 0;
  padding: 0;
}

.terminal-panel__term {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.terminal-panel__term :deep(.xterm) {
  height: 100%;
}

/* Hide entirely on phones — the mobile tab bar owns the bottom there. */
@media (max-width: 768px) {
  .terminal-panel {
    display: none;
  }
}
</style>

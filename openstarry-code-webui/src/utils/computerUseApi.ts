/** Computer-use live preview + WebUI theme sync HTTP client.
 *
 * Served by the gateway (same host, same auth rules as the rest of /api/*).
 * `GET /api/computer-use/state` is a read-only snapshot the preview modal
 * polls; `PUT /api/ui/theme` mirrors the WebUI theme onto the gateway config
 * so engine computer-use guidance and the MCP OSC_THEME env stay in sync.
 */

export type ComputerUseSessionStatus = 'active' | 'aborted' | 'idle'

export interface ComputerUseState {
  status: ComputerUseSessionStatus
  /** Raw base64 (or data URI) of the last screenshot; null when absent. */
  screenshot: string | null
  screenshotWidth: number | null
  screenshotHeight: number | null
  /** Virtual cursor position in screenshot pixel coordinates. */
  cursor: { x: number; y: number } | null
  lastAction: string | null
  updatedAt: string | null
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  try {
    const token = sessionStorage.getItem('opensquilla.wsToken') || ''
    if (token) headers['Authorization'] = `Bearer ${token}`
  } catch { /* storage unavailable */ }
  return headers
}

async function apiRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json() as { error?: string }
      detail = body.error || ''
    } catch { /* non-JSON error body */ }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function parseCursor(raw: Record<string, unknown>): { x: number; y: number } | null {
  const candidates: unknown[] = [
    raw.cursor,
    raw.virtual_cursor,
    raw.pointer,
  ]
  for (const candidate of candidates) {
    if (candidate && typeof candidate === 'object') {
      const obj = candidate as Record<string, unknown>
      const x = asNumber(obj.x)
      const y = asNumber(obj.y)
      if (x !== null && y !== null) return { x, y }
    }
  }
  const x = asNumber(raw.cursor_x)
  const y = asNumber(raw.cursor_y)
  return x !== null && y !== null ? { x, y } : null
}

function parseScreenshot(raw: Record<string, unknown>): {
  data: string | null
  width: number | null
  height: number | null
} {
  let data: string | null = null
  let width = asNumber(raw.screenshot_width) ?? asNumber(raw.width)
  let height = asNumber(raw.screenshot_height) ?? asNumber(raw.height)
  const value = raw.last_screenshot ?? raw.screenshot
  if (typeof value === 'string' && value) {
    data = value
  } else if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>
    data = typeof obj.base64 === 'string' ? obj.base64 : typeof obj.data === 'string' ? obj.data : null
    width = asNumber(obj.width) ?? width
    height = asNumber(obj.height) ?? height
  }
  return { data, width, height }
}

/** Normalize a gateway state payload; tolerant of missing/renamed fields. */
export function normalizeComputerUseState(raw: unknown): ComputerUseState {
  const body = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>
  const session = (body.session && typeof body.session === 'object'
    ? body.session
    : {}) as Record<string, unknown>
  const merged: Record<string, unknown> = { ...session, ...body }

  const rawStatus = String(merged.status ?? merged.session_status ?? 'idle').toLowerCase()
  const status: ComputerUseSessionStatus
    = rawStatus === 'active' || rawStatus === 'aborted' ? rawStatus : 'idle'

  const shot = parseScreenshot(merged)
  return {
    status,
    screenshot: shot.data,
    screenshotWidth: shot.width,
    screenshotHeight: shot.height,
    cursor: parseCursor(merged),
    lastAction: typeof merged.last_action === 'string' ? merged.last_action : null,
    updatedAt: typeof merged.updated_at === 'string' ? merged.updated_at : null,
  }
}

/** Full data URI for the normalized screenshot, or null when absent. */
export function screenshotDataUri(state: ComputerUseState): string | null {
  if (!state.screenshot) return null
  return /^data:image\//i.test(state.screenshot)
    ? state.screenshot
    : `data:image/png;base64,${state.screenshot}`
}

export function fetchComputerUseState(): Promise<ComputerUseState> {
  return apiRequest<unknown>('/api/computer-use/state', { headers: authHeaders() })
    .then(normalizeComputerUseState)
}

/** Fire-and-forget theme mirror; callers swallow failures (silent sync). */
export function putUiTheme(theme: string): Promise<{ theme: string }> {
  return apiRequest('/api/ui/theme', {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ theme }),
  })
}

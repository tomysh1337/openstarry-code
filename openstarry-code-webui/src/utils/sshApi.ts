/** SSH host configuration HTTP client for the settings panel and the
 * terminal panel's SSH selector.
 *
 * These endpoints are served by the gateway (same host, same auth rules as the
 * rest of /api/*). When an operator token exists it is forwarded so token-auth
 * mode works on desktop as well as on loopback. Config management only — the
 * endpoints never open SSH connections; terminal sessions with a host are
 * carried by the system ssh client over the builtin terminal WebSocket
 * (`/ws/builtin/terminal?ssh_host=<id>`).
 */

export interface SshHost {
  id: string
  name: string
  host: string
  port: number
  username: string
  enabled: boolean
}

export interface SshHostInput {
  name: string
  host: string
  port: number
  username?: string
  enabled: boolean
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  try {
    const token = sessionStorage.getItem('opensquilla.wsToken') || ''
    if (token) headers['Authorization'] = `Bearer ${token}`
  } catch { /* storage unavailable */ }
  return headers
}

async function sshRequest<T>(url: string, init?: RequestInit): Promise<T> {
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

export function fetchSshHosts(): Promise<{ hosts: SshHost[] }> {
  return sshRequest('/api/ssh/hosts', { headers: authHeaders() })
}

export function createSshHost(input: SshHostInput): Promise<SshHost> {
  return sshRequest('/api/ssh/hosts', {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function updateSshHost(id: string, input: SshHostInput): Promise<SshHost> {
  // Hand-authored TOML entries may lack an id; the API falls back to name.
  const key = encodeURIComponent(id || input.name)
  return sshRequest(`/api/ssh/hosts/${key}`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function deleteSshHost(id: string, fallbackName = ''): Promise<{ id: string; deleted: boolean }> {
  const key = encodeURIComponent(id || fallbackName)
  return sshRequest(`/api/ssh/hosts/${key}`, { method: 'DELETE', headers: authHeaders() })
}

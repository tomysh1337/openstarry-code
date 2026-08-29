/** FTP host configuration HTTP client for the settings panel.
 *
 * These endpoints are served by the gateway (same host, same auth rules as
 * the rest of /api/*) and mirror the SSH host client. Config management only —
 * the endpoints never open FTP connections; browsing is carried by stdlib
 * ftplib in the IDE panel's remote tab (`/api/remote/*`).
 */

export interface FtpHost {
  id: string
  name: string
  host: string
  port: number
  username: string
  password: string
  tls: boolean
  enabled: boolean
}

export interface FtpHostInput {
  name: string
  host: string
  port: number
  username?: string
  password?: string
  tls?: boolean
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

async function ftpRequest<T>(url: string, init?: RequestInit): Promise<T> {
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

export function fetchFtpHosts(): Promise<{ hosts: FtpHost[] }> {
  return ftpRequest('/api/ftp/hosts', { headers: authHeaders() })
}

export function createFtpHost(input: FtpHostInput): Promise<FtpHost> {
  return ftpRequest('/api/ftp/hosts', {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function updateFtpHost(id: string, input: FtpHostInput): Promise<FtpHost> {
  // Hand-authored TOML entries may lack an id; the API falls back to name.
  const key = encodeURIComponent(id || input.name)
  return ftpRequest(`/api/ftp/hosts/${key}`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function deleteFtpHost(id: string, fallbackName = ''): Promise<{ id: string; deleted: boolean }> {
  const key = encodeURIComponent(id || fallbackName)
  return ftpRequest(`/api/ftp/hosts/${key}`, { method: 'DELETE', headers: authHeaders() })
}

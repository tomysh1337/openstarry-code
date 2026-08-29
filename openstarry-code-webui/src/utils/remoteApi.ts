/** Remote file browsing HTTP client for the right-hand "code interpreter"
 * panel's Remote tab.
 *
 * Read-only endpoints served by the gateway (same host, same auth rules as
 * the rest of /api/*). The Remote tab picks a transport (ssh / ftp / wsl /
 * mcp / git) and a configured server, then browses its file tree and views
 * file contents through these endpoints.
 */

export type RemoteType = 'ssh' | 'ftp' | 'wsl' | 'mcp' | 'git'

export interface RemoteSshSource {
  id: string
  name: string
  host: string
  port: number
  username: string
}

export interface RemoteFtpSource {
  id: string
  name: string
  host: string
  port: number
  username: string
  tls: boolean
}

export interface RemoteWslSource {
  id: string
  name: string
}

export interface RemoteMcpSource {
  id: string
  name: string
  transport: string
}

export interface RemoteGitSource {
  id: string
  name: string
  path: string
}

export interface RemoteSourcesResponse {
  ssh: RemoteSshSource[]
  ftp: RemoteFtpSource[]
  wsl: RemoteWslSource[]
  mcp: RemoteMcpSource[]
  git: RemoteGitSource[]
}

export interface RemoteTreeEntry {
  name: string
  path: string
  type: 'dir' | 'file'
  size?: number
  language?: string | null
}

export interface RemoteTreeResponse {
  path: string
  entries: RemoteTreeEntry[]
}

export interface RemoteFileResponse {
  path: string
  name: string
  content?: string
  language?: string | null
  size?: number
  truncated?: boolean
  binary?: boolean
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  try {
    const token = sessionStorage.getItem('opensquilla.wsToken') || ''
    if (token) headers['Authorization'] = `Bearer ${token}`
  } catch { /* storage unavailable */ }
  return headers
}

async function remoteFetch<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: authHeaders() })
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

export function fetchRemoteSources(): Promise<RemoteSourcesResponse> {
  return remoteFetch('/api/remote/sources')
}

export function fetchRemoteTree(type: RemoteType, id: string, dirPath: string): Promise<RemoteTreeResponse> {
  const query = new URLSearchParams({ type, id })
  if (dirPath) query.set('path', dirPath)
  return remoteFetch(`/api/remote/tree?${query.toString()}`)
}

export function fetchRemoteFile(type: RemoteType, id: string, filePath: string): Promise<RemoteFileResponse> {
  const query = new URLSearchParams({ type, id, path: filePath })
  return remoteFetch(`/api/remote/file?${query.toString()}`)
}

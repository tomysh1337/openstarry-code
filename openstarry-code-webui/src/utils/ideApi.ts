/** IDE panel HTTP client for the right-hand "code interpreter" panel.
 *
 * These endpoints are served by the gateway (same host, same auth rules as the
 * rest of /api/*). When an operator token exists it is forwarded so the
 * token-auth mode works on desktop as well as on loopback.
 */

export interface IdeRootResponse {
  name: string
  path: string
  platform: string // "nt" | "posix"
}

export interface IdeTreeEntry {
  name: string
  path: string
  type: 'dir' | 'file'
  size?: number
  language?: string | null
}

export interface IdeTreeResponse {
  path: string
  entries: IdeTreeEntry[]
}

export interface IdeFileResponse {
  path: string
  name: string
  content?: string
  language?: string | null
  size?: number
  truncated?: boolean
  binary?: boolean
}

export interface IdeHandoffResponse {
  path: string
  name: string
  content: string
}

export interface IdeChangeFile {
  path: string
  mtime: number
  size: number
}

export interface IdeChangesResponse {
  files: IdeChangeFile[]
  serverTime: number
}

export interface IdeDiffEntry {
  type: 'context' | 'add' | 'mod'
  line: string
}

export interface IdeDiffResponse {
  path: string
  has_changes: boolean
  entries: IdeDiffEntry[]
  summary: { added: number; modified: number; removed: number }
}

export interface IdeMutateResponse {
  path: string
  name: string
  type?: 'file' | 'dir'
  previousPath?: string
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {}
  try {
    const token = sessionStorage.getItem('opensquilla.wsToken') || ''
    if (token) headers['Authorization'] = `Bearer ${token}`
  } catch { /* storage unavailable */ }
  return headers
}

async function ideFetch<T>(url: string): Promise<T> {
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

async function idePost<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = ''
    try {
      const errBody = await res.json() as { error?: string }
      detail = errBody.error || ''
    } catch { /* non-JSON error body */ }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function fetchIdeRoot(): Promise<IdeRootResponse> {
  return ideFetch('/api/ide/root')
}

export function fetchIdeTree(dirPath: string): Promise<IdeTreeResponse> {
  const query = dirPath ? `?path=${encodeURIComponent(dirPath)}` : ''
  return ideFetch(`/api/ide/tree${query}`)
}

export function fetchIdeFile(filePath: string): Promise<IdeFileResponse> {
  return ideFetch(`/api/ide/file?path=${encodeURIComponent(filePath)}`)
}

export function fetchIdeHandoff(): Promise<IdeHandoffResponse> {
  return ideFetch('/api/ide/handoff')
}

export function fetchIdeChanges(since: number): Promise<IdeChangesResponse> {
  return ideFetch(`/api/ide/changes?since=${encodeURIComponent(String(since))}`)
}

export function fetchIdeDiff(filePath: string): Promise<IdeDiffResponse> {
  return ideFetch(`/api/ide/diff?path=${encodeURIComponent(filePath)}`)
}

export function createIdeEntry(parentPath: string, name: string, type: 'file' | 'dir'): Promise<IdeMutateResponse> {
  return idePost('/api/ide/create', { path: parentPath, name, type })
}

export function renameIdeEntry(path: string, name: string): Promise<IdeMutateResponse> {
  return idePost('/api/ide/rename', { path, name })
}

export function deleteIdeEntry(path: string): Promise<IdeMutateResponse> {
  return idePost('/api/ide/delete', { path })
}

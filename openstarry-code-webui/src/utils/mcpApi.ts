/** MCP server configuration HTTP client for the settings panel.
 *
 * These endpoints are served by the gateway (same host, same auth rules as the
 * rest of /api/*). When an operator token exists it is forwarded so token-auth
 * mode works on desktop as well as on loopback. Config management only — the
 * endpoints never open MCP protocol connections.
 */

export type McpTransport = 'stdio' | 'http'

export interface McpServer {
  id: string
  name: string
  transport: McpTransport
  command: string | null
  args: string[]
  env: Record<string, string>
  url: string | null
  enabled: boolean
}

export interface McpServerInput {
  name: string
  transport: McpTransport
  command?: string
  args?: string[]
  env?: Record<string, string>
  url?: string
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

async function mcpRequest<T>(url: string, init?: RequestInit): Promise<T> {
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

export function fetchMcpServers(): Promise<{ servers: McpServer[] }> {
  return mcpRequest('/api/mcp/servers', { headers: authHeaders() })
}

export function createMcpServer(input: McpServerInput): Promise<McpServer> {
  return mcpRequest('/api/mcp/servers', {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function updateMcpServer(id: string, input: McpServerInput): Promise<McpServer> {
  // Hand-authored TOML entries may lack an id; the API falls back to name.
  const key = encodeURIComponent(id || input.name)
  return mcpRequest(`/api/mcp/servers/${key}`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function deleteMcpServer(id: string, fallbackName = ''): Promise<{ id: string; deleted: boolean }> {
  const key = encodeURIComponent(id || fallbackName)
  return mcpRequest(`/api/mcp/servers/${key}`, { method: 'DELETE', headers: authHeaders() })
}

// Normalize a gateway WebSocket URL. Operators routinely paste just the
// host:port (`ws://127.0.0.1:18791` or with a trailing `/`), but the gateway
// socket endpoint always lives at the /ws path — the main RPC socket at /ws
// and the built-in terminal at /ws/builtin/terminal. Append the missing path
// so a host-only URL connects instead of 404ing.
export function normalizeWsUrl(raw: string): string {
  const url = raw.trim()
  if (!url) return url
  try {
    const parsed = new URL(url)
    if (parsed.pathname === '' || parsed.pathname === '/') {
      parsed.pathname = '/ws'
      // URL.toString() renders `ws://host:port/ws` — no trailing slash —
      // which is exactly the shape the gateway routes expect.
      return parsed.toString()
    }
  } catch {
    // Not a parseable absolute URL — leave it untouched; the connection
    // error surfaced by the settings panel is the clearer signal.
  }
  return url
}

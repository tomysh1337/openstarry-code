---
name: websocket-client-patterns
description: >
  Design robust WebSocket clients: lifecycle, auth, reconnect/backoff,
  heartbeats, message typing, backpressure, and shutdown. Use when building or
  reviewing browser/native WS clients, realtime feeds, or chat sockets. Not
  primary for CSWSH testing (websocket-security) or binary codec RE.
---

# WebSocket Client Patterns

Engineering design for **operable WebSocket clients**: open, authenticate, stay
healthy, recover, validate messages, and tear down without leaks. Prefer the
repo’s shared socket helpers and schemas over ad-hoc `new WebSocket` per feature.

## Use When

- Implementing or reviewing `WebSocket` / `ws` / socket.io / custom realtime clients
- Designing reconnect, heartbeat/ping, auth ticket, and resubscribe after connect
- Fixing duplicate events, zombie sockets, racey open/close, or unbounded send queues
- Choosing envelopes (JSON, binary, multiplexed channels) on the **client** side
- Mentions: WebSocket client, reconnect, heartbeat, WSS client, socket lifecycle

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized Origin/CSWSH/message authz testing | `websocket-security` |
| Binary frame/opcode reverse engineering | `websocket-binary-reverse-engineering` |
| Shared HTTP-style retry budgets | `retry-backoff-patterns` |
| CSP `connect-src` blocking WSS | `content-security-policy-bypass` |
| General reliability, bounds, tests | `code-quality-standards` |

## Repo Config First

Repo libraries and protocol docs **outrank** defaults below.

1. **Existing clients:** shared `RealtimeClient` / socket.io managers — extend them
2. **Auth model:** cookie upgrade, first-message token, short-lived HTTP ticket, mTLS
3. **URLs/env:** `wss://` per environment; feature flags; no hardcoded prod hosts
4. **Message contract:** schemas, version fields, ack/nack rules
5. **Observability:** connection state, reconnect counts, close codes
6. **CSP:** browser `connect-src` must allow the WSS origin
7. **Neighbors:** copy 2–3 mature open → auth → subscribe → teardown sequences

**Precedence:** Follow repo security rules. Surface cleartext `ws://` for sensitive
data, secrets in query strings, or infinite reconnect without budget.

## Workflow

1. **Contract:** URL, subprotocol, auth timing, message types, failure modes.
2. **Single owner** per session/tab — UI listens to a bus/store, not raw sockets.
3. **State machine:** `idle → connecting → open → authenticating → ready →
   closing → closed` (+ `reconnecting`). Auth failure is terminal until re-login.
4. **Auth safely:** ticket from same-origin HTTPS; avoid long-lived tokens in query.
5. **Heartbeat** if proxies kill idle TCP; honor server close codes.
6. **Reconnect:** exponential backoff + jitter + max budget; resubscribe after `ready`.
7. **Validate inbound** (size + schema); dispatch by type; unknown types safe.
8. **Bound outbound** queues; backpressure or drop-with-metric when not open.
9. **Shutdown:** clear timers, remove listeners, `close(1000)`, abort reconnect on
   logout/unmount/`AbortSignal`.
10. **Test** auth fail, drop+reconnect, double-subscribe, teardown, malformed frames.

## Good / Bad Examples

**Good — single owner, abortable teardown**

```ts
class RealtimeClient {
  private ws?: WebSocket;
  private disposed = false;
  async connect(ticket: string, signal: AbortSignal) {
    const ws = new WebSocket(urlFromEnv()); // wss from config
    this.ws = ws;
    ws.onopen = () => ws.send(JSON.stringify({ type: "auth", ticket }));
    ws.onmessage = (ev) => this.onMessage(ev.data);
    ws.onclose = (ev) => this.scheduleReconnect(ev, signal);
    signal.addEventListener("abort", () => this.dispose());
  }
  dispose() {
    this.disposed = true;
    clearTimeout(this.timer);
    this.ws?.close(1000, "dispose");
    this.ws = undefined;
  }
}
```

**Bad:** `new WebSocket` in every component; no cleanup; infinite reconnect after logout.

**Good — boundary parse**

```ts
function onMessage(raw: string) {
  if (raw.length > MAX) return metrics.oversize++;
  const msg = schema.parse(JSON.parse(raw));
  if (msg.type === "event") bus.emit(msg);
  else if (msg.type === "error") handleServerError(msg);
  else metrics.unknownType++;
}
```

**Bad:** secrets in `wss://host?token=...`; `eval(raw)`; unbounded multi‑MB parse;
blind reconnect on auth close without re-auth UI.

## Anti-Patterns

- Multiple sockets for the same session/server; handlers left on closed sockets
- Reconnect without jitter (thundering herd) or without budget
- Fire-and-forget sends while `CONNECTING` with unbounded queue
- Treating WS as idempotent HTTP without acks
- Masking CSP `connect-src` failures as “random network errors”

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Client lifecycle, reconnect, heartbeats, envelopes | **This skill** | — |
| Authorized Origin/CSWSH/message IDOR testing | `websocket-security` | this when fixing client auth |
| Bounds, validation, errors, tests | `code-quality-standards` | **always** on implementation |
| CSP blocks WSS / `connect-src` | `content-security-policy-bypass` | this for connect behavior |
| Binary codec recovery | `websocket-binary-reverse-engineering` | this after codec known |

Keep **this skill primary** for client design. Always apply
**`code-quality-standards`**. Hand CSWSH/Origin assessment to
**`websocket-security`** (authorized only). Inventory CSP with
**`content-security-policy-bypass`** when browsers refuse connect.

## Checklist

- [ ] Repo helpers, schemas, env URLs, ticket/auth flow inventoried
- [ ] Single connection owner; state machine documented
- [ ] `wss://` for sensitive data; no long-lived secrets in query strings
- [ ] Auth terminal on failure; heartbeat; reconnect backoff + jitter + budget
- [ ] Inbound size/schema bounds; outbound queue bounded; clean dispose
- [ ] Metrics: opens, close codes, reconnects, parse errors (no secrets)
- [ ] Tests: auth fail, reconnect, teardown, malformed frame
- [ ] `code-quality-standards` applied
- [ ] CSP `connect-src` OK (`content-security-policy-bypass` if blocked)
- [ ] Assessment of Origin/CSWSH routed to `websocket-security` when testing

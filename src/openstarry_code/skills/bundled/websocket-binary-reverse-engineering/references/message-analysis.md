# WebSocket Message Analysis

## Boundary Checks

- Reassemble TCP before WebSocket.
- Reassemble continuation frames before application decoding.
- Apply negotiated `permessage-deflate` before codec detection.
- Client masking belongs to WebSocket framing and is not application encryption.
- Multiple application records may share one WebSocket message; one record may also span messages.

## Useful Comparisons

- Same action, new session: identify session IDs, timestamps, nonces, and counters.
- Different action, same session: identify opcode and payload fields.
- Same action, one changed input: establish field semantics.
- Idle connection: identify heartbeat and server push behavior.
- Disconnect/reconnect: identify resume tokens, sequence recovery, and subscription replay.

## State Model

Document states and evidence for transitions such as connect, authenticate, subscribe, ready, request, acknowledgement, push, retry, resume, and close. Do not infer a transition from a single packet when an asynchronous push is also plausible.

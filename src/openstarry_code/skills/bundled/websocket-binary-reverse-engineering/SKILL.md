---
name: websocket-binary-reverse-engineering
description: Recover binary application protocols carried over WebSocket from PCAPs, browser traces, proxy exports, or runtime logs. Use when WebSocket opcode 2 frames are opaque, messages are fragmented, payloads use Protobuf, MessagePack, CBOR, compression, encryption, custom envelopes, heartbeats, sequence numbers, or undocumented request/response state transitions.
---

# WebSocket Binary Reverse Engineering

## Workflow

1. Preserve the HTTP upgrade request and response, negotiated subprotocol, extensions, cookies, and origin.
2. Reassemble fragmented WebSocket messages. Do not treat individual TCP packets or continuation frames as application messages.
3. Separate control frames from business messages: ping, pong, close, and protocol heartbeats are different layers.
4. Record a timeline with direction, opcode, message length, first bytes, and the user action that caused it.
5. Identify the outer envelope before the body codec: magic, version, flags, opcode, request ID, sequence, length, checksum, compression, and encryption markers.
6. Test common body formats with evidence: JSON, Protobuf, MessagePack, CBOR, BSON, FlatBuffers, or a custom binary layout.
7. Vary one application input at a time and compare messages across multiple sessions.
8. Infer request/response pairs, unsolicited pushes, acknowledgements, retries, heartbeats, and reconnect/resume behavior.
9. Validate by writing a passive decoder first. Replay or mutation requires explicit authorization and a controlled environment.

Read `references/message-analysis.md` for framing and state-machine checks.

## Evidence Standard

Produce the upgrade metadata, reconstructed message set, codec evidence, field table, state diagram, passive decoder/dissector, and redacted examples. Mark field semantics as observed, code-backed, controlled-test-backed, or speculative.

Route Protobuf bodies to `protobuf-grpc-reverse-engineering` and TLS visibility problems to `tls-plaintext-acquisition`.

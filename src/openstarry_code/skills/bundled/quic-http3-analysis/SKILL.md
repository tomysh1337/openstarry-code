---
name: quic-http3-analysis
description: Capture, decrypt, and analyze QUIC and HTTP/3 traffic using endpoint key logs, qlog, PCAP, Wireshark, and implementation traces. Use when traffic is UDP-based and encrypted, ALPN is h3, connection IDs replace stable five-tuples, HTTP/3 streams use QPACK, connection migration occurs, or TCP/TLS-oriented capture methods show only opaque packets.
---

# QUIC And HTTP/3 Analysis

## Workflow

1. Confirm QUIC by version, long-header packets, UDP flow behavior, and ALPN when available.
2. Capture PCAP and endpoint diagnostics from process start. Passive PCAP alone generally cannot reveal application plaintext.
3. Prefer endpoint key logs and qlog. Record the implementation and version: Chromium/Cronet, quiche, msquic, ngtcp2, aioquic, or another stack.
4. Load secrets into Wireshark and verify Initial, Handshake, 0-RTT, and 1-RTT packet visibility as applicable.
5. Track connection IDs rather than relying only on IP and port tuples.
6. Map bidirectional and unidirectional streams, HTTP/3 control streams, QPACK encoder/decoder streams, and request streams.
7. Correlate headers and data with user actions. Account for multiplexing, retransmission at the QUIC layer, and connection migration.
8. Export decrypted application bodies and route them to the relevant codec skill.

Read `references/quic-evidence.md` for required artifacts and common traps.

## Output

Produce implementation/version, capture method, key-log or qlog provenance, connection-ID timeline, stream map, HTTP/3 request table, migration or 0-RTT observations, decrypted body artifacts, and unresolved visibility gaps.

Do not claim that UDP payload entropy proves custom encryption; QUIC encrypts most transport metadata and all application data after the Initial keys phase.

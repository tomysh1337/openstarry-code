---
name: tls-plaintext-acquisition
description: Select and validate the least invasive method for obtaining TLS plaintext from owned or explicitly authorized applications. Use when proxy capture is empty, certificate trust fails, SSL pinning is suspected, the app uses native BoringSSL/OpenSSL, mTLS is present, HTTP/2 or HTTP/3 remains encrypted, or PCAP alone only reveals metadata.
---

# TLS Plaintext Acquisition

## Workflow

1. Confirm the authorized process, device, time window, and expected user action.
2. Capture a short baseline PCAP before changing trust or runtime behavior.
3. Identify the network stack: browser, system TLS, Java/OkHttp, native OpenSSL/BoringSSL, Flutter, Cronet, QUIC, or custom transport.
4. Choose the first viable method from the matrix in `references/capture-layer-matrix.md`.
5. Capture plaintext and network traffic concurrently with timestamps and an operation marker.
6. Validate both directions, message completeness, process attribution, and correspondence with the baseline connection.
7. Record limitations such as missing early handshakes, child processes, compression, mTLS, or unsupported TLS libraries.

## Method Order

Prefer methods in this order:

1. Application-supported key logging or debug export.
2. `SSLKEYLOGFILE`, browser/Chromium key logs, qlog, or framework diagnostics.
3. Debug proxy with a trusted test CA for applications designed to support it.
4. TLS-library boundary capture such as eBPF uprobes/eCapture or known read/write hooks.
5. Targeted runtime instrumentation at the verified validation or plaintext boundary.
6. Repackaging or binary patching only when the authorized test requires it and reversible alternatives failed.

Do not start with a universal bypass script. First prove which TLS implementation and validation path the process actually uses.

## Evidence

Produce:

- Baseline PCAP and capture filter.
- Plaintext log or key log with timestamps.
- Process, PID, library, and function boundary used.
- One user action mapped to request and response.
- Redacted note covering tokens, cookies, client certificates, and device identifiers.
- A clear statement of what remains encrypted or unattributed.

Route decoded Protobuf/gRPC to `protobuf-grpc-reverse-engineering`, binary WebSocket payloads to `websocket-binary-reverse-engineering`, and QUIC/HTTP/3 streams to `quic-http3-analysis`.

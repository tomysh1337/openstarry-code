# TLS Capture Layer Matrix

| Observation | Best first method | What it proves | Common failure |
| --- | --- | --- | --- |
| Chromium/browser traffic | `SSLKEYLOGFILE` plus PCAP | Session secrets and exact network flow | Browser launched before variable was set |
| Debuggable app trusts test CA | Explicit proxy | HTTP semantics and easy modification | Pinning or native stack ignores system proxy |
| Java/OkHttp app rejects proxy | Identify pinner and trust manager | Validation path | Hook signature or class loader mismatch |
| Native OpenSSL/BoringSSL traffic | Library-boundary capture or uprobes | Plaintext before encryption/after decryption | Stripped/static library or unsupported ABI |
| Flutter/Cronet/QUIC | Endpoint key log, qlog, or native boundary | Multiplexed stream plaintext | Java hooks never see the traffic |
| PCAP shows TLS but no HTTP | Key log or endpoint instrumentation | Whether payload is HTTP, gRPC, WebSocket, or custom | Wrong process or missing early secrets |
| mTLS handshake fails | Authorized client-certificate diagnostics | Client identity selection and chain | Exporting private material unnecessarily |

Always pair plaintext collection with a PCAP or connection metadata. A plaintext log without process and flow correlation is not sufficient evidence.

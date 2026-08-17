# QUIC Evidence Checklist

- Original PCAP or pcapng with interface and clock details.
- Endpoint key log and qlog captured from process start when supported.
- QUIC implementation, application version, platform, and process identity.
- QUIC version, ALPN, server name when visible, and connection IDs.
- Stream IDs with direction and stream type.
- HTTP/3 headers after QPACK decoding and exported body bytes.
- Evidence of retry, version negotiation, 0-RTT, migration, path validation, or stateless reset when relevant.

## Common Traps

- Treating each UDP datagram as one application message.
- Grouping only by five-tuple and losing migrated connections.
- Confusing QUIC packet numbers with application sequence numbers.
- Expecting `SSLKEYLOGFILE` support from every QUIC implementation.
- Starting endpoint logging after the handshake and missing required secrets.
- Interpreting QPACK-compressed header blocks without the associated control streams.

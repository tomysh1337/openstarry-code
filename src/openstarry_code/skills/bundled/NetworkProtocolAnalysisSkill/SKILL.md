---
name: NetworkProtocolAnalysisSkill
description: >
  Capture and analyze network traffic with PCAP, tshark/Wireshark, Lua dissectors,
  Scapy crafting, state-machine recovery, debugging, and authorized fuzzing. Use
  for pcap triage, custom dissectors, packet reproduction, and controlled protocol
  testing on owned or authorized targets.
---

# Network Protocol Analysis

## When To Use

- PCAP/PCAPNG triage and stream reassembly
- Writing or debugging Wireshark/tshark Lua dissectors
- Crafting or replaying packets with Scapy (authorized)
- Mapping message sequences / simple state machines from captures
- Authorized fuzzing with boofuzz or similar

If the protocol schema is unknown and you need recovery methodology, primary skill is `protocol-reverse-engineering`; this skill supplies capture and tooling.

## Prerequisites

| Tool | Role |
| --- | --- |
| Wireshark / tshark | Dissection, filters, export |
| tcpdump | Capture |
| Scapy | Craft / mutate (authorized) |
| boofuzz (optional) | Authorized fuzzing |
| Python 3 | Scripts and dissectors |

## Workflow

1. **Authorize and baseline**
   - Confirm ownership/authorization for capture and any replay/fuzz.
   - Capture a short baseline with a clear user-action marker and timestamp.

2. **Triage the PCAP**
   - Identify L3/L4, TLS vs cleartext, HTTP/2/3, WebSocket upgrades, custom ports.
   - List conversations and top talkers (`tshark -q -z conv,tcp` style summaries).
   - Export relevant streams only; keep full PCAP immutable.

3. **Reassemble application messages**
   - Do not treat TCP segments as application messages.
   - For TLS, obtain plaintext via `tls-plaintext-acquisition` first.
   - For gRPC/Protobuf/WebSocket/QUIC, hand off body work to the matching codec skill after framing is clear.

4. **Dissector path (when format is partially known)**
   - Start with display filters and manual field notes.
   - Implement a minimal Lua (or Wireshark plugin) dissector for fixed headers first.
   - Validate against multiple sessions; fix length and endianness bugs before semantics.

5. **Craft / replay (authorized only)**
   - Reproduce one known-good message with Scapy or a small script.
   - Change one field at a time; record server/client reaction.

6. **Fuzz (authorized, isolated only)**
   - Prefer isolated lab (`security-sandbox`).
   - Bound mutations; monitor crash/log artifacts; never fuzz production without explicit approval.

## Output Checklist

- [ ] Capture filter, interface, time window, action marker
- [ ] Conversation summary and selected stream IDs
- [ ] Message boundary rules (length prefix, delimiter, fixed size)
- [ ] Field table with evidence (observed / controlled-test / speculative)
- [ ] Dissector or decoder path (if any)
- [ ] Redacted examples only

## Routing Out

| Observation | Next skill |
| --- | --- |
| Still encrypted TLS | `tls-plaintext-acquisition` |
| Protobuf/gRPC bodies | `protobuf-grpc-reverse-engineering` |
| Binary WebSocket | `websocket-binary-reverse-engineering` |
| QUIC/HTTP3 | `quic-http3-analysis` |
| Proprietary state machine | `protocol-reverse-engineering` |
| Logic only in binary | `binary-re` |

## Rules

- No live interception, replay, or fuzz without clear authorization.
- Do not invent exploit chains from PCAP alone.
- Redact secrets from reports and example packets.

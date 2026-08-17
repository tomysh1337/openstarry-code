---
name: protobuf-grpc-reverse-engineering
description: Recover and validate unknown Protobuf, gRPC, and gRPC-Web message structures from captures, application assets, binaries, or runtime traces. Use when payloads contain Protobuf wire data, `application/grpc`, `application/grpc-web+proto`, five-byte gRPC frames, length-prefixed messages, generated descriptor blobs, or `protoc --decode_raw` output without a schema.
---

# Protobuf And gRPC Reverse Engineering

## Workflow

1. Remove transport framing before interpreting Protobuf fields.
2. Determine whether the input is raw Protobuf, gRPC, gRPC-Web binary, gRPC-Web text/base64, or an application envelope.
3. Run `scripts/protobuf_wire_probe.py` on several complete messages.
4. Search client assets and binaries for `.proto` names, generated message classes, field constants, `FileDescriptorSet`, reflection endpoints, and serialized descriptor blobs.
5. Build a sample matrix: operation, direction, message length, stable fields, changed fields, and candidate meaning.
6. Infer field numbers and wire types first. Assign semantic names only after controlled input changes or code evidence.
7. Write the smallest candidate `.proto`, decode all samples, re-encode known messages, and compare bytes.
8. Document uncertainty, defaults, oneof/repeated ambiguity, packed fields, maps, and nested-message alternatives.

## gRPC Framing

A gRPC message starts with one compression byte and a four-byte big-endian message length. HTTP/2 stream frames are not message boundaries. Reassemble the stream before splitting gRPC messages.

For gRPC-Web, account for base64 text mode and trailer frames. Do not treat trailers or the five-byte prefix as Protobuf fields.

## Validation Standard

Accept a schema hypothesis only when:

- It decodes multiple messages in both directions without truncation.
- Length-delimited boundaries remain valid.
- A controlled input change affects the predicted field.
- Re-encoding preserves semantically relevant bytes or explains canonicalization differences.
- The inferred message fits the observed request/response state transition.

Read `references/wire-format-notes.md` when field types or nested boundaries are ambiguous.

## Output

Produce a framing description, candidate `.proto`, evidence table, decoder command or script, redacted examples, and a confidence label for each semantic field.

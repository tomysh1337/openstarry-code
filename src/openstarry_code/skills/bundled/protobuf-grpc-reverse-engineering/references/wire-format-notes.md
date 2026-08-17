# Protobuf Wire Notes

- Key: `(field_number << 3) | wire_type` encoded as a varint.
- Wire type 0: varint. Candidate types include integers, booleans, enums, and zigzag integers.
- Wire type 1: 64-bit fixed value. Candidate types include fixed64, sfixed64, and double.
- Wire type 2: length-delimited. Candidate types include strings, bytes, nested messages, packed repeated values, and maps.
- Wire type 5: 32-bit fixed value. Candidate types include fixed32, sfixed32, and float.
- UTF-8 validity is evidence for a string, not proof.
- Successful recursive decoding is evidence for a nested message, not proof; arbitrary bytes can look valid.
- Repeated appearances of the same field may be repeated values, map entries, or concatenated singular messages.
- Missing fields may be absent defaults. Field order is not a semantic contract.
- Use generated code or descriptors to resolve `oneof`, enum names, packed encoding, and signedness whenever possible.

---
name: vmp-3x-native-deobfuscation
description: "Triage and analyze suspected VMProtect 3.0-3.5 native virtualization with staged static inspection, IDA debugger traces, and controlled dynamic execution. Use MogVMP as a reference for VM handler and dispatcher analysis; preserve evidence and avoid blind transformations."
description_zh: "针对疑似 VMProtect 3.0-3.5 native 虚拟化进行分阶段静态检查、IDA 调试器跟踪和受控动态执行；以 MogVMP 的 VM handler/dispatcher 分析作为参考，保留证据并避免盲目变换。"
triggers:
  - "VMP 3.0"
  - "VMP 3.5"
  - "VMProtect 反混淆"
  - "MogVMP"
  - "native virtualization"
provenance:
  origin: openstarry-code
  license: Apache-2.0
  maintained_by: OpenStarry Code contributors
metadata:
  opensquilla:
    risk: high
    capabilities: [filesystem-read, filesystem-write, process-control]
    requires_tools:
      - exec_command
      - read_file
    requires:
      bins:
        - strings
        - file
        - ida
        - debugger
        - dynamic-sandbox
        - python
---

# VMP 3.x Native Deobfuscation

Reference implementation and research notes: [MogVMP](https://github.com/eversinc33/MogVMP).
Treat its signatures and terminology as hypotheses; confirm them against the
sample's imports, sections, dispatcher behavior, and runtime trace.

## Preserve and fingerprint

Hash the original and create `00-original/`, `01-fingerprint/`, `10-ida/`,
`20-traces/`, `30-recovered/`, and `reports/`. Record PE headers, section
permissions, TLS callbacks, imports, relocations, unusual exception handlers,
VM entry candidates, and packed/virtualized regions. Keep unpacked or dumped
images as separate artifacts with their provenance.

## Static then dynamic loop

1. Locate likely VM entry stubs, dispatcher loops, handler tables, context
   structures, virtual instruction fetch/decode, and exits. Compare control
   flow and constants with MogVMP concepts, but do not label a region solely
   from a byte pattern.
2. In IDA, name only evidence-backed structures and record file offset, RVA,
   module base, register state, and xrefs. Use a debugger to trace a single
   input through the dispatcher and several handlers; log transitions rather
   than dumping uncontrolled process state.
3. Replay the same input in a dynamic sandbox. Correlate trace events with the
   static graph and mark stable handler semantics. Use snapshots and a clean
   copy for every experiment.
4. Recover one narrow routine at a time into pseudocode or an intermediate
   representation. Validate equivalence on a fixture before attempting a
   second routine. Retain opaque blocks and failed hypotheses in the report.

## Completion evidence

Deliver hashes, VMP version hypothesis and confidence, IDA database notes,
debugger/sandbox traces, recovered handler map, input/output fixtures, and a
list of unresolved virtual instructions. Do not claim full devirtualization
without replay evidence for the relevant execution path.

---
name: native-residue-triage
description: "After an initial reverse-engineering pass, detect and classify native residue such as signed -3###### constants, 0x###### addresses, RVA/VA offsets, JNI pointers, and embedded native modules, then validate candidates with static analysis and an IDA debugger or dynamic sandbox."
description_zh: "初步分析后检查 -3######、0x######、RVA/VA 偏移、JNI 指针及嵌入 native 模块等残留，区分普通常量与真实地址，再用静态分析、IDA 调试器或动态沙盒验证。"
triggers:
  - "native 残留"
  - "扫描 0x 地址"
  - "扫描 -3######"
  - "JNI 指针分析"
  - "native residue"
  - "RVA triage"
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
        - rg
        - objdump
        - readelf
        - ida
        - debugger
        - dynamic-sandbox
---

# Native Residue Triage

Run this immediately after the initial static pass for an executable, library,
JAR containing native payloads, Android package, or mixed-language project.

## Scan and classify

1. Preserve the sample and hash it. Extract archives and list PE/ELF/Mach-O,
   `.so`, `.dll`, `.dylib`, JNI declarations, and load paths.
2. Search source, strings, disassembly, and logs for signed decimal patterns
   matching `-3######` and hexadecimal patterns matching `0x######` (also
   uppercase and 64-bit variants). Save file, section, line/offset, encoding,
   and nearby bytes to `reports/native-residue.csv`.
3. Classify each hit as ordinary data, serialized protocol value, file offset,
   RVA/VA, pointer table entry, switch value, JNI method pointer, or probable
   obfuscation residue. A number is an address candidate only when section
   ranges, relocations, architecture, and a reference agree.

## Static-to-dynamic validation

For each high-confidence candidate, map file offset to RVA/VA using the load
segment and image base. In IDA, create a named evidence bookmark and inspect
cross-references, callers, register/stack inputs, and the first decisive write
or return. Attach an IDA debugger trace or a sandbox trace showing module base,
runtime address, input, output, and thread. Do not patch while classifying.

For JNI, correlate `Java_*` exports or `RegisterNatives` entries with the
managed declaration and ABI. For packed/virtualized modules, hand off to
`vmp-3x-native-deobfuscation` rather than treating every constant as a VMP
marker.

## Report

Produce a table with `artifact, section, file_offset, rva_or_va, pattern,
classification, xrefs, runtime_observation, confidence, next_action`. Include
false positives and the exact scan command so another agent can replay it.

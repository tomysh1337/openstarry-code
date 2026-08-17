---
name: android-reverse-engineering-complete
description: "End-to-end Android reverse-engineering workflow for APK/AAB/XAPK/AAR artifacts: framework fingerprinting, DEX/Java/Kotlin static analysis, Recaf and enigma-mcp coordination, JNI/ELF native tracing, dynamic sandbox validation, and structured API or call-flow recovery."
description_zh: "覆盖 APK/AAB/XAPK/AAR 的完整安卓逆向流程：框架指纹、DEX/Java/Kotlin 静态分析、Recaf 与 enigma-mcp 协作、JNI/ELF native 跟踪、动态沙盒验证以及 API/调用链报告。"
triggers:
  - "安卓逆向工程"
  - "反编译 APK"
  - "分析 AAB"
  - "提取 Android API"
  - "JNI native 分析"
  - "Android reverse engineering"
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
      - write_file
    requires:
      bins:
        - jadx
        - apktool
        - dex2jar
        - recaf
        - enigma-mcp
        - adb
        - frida
        - ida
        - dynamic-sandbox
---

# Android Reverse Engineering Complete

This skill incorporates the workflow themes from the
[Forinxy Android reverse-engineering skill collection](https://github.com/Forinxy/-skills/tree/main/Android%E9%80%86%E5%90%91%E5%B7%A5%E7%A8%8B%E6%8A%80%E8%83%BD%E5%AE%8C%E6%95%B4%E5%90%88%E9%9B%86). Keep the original package, split packages, signing metadata, and
derived outputs separate.

## Phase 1: fingerprint and inventory

Hash the artifact and record package/application IDs, versions, split APKs,
ABIs, manifest/exported components, permissions, certificates, DEX count,
assets, native libraries, frameworks (native Kotlin/Java, Flutter, React
Native, Cordova, Xamarin), and network stacks. For Flutter/RN/Cordova/Xamarin,
route to framework-specific assets instead of assuming DEX contains the core
logic.

## Phase 2: managed static analysis

Decode resources with apktool and decompile DEX with jadx; use dex2jar plus
Recaf/Vineflower when a second Java view is useful. Build a UI-to-storage and
UI-to-network call graph, identify reflection, dynamic loading, crypto,
serialization, and exported component boundaries. Use enigma-mcp in the
background for reviewed class/member mappings and keep mapping evidence.

## Phase 3: native boundary

Inventory `lib/<abi>/*.so`, locate `System.loadLibrary`/`dlopen`, then resolve
static `Java_*` exports and dynamic `RegisterNatives`/`JNI_OnLoad`. Match each
managed declaration to module, ABI, runtime address, and offset. Hand native
residue and protected libraries to `native-residue-triage` or
`vmp-3x-native-deobfuscation`.

## Phase 4: dynamic sandbox

Run the copied package in an emulator or dynamic sandbox with a clean snapshot.
Capture one reproducible flow: action, process/thread, API request, JNI call,
native module/offset, input, output, and relevant logcat/Frida/IDA evidence.
Change one variable per replay and keep test data synthetic.

## Completion report

Deliver hashes, decoded resource/DEX trees, component and permission matrix,
call graph, endpoint table, Recaf/enigma mappings, JNI/native table, dynamic
traces, reproduction steps, and unresolved or framework-specific portions.

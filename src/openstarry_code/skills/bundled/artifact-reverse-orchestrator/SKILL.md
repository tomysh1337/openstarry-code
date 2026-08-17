---
name: artifact-reverse-orchestrator
description: "Route reverse-engineering work by artifact type. Start JAR/Java/EXE work with a static project inventory, split modules into focused sub-agent tasks, use Recaf and enigma-mcp as background decompilation and mapping services, and validate selected paths with a debugger or dynamic sandbox. Use for mixed Java, native, C++, Python, and executable artifacts."
description_zh: "按文件类型编排逆向工程：JAR/Java/EXE 先建立静态项目视图，再按模块分发子任务，后台协作 Recaf 与 enigma-mcp，并用调试器或动态沙盒验证；C++/Python 不使用 Java 反编译器。"
triggers:
  - "逆向工程编排"
  - "分析 JAR"
  - "分析 EXE"
  - "静态分析再动态验证"
  - "reverse artifact"
  - "module reverse engineering"
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
      - subagents
      - read_file
      - write_file
    requires:
      bins:
        - recaf
        - enigma-mcp
        - debugger
        - dynamic-sandbox
        - strings
        - file
---

# Artifact Reverse Orchestrator

Use this skill as the entry point for a mixed artifact. Preserve every input
and produce a replayable evidence bundle; never let a sub-agent overwrite the
original.

## 1. Classify and inventory

1. Hash the artifact and copy it to `00-original/` beside a workspace containing
   `reports/`, `static/`, `dynamic/`, `modules/`, `logs/`, and `handoff/`.
2. Identify the real format from magic bytes, not only the filename. Record
   architecture, platform, entry points, imports, embedded archives, and debug
   metadata.
3. For `.jar`, `.class`, Java projects, and `.exe` files, **complete the static
   project view first**: enumerate modules, dependencies, resources, call
   boundaries, and likely execution paths. Save `static/inventory.json` and a
   short `static/project-map.md` before running the target.

## 2. Module task fan-out

After the inventory, create one sub-agent task per coherent module (loader,
codec, network, persistence, UI, JNI/native bridge, or protection layer). Each
task receives a read-only input path, its module scope, an evidence question,
and an output path under `modules/<id>/`. Agents must return:

```text
module | hypothesis | evidence paths/offsets | reproduced input/output |
unresolved symbols | next test
```

Keep one coordinator ledger in `handoff/agent-ledger.json`; merge claims only
when a second static view or a runtime observation supports them.

## 3. Tool routing

- **Java/JAR/EXE:** use static inspection first. Use Recaf for class/resource
  navigation and bytecode views, and enigma-mcp for mapping review in the
  background. A debugger validates a narrow entry point, exception path, or
  module contract after static hypotheses are recorded.
- **Native executable or library:** combine static disassembly/import/strings
  analysis with a dynamic sandbox. Use IDA/Ghidra/x64dbg or the platform
  debugger only against a copied sample; capture module base, offset, inputs,
  and output. Run `native-residue-triage` immediately after the initial pass.
- **C++ and Python:** use the language-native toolchain, symbols, AST/bytecode,
  and the dynamic sandbox. Do not invoke Java decompilers for these artifacts.
  For C++ inspect PE/ELF/Mach-O and DWARF/PDB; for Python inspect wheels,
  bytecode, import hooks, and runtime traces.
- **Android:** first fingerprint APK/AAB/framework, then route Java/Kotlin,
  DEX, JNI, and `.so` portions to `android-reverse-engineering-complete`.

## 4. Verification and handoff

Change one variable at a time. Keep original and derived artifacts separate,
record exact commands and tool versions, and stop a branch when verification
fails. The final report must include hashes, static map, sub-agent ledger,
Recaf/enigma outputs, debugger or sandbox traces, native-residue results, and
unresolved items. A decompiler rendering is a hypothesis until bytecode or a
replayed runtime path confirms it.

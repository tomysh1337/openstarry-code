---
name: java-reverse-toolchain
description: "Build a staged Java/JAR reverse-engineering workspace with static inventory, Recaf inspection, enigma-mcp mappings, decompiler comparison, debugger checks, and reproducible verification. Use for Java projects, JARs, class files, shaded libraries, and multi-release archives."
description_zh: "为 Java 项目、JAR、class、着色库和多版本归档建立分阶段逆向工具链：静态盘点、Recaf、enigma-mcp 映射、反编译对照、调试器验证和可复现检查。"
triggers:
  - "Java 逆向"
  - "JAR 反编译"
  - "Java 字节码分析"
  - "Recaf"
  - "enigma-mcp"
  - "Java reverse"
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
        - java
        - jar
        - javap
        - recaf
        - enigma-mcp
        - vineflower
        - cfr
        - debugger
---

# Java Reverse Toolchain

## Workspace contract

Create a sibling workspace and keep the input immutable:

```text
00-original/  01-static/  10-recaf/  20-decompile/  30-mappings/
40-stages/    50-verify/  logs/
```

Record SHA-256, Java release, class-file major versions, manifest, signatures,
class/resource counts, dependencies, and every command. Remove invalid
signatures only in a derived test artifact and document that action.

## Static-first sequence

1. Run `jar tf`, inspect `META-INF`, service descriptors, module-info, Kotlin
   metadata, multi-release entries, and embedded libraries.
2. Use `javap -c -p -v` on representative classes. Record invokedynamic,
   bootstrap methods, reflection, custom class loaders, and native declarations.
3. Build a package/class/method graph in `01-static/`. Split independent
   modules to sub-agents only after this graph exists.

## Recaf and enigma-mcp

Open the latest verified stage in Recaf with its dependencies. Use it for
resource navigation, bytecode inspection, call graphs, and controlled exports.
Run enigma-mcp in the background for human-reviewed package/class/member
mappings; store each mapping revision under `30-mappings/` with
`old,new,kind,confidence,evidence`. Do not infer semantic names from a single
decompiler output.

Compare at least two decompilers (Vineflower and CFR, or an available
equivalent), then inspect bytecode when their source views disagree. Apply one
transform per stage, re-run inventory, and retain the command/configuration in
`logs/`.

## Runtime check

Use a debugger or a minimal Java fixture after static analysis to validate one
entry point, class-loader path, exception branch, or serialization boundary.
Capture inputs, class path, thread, output, and verification errors. Re-run
`java -Xverify:all` and a narrow build/test after every transformed stage.

## Completion

Deliver original and final hashes, static graph, Recaf notes/exports,
enigma-mcp mappings, decompiler logs, verification output, residual opaque
methods, and an unresolved-symbol list. Never present guessed source as
recovered behavior.

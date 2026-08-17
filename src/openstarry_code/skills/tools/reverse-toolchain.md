# Reverse Toolchain Map

本文件描述逆向类 Skill 的统一初筛和工具分工。输入始终先作为本地
artifact 处理；先保留原始文件，再把静态证据、动态证据和每个 module 的
结论分开保存。`scripts/artifact_triage.py` 负责第一阶段分流，
`scripts/native_residue_scan.py` 在初始静态阶段后负责地址残留检查。

## 标准阶段

1. **保全与初筛**：计算 SHA-256、记录文件大小/魔数，运行
   `artifact_triage.py TARGET`。不要对原文件做重写。
2. **静态总览**：按类型选择反编译器和反汇编器，列出入口、依赖、模块、
   字符串、资源和异常处理；把每个 module 分成可独立复现的子任务。
3. **模块协作**：每个子 Agent 只处理一个 module 或一个证据问题，结果写入
   `module-findings.json`。Java module 的行为用 JDWP/JDB 调试器验证；原生
   module 用 IDA/Ghidra 调试器验证。
4. **动态验证**：Java/原生/Android 在隔离的动态沙盒中复现静态结论，记录
   进程、文件、网络和 JNI 调用；C++/Python 不引入 Java 反编译器。
5. **残留检查**：初始静态阶段完成后立刻运行
   `native_residue_scan.py TARGET`。命中 `-3######` 或 `0x######` 时，把
   偏移交给 IDA 的静态交叉引用和动态调试流程，回填到对应 module。
6. **汇总与复核**：静态、动态和残留证据相互校对，保留原始输出、工具版本、
   命令行和时间戳，再给出可重放的结论。

## 文件类型分流

| 类型 | 静态总览 | module 调试/动态验证 | 其他映射 |
| --- | --- | --- | --- |
| `jar`, `class`, `java` | Recaf 导航；`enigma-mcp` 反编译/符号；Vineflower/CFR；`javap` | JDWP/JDB；动态沙盒中的 JVM 日志、类加载和 JNI 追踪 | 运行 `native_residue_scan.py`；若含 `.so`/JNI，转 IDA/Ghidra |
| `exe`, `dll`, `so` | IDA、Ghidra、`strings`、PE/ELF 头和导入表 | IDA debugger、x64dbg/WinDbg、GDB/LLDB、Frida；动态沙盒 | 命中地址残留后，以偏移为锚点建立交叉引用 |
| `cpp`, `c`, `cc`, `cxx` | 编译器 AST、符号表、Ghidra/IDA；保留构建选项 | GDB/LLDB、 sanitizers、动态沙盒 | 不使用 Recaf、enigma-mcp 或其他 Java 反编译器 |
| `py` | `ast`, `dis`, `compileall`、源码和依赖图 | 受限 Python 沙盒、断点/trace、syscall 与文件事件 | 不使用 Java 反编译器；仍可运行残留扫描检查嵌入原生常量 |
| `apk`, `aar`, `dex` | apktool 资源/Manifest；jadx Java/Kotlin 视图；`aapt2`, `baksmali` | ADB/emulator、Logcat、Frida、动态沙盒 | JNI `.so` 转 IDA/Ghidra；Java 层可用 Recaf/enigma-mcp |

## 工具与 OpenStarry 映射

| 工具/服务 | 能力 | OpenStarry 工具或产物 |
| --- | --- | --- |
| Recaf | Java/JAR/Class 导航、字节码编辑和多反编译视图 | `read_file`, `source_symbols`, `write_file`; 产物写入 `static/recaf/` |
| enigma-mcp | MCP 驱动的 Java 名称恢复、反编译和交叉引用 | `http_request`/MCP bridge；结果写入 `static/enigma/` |
| IDA | PE/ELF 反汇编、Hex-Rays 视图、交叉引用、动态调试 | `read_source`, `grep_search`, `process`; 产物写入 `debug/ida/` |
| Ghidra | 原生反编译、符号和数据流分析 | `source_symbols`, `read_source`; 产物写入 `static/ghidra/` |
| Frida | Java/Native hook、调用栈和运行时观测 | `exec_command`, `background_process`, `process`; 产物写入 `dynamic/frida/` |
| Java JDWP/JDB | 断点、线程、局部变量和类加载调试 | `exec_command`, `process`; 产物写入 `debug/jvm/` |
| 动态沙盒 | 进程、文件、网络、环境变量和崩溃事件采集 | `background_process`, `process`, `read_file`; 产物写入 `dynamic/sandbox/` |
| apktool/jadx/adb | Android 资源、Manifest、DEX 反编译和设备复现 | `exec_command`, `read_file`, `process`; 产物写入 `static/android/` 与 `dynamic/adb/` |
| `native_residue_scan.py` | 发现 `-3######`/`0x######` 字面量并报告字节偏移 | `exec_command`; JSON 作为 IDA/Ghidra 输入 |
| `artifact_triage.py` | 扩展名/魔数初筛，生成阶段和建议工具 | `exec_command`; JSON 作为分流输入 |

## 协作约定

- `enigma-mcp` 和 Recaf 作为 Java 静态协作者在后台运行；它们的输出必须带
  输入哈希和工具版本。
- 对 `jar/java/exe` 先完成静态总览，再把 module 分发给对应调试器；其他
  类型直接按上表执行静态 + 动态沙盒协作。
- 所有脚本输出均为 UTF-8 JSON，路径使用绝对路径，偏移使用从零开始的字节
  偏移；错误作为 `errors` 字段保留，不中断其他文件。

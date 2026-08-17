---
name: java-protector-decompile
description: "Analyze, triage, decompile, and deobfuscate protected Java artifacts and mixed Java/native targets. Use for JAR, WAR, APK, AAB, .class, DEX, JNI .so/.dll/.dylib, Minecraft/plugin jars, Java malware, CTF reverse challenges, and protectors or symptoms such as ZKM/Zelix KlassMaster, JNIC, Java native obfuscator, native-obfuscator, Stringer, Allatori, DashO, ProGuard/R8, invokedynamic obfuscation, encrypted strings, flow obfuscation, native methods replacing Java bytecode, RegisterNatives, JNI_OnLoad, VMProtect/VMP, Themida, Code Virtualizer, packed native libraries, or broken Java decompiler output."
---

# Java Protector Decompile

## Overview

Use this skill to recover behavior from protected Java and Java/native hybrid artifacts. Treat decompiled source as one view, not truth; validate with bytecode, runtime traces, class loading behavior, and native library analysis.

## First Pass

1. Preserve the original artifact. Work from a copy and put extracted files, dumps, patches, and notes in a separate directory.
2. Run the passive triage script:

```powershell
& python scripts/triage_java_protector.py <artifact.jar-or-apk-or-class-or-native> --json
```

3. Record artifact type, Java target, entrypoints, class count, native library count, native methods, protector indicators, and decompiler failures.
4. Choose the narrowest route from the decision tree below.

## Decision Tree

Use `references/protector-matrix.md` for indicators and `references/workflows.md` for detailed playbooks.

- Plain Java obfuscation, readable bytecode, broken source only: use Java bytecode workflow.
- ZKM/Zelix symptoms: prioritize string decryptor discovery, flow flattening notes, exception/control-flow traps, and decompiler cross-checking.
- Stringer/Allatori/DashO-style symptoms: find runtime decryptors and invokedynamic bootstraps before trying full source recovery.
- ProGuard/R8/minified but not protected: recover names from logs, resources, mapping files, manifests, public APIs, and framework entrypoints.
- JNIC/native-obfuscator symptoms: map Java native stubs to native exports, `JNI_OnLoad`, `RegisterNatives`, and extracted `.so/.dll/.dylib` behavior.
- APK/AAB: combine JADX/DEX analysis with native library triage and Android lifecycle entrypoints.
- VMProtect/VMP/Themida on native libraries: switch to native VM/protector analysis; do not expect Java decompilers to recover the protected logic.
- Decompiler crashes or invalid Java: use `javap -v`, ASM/Recaf bytecode view, CFR/Vineflower/JADX cross-output, and targeted bytecode edits.

## Tool Order

Prefer multiple views:

1. Archive and metadata: `jar tf`, `unzip -l`, `aapt`/`apktool` for APKs.
2. Java bytecode: `javap -v`, Recaf bytecode view, ASMifier, Krakatau or equivalent disassembly.
3. Java decompilers: CFR, Vineflower/Fernflower, JADX for APK/DEX, Procyon as a cross-check.
4. Dynamic Java: custom class loader hooks, Java agents, JVMTI, `-verbose:class`, debugger breakpoints, logging around decryptors.
5. Native JNI: `strings`, `readelf`/`objdump`, Ghidra/IDA, Frida hooks for `JNI_OnLoad`, `RegisterNatives`, `GetStringUTFChars`, and exported native methods.
6. Native protection: load `code-obfuscation-deobfuscation`, `vm-and-bytecode-reverse`, `anti-debugging-techniques`, and `binary-re-*` skills for VMP/Themida/native packers.

## Analysis Rules

- Do not trust pretty decompiled Java until bytecode and runtime behavior agree.
- Recover behavior before recovering perfect names.
- Trace decryptors and class loaders at runtime when static string recovery is slow.
- For JNIC, treat Java classes as a dispatcher layer; the meaningful logic may live in native code.
- For VMP-protected native libraries, focus on I/O, JNI boundaries, and traces around the protected function before attempting full devirtualization.
- Patch one layer at a time. Verify each patch by re-running the original entrypoint or a minimal harness.
- Keep clean artifacts: original, extracted, renamed, patched, decrypted, and instrumented copies should be separate.

## References

- `references/protector-matrix.md`: protector indicators, likely artifacts, and starting tactics.
- `references/workflows.md`: step-by-step workflows for ZKM, JNIC, APK/JNI, native VMP, strings, invokedynamic, and bytecode repair.
- `references/toolbox.md`: recommended tools, command patterns, and output interpretation.

## Output Checklist

Return:

- Protector hypothesis with confidence and evidence.
- Artifact map: Java classes, resources, native libraries, entrypoints, suspicious loaders.
- Recovered behavior: decisive methods, strings, config, protocol, license checks, or flag logic.
- Reproduction steps: exact commands, runtime flags, hooks, and generated artifacts.
- Remaining blockers: missing dependencies, unsupported class version, native packer layer, anti-debug, or unresolved decryptor.

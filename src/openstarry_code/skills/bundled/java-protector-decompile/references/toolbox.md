# Toolbox

Use available local tools first. Install new tools only when the task needs them.

## Archive and Java Metadata

```powershell
jar tf sample.jar
javap -classpath sample.jar -v package.ClassName
python -m zipfile -l sample.jar
```

Look for:

- `META-INF/MANIFEST.MF`
- Framework descriptors and service providers
- Mapping files, debug metadata, or accidentally bundled sources
- Native libraries in architecture-specific paths

## Decompilers and Bytecode Editors

- Vineflower/Fernflower: good baseline Java source.
- CFR: useful cross-check, often resilient on modern Java bytecode.
- Procyon: extra source view when others disagree.
- JADX: use for APK/DEX and Android resources.
- Recaf: bytecode editing, bytecode/source view switching, stack-frame-aware patches.
- Krakatau or ASMifier: bytecode-level disassembly and reconstruction.

Cross-check rule: if decompilers disagree on control flow, trust `javap -v` and runtime traces first.

## Native Analysis

Linux/ELF:

```powershell
strings libtarget.so
readelf -h libtarget.so
readelf -S libtarget.so
readelf -Ws libtarget.so
objdump -d libtarget.so
```

Windows/PE:

```powershell
dumpbin /headers target.dll
dumpbin /exports target.dll
strings target.dll
```

Use Ghidra/IDA for decompilation and xrefs. Use Frida, gdb/lldb, x64dbg, or WinDbg for runtime behavior.

## JNI Hook Targets

High-yield functions:

- `JNI_OnLoad`
- `RegisterNatives`
- `FindClass`
- `GetMethodID`
- `GetStaticMethodID`
- `GetFieldID`
- `NewStringUTF`
- `GetStringUTFChars`
- `GetByteArrayElements`
- `Call<Type>Method`

For `RegisterNatives`, log the class name plus each `JNINativeMethod` name, descriptor, and function pointer.

## Runtime Flags

Useful JVM flags:

```powershell
java -verbose:class -jar sample.jar
java -Xcheck:jni -jar sample.jar
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=*:5005 -jar sample.jar
```

Use `-Xcheck:jni` to surface JNI misuse and boundary crashes. Use JDWP only in a local or authorized sandbox.

## Evidence Format

Keep notes compact:

```text
Artifact: sample.jar
Hypothesis: JNIC stacked after ZKM
Evidence: 214 native methods, lib/linux/x86_64/libx.so, JNI_OnLoad, RegisterNatives, encrypted strings in loader class
Verified: hooked RegisterNatives and recovered 53 method mappings
Next: trace native function 0x...
```

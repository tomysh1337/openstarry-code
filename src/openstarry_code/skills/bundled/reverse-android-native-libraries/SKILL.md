---
name: reverse-android-native-libraries
description: "Trace and reverse Android native behavior end to end across Java or Kotlin call sites, JNI static or dynamic registration, APK/AAB/AAR native-library inventory, ELF and ARM/Thumb/AArch64 analysis, Frida or JNItrace validation, algorithm recovery, and minimal binary patching. Use when an Android task mentions native methods, JNI_OnLoad, RegisterNatives, JNINativeMethod, .so files, ABI-specific lib directories, ARM offsets, Thumb bits, Frida native hooks, JNI traces, a Java-to-native boundary, protected native checks, or reproducing a native signing or encryption routine."
---

# Reverse Android Native Libraries

## Objective

Recover one narrow, replayable path from a managed call site to decisive native behavior. Treat decompiler output, symbol names, blog snippets, and comments as hypotheses until runtime evidence or a clean local replay confirms them.

Keep the Android-specific Java/JNI/ELF boundary in this skill. Use the generic `binary-re-*` skills for broad binary triage, tool setup, or final reporting when they are available.

## Start With Evidence

1. Preserve the original APK, split APKs, AAB, AAR, extracted libraries, and any patched copies separately.
2. Record package name, version code, ABI, Android version, process name, app state, triggering action, and expected output.
3. Hash every artifact that enters or leaves the workflow.
4. Reproduce the managed-layer behavior once before hooking or patching. Capture exact inputs and outputs.
5. Run the bundled inventory before choosing a library:

```powershell
python scripts/native_inventory.py target.apk
python scripts/native_inventory.py target.apk --json
python scripts/native_inventory.py libtarget.so --segments
python scripts/native_inventory.py libtarget.so --elf-va 0x31cb
```

Use the bundled Python runtime when `python` is unavailable. The script is read-only.

For an AAR, treat `jni/<abi>/` libraries as runtime packaging candidates and `prefab/` libraries as build-time artifacts. A Prefab copy may retain useful symbols, but use it for static assistance only after hashes, build IDs, load segments, and code bytes match the runtime library. For an APK or AAB, prefer the library path actually installed and mapped by the target process.

## Trace The Boundary

### 1. Locate The Managed Call Site

Trace backward from the observable request, file, UI action, or result to the smallest Java/Kotlin method that declares or calls `native` code.

Record:

- Declaring class and class loader
- Method name and complete JNI signature
- Static or instance method
- Arguments, return type, and nullability
- `System.loadLibrary`, `System.load`, linker namespace, or late `dlopen` path
- Process and thread that execute the call

Do not assume the nearest `loadLibrary` owns the method. Applications may load several libraries, register methods from a dependency, or move registration into a constructor.

### 2. Resolve JNI Registration

Check both branches:

- **Static discovery:** enumerate exports beginning with `Java_`; account for JNI escaping and overload suffixes. Prefer actual exports over a manually guessed name.
- **Dynamic registration:** inspect `JNI_OnLoad`, constructors, `RegisterNatives` cross-references, and `JNINativeMethod` arrays. If symbols are stripped or registration is indirect, trace registration before the target method first executes.

For every resolved method, save this tuple as one evidence row:

```text
class | method | signature | module | fn_ptr | module_base | module_offset | ABI | app version
```

Assign ownership from the module containing `fn_ptr`, not from the helper framework that performed registration. fbjni and similar wrappers may register an implementation located in a consumer library.

Read [runtime-and-addressing.md](references/runtime-and-addressing.md) before writing a registration hook or converting addresses.

### 3. Build A Controlled Trigger

Reduce runtime noise before expanding instrumentation:

1. Trigger one app action at a time.
2. Hold inputs constant, including timestamps, random values, locale, headers, device identifiers, and map iteration order.
3. Prefer an authorized active call to the managed wrapper when constructing valid arguments is practical.
4. Use spawn mode for early registration or constructor activity. Use attach mode only after proving the target is already loaded and initialized.
5. Record injection order when combining tools. Two spawn-based tools cannot independently own the same launch.

The target is not stable until identical inputs produce either identical outputs or an explained source of nondeterminism.

## Analyze The Native Implementation

### 4. Establish Static Ground Truth

Load the exact ABI library observed at runtime. Confirm ELF class, machine, endianness, `PT_LOAD` layout, dependencies, imports, exports, and build identity before using an old database.

Then:

1. Navigate to the registered function offset, not a same-named decoy.
2. Apply the correct JNI prototype. Remember the implicit `JNIEnv*` and `jobject` or `jclass` parameters.
3. Rename functions and values only when evidence supports the name.
4. Recover structures from repeated field offsets and calling behavior.
5. Follow strings, imports, constants, table accesses, and callers in both directions.
6. Validate every important decompiler claim against assembly, ABI rules, or runtime values.

Do not force a full line-by-line translation too early. First identify the input buffer, output buffer, lengths, branch gates, state initialization, and high-value helper calls.

### 5. Correlate Runtime And Static Addresses

Keep these values distinct:

- Runtime absolute address
- ELF load bias
- Module-relative offset
- ELF virtual address
- File offset
- IDA/Ghidra image address

Use `PT_LOAD` program headers to map an ELF virtual address to a file offset. Do not patch `file_offset = runtime_address - module_base` unless the segment mapping proves that equality.

On 32-bit ARM, normalize the Thumb state bit deliberately. Clear it for a code offset or file mapping; set it when attaching to a hard-coded Thumb function pointer. Do not change the bit on pointers returned by Frida APIs because Frida already normalizes them.

### 6. Instrument Narrowly

Start at the boundary and move inward:

- JNI registration tuple
- JNI method entry and return
- Length-bearing buffer transforms
- Comparisons that select the decisive branch
- Candidate hash, cipher, codec, or table helpers
- Final output construction

Interpret each argument using the proven ABI and prototype. Bound every memory read by a validated length, catch unreadable pointers, and keep per-call state on the interceptor invocation rather than in globals.

Treat JNItrace as a call-sequence and value oracle, not as proof of the native algorithm. Filter by module, thread, fixed trigger, and time window before drawing conclusions.

## Recover And Prove Behavior

### 7. Reconstruct The Transform

Work from both directions:

1. Trace forward from controlled input bytes.
2. Trace backward from final output construction.
3. Use constants and recognizable tables only to form candidates.
4. Compare candidates with known implementations by state layout, update/final sequence, block size, padding, and exact byte order.
5. Hook candidate boundaries to capture complete buffers and lengths.
6. Reimplement the smallest transform outside the app.
7. Replay at least two fixtures, including one edge case, and compare byte-for-byte.

If replay differs, return to the earliest uncertain conversion: string encoding, signedness, endianness, field ordering, timestamp units, hidden state, or environment binding.

### 8. Patch Only When Needed

Prefer observation or a local reimplementation when it answers the challenge. When a patch is required:

1. Back up the original and record the original bytes.
2. Prove the branch condition or data dependency dynamically.
3. Map the instruction to a file offset through the correct load segment.
4. Patch the fewest bytes possible without changing instruction width or execution state unexpectedly.
5. Reopen the patched file and verify both bytes and disassembly.
6. Repackage and sign only the challenge-local copy.
7. Repeat the original trigger from a clean baseline and confirm the intended effect plus nearby non-regression behavior.

Do not mark a bypass successful merely because the app stopped crashing. Verify the decisive output or state transition.

## Completion Evidence

Finish with a compact replay record:

```text
Artifact hashes:
Runtime/app/ABI:
Managed call site:
JNI registration tuple:
Controlled input:
Observed native path:
Recovered transform or patch:
Expected output:
Replay command/action:
Residual uncertainty:
```

Read [sources.md](references/sources.md) only when auditing provenance, version assumptions, or the research used to build this workflow.

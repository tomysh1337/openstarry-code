# JNI Runtime And Addressing Reference

Use this reference when resolving JNI bindings, constructing hooks, or converting runtime addresses into static or file locations.

## Evidence Tuple

Keep one row per native method:

```text
class | method | signature | module | fn_ptr | module_base | module_offset | ABI | app version
```

Add process, thread, class loader, and registration timestamp when multiple processes or late-loaded modules exist.

## Static JNI Discovery

The short native name starts with `Java_`, followed by the encoded binary class name and method name. JNI escaping makes hand-built names error-prone:

- `/` in a binary class name becomes `_`
- `_1` encodes `_`
- `_2` encodes `;`
- `_3` encodes `[` 
- `_0xxxx` encodes a Unicode code unit
- An overloaded method may use the long form: `__` followed by the encoded argument descriptor, without the return descriptor

Enumerate actual dynamic exports with `readelf -Ws`, `nm -D`, IDA, Ghidra, rizin, or Frida. Treat a guessed name only as a search lead.

## Dynamic JNI Registration

`JNINativeMethod` is an array of three pointer-sized fields:

```c
typedef struct {
    const char *name;
    const char *signature;
    void *fnPtr;
} JNINativeMethod;
```

Resolve dynamic methods in this order:

1. Inspect `JNI_OnLoad` and native constructors.
2. Find `RegisterNatives` calls or cross-references.
3. Recover the class and method array statically when possible.
4. Trace `RegisterNatives` at runtime when the array is built dynamically, decrypted, or stripped.
5. Record the full tuple before the target call runs.

Internal `libart.so` symbol names vary by Android release. When tracing them, enumerate symbols containing both `JNI` and `RegisterNatives`, exclude `CheckJNI`, and validate the candidate by observing a plausible class, method count, signatures, and implementation modules. Do not hard-code one mangled symbol across versions.

Spawn early when registration happens during startup. If a spawn-based JNI tracer already owns process launch, attach the second tool after initialization and document the order.

## Native Prototypes

A JNI native implementation receives implicit leading parameters:

```c
JNIEnv *env;
jobject thiz;   // instance method
jclass clazz;   // static method
```

The declared Java parameters follow. Apply the complete signature before interpreting register values or pointer arguments.

For AArch64 AAPCS, integer and pointer arguments begin in `x0` through `x7`, and the primary result is returned in `x0`. For 32-bit ARM AAPCS, the first four word-sized arguments begin in `r0` through `r3`. Stack, vector, aggregate, variadic, and hidden-result cases require the full ABI rules; inspect the caller when the prototype is uncertain.

## Address Vocabulary

Never use the word "offset" without qualifying it.

| Value | Meaning |
| --- | --- |
| Runtime address | Absolute virtual address in one process |
| Load bias | Runtime relocation added to ELF virtual addresses |
| Module-relative offset | Runtime address minus an observed module base |
| ELF virtual address | Address encoded in the ELF image and program headers |
| File offset | Byte position in the file |
| Analysis address | Address shown after an IDA/Ghidra image base is applied |

For an ELF virtual address `va` inside a file-backed `PT_LOAD` segment:

```text
p_vaddr <= va < p_vaddr + p_filesz
file_offset = p_offset + (va - p_vaddr)
```

An address between `p_vaddr + p_filesz` and `p_vaddr + p_memsz` is zero-filled memory and has no backing file bytes.

For a proven load bias:

```text
elf_va = runtime_address - load_bias
```

Do not silently substitute a `/proc/<pid>/maps` start or a tool's `module.base` for load bias on unusual ELF layouts. Confirm the first `PT_LOAD`, page alignment, and mapping offsets. Typical Android `ET_DYN` libraries start at ELF virtual address zero, but the workflow must survive exceptions.

Use `scripts/native_inventory.py --segments` to print load segments and `--elf-va` to map a proven ELF virtual address.

## ARM And Thumb State

On 32-bit ARM, bit zero of a function pointer selects instruction state:

- `0`: ARM
- `1`: Thumb

The state bit is not part of the byte address. Clear it before comparing static offsets or mapping file bytes. Set it when attaching Frida to a hard-coded Thumb address. Frida-generated pointers already carry the correct state; do not add or clear the bit again.

AArch64 does not use this Thumb state bit.

AArch64 instructions are fixed-width and must start at a 4-byte-aligned address. A 32-bit ARM-state instruction is also 4-byte aligned; Thumb code may contain 16-bit and 32-bit instructions, so preserve instruction boundaries when selecting or patching bytes.

## Hook Hygiene

- Verify that the target module and exact ABI are loaded before attaching.
- Prefer a resolved export or recorded registration pointer over a guessed base plus offset.
- Validate readable ranges before reading pointers.
- Bound dumps by a proven length and cap unexpectedly large values.
- Decode strings only after proving encoding and termination.
- Store entry data on `this` so concurrent calls do not overwrite each other.
- Interpret return values according to the prototype; a pointer return is not automatically an output buffer.
- Capture process, thread, module, offset, input, and output in every decisive trace.
- Avoid replacing `JNIEnv` function-table entries as a generic trace technique. Hook stable functions or use a maintained JNI tracer instead.

## Static Analysis Checks

- Match APK version and ABI to runtime.
- Inspect `DT_NEEDED`, imports, exports, constructors, and `JNI_OnLoad`.
- Apply JNI and library prototypes before trusting decompiled arguments.
- Repair function boundaries or ARM/Thumb mode only after assembly and control-flow evidence.
- Treat crypto constants, RTTI, and library fingerprints as hypotheses until call shape and runtime buffers agree.
- Recheck assembly when F5/decompiler output reports stack failures, impossible types, or missing control flow.

## Common Failures

| Symptom | Check first |
| --- | --- |
| Hook never fires | Wrong process, ABI, registration mode, load timing, or Thumb state |
| Offset lands in nonsense | Version mismatch, wrong module base, unhandled image base, or file/VA confusion |
| JNI trace is mostly noise | Use a fixed active call, module filter, thread filter, and narrow time window |
| Fixed input changes output | Hidden time, randomness, device state, iteration order, or server state |
| Hook crashes on read | Wrong prototype, invalid pointer, missing length check, or object handle treated as raw memory |
| Patched app crashes | Wrong ABI, signature/repackaging issue, checksum, instruction width, relocation, or nearby data corruption |
| Branch bypasses but output is wrong | Additional environment checks, hidden headers/state, or an incomplete transform chain |

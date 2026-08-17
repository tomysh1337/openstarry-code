# Workflows

## Protected JAR Baseline

1. Copy the artifact to a work directory.
2. List archive contents: `jar tf sample.jar` or `python -m zipfile -l sample.jar`.
3. Run `scripts/triage_java_protector.py sample.jar --json`.
4. Extract manifests, service provider files, config files, native libraries, and suspicious loaders.
5. Identify entrypoints:
   - CLI: `Main-Class` in `META-INF/MANIFEST.MF`
   - Plugin: framework descriptors such as `plugin.yml`, `fabric.mod.json`, `mods.toml`, `paper-plugin.yml`
   - Servlet/server: `web.xml`, annotations, Spring metadata
   - APK: manifest activities, services, receivers, providers
6. Run at least two decompilers and diff key methods against `javap -v`.
7. Write a compact artifact map before patching.

## ZKM / Heavy Java Obfuscation

1. Locate decryptor candidates:
   - High fan-in static methods returning `String`
   - Loops over `char[]` or `byte[]`
   - Switch-heavy code around string creation
   - Calls from class initializers
2. Use bytecode view when source output is invalid.
3. Build a harness inside the same classpath when decryptors depend on class initialization.
4. Dump decrypted strings with method hooks or by patching logging into a copied artifact.
5. Rename classes from entrypoints outward. Preserve a map of old name to new name.
6. If flow is flattened, trace state variable values dynamically and reconstruct only the branch needed for the goal.

## Invokedynamic and Bootstrap Dispatch

1. Inspect `BootstrapMethods` with `javap -v`.
2. Identify bootstrap owner, method name, descriptor, and static arguments.
3. Hook or call the bootstrap in a harness to materialize strings, method handles, or call targets.
4. Replace opaque call sites with resolved constants only after proving the resolved value is stable.

## JNIC / Java Native Workflow

1. On Java side:
   - Search for `native` methods.
   - Search for `System.load`, `System.loadLibrary`, temp extraction, and architecture-specific resource names.
   - Record class names and method descriptors.
2. On native side:
   - Extract `.so`, `.dll`, `.dylib`, or `.jnilib`.
   - Run `strings`, `readelf -Ws`/`objdump -T`, or equivalent export listing.
   - Find `JNI_OnLoad`, `RegisterNatives`, and `Java_` exports.
3. Build the native mapping:
   - For static JNI names, demangle `Java_pkg_Class_method`.
   - For `RegisterNatives`, trace the `JNINativeMethod` array to recover Java names, descriptors, and function pointers.
4. Hook high-value JNI calls:
   - `RegisterNatives`
   - `FindClass`
   - `GetMethodID` / `GetStaticMethodID`
   - `GetFieldID` / `GetStaticFieldID`
   - `NewStringUTF`, `GetStringUTFChars`, `ReleaseStringUTFChars`
   - `GetByteArrayElements`, `SetByteArrayRegion`
5. Reproduce one native method call with controlled inputs before broadening.

## VMP/Themida Native Library

1. Confirm the native library is the decisive layer.
2. Identify load-time behavior: constructors, TLS callbacks, `JNI_OnLoad`, anti-debug checks.
3. Start from Java/JNI boundary values and trace inward.
4. If virtualized code consumes user input, log input buffer, output buffer, return value, and thrown Java exceptions.
5. If the output is enough to solve the task, stop there. Full devirtualization is expensive.
6. If full analysis is required, route to VM handler extraction:
   - Locate VM entry.
   - Find bytecode stream and handler table.
   - Trace handler effects.
   - Lift or emulate the small slice that touches the target input.

## Bytecode Repair and Patching

1. Prefer Recaf/ASM for small targeted edits.
2. Recompute frames with a tool rather than hand-editing StackMapTable where possible.
3. Patch out loader guards or environment checks only in copied artifacts.
4. Verify with:
   - `java -verify`
   - Original entrypoint
   - Minimal harness for the patched method
5. Keep a diff or patch log listing class, method, descriptor, old behavior, and new behavior.

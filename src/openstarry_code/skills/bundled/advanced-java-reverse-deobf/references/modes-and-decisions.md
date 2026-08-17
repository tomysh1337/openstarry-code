# Java JAR Evidence and Decisions

## Probe First

Run `scripts/jar_probe.py` against the original and after every stage. Its signals are triage evidence, not a packer verdict. Compare class versions, class/resource counts, manifest values, metadata files, parse failures, and control-flow/string metrics before and after a transformation.

## Decision Table

| Evidence | First operation | Verification |
| --- | --- | --- |
| Unsupported class major version | Install/select matching JDK; inspect with matching `javap` | `javap -v` parses target classes |
| `META-INF/versions/` or mixed class versions | Treat each MR-JAR class family separately; retain versioned paths | Base and versioned classes load on their intended runtime |
| Short identifiers with normal bytecode | Export a mapping inventory; decompile before renaming | Every renamed reference and resource agrees with the mapping |
| High-entropy/base64-like string constants plus a compact decoder | Locate decoder call sites; recover pure inputs first; replace only verified literals | Original and decoded paths produce identical values in a focused fixture |
| Heavy branches/switches, unreachable blocks, or malformed decompiler output | Inspect `javap -c -p -v`; simplify one method or one pattern at a time | `java -Xverify:all`, instruction-level equivalence tests, then two decompilers |
| `invokedynamic`, `ConstantDynamic`, or bootstrap methods | Inspect bootstrap handles and arguments before modifying callers | Bootstrap tables, descriptors, and runtime linkage remain valid |
| Reflection, resource-loaded class names, services, Fabric/Mixin metadata | Inventory all string/resource references before remapping | Service loading/mod metadata/mixin references resolve after rename |
| Kotlin metadata or lambda-heavy classes | Preserve metadata and compare Kotlin-aware decompiler output | Kotlin metadata remains readable and lambda targets resolve |
| java-deobfuscator tool found locally | Match the observed pattern to a documented transformer and run it into a new stage | Re-probe plus verifier pass; retain the exact config |
| No compatible deobfuscator found | Use bytecode views, targeted scripts, and semantic mapping rather than speculative bulk edits | Verification after every targeted stage |

## Transformation Modes

### Inventory and Static Views

Use this mode for every artifact. Read manifest class paths, services, embedded libraries, module descriptors, Fabric/Forge metadata, and class-version distribution. Compare Vineflower and CFR output; use `javap` as the bytecode authority when they disagree.

### Supported Automated Passes

Use an automated transformer only when the evidence identifies a compatible pattern. Save its config, stdout/stderr, input hash, output hash, and report. A successful process exit alone is not validation.

### Targeted Bytecode Recovery

Use for string decryptors, opaque predicates, arithmetic encodings, dispatch tables, and localized control-flow flattening. Recover a bounded pattern, construct a fixture from observed inputs, verify parity, then apply it to matching call sites. Preserve stack maps or regenerate them with a compatible bytecode library.

### Semantic Mapping

Use after bytecode stabilizes. Derive names from public API shape, call graph, types, resources, constants, and independently confirmed behavior. Store confidence and evidence in the mapping table. Keep unresolved identifiers neutral.

## Validation Order

1. ZIP integrity and manifest/resource inventory.
2. Class-file parse and matching-JDK `javap` output.
3. JVM verifier or a focused class-loading fixture.
4. Narrow behavior tests for each transformed pattern.
5. Two independent decompiler views.
6. Resource, reflection, service, Fabric/Mixin, and Kotlin metadata checks.

Decompiler output is a presentation layer. Bytecode verification and focused behavior checks decide whether a recovered stage is valid.

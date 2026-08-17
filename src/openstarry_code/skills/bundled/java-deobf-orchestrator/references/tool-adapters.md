# Tool Adapters

## Baseline

- Select a JDK whose class-file support covers the highest input major version.
- Use `jar`, `javap -c -p -v`, and `java -Xverify:all` as bytecode authorities.
- Record tool version, command, input hash, output hash, stdout, and stderr.

## Discovery And Missing Tools

Search `PATH`, `JAVA_HOME`, explicit tool roots, workspace `tools/`, Maven/Gradle caches, Codex runtime dependencies, and prior case logs with `rg --files`. Write every candidate and selected adapter to `reports/tool-inventory.json`.

If a required tool is absent, query only its official repository/release metadata when network access is available. Record URL, version, asset name, checksum, compatibility, and disposition in `reports/missing-tools.json`; if downloaded, keep it under the case or workspace tool cache and never overwrite an existing binary. If retrieval is unavailable, continue independent stages and surface the missing capability in the handoff.

## Decompilers

- CFR: `java -jar cfr.jar INPUT.jar --outputdir OUTPUT`
- Vineflower: `java -jar vineflower.jar INPUT.jar OUTPUT`
- Procyon: `java -jar procyon-decompiler.jar -jar INPUT.jar -o OUTPUT`; use it as a third opinion where CFR and Vineflower disagree or fail.
- Recaf is the navigation, call-graph, constant-pool, assembler, and controlled bytecode-editing surface; export every edit into a new stage.

Record per-decompiler class/method failures. Resolve disagreements against descriptors, exception tables, stack maps, and `javap`, not source aesthetics.

## Transformers And Mapping

- Match java-deobfuscator transformers to observed bytecode patterns before running them.
- Use Enigma-MCP for reviewed naming after control flow, constants, descriptors, and metadata are stable.
- Keep transformer configs and Enigma mappings beside the stage that produced them.

For custom ASM passes, emit a pre-pass match inventory, transformed-site list, skipped-site reasons, verifier result, and post-pass residual count. Do not compute frames without a resolver that sees the target JDK and complete dependency hierarchy.

For bootstrap recovery, inventory bootstrap handles and arguments first. Evaluate deterministic call sites in an isolated class loader and record caller `Lookup`, descriptor, arguments, return value/target, JVM version, and side effects. Use a Java agent only for families that require live caller state.

## Build Closure

- Prefer the recovered Gradle/Maven wrapper when trustworthy and complete.
- Otherwise invoke `scripts/compile_audit.py` with the exact dependency classpath.
- Treat missing dependencies separately from illegal source, descriptor damage, and unresolved obfuscation.
- Run parse/type resolution over the entire owned source tree, not only priority packages.
- Reconstruct pinned Java toolchains, dependency versions, annotation processors, generated-source roots, resources, and framework metadata before IDEA import.
- Require the command-line Gradle/Maven build to pass with zero production compile errors; IDEA-ready is not established by opening the directory successfully.

---
name: java-deobf-orchestrator
description: Stateful orchestration for recovering readable, buildable, IDEA-ready Java source from obfuscated JAR and class files. Use for multi-round Java decompilation or deobfuscation, CFR/Vineflower/Procyon comparison, Recaf navigation, java-deobfuscator or custom ASM passes, dynamic bootstrap and string recovery, Enigma-MCP mapping, Fabric/Forge/Mixin/Kotlin metadata repair, full-tree type and compile-error closure, residual audits, authoritative-stage selection, and reproducible handoff generation.
---

# Java Deobf Orchestrator

Recover Java artifacts as an evidence-driven state machine. Keep the original immutable, record every operation, and continue only from the last verified bytecode stage.

## Non-Negotiable State

- Preserve the supplied JAR byte-for-byte under `original/` and record SHA-256, size, timestamp, ZIP entries, manifest, class major versions, and signatures before analysis.
- Treat source produced by a decompiler as a view, not an authoritative transformation. Keep the last verified JAR and the preferred source tree as separate state fields.
- Write every transformed JAR to a new numbered stage. Never overwrite an input, mapping, report, or previous output.
- Record the exact executable, version, command, configuration, input/output hashes, exit code, stdout, and stderr for every external tool.
- Change one bounded pattern per bytecode stage. A failed stage remains evidence and never becomes authoritative.

## Start

Use the bundled dispatcher for a new case:

```powershell
py -3 scripts/orchestrate.py run INPUT.jar --case CASE_DIR --tool-root WORKSPACE
```

If Python is not on `PATH`, use the bundled Codex Python runtime. Pass every known tool directory through repeated `--tool-root`. The command initializes the case, runs the existing advanced Java probe, invokes locally discovered Vineflower and CFR builds, audits both source trees, and writes a handoff.

Case layout:

```text
original/       immutable input and SHA-256
stages/         transformed JARs, one operation per stage
decompiled/     independent decompiler views
mappings/       reviewed symbol mappings
reports/        probe, residual, compile, and verification JSON
logs/           exact commands and stdout/stderr
state.json      authoritative stage and operation ledger
HANDOFF.md      reproducible continuation state
```

Immediately create `reports/tool-inventory.json`. Discover tools in this order:

1. `PATH`, `JAVA_HOME`, selected JDK `bin`, and explicitly supplied `--tool-root` paths.
2. Workspace `tools/`, Maven and Gradle caches, user application folders, and configured Codex runtime dependencies.
3. Existing case logs and sibling reverse-engineering workspaces.
4. If a required adapter is still absent and network access exists, query its official repository or release metadata. Record the queried URL, requested capability, candidate version, checksum when downloaded, and final status.

Use `rg --files` for local discovery. Do not silently replace a missing tool with an unrelated one. Continue independent stages where possible and add the missing capability to `reports/missing-tools.json` and `HANDOFF.md`.

## Operate In Rounds

1. Read `reports/probe-*.json` before choosing a transformer.
2. Apply exactly one bounded operation to a new JAR.
3. Register it with `stage`; do not overwrite an earlier stage.
4. Run `probe`, `java -Xverify:all` or a focused loader fixture, then `decompile`.
5. Compare Vineflower and CFR. Use `javap -c -p -v` when source views disagree.
6. Run `audit` and `compile`; group compiler diagnostics by root cause rather than raw line count.
7. Mark a stage authoritative only after bytecode verification and resource-link checks pass.
8. Generate `handoff` before pausing or changing operators.

Use this phase order unless evidence justifies a narrower branch:

1. **Inventory:** archive structure, signatures, class versions, manifest/module metadata, services, native libraries, nested JARs, reflection strings, and framework resources.
2. **Static views:** run Vineflower and CFR independently. Run Procyon on methods where they disagree or fail. Use Recaf and `javap -c -p -v` to resolve the bytecode truth.
3. **Supported transforms:** run java-deobfuscator only after matching a documented transformer to observed bytecode. Save the complete transformer config.
4. **Targeted ASM:** normalize one proven family such as malformed exception ranges, constant arithmetic, opaque predicates, decoder calls, bootstrap arguments, or dispatcher edges. Preserve descriptors, access flags, stack semantics, exception behavior, bootstrap tables, and metadata references. Recompute frames only with the complete dependency hierarchy.
5. **Dynamic recovery:** classify every `invokedynamic` and `ConstantDynamic` family by bootstrap owner, descriptor, arguments, and caller context. Evaluate pure deterministic families in an isolated loader; use a narrowly scoped Java agent or runtime trace only when caller state is required. Store `callsite -> recovered value/target` with inputs and evidence before rewriting callers.
6. **Mapping:** stabilize bytecode before semantic naming. Use Enigma-MCP for reviewed mappings and export a machine-readable map with original name, new name, kind, confidence, and evidence.
7. **Source closure:** select the best method body per bytecode evidence, repair imports/generics/lambdas only when descriptors support the repair, then run full-tree parsing and type resolution.
8. **IDEA-ready closure:** reconstruct a reproducible Gradle or Maven build, source/resource roots, Java toolchain, exact dependencies, generated sources, annotation processors, and framework metadata. Reach a clean command-line build before declaring IDE import ready.
9. **Residual and handoff:** quantify every unresolved name, decoder, packed wrapper, bootstrap, VM handler, CFG anomaly, decompiler failure, compile diagnostic, and metadata reference.

Read [references/jvm-pattern-routing.md](references/jvm-pattern-routing.md) for evidence-to-pass routing, [references/tool-adapters.md](references/tool-adapters.md) for command adapters, [references/fabric-mixin-kotlin.md](references/fabric-mixin-kotlin.md) for metadata coupling, and [references/completion-gates.md](references/completion-gates.md) before declaring completion.

## Commands

```powershell
py -3 scripts/orchestrate.py init INPUT.jar --case CASE_DIR
py -3 scripts/orchestrate.py probe --case CASE_DIR --tool-root WORKSPACE
py -3 scripts/orchestrate.py decompile --case CASE_DIR --tool-root WORKSPACE
py -3 scripts/orchestrate.py stage OUTPUT.jar --case CASE_DIR --label strings-decoded --verified
py -3 scripts/orchestrate.py audit --case CASE_DIR --source SOURCE_TREE --label round-N
py -3 scripts/compile_audit.py --source-root SOURCE_TREE --output REPORT.json --classpath CLASSPATH
py -3 scripts/orchestrate.py status --case CASE_DIR
py -3 scripts/orchestrate.py handoff --case CASE_DIR
```

Use `--verified` only after a verifier or focused runtime fixture succeeds. A decompiler exit code is not bytecode verification.

## Routing Rules

- Use `advanced-java-reverse-deobf` and its `jar_probe.py` for initial evidence and per-stage probes.
- Use Recaf for navigation, bytecode edits, call graphs, and controlled export, not as the only recovered-source view.
- Use CFR and Vineflower for the baseline source pair. Add Procyon only as an independent tie-breaker; never choose a view by formatting preference alone.
- Use `java-deobfuscator` only when bytecode evidence matches a supported transformer. Run one transformer family per stage and retain its configuration.
- Use Enigma-MCP after bytecode stabilizes; store reviewed names in `mappings/names.csv` with confidence and evidence.
- Use custom ASM passes only when a pre-pass inventory defines exact match criteria and a post-pass audit proves the intended sites changed and unrelated sites did not.
- Treat bootstrap methods as executable inputs. Prefer offline evaluation of pure call sites; isolate dynamic evaluation from normal user profiles and record the JVM/JDK, classpath, caller lookup, arguments, result, and side effects.
- Use native reverse skills only for embedded DLL, SO, or DYLIB branches.
- Use JavaScript AST skills only for scripts embedded in the JAR.
- Never substitute guessed semantic names for unresolved names. Use stable neutral names and record the residual.

## Full-Tree Type And Build Closure

Do not validate only selected feature packages. Enumerate every recovered `.java` file and classify it as compiled, generated, dependency-owned, deliberately excluded, or unresolved. Run these gates across the complete selected source tree:

1. Parse every file with the target language level.
2. Resolve packages, imports, inheritance, interfaces, generic bounds, annotations, records, enums, lambdas, method references, and nested/anonymous classes.
3. Separate missing-classpath diagnostics from damaged source or unresolved obfuscation.
4. Compile all production sources with the exact dependency classpath; then compile tests or fixtures separately.
5. Audit source-to-bytecode coverage: every owned class entry must map to source or a documented generated/excluded artifact.
6. Audit resources after mappings: manifest entrypoints, `META-INF/services`, reflection names, serializers, Fabric/Forge descriptors, mixin configs/refmaps, access wideners, Kotlin metadata, and multi-release paths.
7. Import the generated Gradle/Maven project into IDEA only after the same build succeeds non-interactively. Do not rely on IDE auto-imports to hide missing dependencies.

IDEA-ready means a pinned JDK/toolchain, deterministic dependency resolution, correct source/resource roots, zero production compile errors, no unexplained owned classes, and a documented run/test configuration when one is applicable. It does not require launching a GUI or game client unless explicitly requested.

## Residual Accounting

Write machine-readable counts and top offenders for:

- unresolved short or synthetic class/member names;
- encrypted strings, integer encodings, decoder/runtime scaffolding, and reflection strings;
- `invokedynamic`, `ConstantDynamic`, bootstrap families, and unresolved dynamic targets;
- packed `Object[]` wrappers, bridges, lambda artifacts, VM dispatchers, opaque predicates, irreducible CFG, and malformed exception regions;
- CFR/Vineflower/Procyon failures or disagreements;
- parse/type/compile diagnostics grouped by root cause;
- stale resource and metadata references;
- source/class coverage gaps.

Compare each round against the last authoritative round. A falling raw error count is insufficient if semantic coverage or metadata integrity regresses.

## Completion Contract

Deliver the immutable original hash, final verified JAR, readable source tree, mapping table, both decompiler logs, compiler report, residual report, metadata-reference audit, and handoff. Report every remaining opaque method explicitly.

`full deobf` requires all gates in [references/completion-gates.md](references/completion-gates.md). Zero decompiler crashes alone does not satisfy it.

Before handing off, include the authoritative input and source paths, hashes, last verified stage, exact replay commands, tool inventory and missing tools, mapping location, full-tree compile and residual counts, failed branches, rollback point, and the next bounded operations in priority order.

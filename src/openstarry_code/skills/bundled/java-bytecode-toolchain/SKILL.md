---
name: java-bytecode-toolchain
description: Recover, inspect, deobfuscate, rename, and verify Java JAR bytecode with local java-deobfuscator, Recaf, and Enigma-MCP. Use for obfuscated JARs, class-file triage, source recovery, mapping work, and IDEA-ready Java source exports.
---

# Java Bytecode Toolchain

Use a staged workspace. Treat the original artifact as immutable and make every transform reproducible.

## Workspace

Create a sibling workspace for each input; never write into the source JAR or overwrite a prior stage.

```text
work/
  00-original/          # input JAR plus SHA-256
  01-inventory/         # jar listing, manifest, dependencies, tool detection
  10-deobfuscator/      # config, logs, and one output JAR per pass
  20-recaf/             # exported scripts, bytecode notes, repaired JARs
  30-mappings/          # Enigma mappings and naming decisions
  40-source/            # remapped decompile output
  50-verify/            # javap, load/build, type-audit, and final report
```

Record the input hash, Java target, manifest, class count, resource count, and every command/configuration in `01-inventory/`. Preserve dependencies separately and use the same runtime version that the JAR targets.

## Workflow

1. **Inventory first.** Copy the input to `00-original/`, calculate a SHA-256 hash, inspect `META-INF/MANIFEST.MF`, list classes/resources with `jar tf`, and identify bytecode versions with `javap -verbose`. Keep signed JAR metadata intact in the original; derived artifacts may need invalid signatures removed before testing.
2. **Detect and transform in layers.** Run java-deobfuscator detection before enabling transformers. Save the detection configuration and log. Start with structural passes, then string/control-flow passes, and emit a new JAR for each pass. Re-run detection after every material transformation rather than applying a broad transformer set blindly. See [tool-notes.md](references/tool-notes.md) for command templates.
3. **Inspect the actual bytecode in Recaf.** Open the latest derived JAR with its libraries. Use Recaf to inspect suspicious methods, invokedynamic/bootstrap usage, exceptions, malformed attributes, and references that decompilers render poorly. Keep exported scripts and any bytecode-level repair as a separate `20-recaf/` artifact with a short rationale.
4. **Map names with Enigma-MCP.** Load the current JAR and dependencies into Enigma-MCP. Rename packages/classes first, then fields and methods from call sites, descriptors, constants, and behavior. Add concise Javadocs only where they preserve recovered meaning. Store mappings under `30-mappings/` and export them before remapping; do not infer names from legacy source dumps without bytecode evidence.
5. **Remap and decompile.** Apply the versioned mappings to a new JAR, then decompile that JAR into `40-source/`. Retain the mapping file beside the output so a name can always be traced back to its obfuscated symbol. Use Enigma's GUI/MCP process boundary for mapping work; do not vendor its source into the recovered project.
6. **Verify behavior and structure.** Compare pre/post stage class and resource inventories, inspect representative methods with `javap -c -p`, and load or run a narrow fixture when practical. Run the repository's compiler/type-audit on exported sources. Treat a decompiler failure as a signal to inspect bytecode, not as proof that a class is absent.

## Mapping Rules

- Keep one mapping file per stable recovery milestone; never edit a historical mapping in place.
- Prefer semantic names backed by control flow, API usage, descriptors, and constants. Use stable placeholders such as `UnknownPacketHandler` only when evidence is insufficient.
- Preserve package boundaries unless there is evidence that a move is required for the target build.
- Track unresolved symbols and decompiler defects in the final report separately from verified mappings.

## Completion Evidence

Deliver the original hash, stage-to-stage JAR hashes, java-deobfuscator configs/logs, Recaf scripts/notes, Enigma mappings, source export, dependency list, verification output, and an unresolved-items list. A source tree is IDEA-ready only after its project metadata/dependencies are present and the selected verification command completes without new bytecode or type errors.

Read [tool-notes.md](references/tool-notes.md) when constructing commands or choosing a tool boundary.

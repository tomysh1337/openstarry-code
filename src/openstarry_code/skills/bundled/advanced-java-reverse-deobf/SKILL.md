---
name: advanced-java-reverse-deobf
description: Evidence-driven Java JAR reverse engineering and deobfuscation workflow. Use when inspecting, recovering readable source from, or validating transformations on Java .jar/.class artifacts, including obfuscated desktop applications, Fabric/Forge mods, shaded libraries, and multi-release JARs. Automatically probe the artifact and locally available Java tools, then choose and verify iterative deobfuscation steps.
---

# Advanced Java Reverse Deobf

Use this skill as an evidence-first loop. Preserve the original JAR, make one reversible transformation at a time, and accept a result only after bytecode and behavioral checks pass. For multi-round state, compile closure, residual counts, or handoff generation, route through `java-deobf-orchestrator`.

## Start Every Task
1. Create a work directory beside the artifact: `original/`, `reports/`, `stages/`, `decompiled/`, `mappings/`, and `logs/`.
2. Copy the input into `original/`; record its SHA-256. Never overwrite it.
3. Run the bundled probe before selecting a tool. Prefer the local Python launcher available on the host:

```powershell
$skills = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $HOME ".codex\skills" }
$probe = Join-Path $skills "advanced-java-reverse-deobf\scripts\jar_probe.py"
$runtimePython = Join-Path $HOME ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 $probe INPUT.jar --tool-root WORKSPACE --output reports\probe-00.json
} elseif (Test-Path $runtimePython) {
  & $runtimePython $probe INPUT.jar --tool-root WORKSPACE --output reports\probe-00.json
} else {
  & python $probe INPUT.jar --tool-root WORKSPACE --output reports\probe-00.json
}
```

Use additional `--tool-root` values for known local tool folders. Read `reports/probe-00.json`; it contains the manifest, embedded/external library paths, class versions, ecosystem metadata, obfuscation signals, and installed-tool evidence. Do not infer a packer or an original name solely from a heuristic.

## Iterate From Evidence

Read [references/modes-and-decisions.md](references/modes-and-decisions.md) before selecting a transformation. Follow this loop for every stage:

1. Select exactly one operation from observed evidence: unpack/resource inventory, decompile comparison, a supported transformer pass, string-decoder recovery, control-flow simplification, metadata repair, or semantic renaming.
2. Write the result to `stages/NN-description.jar` and capture the invoked command/config in `logs/NN-description.txt`.
3. Run `jar_probe.py` on that stage and compare its report with the prior report. Keep its SHA-256 and all reports.
4. Verify the stage with `java -Xverify:all` where an entry point or test harness exists. For libraries, load the changed classes in a minimal fixture and inspect them with `javap -c -p -v`.
5. Decompile the verified stage with at least two available views (prefer Vineflower plus CFR; use Recaf for navigation). Treat disagreement as evidence to inspect bytecode, not as a reason to edit source text.

Stop a branch when verification fails, retain its report and logs, and continue from the last verified stage.

## Tool Selection

- Use `java`, `jar`, and `javap` found by the probe as the baseline. Match the highest reported class-file major version with a compatible JDK before processing.
- Use Recaf for class/resource navigation, call graphs, bytecode inspection, and controlled exports.
- Use `java-deobfuscator` only when probe evidence and bytecode inspection match a supported transformation family. Keep its configuration and output JAR as a distinct stage.
- When the probe finds `xingkong-deobfuscator` and the JAR contains matching `ShieldRuntime` calls or `bootstrapStatic` call sites, run that tool into a separate stage before generic transformer passes.
- Use Vineflower and CFR independently for source recovery. Use Enigma only after bytecode is stable to store human-reviewed package/class/member mappings.
- For custom transformations, retain unchanged method descriptors, access semantics, bootstrap methods, stack-map validity, and resource references. Re-probe all class/resource references after remapping.

## Naming and Resources

Create `mappings/names.csv` with `old,new,kind,confidence,evidence`. Assign descriptive names only when behavior, call sites, constants, and types support them. Otherwise use stable neutral names such as `Class_0123` and preserve the original mapping.

Treat `META-INF/services/`, `MANIFEST.MF`, `fabric.mod.json`, `*.mixins.json`, `*.refmap.json`, access wideners, and Kotlin metadata as coupling points. Update them atomically with any confirmed class rename and verify their resulting references. Preserve signatures as evidence; regenerated artifacts need new signing only after all verification is complete.

## Completion Criteria

Deliver a readable source tree, `mappings/names.csv`, the last verified stage JAR, probe reports for original and final artifacts, decompiler logs, compile diagnostics, residual counts, and a concise verification report. Full recovery requires zero source compile errors and an explicit audit of metadata/resource references. State remaining opaque methods explicitly rather than presenting a guessed reconstruction as recovered source.

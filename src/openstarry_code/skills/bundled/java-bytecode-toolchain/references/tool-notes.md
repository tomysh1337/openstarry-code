# Local Tool Notes

Use a fresh stage output for every command. Replace placeholders; do not modify `00-original/INPUT.jar`.

## java-deobfuscator

Run detection first and save both the configuration and log:

```yaml
input: 00-original/INPUT.jar
output: 10-deobfuscator/detect-output.jar
detect: true
```

Then create a separate configuration per transform group, with the previous stage as `input`. Re-run `detect: true` after structural, string, or control-flow changes. Keep only transformations supported by the current evidence and log the selected transformer order.

## Recaf

Use the local Recaf distribution for bytecode inspection and scriptable repairs:

```text
java -jar recaf.jar -i 10-deobfuscator/STAGE.jar
java -jar recaf.jar -i 10-deobfuscator/STAGE.jar -s 20-recaf/repair-script.java
```

Load target libraries before interpreting unresolved members. Export scripts, patched JARs, and before/after method listings into `20-recaf/`.

## Enigma-MCP

Run Enigma-MCP as its own local service and connect through its configured MCP endpoint (normally `http://127.0.0.1:32412/mcp`). Use it to create/export mappings and Javadocs, then apply the exported mapping to a new stage. Keep Enigma, mappings, and decompile output separate because the mapping is the traceability record for recovered names.

## Verification

Use bytecode and source checks together:

```text
jar tf STAGE.jar
javap -classpath STAGE.jar -c -p PACKAGE.CLASS
java -verify -cp STAGE.jar MAIN_CLASS
```

For an IDEA export, retain `pom.xml` or `build.gradle`, dependency coordinates/JARs, generated sources, mappings, and the exact compile/type-audit log. Compare inventories and hashes between stages before declaring a pass complete.

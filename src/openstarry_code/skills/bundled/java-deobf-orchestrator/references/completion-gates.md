# Completion Gates

Declare full recovery only when all applicable gates pass:

1. Original and final SHA-256 values are recorded; the original remains unchanged.
2. ZIP, manifest, and every class file parse with the intended JDK.
3. Final bytecode passes `-Xverify:all` or focused class-loading fixtures.
4. CFR and Vineflower complete; Procyon covers unresolved disagreements, and every selected method is justified against `javap` or ASM evidence.
5. Every owned source file is classified and the complete selected production tree parses, type-resolves, and compiles with zero errors using pinned dependencies and the intended Java toolchain.
6. Fabric, Forge, Mixin, service, reflection, Kotlin, and multi-release references resolve.
7. String decoders, dynamic bootstrap families, VM dispatchers, opaque predicates, malformed CFG, and decompiler-failure markers have zero unexplained instances.
8. Names are semantic only where evidence supports them; unresolved mappings are explicitly listed.
9. Focused behavior tests reproduce the decisive paths from a clean baseline.
10. `HANDOFF.md` names the authoritative artifact, exact replay commands, counts, reports, and remaining work.
11. Tool inventory, missing-tool queries, transformer/ASM configs, dynamic-evaluation inputs, and stdout/stderr logs are retained.
12. Source-to-class coverage has no unexplained owned classes, and the reconstructed Gradle/Maven project builds non-interactively before IDEA-ready is claimed.

If a gate is inapplicable, record why. Do not convert an unknown into a pass.

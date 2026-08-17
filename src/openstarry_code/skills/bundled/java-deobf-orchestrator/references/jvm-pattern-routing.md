# JVM Pattern Routing

| Evidence | Bounded next pass |
| --- | --- |
| Compact decoder plus encrypted LDC values | Evaluate pure decoder inputs and replace verified call sites |
| `invokedynamic` or `ConstantDynamic` clusters | Inventory bootstrap handles, descriptors, and arguments; emulate one family |
| Dispatcher switch and opaque branches | Recover one method CFG from bytecode, verify, then generalize the pattern |
| Malformed exception ranges or stack maps | Repair bytecode structure before source cleanup |
| Reflection and string class names | Build a reflection/resource reference inventory before renaming |
| Short names but stable behavior | Create neutral mappings, then apply semantic names with evidence |
| Java VM interpreter | Recover opcode table, stack model, operands, and one end-to-end virtualized method |
| Embedded native library | Split to a native analysis branch while preserving the Java/JNI contract |
| Fabric/Forge/Mixin resources | Audit metadata and remap resources atomically with class changes |
| Kotlin metadata/lambdas | Preserve metadata; verify descriptors and lambda targets after every remap |

Never stack speculative passes. If verification fails, retain the failed branch and restart from the last verified stage.

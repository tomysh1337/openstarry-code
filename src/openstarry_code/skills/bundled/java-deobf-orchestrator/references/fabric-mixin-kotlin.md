# Fabric, Mixin, And Kotlin Coupling

Audit these before and after any rename:

- `fabric.mod.json`, Forge descriptors, entrypoint classes, access wideners, and nested JAR declarations.
- `*.mixins.json`, `*.refmap.json`, mixin targets, injector method descriptors, accessor/invoker names, and plugin classes.
- `META-INF/services/`, manifest entrypoints, serialization names, reflection strings, and resource paths.
- Kotlin `@Metadata`, object/companion names, default argument bridges, coroutine state machines, and lambda targets.
- Multi-release entries under `META-INF/versions/`; remap each versioned class family consistently.

A source tree that compiles while these links are broken is not a completed recovery.

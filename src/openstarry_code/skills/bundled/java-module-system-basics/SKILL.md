---
name: java-module-system-basics
description: >
  Plan and review JPMS boundaries: module-info.java, requires/exports/opens,
  automatic and unnamed modules, and classpath-to-module-path migration. Use when
  modularizing Java apps/libraries, fixing module graph errors (exports, requires
  transitive, split packages), or multi-module builds — not Java naming/Javadoc style.
---

# Java Module System Basics (JPMS)

Design and migrate **JPMS** modules with explicit `module-info.java` contracts,
safe dependency edges, and a staged path off the classpath. Prefer repository
Maven/Gradle multi-module layout and JDK toolchain over generic defaults.

## When To Use

- Adding or editing `module-info.java` (`requires`, `exports`, `opens`, `uses`/`provides`)
- Migrating JARs from **classpath** to **module path** (or hybrid)
- Diagnosing graph failures: missing requires, illegal access, split packages,
  `module not found`, automatic-module name clashes
- Designing exported API packages vs internals under strong encapsulation
- Mentions: JPMS, Java modules, `module-info`, automatic modules, `requires transitive`, jlink

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Naming, formatting, Javadoc | `java-style-and-javadoc` |
| Reliability, errors, concurrency, security, tests | `code-quality-standards` |
| Deserialization / JNDI bugs | matching security skill |

## Repo Config First

Repository layout and build plugins **outrank** defaults below.

1. **JDK/toolchain** in `pom.xml` / `build.gradle(.kts)`; release matches module features.
2. **Module layout:** one module root per artifact; `module-info.java` under `src/main/java/`.
3. **Build plugins:** Maven compiler/moditect/jlink; Gradle `java.modularity` / patches.
4. **Boundaries:** packages treated as public API; neighbor `module-info`; OSGi notes.
5. **Tests:** opens for reflection; Surefire/JUnit module-path JVM args.
6. **Deps:** explicit modules vs automatic vs classpath-only.
7. **Docs:** `CONTRIBUTING*`, ADRs, package rules in `AGENTS.md` / README.

**Precedence:** Follow repo module names and export policy. Surface blanket `opens`,
exporting internals, or dual-deploy breaks.

## Workflow

### 1. Inventory
List artifacts, packages, SPI (`ServiceLoader`), reflection consumers, resources, JDK
version. Resolve **split packages** (same package in multiple JARs) before the module
path — they block modularization.

### 2. Names and roots
- Reverse-DNS names aligned with root packages (`com.example.billing`); keep stable.
- Prefer **one module per library/deployable**; finer modules only with a clear boundary.
- `module-info.java` at module source root (no package declaration).

### 3. `module-info` contracts
| Directive | Role |
| --- | --- |
| `requires` | Compile/runtime dependency |
| `requires transitive` | Re-export when types appear in your public API |
| `requires static` | Compile-time only; optional at runtime |
| `exports` / `exports … to` | Public API packages (qualified when needed) |
| `opens` / `opens … to` | Deep reflection; prefer qualified `to` |
| `uses` / `provides … with` | ServiceLoader consumer / implementation |

Export **API packages only**. Keep `internal`/`impl` unexported (or qualified). Use
`requires transitive` only when consumers need that dependency via your API.

```java
module com.example.billing {
  requires java.sql;
  requires transitive com.example.money;
  exports com.example.billing.api;
  exports com.example.billing.spi to com.example.billing.plugins;
  opens com.example.billing.internal.jpa to hibernate.core;
  uses com.example.billing.spi.TaxProvider;
  provides com.example.billing.spi.TaxProvider
      with com.example.billing.internal.DefaultTaxProvider;
}
```

### 4. Automatic and unnamed modules
| Kind | Appearance | Notes |
| --- | --- | --- |
| **Explicit** | JAR with `module-info` | Preferred for first-party and mature deps |
| **Automatic** | Module path via `Automatic-Module-Name` or filename | Filename names fragile — pin manifest |
| **Unnamed** | Classpath (no module) | Sees exports; **cannot** be `requires`’d by named modules |

Automatic modules are a **bridge**: they export all packages and read everything.
Prefer real `module-info` or first-party `Automatic-Module-Name` over silent renames.

### 5. Classpath → module path (staged)
1. Fix split packages; align roots with intended modules.
2. Add `Automatic-Module-Name` to first-party JARs still lacking `module-info`.
3. Modularize **leaf libraries first**, applications last.
4. Hybrid only when needed: document classpath leftovers and reflection flags.
5. Replace automatic modules; drop `--add-opens`/`--add-exports` once directives cover needs.
6. Verify compile + tests on the same graph; `jdeps`/`jlink` when a custom runtime is required.

### 6. Common failures
- **Not exported / not accessible** → export API or qualified `opens`; stop reaching internals.
- **Module not found** → wrong automatic name, missing `requires`, or JAR still on classpath.
- **Split package** → merge, rename, or single module-path owner.
- **Service not found** → `provides`/`uses` mismatch or unreachable provider package.
- **Tests fail** → open test packages or document test-only `--add-opens`.

Hand **naming and Javadoc** on exported APIs to `java-style-and-javadoc`. Apply
**`code-quality-standards`** when behavior, errors, or tests change.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| `module-info`, requires/exports/opens, automatic modules, classpath migration | **This skill** | — |
| Java naming, layout, Javadoc on public types | `java-style-and-javadoc` | this for exported packages |
| Implementation quality, tests, security baseline | `code-quality-standards` | this for module boundaries |
| Feature work inside a modular Java service | domain skill if any | this + `java-style-and-javadoc` + CQS |

### Routing notes
- **`java-style-and-javadoc`:** **hand off** for package/type naming and public API docs once
  exports are set; this skill owns the **module graph and encapsulation**.
- **`code-quality-standards`:** SPI, reflection, dual-version deploys still need solid errors/tests.
- JPMS is not a substitute for dependency versioning or CVE response.

## Output Checklist

- [ ] JDK/toolchain and build module settings read from the repo
- [ ] Package ownership mapped; split packages resolved or deferred
- [ ] Module names stable (reverse-DNS); clear artifact boundary per module
- [ ] `requires` / `requires transitive` / `requires static` justified by API surface
- [ ] Only API packages exported; internals unexported or qualified
- [ ] Reflection limited to qualified `opens … to` (or tracked temporary JVM flags)
- [ ] `uses` / `provides` match ServiceLoader; automatic modules treated as bridges
- [ ] Classpath→module-path stages documented; leaves before app when possible
- [ ] Compile/test on intended graph; residual `--add-opens` listed with owners
- [ ] Exported API style/Javadoc via `java-style-and-javadoc`; behavior via `code-quality-standards`

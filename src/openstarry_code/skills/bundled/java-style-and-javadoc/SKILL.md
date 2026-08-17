---
name: java-style-and-javadoc
description: >
  Apply Java naming, Google/Oracle-style layout conventions, and Javadoc discipline
  when writing or reviewing Java (and closely related Kotlin interop surfaces). Use when
  Java style, Javadoc, package/class naming, public API docs, Checkstyle/google-java-format
  alignment, or documenting types, methods, and parameters for Java code.
---

# Java Style And Javadoc

## Use When

- Writing or reviewing Java source for naming, packaging, or formatting consistency.
- Adding or fixing **Javadoc** on public APIs, modules, or shared libraries.
- Aligning new code with Google Java Style or Oracle Code Conventions at a **high level** (not re-litigating every brace rule).
- Touching Checkstyle, Spotless, `google-java-format`, Error Prone, or similar Java style tooling.
- Kotlin/Java boundary types that must keep Java-facing names and docs clear.

Do **not** use this skill as the primary path for architecture, error handling, concurrency, security, or tests — route those to `code-quality-standards` (and domain skills).

## Repo Config First

Repository conventions **outrank** this skill’s defaults. Before inventing style:

1. Read project docs: `CONTRIBUTING*`, `STYLE*`, `AGENTS.md` / `Claude.md`, README coding sections.
2. Read formatter/linter config in order of precedence you find:
   - Spotless / `google-java-format` / `fmt-maven-plugin` / Spotless Gradle
   - Checkstyle (`checkstyle.xml`, `suppressions.xml`)
   - PMD, Error Prone, SpotBugs (style-adjacent only)
   - `.editorconfig`, IDE code-style XML committed to the repo
3. Match **neighboring files** in the same package: naming, import order, Javadoc density, brace and line length habits.
4. If repo config conflicts with this skill, **follow the repo**. Surface security/correctness conflicts instead of silent dual style.
5. Run the project’s format/lint targets on touched files when available (`./mvnw spotless:apply`, `./gradlew spotlessApply`, Checkstyle task, etc.).

## High-Level Style (Google / Oracle)

### Naming

| Kind | Convention | Examples |
| --- | --- | --- |
| Package | All lowercase, reverse-DNS style, no underscores | `com.example.billing` |
| Class / interface / enum / record / annotation | UpperCamelCase; nouns or noun phrases | `PaymentService`, `OrderId` |
| Method | lowerCamelCase; verbs or verb phrases | `findById`, `isActive` |
| Field / local / parameter | lowerCamelCase | `itemCount`, `userId` |
| Constant (`static final` immutable) | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Type parameter | Single capital or descriptive UpperCamelCase | `T`, `E`, `RequestT` |
| Test class | Type under test + `Test` (or repo pattern) | `PaymentServiceTest` |

- Prefer domain words over hungarian or type-noise (`listOfUsers` → `users` when type is clear).
- Boolean names read as predicates: `isReady`, `hasChildren`, `canRetry`.
- Avoid one-letter names except idiomatic loops/lambdas (`i`, `e` for exception when short-lived).

### Structure And Layout (high-level)

- One top-level type per file; file name matches public type.
- Order typically: license/package → imports → type docs → type declaration → static fields → instance fields → constructors → methods (match neighbors).
- Keep methods short enough that purpose is obvious; extract when nesting or mixed concerns dominate.
- Prefer explicit access modifiers; avoid package-private “by accident” on API surface you mean to keep internal.
- Use `final` on locals/fields when the repo already does; do not mass-rewrite unrelated code for `final`.
- Braces and indentation: whatever formatter/repo uses. Do not hand-fight `google-java-format` or Spotless.
- Imports: no wildcards unless repo allows; remove unused imports via tooling.

### API Clarity (style-adjacent)

- Prefer clear parameter types over `Object` / raw types.
- Prefer `Optional` only at return boundaries when the codebase already does; do not wrap every nullable field.
- Prefer enums or sealed hierarchies over magic strings/ints when the set is closed.
- Keep overloaded methods consistent in argument order and units.

## Javadoc: When And What

### When to write Javadoc

| Surface | Expectation |
| --- | --- |
| Public / protected API of libraries, shared modules, SPI | **Yes** — class + non-obvious methods |
| Package-private helpers in app code | Only when behavior is non-obvious or contract-heavy |
| Overrides that inherit clear docs | `{@inheritDoc}` or omit if tooling/repo prefers inheritance |
| Getters/setters that only expose a field | Usually **no** unless constraints, units, or side effects exist |
| Trivial private methods | Prefer good names; Javadoc only for invariants or algorithms |

### What to put in Javadoc

- **First sentence**: summary fragment that stands alone (what, not how).
- **Body**: contracts, invariants, thread-safety, units, nullability, idempotency, side effects.
- **Tags**: `@param`, `@return`, `@throws` for checked and important unchecked failures; `@since` / `@deprecated` / `@see` when true.
- **Nullability**: document null allowances when annotations (`@Nullable` / `@NonNull`) are absent or incomplete.
- Do **not** narrate the code (“increments i then returns”). Do **not** paste signatures as the only content.

```java
/**
 * Settles a pending payment against the configured acquirer.
 *
 * <p>Idempotent for the same {@code paymentId}: repeated calls return the original result.
 *
 * @param paymentId stable client-visible payment identifier; must not be blank
 * @param amount minor units (e.g. cents); must be positive
 * @return settled payment view; never {@code null}
 * @throws PaymentNotFoundException if {@code paymentId} is unknown
 * @throws IllegalArgumentException if {@code amount} is not positive
 */
public Payment settle(String paymentId, long amount) { ... }
```

## Workflow

1. **Locate style sources** — config files, neighbor packages, existing Javadoc density.
2. **State the change surface** — new type, method rename, public API, or internal cleanup.
3. **Name first** — packages and types that match domain language already used in the module.
4. **Implement with local patterns** — builders, factories, records, exceptions as nearby code does.
5. **Document public contracts** — Javadoc where the table above requires it; annotations for nullability if the project uses them (`jspecify`, `javax.annotation`, JetBrains, etc.).
6. **Format and lint** — project formatter + Checkstyle/Error Prone on touched paths only.
7. **Review the diff** — no drive-by renames, no Javadoc walls on private glue, no style-only churn mixed into behavioral PRs unless requested.

## Examples

### Good

```java
package com.example.billing;

/**
 * Creates and tracks customer invoices for a single tenant.
 *
 * <p>Implementations must be safe for concurrent use by the web tier.
 */
public interface InvoiceService {

  /**
   * Issues an invoice for the given order.
   *
   * @param orderId order identifier owned by the current tenant
   * @return newly issued invoice id
   */
  InvoiceId issueForOrder(OrderId orderId);
}
```

```java
private static final int MAX_ATTEMPTS = 3;

boolean isRetryable(Status status) {
  return status == Status.TRANSIENT_FAILURE;
}
```

### Bad

```java
// Vague names, wrong case, useless Javadoc, wildcard import noise
import com.example.billing.*;

/** This is the invoice service class. */
public class invoice_service {
  public static final int maxAttempts = 3;

  /** Does the thing. @param o order @return result */
  public Object DoWork(Object o) { ... }
}
```

```java
/** @return the name */
public String getName() {
  return name;
}
```

(Trivial getter noise when no contract exists.)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Java naming, layout, Javadoc | **This skill** | — |
| Correctness, errors, resources, concurrency, security, tests | `code-quality-standards` | this for naming/docs only |
| Feature work in a Java service | Domain / feature skill if any | **this** + `code-quality-standards` |
| Insecure deserialization / JNDI class of bugs | matching security skill | not style-only review |
| Pure formatting with no human judgment | project Spotless / google-java-format | this only if config missing |

Always apply **`code-quality-standards`** as the implementation baseline when behavior changes. This skill specializes **style, naming, and Javadoc**; it does not replace quality, testing, or security rules.

## Checklist

- [ ] Repo formatter/linter/docs checked before applying defaults
- [ ] Package, type, method, field, and constant names match conventions and domain language
- [ ] File name matches public top-level type
- [ ] No wildcard imports unless repo standard
- [ ] Public/protected API has useful Javadoc (summary + contracts, not narration)
- [ ] `@param` / `@return` / `@throws` present where they add information
- [ ] Nullability, units, thread-safety, and idempotency noted when non-obvious
- [ ] No trivial Javadoc on obvious getters/private glue
- [ ] Formatter/Checkstyle (or project equivalent) run on touched files
- [ ] Behavioral concerns reviewed under `code-quality-standards`
- [ ] Diff free of unrelated style churn

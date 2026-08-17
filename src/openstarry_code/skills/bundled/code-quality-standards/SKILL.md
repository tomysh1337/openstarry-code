---
name: code-quality-standards
description: Apply repository-aligned coding standards while adding features, fixing bugs, refactoring, or reviewing implementation changes. Use when writing or modifying production code and the task needs maintainability, clear boundaries, type and data-model discipline, error handling, resource cleanup, concurrency safety, security hygiene, focused tests, formatting, or proportionate verification across Python, JavaScript/TypeScript, Go, Rust, Java, .NET, and similar projects.
---

# Code Quality Standards

## Working Order

1. Read repository instructions, build files, formatter/linter configuration, nearby code, and relevant tests.
2. State the behavioral contract: inputs, outputs, side effects, failure modes, compatibility, and invariants.
3. Match existing architecture, naming, dependency direction, and public API style.
4. Make the smallest coherent change that fully implements the behavior.
5. Test at the narrowest layer that proves the contract, then expand verification according to risk.
6. Run the repository formatter, linter, type checker, tests, and build commands that apply to touched code.
7. Review the final diff for unrelated churn, accidental API changes, secrets, generated files, and missing cleanup.

Repository conventions outrank generic preferences unless they create a correctness, security, or data-loss risk. Surface that conflict instead of silently introducing a second style.

## Implementation Rules

### Boundaries

- Keep domain logic separate from transport, storage, framework, and presentation details.
- Validate untrusted data at the boundary and convert it into a stable internal representation.
- Preserve public behavior unless the request explicitly changes it.
- Avoid hidden global state, manual cross-module synchronization, and duplicated sources of truth.
- Add an abstraction only when it removes demonstrated complexity or matches an established local pattern.

### Naming And Structure

- Name by domain meaning and observable responsibility, not implementation trivia.
- Keep functions focused enough that inputs, outputs, and side effects are visible.
- Prefer early returns for invalid or terminal cases when they reduce nesting.
- Keep constants, units, time zones, encodings, and ownership explicit.
- Comment decisions, invariants, compatibility constraints, and non-obvious algorithms. Do not narrate syntax.

### Errors And Resources

- Never swallow errors without an intentional fallback and observable evidence.
- Add context when crossing subsystem boundaries; preserve the original cause.
- Distinguish invalid input, expected absence, transient failure, cancellation, timeout, and internal defects.
- Close files, sockets, transactions, processes, subscriptions, timers, and locks on every exit path.
- Make retries bounded, idempotency-aware, cancellable, and observable.

### Data And Security

- Use structured parsers and serializers instead of ad hoc string construction.
- Parameterize database and shell inputs. Avoid dynamic code evaluation for data processing.
- Do not log secrets, tokens, cookies, private keys, personal data, or full sensitive payloads.
- Define integer ranges, overflow behavior, collection limits, and maximum input sizes where relevant.
- Treat deserialization, archive extraction, paths, redirects, and external URLs as trust boundaries.

### Async And Concurrency

- Define ownership, cancellation, timeout, ordering, and shutdown behavior.
- Avoid detached work unless its lifecycle and error reporting are explicit.
- Protect shared mutable state or eliminate sharing.
- Test stale callbacks, retries, duplicate delivery, partial failure, and shutdown races when the design permits them.

## Testing Standard

- Test behavior and invariants, not private implementation details.
- Add a regression test for a fixed bug when the failure is reproducible.
- Cover success, important boundary cases, and meaningful failure paths.
- Prefer deterministic tests; control clocks, randomness, network, filesystem, and concurrency where practical.
- Do not weaken assertions, disable tests, or replace integration coverage with mocks merely to make a change pass.
- Scale coverage with blast radius: shared contracts, migrations, authentication, concurrency, and persistence require broader tests.

Read `references/language-rules.md` for language-specific guidance. Use `references/final-review.md` before completing a substantial change.

## Completion Report

Report changed behavior, important design decisions, verification performed, and any remaining test gap or operational risk. Do not claim checks that were not run.

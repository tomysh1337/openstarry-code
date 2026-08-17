# Language Rules

## Python

- Follow the repository's formatter and type-checking level.
- Prefer context managers for resource ownership.
- Avoid mutable default arguments and broad `except Exception` without re-raising, logging, or a defined fallback.
- Keep sync and async APIs distinct; do not block an event loop with synchronous I/O.
- Use dataclasses, typed models, enums, or validated structures when dictionaries obscure invariants.

## JavaScript And TypeScript

- Preserve strictness; do not introduce `any` to bypass a model problem.
- Distinguish absent, `undefined`, `null`, and empty values deliberately.
- Handle rejected promises and cancellation; clean up listeners, observers, intervals, and effects.
- Avoid stale closures and state updates after component or request disposal.
- Validate runtime input even when compile-time types exist.

## Go

- Return errors with context and keep the original error available for `errors.Is`/`errors.As`.
- Pass `context.Context` through blocking or remote operations; honor cancellation.
- Close response bodies and stop tickers. Avoid goroutine leaks and unbounded fan-out.
- Keep interfaces consumer-owned and small.
- Run `gofmt`, `go vet`, and focused tests; use the race detector for concurrency-sensitive changes when feasible.

## Rust

- Model invalid states out of the type system when it remains readable.
- Avoid `unwrap`/`expect` on runtime-controlled paths unless an invariant is proven locally.
- Minimize `unsafe`; document and test every safety invariant.
- Use explicit error types at library boundaries and contextual errors at application boundaries.
- Run formatting, clippy, and tests appropriate to the crate or workspace.

## Java And Kotlin

- Preserve nullability contracts and avoid sentinel values when a type can express absence.
- Use try-with-resources or structured resource ownership.
- Do not catch broad exceptions unless translating at a boundary or implementing a documented fallback.
- Keep transactions explicit and avoid remote calls while holding locks or transactions without justification.
- Verify thread safety of shared services, caches, and singleton state.

## .NET And C#

- Propagate `CancellationToken` through async operations.
- Dispose `IDisposable`/`IAsyncDisposable` resources and avoid sync-over-async.
- Preserve exception causes and avoid using exceptions for normal control flow.
- Respect nullable reference types; do not suppress warnings without a proven invariant.
- Make service lifetimes and shared mutable state safe for the dependency-injection scope.

## SQL And Persistence

- Use parameterized queries and explicit transactions.
- Make migrations forward-safe, observable, and compatible with mixed application versions when required.
- Define uniqueness, foreign-key, and idempotency guarantees in the database when they are true invariants.
- Test rollback, partial failure, duplicate processing, and large data volumes according to risk.

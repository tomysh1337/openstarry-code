---
name: rust-style-and-clippy
description: >
  Apply rustfmt, Clippy, Rust API Guidelines (high level), rustdoc, and idiomatic
  error and naming style when writing or reviewing Rust code. Use when Rust style,
  clippy, rustfmt, rustdoc, API guidelines, or Cargo workspace formatting and lints
  are in scope.
---

# Rust Style And Clippy

Language-level style for Rust crates and workspaces. Prefer repository config over
generic defaults. Pair with `code-quality-standards` for boundaries, tests, security,
and lifecycle. This skill does not replace domain design or `unsafe` audit depth beyond
style and documentation expectations.

## Use When

- Writing, refactoring, or reviewing Rust (`.rs`) sources, crates, or workspaces.
- User mentions **Rust style**, **clippy**, **rustfmt**, **rustdoc**, or API guidelines.
- CI fails on `cargo fmt --check`, `cargo clippy`, or rustdoc warnings (`missing_docs`).
- Public APIs need naming, builder, error, or docs consistency.
- Choosing idiomatic Rust vs generic OOP-style patterns (`unwrap` chains, stringly errors).

**Do not use as primary when:** the task is non-Rust code, pure reverse engineering of binaries without Rust source, or exploit development. For deep correctness/safety design beyond style, still load `code-quality-standards`.

## Repo Config First

Read and obey the repo before applying generic rules. Conflicts with soundness or security: surface them; do not invent a second style.

| Source | What to take |
| --- | --- |
| `Cargo.toml` / workspace `Cargo.toml` | Edition, lints, features, workspace members |
| `rustfmt.toml` / `.rustfmt.toml` | Edition, width, imports granularity, brace style |
| `clippy.toml` / `.clippy.toml` | MSRV, disallowed methods/types, cognitive complexity |
| `[lints]` / `[workspace.lints]` in Cargo | `rust` and `clippy` lint levels |
| `cargo-hakari` / workspace inheritance | How to touch deps and metadata |
| `Makefile` / `justfile` / CI | Exact `fmt`, `clippy -- -D warnings`, test matrix |
| `README` / `CONTRIBUTING` / `AGENTS.md` | Team Rust conventions, MSRV policy |
| Existing modules | Error type (`thiserror` vs `anyhow`), prelude, logging |

**Defaults only when the repo is silent:**

1. `cargo fmt` (rustfmt stable defaults for the crate edition).
2. `cargo clippy --all-targets --all-features` (or workspace equivalent) with warnings treated as the repo treats them.
3. `cargo test` for touched crates.
4. Rust API Guidelines for public items; rustdoc on public API when the crate is a library.
5. Prefer `Result` + structured errors at library boundaries; application crates may use contextual boxed errors if already standard there.

## Workflow

### 1. Align tooling

```text
cargo fmt
cargo clippy --all-targets --all-features
cargo test
# docs when public API changed:
cargo doc --no-deps
# optional stricter local gate many repos use:
cargo clippy --all-targets --all-features -- -D warnings
```

- Never commit files `cargo fmt` would change.
- Fix Clippy findings with idiomatic rewrites, not blanket `#[allow(...)]`, unless the allow is local, justified, and matches repo practice.
- Respect MSRV if the project sets it (`package.rust-version` or CI toolchain).

### 2. rustfmt scope

- Format all hand-written Rust in the change set.
- Do not fight rustfmt with manual alignment; configure `rustfmt.toml` if the team wants different width/imports.
- Leave generated code (`OUT_DIR`, protobuf, bindgen) to the generator; exclude via rustfmt skip attributes only when the repo already does.

### 3. Clippy discipline

- Run Clippy on the same targets CI runs (`--all-targets`, `--all-features`, workspace package set).
- Prioritize correctness and idioms: `unwrap_used`/`expect_used` (if pedantic/restricted enabled), `panic` in libraries, needless clones, dead code, wrong lifetimes patterns Clippy flags.
- Prefer fixing the design (types, ownership, iterators) over silencing.
- `#[allow(clippy::lint)]` requires a one-line **why** when the lint is wrong-positive for a proven invariant.
- Do not globally allow `clippy::all` in library code to hide debt.

### 4. Naming and structure (high-level API guidelines)

| Item | Guidance |
| --- | --- |
| Crates | `snake_case`, crates.io-safe; avoid `useless` prefixes |
| Types / traits | `UpperCamelCase` |
| Functions / modules / crates paths | `snake_case` |
| Consts / statics | `SCREAMING_SNAKE_CASE` |
| Acronyms | consistent with nearby code (`Http` vs `HTTP` as the crate already does) |
| Conversions | `from`/`try_from`/`as_`/`to_`/`into_` per API Guidelines meaning |
| Fallible constructors | `try_...` or `FnOnce() -> Result` |
| Getters | `fn field(&self) -> &T` without `get_` unless `get` means map lookup |
| Feature flags | documented; additive when possible |

- Keep modules focused; `mod utils` only when the repo already uses that pattern.
- Prefer small traits with clear implementors; avoid kitchen-sink extension traits without need.

### 5. Types, errors, and panics

- Encode illegal states out of the type system when it stays readable (newtypes, enums over bool pairs).
- Library boundaries: explicit error types (`thiserror` or hand-written) with `Display` + `Error` + `From` where useful.
- Application boundaries: contextual errors (`anyhow`/`eyre`) only if the crate already uses them.
- Reserve `unwrap`/`expect` for:
  - tests;
  - proven invariants immediately local (document why in `expect` message);
  - const/context where failure is truly unrecoverable at process start.
- Minimize `unsafe`; every block needs a safety comment stating the invariant. Prefer safe wrappers.
- Do not use `clone` to satisfy the borrow checker by default — restructure lifetimes or ownership when Clippy/`needless_pass_by_value` points at a clearer API.

### 6. rustdoc

- Public items: `///` docs describing behavior, errors, panics, safety, and feature gates.
- Crate-level docs in `lib.rs` (`//!`) for libraries: purpose, example, feature flags.
- Use `[`Item`]` intra-doc links; keep examples compiling (`cargo test --doc`) when examples are non-trivial.
- Document `Panic` conditions and `Error` variants that callers must handle.
- `#[cfg_attr(docsrs, feature(...))]` only when the repo already docsrs-gates features.

### 7. Verify before finish

1. `cargo fmt --check` clean.
2. Clippy clean at the repo’s lint level on touched packages.
3. Tests for changed behavior; doc-tests if examples or public contracts changed.
4. Public API rustdoc filled in; no new dead `pub` without reason.
5. Diff free of unrelated edition-wide reformat unless requested.

## Good And Bad Examples

### rustfmt / module layout

```rust
// GOOD — rustfmt-friendly imports; clear module role
use std::io::{self, Read};

use serde::{Deserialize, Serialize};

use crate::error::Error;

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub endpoint: String,
}
```

```rust
// BAD — hand-aligned; noisy wildcard; public fields with no docs in a library
use std::io::*;
use serde::{Serialize,Deserialize};
use crate::error::Error;
pub struct Config{pub endpoint:String}
```

### Errors vs unwrap

```rust
// GOOD — structured error; map context at the boundary
pub fn load(path: &Path) -> Result<Config, Error> {
    let data = std::fs::read_to_string(path).map_err(|e| Error::Io {
        path: path.to_path_buf(),
        source: e,
    })?;
    Ok(toml::from_str(&data)?)
}
```

```rust
// BAD — library panics on normal I/O; stringly typed
pub fn load(path: &Path) -> Config {
    let data = std::fs::read_to_string(path).unwrap();
    toml::from_str(&data).unwrap()
}
```

### Clippy-minded iterators

```rust
// GOOD — idiomatic iterator; no needless collect/clone
pub fn names(users: &[User]) -> Vec<&str> {
    users.iter().map(|u| u.name.as_str()).collect()
}
```

```rust
// BAD — index soup; clones everything
pub fn names(users: &[User]) -> Vec<String> {
    let mut out = Vec::new();
    for i in 0..users.len() {
        out.push(users[i].name.clone());
    }
    out
}
```

### rustdoc and API surface

```rust
// GOOD — docs name the type; errors and panics covered
/// Token bucket rate limiter for a single key space.
///
/// # Errors
///
/// Returns [`Error::Overflow`] if `rate` is zero.
pub fn open(rate: u32) -> Result<Limiter, Error> {
    // ...
}
```

```rust
// BAD — pub with no docs; vague name; hidden panic
pub fn do_it(x: u32) -> Limiter {
    assert!(x > 0);
    // ...
}
```

### Allow attributes

```rust
// GOOD — narrow allow + reason tied to invariant
#[allow(clippy::unwrap_used)] // alphabet is const non-empty; index built from same array
fn letter(i: usize) -> char {
    const ALPHABET: &[u8] = b"abcdef";
    ALPHABET.get(i).copied().unwrap() as char
}
```

```rust
// BAD — crate-wide silence
#![allow(clippy::all)]
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| rustfmt, Clippy, rustdoc, Rust API style | `rust-style-and-clippy` (this) | `code-quality-standards` |
| Feature work / bugfix in Rust | domain skill if any | this + `code-quality-standards` |
| Unsafe correctness / soundness deep dive | `code-quality-standards` | this for docs/`fmt`/clippy gate |
| FFI / bindgen noise | this for safe wrappers style | repo FFI docs |
| Non-Rust languages | matching language skill / `code-quality-standards` | — |
| Binary reverse of a Rust build without source | `binary-re` | not this |

## Checklist

- [ ] Edition, MSRV, `rustfmt.toml`, Clippy/Cargo lints read and applied
- [ ] `cargo fmt` clean on touched crates
- [ ] Clippy run at repo-equivalent flags; new `allow`s justified and scoped
- [ ] No new library `unwrap`/`expect` on runtime input without invariant proof
- [ ] Errors: typed at lib boundary; context preserved; `Display` useful
- [ ] Public items rustdoc’d; crate-level `//!` for libraries when API changed
- [ ] Naming follows snake_case / UpperCamelCase conventions of the crate
- [ ] `unsafe` minimized with SAFETY comments when present
- [ ] Feature flags documented; additive behavior preferred
- [ ] Tests (and doc-tests if relevant) run; report what ran
- [ ] No drive-by full-workspace reformat unless requested
- [ ] Conflicts between team config and these rules called out explicitly

## Rules

- Repository conventions outrank this skill unless they harm soundness, safety, or security.
- Do not “fix” Clippy by disabling lints project-wide without explicit team direction.
- Prefer small, fmt-clean diffs; do not mix massive style churn with behavior changes.
- Do not claim `fmt`/`clippy`/`test` passed unless those commands were actually run.
- Generated Rust: regenerate from sources; do not hand-edit as a style fix.

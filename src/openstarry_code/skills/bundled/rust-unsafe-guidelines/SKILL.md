---
name: rust-unsafe-guidelines
description: >
  Decide when Rust `unsafe` is justified, document soundness invariants, minimize
  unsafe surface, and verify with Miri and review checklists. Use when writing,
  reviewing, or refactoring `unsafe` blocks, raw pointers, FFI, transmute,
  interior mutability that needs unsafe, SAFETY comments, or Miri runs in Rust.
---

# Rust Unsafe Guidelines

Soundness-first rules for `unsafe` in Rust crates. Prefer safe APIs; treat every
`unsafe` block as a contract that must stay true for all callers and futures.
Hand off formatting, Clippy, rustdoc style, and idiomatic safe Rust to
`rust-style-and-clippy`. Pair with `code-quality-standards` for tests, boundaries,
and production change hygiene.

## When To Use

- Adding, changing, or reviewing `unsafe` blocks, `unsafe fn`/`trait`/`impl`, or `#![deny(unsafe_code)]` exceptions.
- Raw pointers, `MaybeUninit`, `transmute`, union fields, manual drop glue, or custom smart pointers.
- FFI (`extern "C"`, bindgen output, C/C++/OS calls) and `Send`/`Sync` impls.
- User asks for SAFETY comments, soundness proofs, or **Miri** validation.
- Auditing crates that expand unsafe surface or silence `unsafe_code` / Clippy unsoundness lints.

**Do not use as primary when:** the work is pure rustfmt/Clippy/API style with no unsafe (use `rust-style-and-clippy`); binary RE without Rust source (`binary-re`); or CTF exploit construction without a codebase safety goal.

## Repo Config First

Repository policy outranks generic preference on where unsafe may live; it does **not** outrank soundness.

| Source | What to take |
| --- | --- |
| `Cargo.toml` / workspace lints | `unsafe_code`, `unsafe_op_in_unsafe_fn`, crate features |
| `clippy.toml` / `[lints]` | `undocumented_unsafe_blocks`, disallowed methods |
| `#![forbid(unsafe_code)]` modules | Keep forbidden; isolate exceptions in dedicated modules |
| CI / `justfile` / Makefile | Miri job, sanitizers, target matrix |
| Existing `// SAFETY:` style | Match comment shape and placement |
| `README` / `CONTRIBUTING` / `AGENTS.md` | Team unsafe/FFI policy, MSRV, no-std constraints |
| FFI / bindgen layout | Generated vs hand wrappers; where SAFETY lives |

**Defaults when the repo is silent:** forbid new crate-wide unsafe; confine unsafe to small modules; require `// SAFETY:` (or `# Safety`) on every block and unsafe fn; run Miri on tests that exercise unsafe paths when feasible.

## Workflow

### 1. Justify before writing

Use `unsafe` only when a **safe** API cannot express the needed guarantee or performance boundary without it, commonly:

- FFI to foreign code with documented preconditions.
- Building safe abstractions over raw memory (pools, arenas, custom containers) with a proven invariant.
- Performance-critical paths where the optimizer cannot see a bound you have already checked (document the check).
- Implementing `Send`/`Sync` or low-level concurrency primitives with a clear ownership story.

Do **not** use unsafe to “skip the borrow checker,” silence Clippy, or avoid designing ownership. Prefer safe wrappers (`slice::get`, `NonNull`, `Pin`, standard collections) first.

### 2. Minimize surface

- Prefer `unsafe` **blocks** inside safe functions over public `unsafe fn` when preconditions can be enforced at the boundary.
- Keep unsafe regions **short** and contiguous; pull pure computation into safe helpers.
- Isolate FFI and pointer work in a dedicated module (`ffi`, `raw`, `sys`) behind a safe public API.
- Avoid `transmute` when `from_ne_bytes`, `bytemuck` (if allowed), pointer casts with provenance-aware APIs, or `MaybeUninit` init patterns suffice.
- Do not spread the same invariant across many crates without a single owning abstraction.

### 3. Document invariants

Every `unsafe` block and every `unsafe fn` must state:

1. **What** is assumed true (alignment, initialization, provenance, aliasing, lifetime, thread exclusivity, FFI validity).
2. **Why** it is true here (prior check, type invariant, caller contract, foreign docs).
3. **What** would break if the assumption fails (UB class: data race, invalid value, use-after-free).

Public `unsafe fn` / `unsafe trait`: rustdoc `# Safety` section is mandatory. Safe wrappers: document what the type guarantees so maintainers do not re-open UB later. Prefer type-level enforcement (newtypes, sealed tokens, private fields) over comment-only invariants when practical.

### 4. Write and review for soundness

- Uphold stacked-borrows / tree-borrows-friendly aliasing: no aliasing `&mut`; no invalid shared XOR mutable stories.
- Initialize before read; track `MaybeUninit` state explicitly.
- Honor drop and panic safety: no double-free, no leak of half-built invariants on unwind when the type claims otherwise.
- `Send`/`Sync`: justify exclusivity and race freedom; never impl for convenience alone.
- FFI: match C layout/ABI, nullability, ownership of buffers, errno/thread-local contracts, and free/allocator pairing.
- Prefer `ptr::read`/`write`, `NonNull`, `offset`/`add` with in-bounds proofs over ad hoc integer address math.

### 5. Verify with Miri and tests

```text
# Nightly often required for full Miri; match repo toolchain docs
cargo +nightly miri test
# Scope to the crate or test that hits unsafe:
cargo +nightly miri test -p <crate> -- <filter>
```

- Exercise every unsafe path with unit/integration tests Miri can run (avoid opaque foreign calls when pure-Rust models exist).
- For FFI that Miri cannot execute, test the safe wrapper’s preconditions in pure Rust and document residual foreign risk.
- Optionally: ASan/TSan on supporting targets for native interop; do not treat them as a full substitute for Miri on Rust UB.
- After refactors that touch lifetimes, interior mutability, or drop glue, re-run Miri even if “logic” tests pass.

### 6. Unsafe review checklist (every change)

1. Is there a safe alternative with acceptable cost?
2. Is the unsafe region minimal and behind a safe API?
3. Are all preconditions checked or type-enforced before the block?
4. Are SAFETY / `# Safety` comments complete and accurate?
5. Do panics, `?`, and early returns preserve invariants?
6. Are `Send`/`Sync` and lifetime claims still true?
7. Did Miri (or documented exception) cover the path?

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Justify, document, minimize, review `unsafe` / Miri | **This skill** | `code-quality-standards` |
| rustfmt, Clippy, rustdoc, idiomatic **safe** style | `rust-style-and-clippy` | this only if unsafe is present |
| Production feature/fix touching unsafe modules | domain skill if any | this + `rust-style-and-clippy` + CQS |
| Naming/comments only (no soundness) | `comment-writing-standards` / `rust-style-and-clippy` | — |
| Binary RE of a Rust artifact without source | `binary-re` | not this |

Always hand off **style tooling** (fmt, Clippy lint noise, public API polish) to `rust-style-and-clippy` after soundness is settled.

## Output Checklist

- [ ] Unsafe justified; safe alternatives considered and rejected with reason
- [ ] Surface minimized (module boundary + short blocks; safe public API where possible)
- [ ] SAFETY / `# Safety` documents assumptions, proof, and UB if violated
- [ ] Aliasing, init, drop/panic, FFI ABI, and `Send`/`Sync` reviewed
- [ ] No unjustified `transmute`, unbounded offset, or convenience `unsafe impl`
- [ ] Miri (or explicit, documented skip with residual risk) run on relevant tests
- [ ] Style/fmt/Clippy deferred to or paired with `rust-style-and-clippy`
- [ ] Repo `unsafe_code` / forbid policy and CI gates respected
- [ ] Diff free of drive-by unsafe expansion outside the change’s goal

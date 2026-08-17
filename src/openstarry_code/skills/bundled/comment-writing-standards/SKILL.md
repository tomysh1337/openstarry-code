---
name: comment-writing-standards
description: >
  Standards for when and why to write comments, what not to narrate, and how to
  document decisions, invariants, and non-obvious constraints in code. Use when
  writing comments, reviewing comment quality, documenting intent, 写注释,
  注释规范, comment style, or deciding whether code needs a comment at all.
  Complements code-quality-standards; does not replace naming or structure work.
---

# Comment Writing Standards

Clean Code guidance: prefer expressive code; comments explain *why* and *constraints*,
not *what* syntax already says. A wrong comment is worse than none—update or delete
comments in the same change as the code they describe.

## When To Use

- Adding, editing, or reviewing comments, docstrings, module headers, or `TODO`/`FIXME`.
- Reviewers ask “why this way?” or “is this safe under X?” after the code is correct.
- Mixed Chinese/English teams: align comment language, tone, and placement.
- Naming pass done; residual non-obvious algorithms, trade-offs, or external contracts remain.
- **Not** renames alone → `naming-conventions-general`. **Not** full quality review → `code-quality-standards`.

## Repo Config First

1. Read `AGENTS.md` / `CONTRIBUTING` / in-repo style guides—they outrank this skill.
2. Honor docstring/lint tools (`pydocstyle`, TSDoc, rustdoc, godoc) and rules that forbid noisy comments.
3. Match nearby files: EN vs 中文, comment syntax, line length, required public API docs.
4. If the repo bans narrative comments or requires bilingual public docs, follow that. Surface conflicts; do not invent a second house style.

## Core Rules

| Prefer | Avoid |
| --- | --- |
| Intent, decision, trade-off | Restating the next line in EN/中文 |
| Invariants and pre/post conditions | “Loop over items”, “increment i” |
| Compatibility / bug / law / protocol notes | Change-log comments—use VCS |
| Subtle failure modes; stable ticket/RFC links | Apologies for bad code; pasted dumps |

**Language policy (mixed codebases).** Public API docs: product primary language unless exports must be English. Inline comments: match the package majority; do not mix languages mid-sentence. Keep **canonical** protocol/vendor/metric tokens (often English) even inside Chinese prose so search stays consistent. Never ship machine-translated “why” without a human pass.

## Workflow

1. **Can the name carry it?** Clearer symbol or extracted helper first. If the comment only renames the code, delete it and rename.
2. **Classify the gap.** *Decision* (A not B), *invariant*, *external contract* (API/protocol/DB/law), *algorithm subtlety* (order, units, edge), *workaround* (vendor/OS/bug), *security/privacy*. If none apply, leave silent.
3. **Place where readers look.** File: purpose and non-goals. Public type/fn docstring: caller contract (I/O, errors, side effects)—not an implementation tour. Block: immediately above the subtle code. EOL: short unit/flag notes only.
4. **Write the constraint, not the story.** “Must not re-enter while holding `mu`” beats “we lock because of an old concurrency bug.”
5. **Debt and workarounds.** `TODO(owner): action — ticket`. `WORKAROUND: …; remove when …; see ISSUE-…`. No bare `TODO`; no commented-out code (use VCS).
6. **Public docstrings.** Observable behavior; units; nil/null/throws; thread-safety when types hide it. Do not restate parameter names.
7. **Diff review.** Every touched comment still true? Still needed after rename? Secrets/PII? Dead comments on deleted code removed?

## Good vs Bad Examples

```python
# bad — narrates syntax
# increment retry counter
retry_count += 1

# good — silence; name is enough
retry_count += 1
```

```go
// good — decision + exit criterion
// Linear scan over map: n <= 8; map alloc shows in hot path (BenchmarkResolve-8).
// Revisit if allowlist grows past ~32.
for _, p := range allowlist {
    if p == path {
        return true
    }
}
```

```typescript
// good — invariant
// INVARIANT: balanceCents is never negative on return. Oversized debit clamps + Underflow.
```

```java
// bad — lies after refactor (now Optional / often external ref)
// Returns the user id
public Optional<String> resolve(User u) { ... }
```

```python
# good — CN+EN; wire token seq stays canonical
# 协议要求：seq 必须单调递增；重连从 last_ack+1 起，禁止从 0 重置。
# Retransmit window inclusive of last_ack (design/seq.md §3.2).
```

```c
// good workaround
// WORKAROUND(win10): Sleep(0) after CancelIoEx or completion races (b/48211). Drop on Win11+.

// bad logbook
// 2020-01-12 John fixed crash
```

```rust
// good — security constraint
// Never log `token` or raw Authorization; redact to last 4 chars only.
```

## What Not To Comment

- Types/getters/control flow the language already expresses.
- Commented-out code; jokes/insults; secrets, hostnames, customer data, full tokens.
- Docstring duplicated on every private helper in the same file.

## Routing

| Need | Skill |
| --- | --- |
| Comment when/why/what not | **This skill** |
| Symbol/file/domain names | `naming-conventions-general` |
| Maintainability, errors, tests, security hygiene | `code-quality-standards` |
| Feature implement/review | Domain skill + `code-quality-standards`; this skill for comment pass |
| Protocol meaning from captures | Domain RE skill first; this skill for durable in-code notes |

## Output Checklist

- [ ] Tried rename/extract before adding comments
- [ ] Each comment is decision, invariant, contract, subtlety, workaround, or security note
- [ ] No syntax narration; no commented-out blocks; no secrets/PII
- [ ] Comments updated/removed with the code they describe
- [ ] TODOs have owner + action (+ ticket); workarounds have removal condition
- [ ] Language matches package policy; domain tokens keep canonical spelling
- [ ] Public docstrings cover contract, not implementation tour
- [ ] Aligned with repo AGENTS.md / linter / docstring conventions

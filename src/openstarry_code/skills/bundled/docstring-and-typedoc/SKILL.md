---
name: docstring-and-typedoc
description: >-
  Decide when and how to write Python docstrings (PEP 257) and JS/TS
  JSDoc/TSDoc for public APIs, with templates and anti-patterns. Use when
  docstring, JSDoc, TSDoc, 文档字符串, API docs comments, typedoc, pydoc,
  or documenting exported functions/classes/modules.
---

# Docstring And Typedoc

## When To Use

- Writing or reviewing documentation comments on public Python or JS/TS APIs.
- Choosing between **no comment**, **short summary**, and **structured tags**.
- Generating docs via Sphinx/MkDocs (Python) or TypeDoc/API Extractor (TS).
- User mentions: docstring, JSDoc, TSDoc, 文档字符串, typedoc, pydoc.

Use **`python-style-and-typing`** for PEP 8 and type hints. Use **`code-quality-standards`** for behavior, errors, and tests. This skill owns **documentation comments**, not README design.

## Repo Config First

1. Find existing conventions before inventing a style:
   - Python: PEP 257 one-liners vs Google / NumPy / reST / Sphinx Napoleon; `docs/`, mkdocs, sphinx `conf.py`.
   - JS/TS: TSDoc, TypeDoc, API Extractor, ESLint `jsdoc/*` or `eslint-plugin-tsdoc`.
2. Match nearby public modules: section order, tag set, language (EN vs CN).
3. Prefer the project’s documentation generator tags over personal favorites.
4. In TypeScript, **types live in the type system** — do not restate parameter types in JSDoc unless the file is plain JS or the generator requires tags.
5. Never invent false docs. If unclear, read code/tests — do not guess contracts.

## When To Write (And When Not)

**Write or update when:** public library/SDK surface; non-obvious invariants, units, side effects, or failures; security/async constraints; docs tooling extracts comments.

**Skip or keep minimal when:** private helpers with clear names/types; pure one-liners; restating the type signature; comments that will rot (“called from Foo” lists).

**Update docs in the same change** that alters behavior, defaults, or errors. Stale docs are worse than none.

## Workflow

1. **Identify audience** — SDK user, internal peer, or future maintainer.
2. **State the contract** — inputs, outputs, side effects, errors, cancellation, idempotency.
3. **Choose form** — Python module/class/function docstring (Google/NumPy/reST per repo); TS TSDoc on exports (`@public`/`@internal` if API Extractor); JS without types: JSDoc `@param`/`@returns` for editors/`checkJs`.
4. **Summary first line** — complete sentence or imperative; keep ~one line when possible.
5. **Structured sections only for real complexity** — units, raises, examples.
6. **Link, don’t duplicate** — long rationale belongs in design docs; keep the docstring operational.
7. **Verify** — docs build / TypeDoc-Sphinx tag warnings; re-read against tests.

## Templates

**Python (Google-style sketch; adapt to repo):**

```python
def transfer(amount: Decimal, to: AccountId, *, memo: str | None = None) -> Receipt:
    """Move funds to ``to`` and return a settlement receipt.

    Args:
        amount: Positive decimal in major currency units.
        to: Destination account id (already validated).
        memo: Optional short note stored with the ledger entry.

    Returns:
        Receipt with ``tx_id`` and settlement time (UTC).

    Raises:
        InsufficientFunds: Balance would go negative.

    Note:
        Not idempotent; supply a dedupe key at the API edge.
    """
```

**TypeScript (TSDoc)** — types on the signature, not restated:

```ts
/**
 * Move funds to `to` and return a settlement receipt.
 * @param amount - Positive major-unit decimal string
 * @throws InsufficientFundsError when balance would go negative
 * @public
 */
export function transfer(amount: string, to: AccountId): Promise<Receipt>;
```

**JavaScript (JSDoc when no TS):** `@param {string} path` / `@returns {import('./types').Config}` on exports that editors/`checkJs` need.

## Good Vs Bad Examples

| Good | Bad |
| --- | --- |
| Units/side effects/errors types cannot express | “Takes int, returns float” / narrates syntax |
| TSDoc summary; types stay on the signature | `@param {string} id` duplicating `id: string` in `.ts` |
| Docs updated with behavior; examples match API | “Never raises” while code re-raises; stale params |

```python
# Good: """Return delay seconds for ``attempt`` (0-based), capped at 30s."""
# Bad:  """Takes attempt as int and returns a float."""
```

## Routing

| Need | Skill |
| --- | --- |
| Docstrings / JSDoc / TSDoc when-to-write and templates | **This skill** (primary) |
| Python PEP 8, type hints, mypy/pyright, black/ruff | `python-style-and-typing` |
| Production change quality: errors, security, tests | `code-quality-standards` (helper on production changes) |
| OpenAPI/Swagger HTTP surface inventory | `api-recon-and-docs` |

Always apply **`code-quality-standards`** when the same change implements behavior; docs must match real contracts.

## Output Checklist

- [ ] Repo docstring/TSDoc convention identified (Google/NumPy/reST/TSDoc/…)
- [ ] Documented surface is public or non-obvious; private noise avoided
- [ ] First line is a useful summary; no type-restating filler
- [ ] Side effects, units, errors, and defaults captured when relevant
- [ ] Tags valid for the docs toolchain (TypeDoc/Sphinx/API Extractor)
- [ ] TS: types not duplicated from signatures unless required (JS or generator)
- [ ] Docs updated in lockstep with behavior changes
- [ ] No secrets, internal hostnames, or live credentials in examples

## Rules

- Prefer accurate silence over confident fiction.
- Do not use docstrings as a substitute for clear names or proper types.
- Keep examples minimal, copy-pasteable, and consistent with current APIs.
- Prefer English unless the repository’s public docs already use another language.
- Mark experimental/internal APIs (`@internal`, “unstable”).
- Redact tokens and PII from sample payloads in comments.

---
name: naming-conventions-general
description: >
  General naming conventions for variables, functions, types, files, and packages:
  domain language, consistency, and avoiding Hungarian notation or noisy prefixes.
  Use when naming, renaming, choosing identifiers, 命名规范, 变量命名, 函数命名,
  file naming, or when reviews flag unclear or inconsistent names. Pairs with
  code-quality-standards; does not replace repo style guides or formatters.
---

# Naming Conventions (General)

Google-style / Clean Code naming: names reveal intent; length scales with scope; one
concept maps to one word; consistency beats cleverness. **Case laws** (snake vs camel)
come from the repo and ecosystem—this skill does not invent a global case standard.

## When To Use

- Introducing or renaming variables, parameters, functions, types, constants, files, packages.
- Reviews: “what is `data`?”, “why `strTemp`?”, mixed EN/中文 identifiers.
- Aligning APIs with domain (ubiquitous) language before comments paper over bad names.
- **Not** comment content → `comment-writing-standards`. **Not** full quality gates → `code-quality-standards`.

## Repo Config First

1. Adopted guides (Google, PEP 8, Effective Go, rustc API, C# FDG) plus **project** overrides: `AGENTS.md`, eslint/ruff/clippy/checkstyle, editorconfig.
2. Match neighboring names and export patterns over purity. Do not introduce a second convention in one file without a migration plan.
3. Formatters do not fix names; run case/export linters after renames.
4. Stable/public APIs need alias, deprecation, or versioning; private locals may rename in-change.
5. Repo rules outrank this skill unless a name creates security/correctness hazard (e.g. “safe” name that still logs secrets)—raise the conflict.

## Core Principles

| Principle | Practice |
| --- | --- |
| Reveal intent | `elapsedMs`, `isRetryable` — not `t`, `flag`, `x1` |
| Domain language | `Order` not `DataObject`; product terms over CS filler |
| One word per concept | Don’t mix `fetch`/`get`/`retrieve` for the same op in one package |
| Scope ↔ length | `i` in a 3-line loop OK; package-level `i` is not |
| Searchable | `generatedAt` not `genymdhms` |
| No encoding schemes | No Hungarian (`lpsz`, `iCount`) or new `m_`/`s_` unless already required |
| Boolean predicates | `isReady`, `hasChildren`, `canRetry`; prefer `isEnabled` over `isNotDisabled` |
| Units in name | `timeoutMs`, `sizeBytes` when types are unitless |
| Side effects visible | `saveUser` / `writeCache` vs pure `userFromRow` |

**Chinese/English codebases.** Prefer **English identifiers** unless the whole repo mandates Chinese symbols. UI copy may be Chinese; code, paths, and wire bindings stay English and match schema when fixed. Never mix scripts in one token (`用户Id` → `userId`).

## By Symbol Kind

- **Vars/params:** nouns; qualify (`activeUsers`, `rawBody`/`parsedBody`). Avoid bare `temp`/`data`/`info`/`obj`/`retval`.
- **Functions:** verbs for actions (`createInvoice`); queries follow local idiom (`empty` in Go vs `isEmpty` in Java). `getX` must not silently mutate (command–query).
- **Types:** nouns (`PaymentSchedule`). Interfaces by role (`UserRepository`, `Closeable`)—force `I` only if the repo already does. Enums: singular type + clear cases.
- **Constants:** meaning not value (`MaxRetries` not `THREE`); case per language.
- **Files/packages:** ecosystem defaults (`snake_case.py`, `PascalCase.cs`, Go short lowercase). Name after primary export. Avoid `utils2`, `helpers_new`, vague `common`.
- **Tests:** mirror unit + behavior or bug id (`handles_empty_jwks`).

## Workflow

1. **Inventory:** domain thing, role (id/count/duration/handle), mutability, units.
2. **Precedent:** reuse the package’s established term; dedicated rename if that term is wrong.
3. **Ecosystem case (defaults, not overrides):** Python PEP 8 snake/Pascal/UPPER; Java/TS/C# camel methods + Pascal types; Go mixedCaps + export capital; Rust snake fns / Pascal types / SCREAMING consts.
4. **Strip noise:** `strName`→`name`, `listUsers`→`users` when types suffice; drop empty `Info`/`Data`/`Manager`/`Helper`.
5. **Disambiguate:** `billingAccount` vs `loginAccount`, not `account2`.
6. **Rename with tools:** IDE rename; change serialization tags only when wire format intentionally changes.
7. **Searchability:** one primary term under `rg`. If wire name differs (`uid` vs `userId`), map explicitly; short comment only if needed (`comment-writing-standards`).
8. **Consistency scan:** same lifecycle verbs in a module (`start`/`stop` vs `open`/`close`); no single-letter names outside tiny scopes.

## Good vs Bad Examples

```python
# bad
d, tmp = {}, load()
def proc(x): ...
str_name, arr_list = user.name, []

# good
orders_by_id: dict[OrderId, Order] = {}
raw_config = load_config()
def apply_discount(order: Order) -> Order: ...
name, pending_ids = user.name, []  # pending_ids: list[OrderId]
```

```typescript
// bad: function data(d: any); const flag = true; const ms = 5;
// good:
function serializeInvoice(invoice: Invoice): string { ... }
const isFeatureEnabled = true;
const debounceMs = 5;
```

```go
// bad: type IUserManager struct{}; func (u *IUserManager) Do()
// good:
type UserRepository struct{}
func (r *UserRepository) FindByID(ctx context.Context, id UserID) (*User, error)
```

```text
# files bad: Utils.java, misc_helpers2.py, CommonFinal.cs
# files good: InvoiceTaxCalculator.java, order_repository.py, PaymentSchedule.cs
```

```java
// wire vs domain — good mapping
@JsonProperty("uid") String userId;
```

```c
// bad Hungarian: char *lpszPath; int nCount; bool bIsOk;
// good: const char *path; int count; bool ok;  // is_valid at wider scope
```

## Anti-Patterns

- Meaningless stacks: `AbstractFactoryProviderImpl` with no domain noun.
- Lies: `getUser` creates; `safeParse` panics; `empty` allocates.
- Invented abbreviation piles (`mgrSvcCtl`); jokes/offensive names; `HandlerHandler`.
- Renaming one layer only so DB, JSON, and type disagree without an explicit map.

## Routing

| Need | Skill |
| --- | --- |
| Identifier / file / domain naming | **This skill** |
| Comments, invariants, 写注释 | `comment-writing-standards` |
| Structure, errors, tests, security, verification | `code-quality-standards` |
| Feature work with renames | Domain skill + this skill + `code-quality-standards` baseline |
| Protocol field recovery | Domain RE/API skill first; then stable domain names here |

## Output Checklist

- [ ] Domain language; no bare `data`/`temp`/`info`/`obj` without a noun
- [ ] Case/export rules match language + repo linters
- [ ] One vocabulary for the same concept/operation in the package
- [ ] Boolean predicates; units when types are unitless
- [ ] No new Hungarian/random prefixes unless codebase-standard
- [ ] English identifiers (unless policy otherwise); no mixed-script tokens
- [ ] Public renames note compatibility or intentional breakage
- [ ] Wire/schema vs domain mapping explicit when they differ
- [ ] Call sites/tests updated; search finds one primary term

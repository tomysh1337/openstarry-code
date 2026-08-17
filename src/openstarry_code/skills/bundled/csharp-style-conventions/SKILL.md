---
name: csharp-style-conventions
description: >
  Apply C# and .NET naming conventions, XML documentation comments, and nullable
  reference type style when writing or reviewing C# code. Use when C# style, .NET
  naming, XML docs, nullable reference types, EditorConfig/StyleCop alignment, or
  public API documentation for C# / .NET projects.
---

# C# Style Conventions

## Use When

- Writing or reviewing C# for **naming**, file layout, or API surface consistency.
- Adding or fixing **XML documentation** (`///`) on public types and members.
- Working under **nullable reference types** (NRT): annotations, flow, and suppression discipline.
- Aligning with .NET runtime / Framework Design Guidelines-style naming at a high level.
- Touching `.editorconfig`, StyleCop Analyzers, Roslyn analyzers, or `Directory.Build.props` style settings.

Do **not** use this skill as the primary path for DI lifetimes, async/cancellation correctness, security, or test strategy — route those to `code-quality-standards` (and domain skills).

## Repo Config First

Repository conventions **outrank** this skill’s defaults. Before inventing style:

1. Read `CONTRIBUTING*`, coding docs, `AGENTS.md` / `Claude.md`, and solution README sections.
2. Read style configuration in discovery order:
   - `.editorconfig` (naming rules, indent, `dotnet_` / `csharp_` options)
   - `Directory.Build.props` / `Directory.Packages.props` (e.g. `Nullable`, `TreatWarningsAsErrors`, analyzer packages)
   - StyleCop / Roslynator / Meziantou / other analyzer `.ruleset` or `.globalconfig`
   - `.globalconfig`, `stylecop.json`, `.ruleset`
3. Match **neighboring code** in the same project: field prefixes (`_`, `s_`, none), `this.` usage, file-scoped namespaces, primary constructors, XML-doc density.
4. If repo config conflicts with this skill, **follow the repo**. Surface correctness/security conflicts instead of dual style.
5. Build/analyze touched projects (`dotnet format`, `dotnet build`) so naming and nullable diagnostics stay clean.

## Naming (.NET High-Level)

| Kind | Convention | Examples |
| --- | --- | --- |
| Namespaces | PascalCase, company/product hierarchy | `Contoso.Billing` |
| Classes, structs, records, enums, delegates | PascalCase | `PaymentService`, `OrderId` |
| Interfaces | PascalCase with `I` prefix | `IInvoiceRepository` |
| Type parameters | PascalCase; often `T` prefix | `T`, `TKey`, `TRequest` |
| Methods, properties, events | PascalCase | `FindById`, `IsActive` |
| Local functions | PascalCase (common) or match neighbors | `ParseCore` |
| Parameters, locals | camelCase | `orderId`, `itemCount` |
| Private instance fields | match repo: `_camelCase` (common) or `camelCase` | `_options` |
| Private static fields | match repo: `s_camelCase` or `_camelCase` | `s_instance` |
| Public fields (rare) | PascalCase | `MinValue` |
| Constants / static readonly | PascalCase (prefer over SCREAMING) unless repo uses UPPER | `MaxRetryCount` |
| Async methods | `Async` suffix when returning awaitable | `SaveAsync` |
| Boolean members | predicate language | `IsReady`, `HasChildren`, `CanRetry` |
| Attributes | PascalCase with `Attribute` suffix on type | `JsonIgnoreAttribute` → usage `[JsonIgnore]` |
| Test methods | repo pattern (Method_Scenario_Expected or descriptive) | match neighbors |

- Prefer clarity over abbreviation; keep domain acronyms consistent (`Id`, `Http`, `Xml` casing as in BCL).
- Do not use Hungarian notation (`strName`, `iCount`).
- Avoid vague names (`Manager2`, `Helper`, `data`, `temp`) on public API.

## XML Documentation

### When to write `///`

| Surface | Expectation |
| --- | --- |
| Public / protected API of libraries, packages, shared projects | **Yes** — types and non-obvious members |
| Internal app code | When contracts, units, or edge cases are non-obvious |
| Trivial property getters/setters | Usually **no** unless value constraints or side effects exist |
| Overrides with clear base docs | Prefer inheritance; add docs only for behavioral differences |
| Private helpers | Good names first; XML docs only for non-obvious algorithms |

Enable or respect `GenerateDocumentationFile` when the project already treats missing docs as warnings (`CS1591`) — fix docs on **touched public surface**, do not mass-document unrelated APIs unless asked.

### What to put in XML docs

- `<summary>`: one clear purpose statement (what, not implementation walkthrough).
- `<param>`, `<returns>`, `<exception>`: only when they add information beyond the signature.
- `<remarks>`: thread-safety, idempotency, performance, units, ordering guarantees.
- `<value>` for non-obvious properties; `<seealso>` / `<c>` / `<see cref="..."/>` for cross-links.
- Document nullability in prose only when NRT annotations are insufficient or for shipped multi-TFM confusion.

```csharp
/// <summary>
/// Settles a pending payment against the configured acquirer.
/// </summary>
/// <param name="paymentId">Stable client-visible payment identifier.</param>
/// <param name="amount">Amount in minor units (e.g. cents); must be positive.</param>
/// <returns>The settled payment view.</returns>
/// <exception cref="PaymentNotFoundException">Thrown when <paramref name="paymentId"/> is unknown.</exception>
/// <remarks>Idempotent for the same <paramref name="paymentId"/>.</remarks>
public Task<Payment> SettleAsync(string paymentId, long amount, CancellationToken cancellationToken = default)
```

## Nullable Reference Types Style

- Prefer project-wide `<Nullable>enable</Nullable>` (or match existing per-project setting). Do not disable NRT to silence warnings.
- Express absence with nullable annotations (`string?`, `Foo?`) and clear flow; prefer early returns over nested null checks when readable.
- Use `is null` / `is not null` patterns consistent with neighbors (C# 7+ / 9+ idioms as already used).
- For definite assignment and post-construction init, prefer `required`, constructors, or `init` over scattered `null!`.
- `null!` / `!` (null-forgiving) only when an invariant is **proven** and NRT cannot see it (e.g. framework callbacks). Comment the invariant if non-local.
- Do not suppress nullable warnings with broad `#pragma` or global “ignore CS86xx” without a written reason.
- Argument validation: `ArgumentNullException.ThrowIfNull` (or repo helper) at **public** boundaries; trust internal calibrated flow where NRT already enforces.
- Collections: decide empty vs null deliberately; prefer empty enumerable for “no items” when the API is public and callers iterate.
- Generics: annotate `T?` correctly depending on `class`/`struct` constraints; avoid lying annotations to force compile.

## Structure Notes (high-level)

- Prefer **file-scoped namespaces** when the project already uses them.
- One primary public type per file is common; match neighbors for partials and nested types.
- Usings: outside namespace (file-scoped) as repo dictates; remove unused usings via tooling.
- Prefer `var` when the type is obvious from the right-hand side **if** the repo does; otherwise explicit types — never mix randomly in one PR.
- Expression-bodied members for trivial one-liners when neighbors do; not for multi-branch logic.
- `async`/`await`: keep `Async` suffix and pass `CancellationToken` on public async APIs (quality details in `code-quality-standards`).

## Workflow

1. **Locate style sources** — `.editorconfig`, props, analyzer config, neighbor files.
2. **State the surface** — public package API vs internal app code; NRT enabled or not.
3. **Name with domain language** already used in the assembly.
4. **Implement** using local patterns (records, primary constructors, DI registration style).
5. **Annotate nullability** correctly; avoid new `!` suppressions without invariants.
6. **Document public contracts** with `///` where the table requires it.
7. **Format and build** — `dotnet format` / IDE format + build so naming and nullable warnings are clean on touched code.
8. **Review the diff** — no drive-by renames, no solution-wide nullable cleanup mixed into feature work unless requested.

## Examples

### Good

```csharp
namespace Contoso.Billing;

/// <summary>
/// Creates and tracks customer invoices for a single tenant.
/// </summary>
public interface IInvoiceService
{
    /// <summary>
    /// Issues an invoice for the given order.
    /// </summary>
    /// <param name="orderId">Order identifier owned by the current tenant.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The newly issued invoice identifier.</returns>
    Task<InvoiceId> IssueForOrderAsync(OrderId orderId, CancellationToken cancellationToken = default);
}
```

```csharp
private readonly IAcquirerClient _acquirer;
private const int MaxAttempts = 3;

public bool IsRetryable(Status status) => status == Status.TransientFailure;

public async Task SaveAsync(Order order, CancellationToken cancellationToken)
{
    ArgumentNullException.ThrowIfNull(order);
    await _store.SaveAsync(order, cancellationToken).ConfigureAwait(false);
}
```

```csharp
public string? MiddleName { get; init; }  // absence is explicit
public string LastName { get; init; } = "";  // or required + ctor — match repo
```

### Bad

```csharp
// Wrong case, vague names, lying nullability, noise docs
namespace contoso.billing;

public class invoice_service
{
    public static int MAX_ATTEMPTS = 3;
    private String m_data = null!; // no invariant

    /// <summary>Does work.</summary>
    public Object do_work(Object o) => o;
}
```

```csharp
#pragma warning disable CS8602 // entire file
// "fixes" nullability without modeling absence
```

```csharp
/// <summary>Gets or sets the name.</summary>
public string Name { get; set; }
```

(Trivial doc that only restates the name.)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| C# naming, XML docs, NRT style | **This skill** | — |
| Correctness, async/cancellation, DI lifetimes, disposal, security, tests | `code-quality-standards` | this for naming/docs/NRT style only |
| Feature work in a .NET service | Domain / feature skill if any | **this** + `code-quality-standards` |
| Pure mechanical format | `dotnet format` / EditorConfig | this if rules are missing or unclear |

Always apply **`code-quality-standards`** as the implementation baseline when behavior changes. This skill specializes **.NET naming, XML documentation, and nullable style**; it does not replace quality, testing, or security rules.

## Checklist

- [ ] Repo `.editorconfig` / props / analyzers checked before applying defaults
- [ ] Namespaces, types, methods, parameters, fields match .NET naming and local field prefix rules
- [ ] Interfaces use `I` prefix; async methods use `Async` suffix when appropriate
- [ ] Public/protected library surface has useful XML docs (summary + real contracts)
- [ ] No trivial `<summary>` noise on obvious properties/private glue
- [ ] NRT enabled as in project; new APIs express `?` vs non-null deliberately
- [ ] No unexplained `null!`, `!`, or broad nullable warning suppressions
- [ ] Public async APIs accept `CancellationToken` when the codebase standard requires it
- [ ] `dotnet format` / build analyzers clean on touched files
- [ ] Behavioral concerns reviewed under `code-quality-standards`
- [ ] Diff free of unrelated style churn

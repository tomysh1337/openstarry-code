---
name: sql-injection-defenses-orm
description: >
  Defend against SQL injection with parameterized queries and safe ORM patterns:
  bind values (never concatenate), allowlist ORDER BY/identifiers, avoid unsafe
  raw SQL APIs, and correct Sequelize/Prisma/SQLAlchemy/EF usage. Use when
  hardening data access, reviewing query builders, fixing raw SQL, sort/filter
  injection, or ORM .raw/.query/.FromSql risks on owned applications — not for
  offensive SQLi proofs (hand off sqli-sql-injection).
---

# SQL Injection Defenses (ORM And Parameterized Queries)

Ship **data-access code** that cannot be driven into SQL syntax by untrusted
input. Prefer **bound parameters for values** and **allowlists for identifiers**
(`ORDER BY`, table/column names). **Defensive secure coding only** — no exploit
PoCs or payload catalogs.

## Scope And Authorization

- Design, implement, and review on systems you **own** or are contracted to harden.
- Do **not** produce exploit PoCs, sqlmap runs, or attack recipes here.
- Authorized offensive detection/proof → `sqli-sql-injection` (lab/CTF/written scope).
- Redact connection strings, dumps, and PII from reports and examples.

## When To Use

- Reviewing or writing queries via Sequelize, Prisma, SQLAlchemy, EF Core, Knex,
  TypeORM, Django ORM, or similar
- Fixing string-concatenated SQL, unsafe `$queryRaw`, `text()`, `FromSqlRaw`, or
  `.literal()` / `.order()` fed from request params
- Hardening dynamic **sort**, **filter field**, **search**, or multi-tenant table
  selection without turning user strings into SQL fragments
- Mentions: parameterized query, prepared statement, ORM SQLi defense, ORDER BY
  injection, identifier escaping, raw SQL pitfall, 参数化查询, ORM 防注入

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Offensive SQLi testing / exploitation | `sqli-sql-injection` |
| Injection class unknown (assessment) | `injection-checking` |
| NoSQL operator injection | `nosql-injection` |
| Request schema / sort-key allowlists at HTTP edge | `input-validation-patterns` |
| Schema migration safety (locks, expand/contract) | `database-migration-safety` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Repo data-access patterns and linters **outrank** generic defaults.

1. **ORM / driver:** Sequelize, Prisma, SQLAlchemy, EF, Knex, TypeORM, Django,
   JDBC/ADO — use that stack’s bind APIs, not a parallel ad-hoc wrapper
2. **Existing query helpers:** shared repositories, builders, allowlist maps for
   sort/filter — extend them; do not invent a second raw-SQL style
3. **Lint and SAST:** rules for `.raw` / string SQL; honor CI gates
4. **Dialect:** Postgres, MySQL, SQL Server, SQLite — never hand-roll value escaping
5. **Multi-tenant / RLS:** existing tenant scope — parameters do not replace authz
6. **Migrations/models:** keep aligned (`database-migration-safety` for ship order)
7. **Neighbors:** copy mature repository methods before adding raw SQL

**Precedence:** Follow the repo. Flag code that concatenates user data into SQL
while binding only some parameters.

## Workflow

1. **Inventory sinks.** Map request/event input → SQL: ORM filters, `.raw` /
   `$queryRaw` / `text()` / `FromSql*`, reporting builders, admin advanced filters.

2. **Separate values from identifiers.**
   - **Values** (IDs, text, dates, validated limits): always **bind** (`?`, `$1`,
     named params, ORM criteria). Never string-concat.
   - **Identifiers** (column/table, `ORDER BY`/`GROUP BY`, `ASC`/`DESC`): engines
     do **not** treat bound strings as identifiers. Use a fixed **allowlist map**
     API name → SQL name (and direction enum).

3. **Prefer structured ORM APIs.** Typed `where` / query builder for filters,
   joins, pagination. Raw SQL only when necessary — then parameterize every value.

4. **ORM-specific raw pitfalls (defensive).**

   | Stack | Prefer | Avoid |
   | --- | --- | --- |
   | **Sequelize** | `where: { id }`, `replacements`/`bind` on `query` | template concat, unallowlisted `order`, `literal(user)` |
   | **Prisma** | `findMany({ where })`, tagged `$queryRaw` with params | `$queryRawUnsafe` / `$executeRawUnsafe` + concat |
   | **SQLAlchemy** | `select().where(col == val)`, `bindparam` | `text(f"...{x}")`, `order_by(text(user_sort))` |
   | **EF Core** | LINQ, `FromSqlInterpolated` | `FromSqlRaw` + concat; untrusted raw fragments |
   | **Django** | ORM `filter()`, `params=` on `raw()` | `%`/`+` concat; `order_by(user_input)` |
   | **Knex/TypeORM** | `.where`, `.orderBy` + allowlisted keys | `.raw('...'+input)`, raw client `orderBy` |

5. **ORDER BY / sort injection.** Accept only keys in a server map
   (`createdAt` → `created_at`). Direction: allowlist `asc`/`desc` only. Reject
   unknown keys with stable 400; never interpolate the raw query string.

6. **LIKE / IN.** Bind patterns; escape `%`/`_` when user text must be literal.
   Build `IN` with one bound placeholder per element (or ORM `.in` / `in: ids`).

7. **Dynamic identifiers (rare).** Prefer schema that avoids client-chosen
   table/column names. Multi-tenant shards: resolve names only from **server**
   config keyed by authenticated tenant — never raw path/query segments.

8. **Defense in depth.** Least-privilege DB roles; hide detailed SQL errors from
   clients; validate types/ranges at the edge (`input-validation-patterns`).
   Bound queries do not authorize access — enforce tenant/object checks.

9. **Verify.** Tests: hostile quotes in values do not change SQL structure;
   unknown sort keys rejected; raw helpers require binds. Residual offensive
   retest under authorization → `sqli-sql-injection`. Apply
   `code-quality-standards` on every code change.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Parameterized queries, ORM raw safety, ORDER BY allowlists | **This skill** | — |
| Authorized offensive SQLi proof / sqlmap | `sqli-sql-injection` | this for remediation |
| Injection class not yet identified | `injection-checking` | this when fixing SQL sinks |
| HTTP/schema allowlists, sort keys at edge | `input-validation-patterns` | this for SQL identifier maps |
| NoSQL `$where` / operator injection | `nosql-injection` | — |
| Migration expand/contract, locks | `database-migration-safety` | this if migration SQL needs binds |
| Implement repositories, errors, tests | `code-quality-standards` | **always** on code |

- **`sqli-sql-injection`:** detect/prove SQLi in authorized tests; remediate here.
- **`input-validation-patterns`:** request-shape allowlists; this skill binds values and maps sort/filter keys into SQL.
- **`code-quality-standards`:** typed APIs, fail closed, no secret/SQL leakage, regression tests for binds and rejects.

## Output Checklist

- [ ] All SQL sinks from untrusted input inventoried (ORM + raw + reports)
- [ ] Values bound via parameters/ORM criteria — no concat for data
- [ ] Identifiers (`ORDER BY`, columns, tables) via allowlist maps only
- [ ] Sort direction restricted to `ASC`/`DESC` (or dialect equivalents)
- [ ] Unsafe raw APIs (`*Unsafe`, `FromSqlRaw`+concat, `literal(user)`) removed or bind-only
- [ ] Stack patterns (Sequelize/Prisma/SQLAlchemy/EF/etc.) match the table above
- [ ] LIKE/IN/search use binds; wildcards handled intentionally
- [ ] DB least privilege; client errors do not dump SQL/secrets
- [ ] Authz/tenant filters separate from parameterization
- [ ] Tests cover hostile values and invalid sort keys
- [ ] Residual offensive retest → `sqli-sql-injection` when in scope
- [ ] `code-quality-standards` applied; repo query helpers extended not forked

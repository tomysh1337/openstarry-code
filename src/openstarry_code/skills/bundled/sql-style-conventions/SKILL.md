---
name: sql-style-conventions
description: >
  Format and structure SQL for readability and safe evolution: consistent
  keyword casing, clear table/column naming, explicit joins, migration hygiene,
  and review-friendly diffs. Use when SQL style, SQL 规范, schema naming,
  migration readability, query formatting, or aligning SQL with repository
  conventions during features, refactors, or review.
---

# SQL Style Conventions

## Use When

- Writing or reviewing `.sql` files, migrations, seeds, views, or stored procedures.
- Naming tables, columns, indexes, constraints, or foreign keys.
- Formatting SELECT/DML for readable review diffs.
- User mentions SQL style, SQL 规范, migration readability, or schema conventions.
- Aligning ORM raw SQL / query-builder fragments with project norms.

Do **not** use as primary for:

- SQL injection testing or exploit methodology → `sqli-sql-injection`
- General application code quality outside SQL artifacts → `code-quality-standards`
- NoSQL / Mongo operator issues → `nosql-injection`

## Repo Config First

Repository conventions outrank generic preferences unless they create a correctness, security, or data-loss risk. Surface the conflict instead of silently introducing a second style.

1. Read migration tool docs in-repo: Flyway, Liquibase, Alembic, Django/Rails/ActiveRecord, Knex, Prisma migrate, golang-migrate, Sqitch, etc.
2. Honor SQLFluff / sqlfmt / pgFormatter / Squawk / DDLLint configs (`.sqlfluff`, `sqlfluff.cfg`, `pyproject.toml`, editorconfig).
3. Match existing keyword case, indent width, and identifier style already dominant in `migrations/`, `db/`, or `sql/`.
4. Follow established naming: `snake_case` vs quoted camelCase; plural vs singular tables; `id` vs `table_id`; soft-delete columns.
5. Prefer project helpers (enum types, shared audit columns, RLS policies, tenant keys) over inventing parallel patterns.
6. Never rewrite historical migrations for style alone; apply style to **new** migrations and to views/procedures that are intentionally edited.
7. Dialect matters: PostgreSQL, MySQL/MariaDB, SQLite, SQL Server — use features and types the project already depends on.

## Workflow

### 1. Establish the local dialect and layout

| Check | Action |
| --- | --- |
| Migration runner | One change per migration; forward-only unless project allows down |
| Identifier quoting | Prefer unquoted `snake_case` so names fold consistently per dialect rules |
| Schema layout | Respect `public` / app schemas / multi-tenant schemas already used |
| ORM models | Keep SQL names aligned with models and documented mapping |

### 2. Formatting (readability)

- One major clause per line for non-trivial queries: `SELECT`, `FROM`, `JOIN`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `LIMIT`.
- Align column lists and long `SET` lists vertically when it improves scanability; keep short statements compact.
- Prefer explicit column lists in `INSERT` and production `SELECT` over bare `SELECT *` (except existence checks or temporary exploration).
- Put each `JOIN` on its own line with the join condition immediately attached.
- Keep trailing commas policy consistent with formatter/repo (if any).
- Use consistent keyword casing **as the repo does** (many codebases use uppercase keywords + lowercase identifiers).

### 3. Naming tables and columns

| Object | Convention (default when repo is silent) |
| --- | --- |
| Tables | Plural `snake_case` nouns: `order_items` |
| Columns | `snake_case`; avoid reserved words (`user` → `users` table, column `users.id`) |
| Primary key | `id` or `<table_singular>_id` — match existing pattern, never mix in one table |
| Foreign key column | `<referenced_table_singular>_id` (e.g. `customer_id`) |
| Booleans | `is_` / `has_` prefix: `is_active`, `has_shipping` |
| Timestamps | `created_at`, `updated_at`, `deleted_at` (timestamptz when project uses TZ-aware) |
| Indexes | `idx_<table>_<cols>`; unique: `uq_<table>_<cols>` |
| Constraints | `pk_`, `fk_`, `ck_`, `uq_` prefixes with table context |
| Junction tables | `foo_bar` or `foo_bars` per local pattern; include both FKs + unique pair |

- Avoid cryptic abbreviations (`cust_nm`) unless the domain standard already uses them.
- Do not encode type in the name (`name_string`); do encode unit when ambiguous (`duration_ms`, `size_bytes`).
- Prefer stable domain names over storage technology (`email`, not `varchar_email`).

### 4. Query structure and correctness style

- Prefer `INNER JOIN` / `LEFT JOIN` explicit syntax over implicit comma joins.
- Filter in `WHERE` for row filters; keep join predicates in `ON` (except intentional post-join filters on outer joins).
- Parameterize application queries; never concatenate untrusted input into SQL (security is mandatory even when this skill is about style).
- Use transactions for multi-step migrations that must be atomic when the engine allows.
- Prefer idempotent data backfills where operationally required (`WHERE missing`, re-runnable scripts).
- Document non-obvious predicates, lock hints, and online-migration assumptions in SQL comments sparingly.

### 5. Migrations readability

1. **Name** files the way the tool expects (`YYYYMMDDHHMMSS_add_orders_status.sql`, `V12__add_orders_status.sql`).
2. **One purpose** per migration: schema XOR large backfill when possible; if combined, section with comments.
3. Order: create tables → constraints/indexes → data backfill → dependent views.
4. Expand/contract for breaking changes when zero-downtime is required: add nullable column → backfill → enforce constraints → remove old.
5. Avoid destructive `DROP` without a prior deploy that stopped using the object; prefer multi-PR expand/contract.
6. Do not edit applied migrations in shared environments; add a new migration to fix.
7. For indexes on large tables, follow dialect-safe online patterns the project already uses (`CREATE INDEX CONCURRENTLY` in Postgres only when allowed by the runner/transaction rules).

### 6. Review and verification

1. Run the project SQL formatter/linter if configured.
2. Apply migrations on a disposable database or use the project’s `migrate` dry-run.
3. Sanity-check EXPLAIN only when performance is in scope; style skill does not replace query tuning.
4. Confirm ORM models, generated types, and API contracts still match renamed columns.

## Good And Bad Examples

### Query formatting

```sql
-- Good
SELECT
    o.id,
    o.customer_id,
    o.status,
    c.email
FROM orders AS o
INNER JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.status = 'open'
  AND o.created_at >= :start_at
ORDER BY o.created_at DESC
LIMIT 50;
```

```sql
-- Bad
select o.*,c.* from orders o, customers c where o.customer_id=c.id and o.status='open' order by 1
```

### Naming

```sql
-- Good
CREATE TABLE order_items (
    id              bigserial PRIMARY KEY,
    order_id        bigint NOT NULL,
    product_id      bigint NOT NULL,
    quantity        integer NOT NULL,
    unit_price_cents integer NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders (id),
    CONSTRAINT uq_order_items_order_product
        UNIQUE (order_id, product_id)
);

CREATE INDEX idx_order_items_product_id ON order_items (product_id);
```

```sql
-- Bad
CREATE TABLE OrderItem (
  OrderItemID int,
  OrderID int,
  qty int,
  price float, -- ambiguous unit/precision
  name string  -- invalid / vague
);
```

### INSERT clarity

```sql
-- Good
INSERT INTO customers (email, display_name, is_active)
VALUES (:email, :display_name, TRUE);
```

```sql
-- Bad
INSERT INTO customers VALUES (:email, :display_name, true); -- column order brittle
```

### Migration readability

```sql
-- Good: V202607111200__add_orders_status.sql
-- Add order status with safe default for existing rows.
ALTER TABLE orders
    ADD COLUMN status text NOT NULL DEFAULT 'draft';

ALTER TABLE orders
    ADD CONSTRAINT ck_orders_status
    CHECK (status IN ('draft', 'open', 'paid', 'cancelled'));

CREATE INDEX idx_orders_status ON orders (status);
```

```sql
-- Bad: style-only rewrite of old migration + destructive surprise
-- (edited V3__init.sql in place)
DROP TABLE orders;
CREATE TABLE orders ( ... ); -- data loss; breaks migration history
```

### Outer join filter placement

```sql
-- Good: preserve unmatched left rows; filter right table in ON
SELECT c.id, o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'open';
```

```sql
-- Bad: WHERE on right table turns LEFT JOIN into effective INNER JOIN
SELECT c.id, o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'open';
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SQL formatting, naming, migration readability | `sql-style-conventions` (this) | — |
| Application code around queries | `code-quality-standards` | this for SQL artifacts |
| SQL injection assessment | `sqli-sql-injection` | this when writing parameterized fixes |
| Shell scripts that apply SQL files | `shell-script-style` | this for SQL content |
| ORM-only model change with no SQL | `code-quality-standards` | this if raw SQL/migrations also change |
| NoSQL query operators | `nosql-injection` | — |

## Checklist

- [ ] Repo migration tool, dialect, and SQL linter/formatter config identified and followed
- [ ] Keyword/identifier casing matches existing SQL in the project
- [ ] Tables/columns/indexes/constraints use consistent, domain-clear names
- [ ] Joins explicit; no comma joins; `ON` vs `WHERE` correct for outer joins
- [ ] `INSERT`/`SELECT` use explicit columns where production-relevant
- [ ] Application SQL parameterized; no string-concatenated untrusted input
- [ ] New migration is single-purpose, ordered, and forward-compatible with deploy process
- [ ] No in-place edits to already-applied migrations for style
- [ ] Destructive changes use expand/contract or explicit approved downtime plan
- [ ] Formatter/linter and migration dry-run or disposable DB apply performed when available

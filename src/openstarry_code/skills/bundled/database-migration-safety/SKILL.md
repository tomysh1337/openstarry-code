---
name: database-migration-safety
description: >
  Plan and review safe database migrations: expand/contract, backward-compatible
  deploys, locking/index risks, backfills, and zero-downtime notes. Use when DB
  migration, 数据库迁移, schema change, online DDL, expand/contract, dual-write,
  backfill, or shipping migrations without downtime. Complements SQL style;
  not a substitute for SQL injection testing.
---

# Database Migration Safety

Ship **schema and data changes** that respect deploy order, old and new
application versions, lock behavior, and rollback reality. Prefer expand/contract
over rewrite-in-place. Repository migration tooling and production runbooks
outrank generic preferences.

## Use When

- Writing or reviewing Flyway, Liquibase, Alembic, Django/Rails, Prisma, Knex,
  golang-migrate, Sqitch, Atlas, or raw ordered SQL migrations
- Changing columns, indexes, constraints, enums, FKs, or large data backfills
- Targeting zero or low downtime: online DDL, concurrent indexes, multiphase
  expand → migrate → contract
- Dual-running app versions during rolling deploys or blue/green
- User mentions: DB migration, 数据库迁移, expand/contract, zero-downtime
  migration, `CREATE INDEX CONCURRENTLY`, backfill, drop column safely

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SQL formatting, identifier naming, readable migration style | `sql-style-conventions` |
| JSON/OpenAPI payload design for APIs | `json-schema-design` |
| SQL injection assessment | `sqli-sql-injection` |
| General application code quality | `code-quality-standards` |
| API version deprecation for HTTP clients | `api-versioning-design` |

## Repo Config First

Repo tooling, dialect, and ops policy **outrank** this skill’s defaults.

1. **Migration runner:** Flyway/Liquibase/Alembic/Django/Prisma/etc.; whether
   migrations wrap each file in a transaction; support for `CONCURRENTLY` /
   offline DDL; down migrations allowed or forward-only
2. **Dialect and version:** PostgreSQL, MySQL/MariaDB, SQL Server, SQLite —
   online DDL and lock semantics differ; use only features the project runs
3. **Deploy model:** rolling pods, blue/green, maintenance window, single
   instance — dual-version compatibility length is defined by this model
4. **Naming and layout:** existing `migrations/` patterns, expand/contract
   PR habit, separate backfill jobs vs in-migration SQL
5. **Safety linters:** Squawk, pg-osc, pt-online-schema-change, gh-ost,
   strong_migrations, custom CI checks — honor their rules
6. **Data classes:** multi-tenant keys, RLS, encryption-at-rest, PII columns —
   follow existing handling; never log row contents with secrets/PII
7. **Neighboring migrations:** copy recent safe multiphase examples in-repo
   before inventing a new pattern

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that risk data loss, prolonged locks, or break old app
binaries still serving traffic.

## Workflow

1. **State the change and blast radius.**
   - Additive vs destructive; table size; hot paths; replicas; SLA
   - Whether downtime is approved or online migration is required
2. **Map application compatibility.**
   - Which app versions will run against DB during the change
   - Rule: **DB expands first, contracts last**; app may dual-read/dual-write
     in the middle
3. **Pick a migration shape.**

   | Shape | When | Notes |
   | --- | --- | --- |
   | Single additive migration | Small table, nullable column, new table/index with online path | Still avoid long locks |
   | Expand / migrate / contract | Rename, type change, NOT NULL without safe default, drop column | Multiple deploys |
   | Maintenance window | Approved downtime; simpler DDL | Document freeze and rollback |
   | Online schema tool | Very large MySQL/Postgres tables | gh-ost, pt-osc, pg-osc per ops |

4. **Design expand phase (backward compatible).**
   - Add nullable columns, new tables, new indexes (online when needed)
   - Do not drop/rename/change types yet
   - Defaults: prefer application-backfill or explicit DB default that old
     writers satisfy
5. **Design data move.**
   - Backfill in batches; idempotent; rate-limited; observable progress
   - Prefer job/worker over multi-hour transaction on large tables
   - Verify row counts / checksums / spot queries before contract
6. **Design contract phase (after app no longer depends on old shape).**
   - Remove old columns/triggers/dual-write only when metrics show idle
   - Enforce `NOT NULL` / FKs / CHECKs only after backfill complete
7. **Assess locks and performance.**
   - Long `ACCESS EXCLUSIVE` (Postgres) or table rebuilds (MySQL variants)
   - Index build strategy; autovacuum; replica lag; statement timeouts
8. **Plan rollback and order.**
   - Expand should be roll-forward friendly; avoid irreversible DROP early
   - App rollback must still work against expanded schema
   - Never edit already-applied migrations in shared environments; add new ones
9. **Ship with verification.**
   - Migrate on disposable DB or staging clone; run app dual-version smoke
   - CI migration lint when available; document runbook for prod

## Expand / Contract Pattern

### Typical rename (zero-downtime sketch)

1. **Expand:** `ADD COLUMN new_name` (nullable or with default); keep `old_name`
2. **App deploy A:** dual-write both; read prefer `new_name` with fallback to `old_name`
3. **Backfill:** copy `old_name` → `new_name` where null; batched
4. **App deploy B:** read/write only `new_name`
5. **Contract:** drop `old_name` (and dual-write code) after soak

### Typical NOT NULL add

1. Add nullable column (or with temporary default)
2. Deploy writers that always set the column
3. Backfill existing rows
4. Validate no nulls; `SET NOT NULL` / drop temporary default in a controlled step
5. Avoid `ADD COLUMN … NOT NULL` without default on large busy tables

### Typical index on large Postgres table

1. Prefer `CREATE INDEX CONCURRENTLY` when the runner allows non-transactional
   statements (often **cannot** sit inside a transaction block)
2. If concurrent not available, schedule off-peak or use approved online tool
3. `UNIQUE` indexes: handle duplicates before enforcing uniqueness

### Typical column drop

1. Deploy app that stops reading/writing the column
2. Soak; confirm no queries reference it (logs, `pg_stat_statements`, code search)
3. Drop column in a later migration
4. Do not drop in the same release that still might roll back to old code

## Zero-Downtime Notes

- **Rolling deploy:** every migration must leave DB compatible with **both**
  old and new app binaries for the full roll
- **Blue/green:** cut traffic only after expand+backfill verified; contract after
- **Locks:** treat multi-second exclusive locks on hot tables as outages unless
  approved; test on production-sized data
- **FKs:** adding FKs can scan/lock; create `NOT VALID` then `VALIDATE` when
  dialect supports phased validation (Postgres)
- **Enums:** prefer additive new values; removing enum values is hard — plan
  multiphase or check constraints on text instead when churn is high
- **Views/materialized views/triggers:** update in order that keeps old app working
- **Replicas:** long transactions and heavy backfills cause lag — throttle
- **SQLite / small apps:** simpler migrations OK; still avoid data-loss DROP
  without backup and explicit intent

## Good / Bad Examples

### Expand before break

**Good** — additive first:

```sql
-- V202607111200__orders_status_expand.sql
ALTER TABLE orders
    ADD COLUMN status text;

-- App dual-writes status; backfill job fills nulls next.
-- Later migration: SET NOT NULL + CHECK after verification.
```

**Bad** — rewrite in place on live system:

```sql
-- Drops data path old app still uses during roll
ALTER TABLE orders DROP COLUMN state;
ALTER TABLE orders ADD COLUMN status text NOT NULL;
```

### Concurrent index (Postgres)

**Good**

```sql
-- Run outside a transaction if required by the migration tool
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_id
    ON orders (customer_id);
```

**Bad**

```sql
-- Blocks writes for a long time on large tables
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
```

### Backfill batching

**Good**

```sql
-- Idempotent batch; repeat until 0 rows updated
UPDATE orders
SET status = 'open'
WHERE id IN (
    SELECT id FROM orders
    WHERE status IS NULL
    ORDER BY id
    LIMIT 1000
);
```

**Bad**

```sql
-- One huge transaction; long locks; hard to resume
UPDATE orders SET status = 'open' WHERE status IS NULL;
```

### Drop column safety

**Good** (sequence across releases)

```text
R1: App ignores column deprecated_at (stop writes)
R2: Confirm no reads; migration DROP COLUMN deprecated_at
```

**Bad**

```sql
-- Same deploy as app that might roll back to code selecting the column
ALTER TABLE users DROP COLUMN legacy_flag;
```

### Constraint after clean data

**Good**

```sql
-- After backfill verified
ALTER TABLE orders
    ALTER COLUMN status SET NOT NULL;

ALTER TABLE orders
    ADD CONSTRAINT ck_orders_status
    CHECK (status IN ('draft', 'open', 'paid', 'canceled'));
```

**Bad**

```sql
-- Fails mid-deploy or locks while checking dirty data
ALTER TABLE orders
    ADD COLUMN status text NOT NULL;
```

## Anti-Patterns

- Editing applied migrations instead of adding corrective migrations
- Combining irreversible DROP with expand in one shot on shared environments
- Multi-hour exclusive locks on peak traffic without approval
- Non-idempotent backfills that corrupt on retry
- Enforcing UNIQUE/NOT NULL before cleaning duplicates/nulls
- Assuming MySQL and Postgres lock behavior are the same
- Silent data type changes that truncate values (`text` → `varchar(10)`)
- Migrating production without a backup/PITR story appropriate to the org
- Putting heavy backfills only in a blocking migration transaction “to keep it simple”
- Forgetting ORM models, generated types, and API schemas must track the multiphase reality

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Safe multiphase migration, locks, zero-downtime, 数据库迁移 | **This skill** | — |
| SQL naming, formatting, readable single-file style | `sql-style-conventions` | this for safety phasing |
| JSON/API schema for payloads that mirror columns | `json-schema-design` | this when columns change |
| OpenAPI prose for APIs affected by schema change | `api-documentation-writing` | this for ship order |
| Application dual-read/dual-write implementation | `code-quality-standards` | **always apply** on code |
| SQL injection testing | `sqli-sql-injection` | — |

### Routing to shared skills

- **`sql-style-conventions`:** identifier naming, keyword case, one-purpose file
  readability; keep **this skill primary** for expand/contract, lock risk, and
  deploy ordering
- **`code-quality-standards`:** always apply when implementing dual-write,
  backfill jobs, or data access changes:
  - Explicit compatibility window and feature flags if used
  - Idempotent jobs; bounded batches; cancellation/timeout
  - No secret/PII logging from row dumps
  - Tests for old+new schema compatibility where feasible
  - Parameterized SQL; transactions scoped correctly
- **`api-documentation-writing` / `json-schema-design`:** when HTTP/event
  contracts change with columns, update schemas and docs in the matching phase
  (additive API fields with expand; removals with contract)

This skill specializes **operationally safe schema evolution**. It does not
replace SQL style preferences, JSON contract design, or full app quality gates.

## Checklist

- [ ] Migration tool, dialect, transaction/`CONCURRENTLY` constraints, and deploy model identified
- [ ] Change classified: additive, multiphase expand/contract, or approved downtime
- [ ] Old and new app versions remain compatible for the full roll / dual-run window
- [ ] Expand ships before rename/type/NOT NULL/drop contract steps
- [ ] Backfills batched, idempotent, observable; verified before enforce/drop
- [ ] Lock and index strategy safe for table size and peak traffic
- [ ] FKs/CHECKs/UNIQUE enforced only on clean data; phased validate when available
- [ ] No in-place edits to already-applied migrations
- [ ] Rollback story: app can roll back onto expanded schema; irreversible steps deferred
- [ ] ORM/models, `json-schema-design` / OpenAPI, and jobs updated per phase
- [ ] Staging or clone dry-run done; safety linter (Squawk/strong_migrations/etc.) clean when configured
- [ ] `sql-style-conventions` followed for new SQL artifacts
- [ ] `code-quality-standards` applied for dual-write/backfill code, errors, and tests
- [ ] Prod runbook notes: order of deploy, monitoring (locks, lag, error rate), abort criteria

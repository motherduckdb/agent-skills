<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Migrate to MotherDuck

Use this skill when the user needs a migration plan from an existing warehouse, database, or analytics stack onto MotherDuck. This is a use-case skill: it combines connection strategy, ingestion, modeling, query migration, and rollout sequencing into one plan.

## Source Of Truth

- Prefer current MotherDuck public documentation and product pages first.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to general web search.
- For migration decisions, verify current guidance on:
  - connection paths
  - `pg_duckdb`
  - Hypertenancy and read scaling
  - DuckLake
- If `ask_docs_question` is unavailable, use public pages on `motherduck.com` and `motherduck.com/docs`.

## Verified Delivery Defaults

The repeated repo runs point to a stable migration posture:

- decide the target MotherDuck pattern before arguing about tooling
- migrate in slices with source-vs-target validation at each step
- treat metric comparison and missing-key checks as mandatory, not optional
- keep rollback and cutover posture explicit in the first migration plan

## Validation Signals

Use these signals for testing, review, and regression checks. They are not an instruction to include a separate "Validation Signals" section in normal user-facing replies.

- run `artifacts/migration_validation_example.py` against temporary MotherDuck databases
- verify the output contains metric comparison plus `new_records` and `deleted_records`
- require an explicit acceptable variance posture for every migration slice
- treat plans without rollback and cutover checkpoints as incomplete

## When To Use

- The user is migrating from Snowflake, Redshift, Postgres, or another warehouse.
- The user is asking about dbt, connectors, CDC, or cutover sequencing.
- The user needs to decide whether to land on native MotherDuck storage or DuckLake.

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** for migration execution examples:
  - extract/load scripts
  - validation checks
  - data comparison jobs
  - migration notebooks and cutover helpers
- Prefer **TypeScript/Javascript** when the migration is really about:
  - moving a product backend to MotherDuck
  - preserving Node.js service interfaces
  - re-pointing app-side query paths
- If the task includes both product and data movement, show Python for migration mechanics and TypeScript/Javascript for the app cutover path.

## TypeScript/Javascript Cutover Starter

```ts
type CustomerQueryTarget = {
  mode: "legacy-postgres" | "motherduck-pg" | "pg-duckdb";
  database: string;
};

const rolloutMap: Record<string, CustomerQueryTarget> = {
  acme: { mode: "motherduck-pg", database: "customer_acme" },
  globex: { mode: "legacy-postgres", database: "globex_prod" },
};
```

## Python Validation Starter

```python
import duckdb

def compare_metrics(conn, source_table: str, target_table: str, column: str) -> dict:
    """Compare a numeric column between source and target with % variance."""
    results = {}
    for agg in ["count(*)", f"SUM({column})", f"AVG({column})", f"MIN({column})", f"MAX({column})"]:
        src = conn.sql(f"SELECT {agg}::DOUBLE FROM {source_table}").fetchone()[0]
        tgt = conn.sql(f"SELECT {agg}::DOUBLE FROM {target_table}").fetchone()[0]
        pct = round(100.0 * (tgt - src) / src, 4) if src else None
        results[agg] = {"source": src, "target": tgt, "pct_variance": pct}
    return results

def find_missing_keys(conn, source_table: str, target_table: str, key_col: str) -> dict:
    """Find new, deleted, and changed records between source and target."""
    new = conn.sql(
        f"SELECT {key_col} FROM {target_table} EXCEPT SELECT {key_col} FROM {source_table}"
    ).fetchall()
    deleted = conn.sql(
        f"SELECT {key_col} FROM {source_table} EXCEPT SELECT {key_col} FROM {target_table}"
    ).fetchall()
    return {"new_records": len(new), "deleted_records": len(deleted)}
```

See `references/MIGRATION_VALIDATION.md` for the full validation suite: row counts, metric comparisons with % variance, uniqueness checks, new/deleted/changed record tracking, and a Python orchestrator.

## Migration Workflow

Follow this order:

1. Identify the current source of truth.
2. Identify the serving pattern after migration.
3. Pick the connection and ingestion path.
4. Migrate schema and data.
5. Port or rewrite critical SQL.
6. Validate correctness.
7. Cut over in phases.

## Official Product Anchors To Use

- `pg_duckdb` is the official path for adding analytical power to an existing PostgreSQL estate. MotherDuck describes it as a way to keep OLTP fast while handling OLAP through DuckDB, with support for joining PostgreSQL and cloud data and even zero-data-movement analytics on existing PostgreSQL data.
- Hypertenancy is the official pattern for giving each customer or user isolated compute. MotherDuck documents one Duckling per user or customer, provisioned automatically per service account.
- Read Scaling is the official answer for read-heavy workloads like BI dashboards or high-concurrency read-only apps.
- DuckLake is explicitly opt-in. MotherDuck positions it for open-table-format and large lakehouse-style needs, while native MotherDuck storage remains the simpler default for many migrations.

## Step 1: Classify the Starting Point

Workload classes:

- warehouse replacement
- Postgres extension or hybrid analytics
- app-serving migration
- dashboard and BI migration
- lakehouse or open-table-format migration

Do not design the destination before classifying the current stack.

## Step 2: Pick the Target Pattern

- Use the PG endpoint when the environment already assumes PostgreSQL wire compatibility.
- Use the native DuckDB API when local files, hybrid queries, or rich DuckDB control matter.
- Use `pg_duckdb` when extending an existing PostgreSQL estate is the least disruptive path. MotherDuck's public Postgres Integration guidance emphasizes:
  - analytical acceleration inside PostgreSQL
  - joins across PostgreSQL, MotherDuck, and object storage
  - zero-data-movement analytics on existing PostgreSQL data
  - hybrid workload optimization so OLTP stays in PostgreSQL while OLAP moves to DuckDB
- Use DuckLake only when open-table-format requirements are explicit.

Important migration gotcha:

- the PG endpoint still runs DuckDB SQL, not PostgreSQL SQL
- do not assume PostgreSQL-specific syntax, temp-table habits, local-file imports, or extension management will survive unchanged over the PG endpoint
- when the migration depends on local DuckDB features, use a native DuckDB client path instead of forcing everything through PostgreSQL drivers

## Migration Decision Matrix

- Source is PostgreSQL and the team wants minimal disruption:
  - start with `pg_duckdb`
  - keep transactional paths in PostgreSQL
  - offload analytical paths to MotherDuck only where needed
- Source is a warehouse and the team wants a cleaner MotherDuck landing zone:
  - move data into native MotherDuck storage first
  - rebuild the analytics model in DuckDB SQL
  - add Hypertenancy or read scaling later if the serving workload demands it
- Source is an Iceberg or data-lake estate:
  - evaluate DuckLake only if open-table-format interoperability or bring-your-own-bucket requirements are real
  - do not default to DuckLake just because the source system was lake-based

## Step 3: Move Data

Use `load-data` patterns for the raw move:

- Parquet for bulk movement when you control extracts
- cloud object storage for staged imports
- append-only raw landing first, then transform
- validate row counts and key aggregates after every load
- avoid row-by-row insert loops; prefer bulk paths, Arrow/dataframes, or `COPY`

Prefer these patterns:

- use direct cloud-to-MotherDuck ingest when the source data already lives in object storage
- keep raw, staging, and analytics boundaries explicit during cutover
- preserve rollback by leaving the old source of truth untouched until validations pass

## Step 4: Rebuild the Analytical Model

- Prefer wide analytical tables for BI and dashboard workloads.
- Keep raw, staging, and analytics boundaries explicit.
- Rework source-specific SQL into DuckDB SQL where needed.
- Validate every critical join, aggregate, and date transformation.

Specific rewrite checks:

- Postgres-specific SQL and extensions
- warehouse-specific DDL assumptions
- dbt macros that assume another engine
- nested JSON and semi-structured data behavior
- time travel or snapshot workflows that need a MotherDuck-native equivalent

## Step 5: Validate Correctness

Run source-vs-target checks before cutting over. Every check should output a `pct_variance` so the user can decide what is acceptable.

1. **Row counts** — compare total rows between source and target.
2. **Metric comparison** — compare SUM, AVG, MIN, MAX on key numeric columns side by side.
3. **Uniqueness** — verify the target has no duplicate keys introduced by the migration.
4. **New records** — identify IDs in the target that do not exist in the source.
5. **Deleted records** — identify IDs in the source that are missing from the target.
6. **Changed records** — find records present in both but with different values. Track the specific IDs.
7. **% variance** — report variance on every metric so the user can set their own threshold for pass/fail.

Whether the migration is a 1:1 port or an intentional refactor determines what variance is acceptable. The skill provides the measurements; the user decides.

## Step 6: Cut Over Safely

- run old and new outputs side by side
- compare row counts and business metrics using the validation patterns above
- cut over one workload or consumer at a time
- keep rollback simple until confidence is earned

When the target workload is user-facing:

- move to Hypertenancy before general availability if strong tenant isolation is a hard requirement
- add read scaling only after concurrency is proven to be the bottleneck
- keep one service account and token boundary per customer or workload slice rather than sharing a single broad token

## DuckLake Guidance

Use DuckLake when the user explicitly needs one of these:

- open-table-format storage
- bring-your-own-bucket storage ownership
- use of their own compute against the same storage
- migration from Iceberg-oriented lake workflows

Do not recommend DuckLake by default when:

- the workload is mainly warehouse-style analytics
- the user wants the simplest managed path
- the team does not have a concrete interoperability or storage-ownership requirement

MotherDuck's public DuckLake guidance currently distinguishes:

- fully-managed DuckLake for the easiest start
- bring-your-own-bucket DuckLake when storage must remain in the user's cloud
- use-your-own-compute scenarios only with bring-your-own-bucket setups today

MotherDuck's public DuckLake guidance also says native MotherDuck storage reads are often materially faster than DuckLake for normal analytical reads. That means warehouse migrations should stay native unless the open-table-format requirement is real.

If the migration really needs bring-your-own-bucket DuckLake:

- keep the bucket in the same region as the target MotherDuck deployment when possible
- plan for explicit maintenance behavior instead of assuming MotherDuck will compact and maintain files automatically

## Source-Specific Questions To Answer

- Snowflake: what external functions, orchestration, or security assumptions need replacement?
- Redshift: what distribution-key or cluster assumptions disappear?
- Postgres: is `pg_duckdb` enough, or should the workload move fully to MotherDuck? Are zero-data-movement analytics or hybrid operational/analytical joins enough for phase one?
- dbt-heavy stacks: which models move unchanged, and which need DuckDB-specific rewrites?
- Lakehouse source: does the user actually need DuckLake, or would managed MotherDuck storage simplify the migration?

The output of this skill should be a phased migration plan, not just a list of features.

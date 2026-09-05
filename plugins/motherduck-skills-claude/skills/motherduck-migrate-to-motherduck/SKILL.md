---
name: motherduck-migrate-to-motherduck
description: Plan or implement migrations to MotherDuck with SQL translation, source-to-target validation, cutover, and rollback.
argument-hint: [source-system-or-migration-goal]
license: MIT
---

# Migrate to MotherDuck

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Migration Defaults

- native MotherDuck storage first
- `pg_duckdb` when extending an existing PostgreSQL estate is the least disruptive path
- validate before cutover
- port SQL dialect and data types deliberately before performance tuning
- phased cutover over big-bang replacement
- remote DuckDB database-file import when the source is already packaged in cloud storage
- capture validated business definitions, join rules, and cutover caveats in Guides after the target model stabilizes

## Workflow

1. Inspect the available MotherDuck server or supplied source and target context.
2. Classify the source system and the target serving pattern.
3. Inspect the target-side MotherDuck layout if available.
4. Pick the connection and ingestion path.
5. Inventory incompatible SQL, functions, data types, and operational assumptions.
6. Rebuild the analytical model in DuckDB SQL.
7. Run source-vs-target validation.
8. Create or update the relevant MotherDuck Guides so post-cutover agents use the validated target definitions.
9. Cut over one workload at a time.

Match execution to the request: answer, review, or planning work returns the requested migration artifacts; build or change work executes only the requested in-scope migration slice and validates it. Require confirmation for cutover, destructive source changes, or external writes not already authorized.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.6.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- the target pattern
- the migration sequence
- the validation plan
- the rollback path
- the first cutover slice

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/MIGRATION_PLAYBOOK.md` -- target-pattern selection, migration decision matrix, DuckLake posture, and source-specific questions (Snowflake, Redshift, Postgres, dbt, lakehouse)
- `references/MIGRATION_VALIDATION.md` -- copy-adaptable validation SQL (row counts, metrics with `pct_variance`, new/deleted/changed records) and a Python orchestrator

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [migration_validation_example.py](artifacts/migration_validation_example.py)
- [migration_validation_example.ts](artifacts/migration_validation_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` -- choose the connection path for the target system
- `motherduck-explore` -- inspect the target-side MotherDuck workspace
- `motherduck-load-data` -- bulk movement and raw landing patterns
- `motherduck-model-data` -- shape the target analytical model
- `motherduck-query` -- port and validate critical SQL
- `motherduck-ducklake` -- only when open-table-format requirements are explicit
- `motherduck-manage-guides` -- preserve validated target semantics and migration caveats

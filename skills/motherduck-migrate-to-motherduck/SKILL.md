---
name: motherduck-migrate-to-motherduck
description: Plan a migration onto MotherDuck. Use when moving from Snowflake, BigQuery, Redshift, PostgreSQL, dbt-heavy stacks, or lakehouse tooling and the key decisions are target pattern, cutover slices, source-vs-target validation, rollback, and native-versus-DuckLake posture.
license: MIT
---

# Migrate to MotherDuck

Use this skill when the user needs a migration plan from another warehouse, PostgreSQL estate, or mixed analytics stack onto MotherDuck.

This is a use-case skill. It orchestrates `motherduck-connect`, `motherduck-explore`, `motherduck-load-data`, `motherduck-model-data`, `motherduck-query`, and `motherduck-ducklake`.

## Start Here: Is a MotherDuck Server Active?

- If a **remote MotherDuck MCP server** or **local MotherDuck server** is active, use it.
- Discover the target database or workspace from the active context. Ask only when multiple plausible targets remain and the choice would materially change the migration.
- Explore the live target side first when available:
  - existing databases and schemas
  - current landing zones
  - current analytical tables
  - naming conventions
  - any partial migration already in place

Also capture the source-side shape:

- source platform
- source table grain
- key metrics
- validation keys
- serving workloads after cutover

If no server is active, use any supplied source and target context. For planning work, proceed with explicit assumptions when safe; ask for missing schema details only when they block a reliable result.

## Migration Defaults

- native MotherDuck storage first
- `pg_duckdb` when extending an existing PostgreSQL estate is the least disruptive path
- validate before cutover
- port SQL dialect and data types deliberately before performance tuning
- phased cutover over big-bang replacement

## Workflow

1. Inspect the available MotherDuck server or supplied source and target context.
2. Classify the source system and the target serving pattern.
3. Inspect the target-side MotherDuck layout if available.
4. Pick the connection and ingestion path.
5. Inventory incompatible SQL, functions, data types, and operational assumptions.
6. Rebuild the analytical model in DuckDB SQL.
7. Run source-vs-target validation.
8. Cut over one workload at a time.

Match execution to the request: answer, review, or planning work returns the requested migration artifacts; build or change work executes only the requested in-scope migration slice and validates it. Require confirmation for cutover, destructive source changes, or external writes not already authorized.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.5.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

The output of this skill should be:

- the target pattern
- the migration sequence
- the validation plan
- the rollback path
- the first cutover slice

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.
This is mainly for automated tests, regression checks, or downstream tooling that needs a stable machine-readable shape. Normal human-facing use of the skill can stay in prose unless JSON is explicitly requested.

Use this exact top-level shape when JSON is requested:

```json
{
  "summary": {},
  "assumptions": [],
  "implementation_plan": [],
  "validation_plan": [],
  "risks": []
}
```

## References

Read these as reference, not as scripts to execute:

- `references/MIGRATION_PLAYBOOK.md` -- target-pattern selection, migration decision matrix, DuckLake posture, and source-specific questions (Snowflake, Redshift, Postgres, dbt, lakehouse)
- `references/MIGRATION_VALIDATION.md` -- copy-adaptable validation SQL (row counts, metrics with `pct_variance`, new/deleted/changed records) and a Python orchestrator

## Runnable Artifact

- `artifacts/migration_validation_example.py` -- MotherDuck-backed Python example for source-vs-target validation and variance reporting
- `artifacts/migration_validation_example.ts` -- TypeScript companion artifact with the same validation output contract

Run it with:

```bash
uv run --with duckdb python skills/motherduck-migrate-to-motherduck/artifacts/migration_validation_example.py
```

Run the same validation flow against temporary MotherDuck databases:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/motherduck-migrate-to-motherduck/artifacts/migration_validation_example.py
```

Validate the TypeScript companion artifact:

```bash
uv run scripts/test_typescript_artifacts.py
```

## Related Skills

- `motherduck-connect` -- choose the connection path for the target system
- `motherduck-explore` -- inspect the target-side MotherDuck workspace
- `motherduck-load-data` -- bulk movement and raw landing patterns
- `motherduck-model-data` -- shape the target analytical model
- `motherduck-query` -- port and validate critical SQL
- `motherduck-ducklake` -- only when open-table-format requirements are explicit

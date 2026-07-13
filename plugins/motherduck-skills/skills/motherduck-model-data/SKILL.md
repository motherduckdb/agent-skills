---
name: motherduck-model-data
description: Design and build database schemas and data models in MotherDuck. Produces a file-based SQL project scaffold with a model manifest. Use for any schema design or data modeling task — creating tables, choosing data types, star schemas, wide denormalized tables, raw/staging/analytics layers, dbt-style transformation projects, or restructuring data for analytics workloads.
license: MIT
---

# Model Data in MotherDuck

## Core Behavior

For multi-model or transformation-layer work, default to a file-based project scaffold rather than warehouse-only SQL execution.

The project scaffold includes:

- **SQL files** organized by lifecycle stage (`raw/`, `staging/`, `analytics/`)
- **A manifest** (`model_manifest.yml`) defining the DAG: model names, dependencies, materialization strategy, and target database

This is a lightweight framework-agnostic convention for organizing SQL transformations that can be reviewed, versioned, and rerun.

## Prerequisites

- MotherDuck connection established via `motherduck-connect`
- Existing source shape understood via `motherduck-explore`
- DuckDB SQL syntax available via `motherduck-duckdb-sql`

## Default Posture

- Design for analytical reads, not transactional writes.
- Prefer wide denormalized tables and pre-aggregated serving tables over highly normalized OLTP-style schemas.
- Use fully qualified names and add comments to tables and columns.
- Use `NOT NULL` aggressively; do not assume primary keys or foreign keys are enforced.
- Reuse an existing dbt, SQLMesh, or repo-local modeling convention when one is already present; create the lightweight scaffold only when there is no established project shape.
- Separate `raw`, `staging`, and `analytics` lifecycle stages when the project is non-trivial.

## Workflow

1. Inspect the current source tables and actual column types before designing new models.
2. Choose the target lifecycle stage and grain for each modeled table. Map dependencies between models.
3. Create the project directory structure with SQL files and manifest.
4. Author each model as a standalone SQL file. Use explicit types, nullability, comments, and fully qualified names. Decide between a table, CTAS rebuild, or view based on freshness and cost.
5. Fill in the manifest with model metadata: name, path, stage, materialization, database, and `depends_on` references.
6. When the request includes implementation, run the models and verify that the resulting tables match the expected grain and row counts. If MCP is the runner, use `query_rw` because DDL and CTAS are writes; the user's implementation request authorizes in-scope execution. For answer, review, or planning requests, keep the deliverable to SQL files plus the manifest and do not mutate the warehouse.

## Expected Project Structure

```
<project-name>/
  models/
    raw/
      raw_<entity>.sql           -- DDL for raw landing tables
    staging/
      stg_<entity>.sql           -- Deduplicated, typed, filtered
    analytics/
      dim_<entity>.sql           -- Dimension tables
      fct_<entity>.sql           -- Fact / metric tables
  model_manifest.yml             -- DAG: names, deps, materialization
```

## When to Skip the Scaffold

If the user explicitly asks for a single table, a quick DDL statement, or an ad-hoc exploration query, produce the SQL directly. The scaffold is the default for **modeling work** — multi-table, multi-stage transformations with dependencies.

## Open Next

- Read `references/MODELING_PLAYBOOK.md` for schema patterns, data-type guidance, CTAS/view decisions, complex types, constraints, project scaffold conventions, and common modeling mistakes.

## Related Skills

- `motherduck-duckdb-sql` for type syntax and function details
- `motherduck-query` for executing DDL, rebuilds, and validation queries
- `motherduck-explore` for understanding the source schema before remodeling
- `motherduck-load-data` for ingestion paths that feed the modeled tables

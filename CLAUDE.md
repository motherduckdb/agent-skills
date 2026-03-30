# MotherDuck Skills -- Claude Code Context

## What MotherDuck Is

MotherDuck is a serverless cloud data warehouse built on DuckDB.

This repo is optimized for AI builders using MotherDuck to ship apps, pipelines, Dives, and customer-facing analytics.

## Non-Negotiable Rules

- Always write **DuckDB SQL**, not PostgreSQL SQL.
- Prefer fully qualified table names: `"database"."schema"."table"`.
- Never hardcode access tokens; use `MOTHERDUCK_TOKEN`.
- Never assume runtime extension installation is available.
- Treat DuckLake as opt-in, not the default storage path.

## Connection Guidance

- Use the **Postgres endpoint** for thin clients, serverless runtimes, and existing PostgreSQL ecosystems.
- Use the **native DuckDB API** for local execution, hybrid queries, and direct file access.
- Use **pg_duckdb** when extending an existing PostgreSQL deployment.
- Use **DuckDB-Wasm** only for deliberate browser-side analytics patterns.

## Product-Level Defaults

- Use MCP-assisted exploration when available.
- Call `get_dive_guide` before `save_dive` or `update_dive`.
- Prefer Parquet when choosing formats.
- Prefer comments on analytical tables and columns.
- Prefer per-customer isolation for serious B2B customer-facing analytics.
- Prefer native MotherDuck storage unless DuckLake is explicitly the better fit.

## Skill Catalog

| Skill | Invoke | Description |
|---|---|---|
| connect | `/connect` | Choose and configure the right connection path. |
| query | `/query` | Structure and optimize DuckDB SQL for MotherDuck. |
| explore | `/explore` | Discover databases, schemas, tables, columns, views, and shares. |
| duckdb-sql | `/duckdb-sql` | Look up DuckDB SQL and MotherDuck-specific constraints. |
| load-data | `/load-data` | Ingest files, cloud objects, and upstream data into MotherDuck. |
| model-data | `/model-data` | Design analytics-ready schemas and tables. |
| share-data | `/share-data` | Distribute data with shares and share Dive-backed data safely. |
| create-dive | `/create-dive` | Build, theme, preview, save, and update Dives. |
| ducklake | `/ducklake` | Decide when DuckLake is appropriate and how to use it safely. |
| build-cfa-app | `/build-cfa-app` | Build customer-facing analytics products on MotherDuck. |
| build-dashboard | `/build-dashboard` | Create a coherent Dive-backed analytics dashboard. |
| build-data-pipeline | `/build-data-pipeline` | Build ingestion-to-serving workflows on MotherDuck. |

## Layering Rule

- Utility skills do not require other skills.
- Workflow skills depend only on utility skills.
- Use-case skills depend only on utility and workflow skills.

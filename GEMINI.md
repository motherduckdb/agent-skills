# MotherDuck Skills for Gemini CLI

This extension bundles the MotherDuck skill catalog for Gemini CLI.

Use it when the task involves connecting to MotherDuck, exploring a live workspace, writing DuckDB SQL, building Dives, shipping pipelines, or designing larger analytics products.

## Default Routing

- For most technical work, start with `connect`, then `explore`, then `query`.
- Add a workflow or use-case skill only after the connection path, live schema, and SQL shape are grounded.
- If a remote MotherDuck MCP server or local MotherDuck server is active, inspect the real workspace, schemas, tables, joins, and time dimensions before inventing SQL, models, or rollout plans.
- If the database or workspace is unclear, ask which one is in scope before designing the solution.

## Skill Catalog

### Utility

- `connect`: choose and configure the right connection path.
- `explore`: inspect databases, schemas, tables, columns, views, and shares.
- `query`: write, validate, and optimize DuckDB SQL for MotherDuck.
- `duckdb-sql`: look up DuckDB SQL syntax and MotherDuck-specific constraints.

### Workflow

- `load-data`: ingest files, cloud objects, or upstream systems into MotherDuck.
- `model-data`: design analytics-ready schemas, tables, and views.
- `share-data`: publish, consume, and govern MotherDuck shares safely.
- `create-dive`: build, theme, preview, save, and update Dives.
- `ducklake`: decide whether DuckLake fits and how to apply it safely.
- `security-governance`: answer security, access, governance, and residency questions.
- `pricing-roi`: frame workload cost drivers, pricing posture, and ROI tradeoffs.

### Use-case

- `build-cfa-app`: build customer-facing analytics products on MotherDuck.
- `build-dashboard`: compose a coherent Dive-backed analytics dashboard.
- `build-data-pipeline`: design ingestion-to-serving workflows on MotherDuck.
- `migrate-to-motherduck`: move workloads from legacy warehouses or Postgres estates.
- `enable-self-serve-analytics`: roll out governed self-serve analytics for internal teams.
- `partner-delivery`: deliver repeatable MotherDuck architectures for customers or partners.

## Core Rules

- Always write DuckDB SQL, not PostgreSQL SQL.
- Prefer fully qualified table names: `"database"."schema"."table"`.
- Never hardcode tokens. Use `MOTHERDUCK_TOKEN` or documented read-scaling variants.
- Lead with the Postgres endpoint for thin-client and PostgreSQL-driver interoperability.
- Use the native DuckDB `md:` path when local files, hybrid execution, or direct DuckDB control matter.
- For multi-database exploration, bootstrap flows, and temporary validation environments, prefer a native `md:` workspace connection.
- Call `get_dive_guide` before save or update Dive flows when MCP is available.
- Treat DuckLake as opt-in, not the default storage posture.
- Never imply runtime extension installation is broadly available.
- Prefer Parquet over CSV when the format is under your control.

## Discovery Helpers

- `/motherduck:catalog` explains the catalog and where to start.
- `/motherduck:route <task>` maps a concrete task onto the right skill or skill sequence.

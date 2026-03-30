# MotherDuck Skills -- Agent Context

## What MotherDuck Is

MotherDuck is a serverless cloud data warehouse built on DuckDB.

Agents working in this repo should optimize for app builders using MotherDuck through one of four paths:

- Postgres endpoint for thin clients and broad driver compatibility
- native DuckDB API for local execution and hybrid queries
- pg_duckdb when extending an existing PostgreSQL estate
- DuckDB-Wasm for deliberate browser-side analytics

## Non-Negotiable Rules

- Always write **DuckDB SQL**, not PostgreSQL SQL.
- Prefer fully qualified table names: `"database"."schema"."table"`.
- Never hardcode access tokens; use `MOTHERDUCK_TOKEN`.
- Never assume runtime extension installation is available.
- Treat DuckLake as opt-in, not the default storage path.

## Connection Guidance

Pick the connection path by scenario:

- Use the **Postgres endpoint** when the environment already speaks PostgreSQL wire protocol or cannot run DuckDB directly.
- Use the **native DuckDB API** when you need local file access, hybrid local/cloud execution, or richer DuckDB control.
- Use **pg_duckdb** when the app already has PostgreSQL and wants MotherDuck as an analytical extension.
- Use **Wasm** only for explicit browser-side analytics designs.

Postgres endpoint quick shape:

```text
postgresql://postgres:<MOTHERDUCK_TOKEN>@<pg-endpoint-host>:5432/<database>?sslmode=verify-full&sslrootcert=system
```

Use the documented regional hostname for the target organization, for example `pg.us-east-1-aws.motherduck.com` or `pg.eu-central-1-aws.motherduck.com`. SSL is required.

## Product-Level Defaults

- Prefer MCP-assisted exploration when an agent has MotherDuck MCP access.
- Prefer `get_dive_guide` before saving or updating Dives.
- Prefer Parquet when choosing file formats.
- Prefer comments on analytical tables and columns.
- Prefer structural isolation over query-time tenant filtering for serious B2B CFA.
- Prefer native MotherDuck storage unless DuckLake requirements are explicit.

## Skill Catalog

### Utility

- `connect`: choose and configure a connection path
- `query`: structure and optimize DuckDB SQL for MotherDuck
- `explore`: discover databases, schemas, tables, columns, views, and shares
- `duckdb-sql`: DuckDB SQL reference and MotherDuck-specific constraints

### Workflow

- `load-data`: ingest data from files, cloud storage, and upstream systems
- `model-data`: design analytics-ready schemas and tables
- `share-data`: distribute data with shares and share Dive data safely
- `create-dive`: build, theme, preview, save, and update Dives
- `ducklake`: use DuckLake when open-table-format storage is actually warranted
- `security-governance`: answer residency, access control, and governance questions
- `pricing-roi`: frame pricing, workload cost, and ROI tradeoffs

### Use-case

- `build-cfa-app`: build customer-facing analytics products on MotherDuck
- `build-dashboard`: create a coherent Dive-backed analytics dashboard
- `build-data-pipeline`: build ingestion-to-serving workflows on MotherDuck
- `migrate-to-motherduck`: plan and sequence warehouse or Postgres migrations
- `enable-self-serve-analytics`: roll out governed self-serve analytics for internal teams
- `partner-delivery`: package repeatable multi-client delivery patterns for partners

## Layering Rule

- Utility skills do not require other skills.
- Workflow skills depend only on utility skills.
- Use-case skills depend only on utility and workflow skills.

If a change violates this, fix the graph instead of explaining it away in prose.

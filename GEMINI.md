# MotherDuck Skills for Gemini CLI

This extension bundles the MotherDuck skill catalog for Gemini CLI.

Use it when the task involves connecting to MotherDuck, exploring a live workspace, writing DuckDB SQL, building Dives, shipping pipelines, or designing larger analytics products.

## Default Routing

- Start with the skill that matches the task; use connection setup or discovery only when that context is missing.
- For end-to-end work, start with the matching use-case skill and load lower-level guidance as needed.
- If a remote MotherDuck MCP server or local MotherDuck server is active, inspect the real workspace, schemas, tables, joins, and time dimensions before inventing SQL, models, or rollout plans.
- Resolve the database or workspace from the request and active context; ask only if a remaining ambiguity materially changes the result.

## Skill Catalog

### Utility

- `motherduck-connect`: choose and configure the right connection path.
- `motherduck-cli`: operate MotherDuck from shell, files, and structured output.
- `motherduck-explore`: inspect databases, schemas, tables, columns, views, and shares.
- `motherduck-query`: write, validate, and optimize DuckDB SQL for MotherDuck.
- `motherduck-duckdb-sql`: look up DuckDB SQL syntax and MotherDuck-specific constraints.
- `motherduck-rest-api`: use the REST API for service accounts, tokens, Duckling config, active accounts, and Dive embed sessions.

### Workflow

- `motherduck-load-data`: ingest files, cloud objects, or upstream systems into MotherDuck.
- `motherduck-model-data`: design analytics-ready schemas, tables, and views.
- `motherduck-manage-guides`: create, discover, version, and govern durable agent context.
- `motherduck-share-data`: publish, consume, and govern MotherDuck shares safely.
- `motherduck-create-dive`: build, theme, preview, save, and update Dives.
- `motherduck-create-flight`: create, schedule, run, and debug Flights (Python jobs on MotherDuck compute).
- `motherduck-design-dive`: design responsive, reusable Dives with filters and light/dark themes.
- `motherduck-ducklake`: decide whether DuckLake fits and how to apply it safely.
- `motherduck-security-governance`: answer security, access, governance, and residency questions.
- `motherduck-pricing-roi`: frame workload cost drivers, pricing posture, and ROI tradeoffs.

### Use-case

- `motherduck-build-cfa-app`: build customer-facing analytics products on MotherDuck.
- `motherduck-build-dashboard`: compose a coherent Dive-backed analytics dashboard.
- `motherduck-build-data-pipeline`: design ingestion-to-serving workflows on MotherDuck.
- `motherduck-migrate-to-motherduck`: move workloads from legacy warehouses or Postgres estates.
- `motherduck-enable-self-serve-analytics`: roll out governed self-serve analytics for internal teams.
- `motherduck-partner-delivery`: deliver repeatable MotherDuck architectures for customers or partners.

## Core Rules

- Always write DuckDB SQL, not PostgreSQL SQL.
- Prefer fully qualified table names: `"database"."schema"."table"`.
- Never hardcode tokens. Use `MOTHERDUCK_TOKEN` or documented read-scaling variants.
- Lead with the Postgres endpoint for thin-client and PostgreSQL-driver interoperability.
- Use the native DuckDB `md:` path when local files, hybrid execution, or direct DuckDB control matter.
- For multi-database exploration, bootstrap flows, and temporary validation environments, prefer a native `md:` workspace connection.
- Call `get_dive_guide` before save or update Dive flows when MCP is available.
- Call `get_query_guide` before business-semantic queries and traverse relevant Guide topics.
- Prefer the MotherDuck CLI for file-shaped Dive/Flight work when a shell is available; prefer MCP for chat-only exploration.
- Treat DuckLake as opt-in, not the default storage posture.
- Never imply runtime extension installation is broadly available.
- Prefer Parquet over CSV when the format is under your control.

## Discovery Helpers

- `/motherduck:catalog` explains the catalog and where to start.
- `/motherduck:route <task>` maps a concrete task onto the right skill or skill sequence.

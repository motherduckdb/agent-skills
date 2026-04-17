# MotherDuck Skills -- Claude Code Context

## What MotherDuck Is

MotherDuck is a serverless cloud data warehouse built on DuckDB.

This repo is optimized for AI builders using MotherDuck to ship apps, pipelines, Dives, and customer-facing analytics.

## Default Routing

- For most narrow technical work, start with `motherduck-connect`, then `motherduck-explore`, then `motherduck-query`.
- For larger product work, start with the matching use-case skill and let it orchestrate the lower layers.
- If a remote MotherDuck MCP server or local MotherDuck server is active, inspect the live workspace before inventing SQL, models, or rollout plans.

## Install Notes

- For shared Skills CLI installs, assume the prerequisite is `npm install -g @fountainai/skills` unless the environment already has the CLI.
- The dedicated Claude plugin package lives at `plugins/motherduck-skills-claude`.

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
- For use-case skills, if a remote MotherDuck MCP server or local MotherDuck server is active, start from the real database in scope.
- If the database or workspace is unclear, ask which one should back the project before designing the solution.
- Inspect schemas, tables, columns, joins, and time dimensions before inventing example models or rollout steps.
- Call `get_dive_guide` before `save_dive` or `update_dive`.
- Prefer Parquet when choosing formats.
- Prefer comments on analytical tables and columns.
- Prefer per-customer isolation for serious B2B customer-facing analytics.
- Prefer native MotherDuck storage unless DuckLake is explicitly the better fit.
- In use-case skills, structured JSON is an explicit test/tooling contract, not the default human-facing response format.
- `Validation Signals` sections in references are maintainer/reviewer guidance, not a required heading in normal user-facing replies.
- Shipped skill content must be self-contained; `motherduck-examples` may inform authoring but must not appear as a runtime dependency.

## Repo Maintenance Layout

- Treat root `scripts/` as executable entrypoints only.
- Shared script implementation lives under `scripts/_lib/`.
- Shared test implementation lives under `tests/_lib/`.
- When artifact behavior changes, keep the Python and TypeScript companion artifacts aligned when both exist.

## Skill Catalog

| Skill | Invoke | Description |
|---|---|---|
| motherduck-connect | `/motherduck-connect` | Choose and configure the right connection path. |
| motherduck-query | `/motherduck-query` | Structure and optimize DuckDB SQL for MotherDuck. |
| motherduck-explore | `/motherduck-explore` | Discover databases, schemas, tables, columns, views, and shares. |
| motherduck-duckdb-sql | `/motherduck-duckdb-sql` | Look up DuckDB SQL and MotherDuck-specific constraints. |
| motherduck-rest-api | `/motherduck-rest-api` | Manage service accounts, tokens, Duckling config, active accounts, and Dive embed sessions. |
| motherduck-load-data | `/motherduck-load-data` | Ingest files, cloud objects, and upstream data into MotherDuck. |
| motherduck-model-data | `/motherduck-model-data` | Design analytics-ready schemas and tables. |
| motherduck-share-data | `/motherduck-share-data` | Distribute data with shares and share Dive-backed data safely. |
| motherduck-create-dive | `/motherduck-create-dive` | Build, theme, preview, save, and update Dives. |
| motherduck-ducklake | `/motherduck-ducklake` | Decide when DuckLake is appropriate and how to use it safely. |
| motherduck-security-governance | `/motherduck-security-governance` | Answer security, governance, access, and residency questions. |
| motherduck-pricing-roi | `/motherduck-pricing-roi` | Frame workload cost, pricing posture, and ROI tradeoffs. |
| motherduck-build-cfa-app | `/motherduck-build-cfa-app` | Build customer-facing analytics products on MotherDuck. |
| motherduck-build-dashboard | `/motherduck-build-dashboard` | Create a coherent Dive-backed analytics dashboard. |
| motherduck-build-data-pipeline | `/motherduck-build-data-pipeline` | Build ingestion-to-serving workflows on MotherDuck. |
| motherduck-migrate-to-motherduck | `/motherduck-migrate-to-motherduck` | Plan migrations from legacy warehouses and Postgres estates. |
| motherduck-enable-self-serve-analytics | `/motherduck-enable-self-serve-analytics` | Roll out governed self-serve analytics for internal teams. |
| motherduck-partner-delivery | `/motherduck-partner-delivery` | Deliver repeatable MotherDuck architectures for clients and partners. |

## Layering Rule

- Utility skills do not require other skills.
- Workflow skills depend only on utility skills.
- Use-case skills depend only on utility and workflow skills.

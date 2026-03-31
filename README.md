<h1><img src="assets/duck_skills.png" alt="MotherDuck Skills" height="80" align="center" /> MotherDuck Skills for AI Agents</h1>

MotherDuck Skills is the public skill catalog for agents building on MotherDuck.

It gives coding agents durable, opinionated guidance for the work people actually do on MotherDuck: connecting applications, exploring live data, writing DuckDB SQL, modeling analytics tables, building Dives, and shipping larger end-to-end patterns like customer-facing analytics, dashboards, migrations, and data pipelines.

This repo is intentionally agent-oriented:

- it assumes the agent may have MotherDuck MCP access
- it prefers live schema discovery over invented schemas when a server is available
- it keeps detailed guidance in `references/`
- it packages runnable use-case artifacts inside the skill folders
- it now tests those artifacts against temporary real MotherDuck databases, not just local DuckDB

## Install

```bash
npx skills add motherduckdb/agent-skills
```

Claude Code plugin install:

```bash
/plugin marketplace add motherduckdb/agent-skills
/plugin install motherduck-skills@motherduck-agent-skills
```

Codex plugin install:

1. Clone or open this repo in Codex.
2. Restart Codex if it was already running for the repo.
3. Open `/plugins`.
4. Install **MotherDuck Skills** from the repo marketplace.

## What Agents Can Build With This Repo

- connect apps and services to MotherDuck with the right connection path
- inspect real databases and shape work around the actual schema
- write and validate DuckDB SQL for analytics workloads
- model analytics-ready tables and views
- create, theme, and save Dives
- build full use cases like dashboards, pipelines, migrations, self-serve analytics, partner delivery, and customer-facing analytics

## How Agents Should Use This Repo

For most real tasks, the right flow is:

1. `connect`
2. `explore`
3. `query`
4. move into the workflow or use-case skill that matches the job

That sequence is deliberate:

- `connect` decides PG endpoint vs native DuckDB vs other paths
- `explore` establishes the real MotherDuck data model in scope
- `query` validates the actual SQL shape before higher-level orchestration
- the higher-level skill should then stay focused on architecture and delivery

When a use-case skill is involved and a remote or local MotherDuck server is active, the agent should not guess the schema:

1. ask which database or workspace is in scope if unclear
2. inspect databases, schemas, tables, columns, joins, and date fields
3. let the actual data model drive the architecture, implementation plan, and examples

## Featured Skills

- `connect` -- choose PG endpoint, native DuckDB, `pg_duckdb`, or Wasm
- `query` -- write and validate DuckDB SQL against MotherDuck
- `create-dive` -- build, theme, preview, save, and update Dives
- `build-dashboard` -- compose one coherent multi-section Dive-backed dashboard
- `build-cfa-app` -- design serious customer-facing analytics with isolation and serving boundaries
- `build-data-pipeline` -- land, transform, and publish analytics-ready data
- `migrate-to-motherduck` -- move off legacy warehouses and validate cutover

## Skills Overview

| Skill | Layer | Description |
|-------|-------|-------------|
| `connect` | Utility | Connect to MotherDuck via the Postgres endpoint, native DuckDB API, `pg_duckdb`, or Wasm |
| `query` | Utility | Execute and optimize DuckDB SQL queries against MotherDuck |
| `explore` | Utility | Discover databases, tables, columns, views, and shares |
| `duckdb-sql` | Utility | DuckDB SQL syntax reference for MotherDuck |
| `load-data` | Workflow | Ingest data from files, cloud storage, HTTP, and upstream systems |
| `model-data` | Workflow | Design schemas and data models for analytical workloads |
| `share-data` | Workflow | Create and consume MotherDuck shares safely |
| `create-dive` | Workflow | Build, theme, preview, save, and update Dives |
| `ducklake` | Workflow | Decide when DuckLake fits and how to use it on MotherDuck |
| `security-governance` | Workflow | Answer security, governance, residency, and access-control questions with MotherDuck-specific guidance |
| `pricing-roi` | Workflow | Frame MotherDuck pricing, workload cost drivers, and ROI tradeoffs for technical and commercial buyers |
| `build-cfa-app` | Use-case | Build customer-facing analytics applications |
| `build-dashboard` | Use-case | Create multi-section analytics dashboards backed by Dives |
| `build-data-pipeline` | Use-case | Design ingestion-to-serving data pipelines |
| `migrate-to-motherduck` | Use-case | Plan migrations from Snowflake, Redshift, Postgres, and dbt-heavy stacks onto MotherDuck |
| `enable-self-serve-analytics` | Use-case | Roll out self-serve analytics, sharing, and Dive-backed dashboards for internal teams |
| `partner-delivery` | Use-case | Deliver repeatable multi-client MotherDuck architectures for consultants and partners |

## Repo Shape

Each skill folder can contain:

- `SKILL.md` -- the concise router the agent should load first
- `references/` -- preserved detailed guidance and playbooks
- `artifacts/` -- runnable local examples or helpers

Some use-case skills also ship a fuller runnable reference project under `references/` when the local artifact is intentionally smaller than the real workflow.

The machine-readable index lives at:

- `skills/catalog.json`

That catalog tracks:

- skill names and descriptions
- layer and dependencies
- reference files
- runnable artifacts
- source docs
- whether a use-case should begin with live MotherDuck discovery

## Runnable Use-Case Artifacts

These are local-first examples packaged with the skills:

```bash
uv run --with duckdb python skills/build-cfa-app/artifacts/customer_routing_example.py
uv run --with duckdb python skills/build-dashboard/artifacts/dashboard_story_example.py
uv run --with duckdb python skills/build-data-pipeline/artifacts/pipeline_stage_example.py
uv run --with duckdb python skills/migrate-to-motherduck/artifacts/migration_validation_example.py
uv run --with duckdb python skills/enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
uv run --with duckdb python skills/partner-delivery/artifacts/client_delivery_example.py
```

They are not meant to replace production code. They are small runnable patterns that help an agent move from plan to implementation faster.

To run the whole artifact suite against temporary real MotherDuck databases with your token:

```bash
uv run scripts/test_motherduck_artifacts.py
```

That suite:

- runs all six use-case artifacts against temporary MotherDuck databases
- runs the full `dlt + dbt + MotherDuck` reference pipeline
- drops the temporary databases afterward

For a fuller MotherDuck pipeline example, `build-data-pipeline` also includes:

```bash
cd skills/build-data-pipeline/references/dlt-dbt-motherduck-project
export MOTHERDUCK_TOKEN=...
export MOTHERDUCK_PIPELINE_DB=md_skills_pipeline_demo
uv sync --python 3.12
uv run python pipeline/run_all.py
uv run python pipeline/cleanup.py
```

## Why This Repo Is Opinionated

These skills are not a neutral encyclopedia.

They preserve a few strong defaults:

- DuckDB SQL, not PostgreSQL SQL
- fully qualified table names
- PG endpoint for thin-client interoperability paths
- native DuckDB APIs when local files or hybrid execution matter
- Parquet over CSV when the format is under our control
- native MotherDuck storage unless DuckLake is explicitly required
- structural isolation over query-time tenant filtering for serious customer-facing analytics
- MCP-first exploration and Dive workflows when MotherDuck MCP is available

## Authoring and Sync

If you are editing the repo itself:

- `docs/skill-authoring.md` -- how skills should be structured here
- `docs/skills-sync.md` -- how product docs, skills, references, and artifacts should stay aligned

## Validation

```bash
uv run scripts/validate_skills.py
uv run --with duckdb --with pyyaml python tests/validate_snippets.py
uv run scripts/test_codex_plugin.py
uv run scripts/test_codex_use_cases.py
uv run scripts/test_motherduck_artifacts.py
uv run scripts/benchmark_motherduck_artifacts.py --runs 2
```

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a branch.
3. Make the skill, reference, artifact, or catalog change.
4. Run the validators.
5. Open a PR with a clear explanation of what changed and why.

## Links

- [MotherDuck Documentation](https://motherduck.com/docs/)
- [MotherDuck MCP Server](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-setup/)
- [MotherDuck Dive Gallery](https://motherduck.com/dive-gallery/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckLake](https://ducklake.select/)
- [Agent Skills Specification](https://agentskills.io)

## License

This project is licensed under the [MIT License](LICENSE).

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

Choose one install path for each agent. For packaged installs, the order below is Claude Code first, Codex second, and Gemini CLI third. For cross-agent raw skill installs, the Skills CLI remains the simplest default.

Avoid mixing plugin installs and raw skill installs for the same agent unless you are testing packaging behavior.

### Choose an install path

| Goal | Recommended path |
|-------|------------------|
| Use the packaged Claude Code plugin from the repo marketplace | Claude Code plugin install |
| Use the packaged Codex plugin from the repo marketplace | Codex plugin install |
| Install the whole MotherDuck catalog in Gemini CLI | Gemini CLI extension install |
| Install one or two skills in Gemini CLI without the packaged extension | Gemini CLI skills install |
| Install the whole MotherDuck catalog quickly | Skills CLI |
| Install only one or two skills | Skills CLI with `--skill` |
| Vendor one skill directly into a repo or agent home without plugin tooling | Manual per-skill install |

### Claude Code plugin install

```bash
/plugin marketplace add motherduckdb/agent-skills
/plugin install motherduck-skills@motherduck-agent-skills
```

After install, restart Claude Code if it was already running. The skills load automatically and should trigger when relevant.

This plugin packages the whole MotherDuck catalog. You do not need to install each skill separately.

### Codex plugin install

1. Clone or open this repo in Codex.
2. Restart Codex if it was already running for the repo.
3. Open `/plugins`.
4. Install **MotherDuck Skills** from the repo marketplace.

This path installs the packaged repo-local Codex plugin. After installation, the skills are available automatically when relevant.

### Gemini CLI extension install

Install from GitHub:

```bash
gemini extensions install https://github.com/motherduckdb/agent-skills --consent
```

For local development from a checkout:

```bash
gemini extensions link .
```

After installation, restart Gemini CLI or reload your session. Useful follow-ups:

```bash
gemini extensions list
gemini skills list
```

Inside Gemini CLI you can also use:

- `/extensions list`
- `/skills list`
- `/motherduck:catalog`
- `/motherduck:route build a dashboard over my MotherDuck analytics tables`

### Gemini CLI skills install

If you want only one specific MotherDuck skill in Gemini CLI, install it directly as an Agent Skill instead of installing the full extension:

```bash
gemini skills install https://github.com/motherduckdb/agent-skills.git --path skills/connect
```

You can also link the repo's skills locally:

```bash
gemini skills link skills
```

### Skills CLI: install all skills

```bash
npx skills add motherduckdb/agent-skills
```

### Skills CLI: install one or more specific skills

```bash
npx skills add motherduckdb/agent-skills --skill connect --skill explore --skill query
```

You can also install directly from a single skill path in the repo:

```bash
npx skills add https://github.com/motherduckdb/agent-skills/tree/main/skills/connect
```

Useful variants:

```bash
# list the skills in this repo without installing
npx skills add motherduckdb/agent-skills --list

# install only selected skills
npx skills add motherduckdb/agent-skills --skill connect --skill explore --skill query

# install only to Claude Code, globally
npx skills add motherduckdb/agent-skills --skill connect -a claude-code -g

# install only to Codex, globally
npx skills add motherduckdb/agent-skills --skill connect -a codex -g

# install one skill from the repo path, to Claude Code only
npx skills add https://github.com/motherduckdb/agent-skills/tree/main/skills/connect -a claude-code -g
```

Best practices:

- the default install scope is project-local; use that when the skills should travel with the repo
- add `-g` when you want a personal cross-project install
- use `--skill <name>` when you want only a few skills instead of the whole catalog
- prefer the repo-level install plus `--skill` over many one-off path installs when you want multiple MotherDuck skills from this catalog

### Manual per-skill install

Copy the whole skill directory, not just `SKILL.md`, so any bundled `references/`, `scripts/`, and `artifacts/` remain available.

Project-local manual install:

```bash
mkdir -p .agents/skills
cp -R skills/connect .agents/skills/connect
```

Global manual install for a specific agent:

```bash
mkdir -p ~/.claude/skills ~/.codex/skills
cp -R skills/connect ~/.claude/skills/connect
cp -R skills/connect ~/.codex/skills/connect
```

Replace `connect` with any skill name from this repo, for example `query`, `create-dive`, or `build-dashboard`.

For manual installs, prefer `.agents/skills/<name>` when the skill should be shared with the project. Use `~/.claude/skills/<name>` or `~/.codex/skills/<name>` only for personal cross-project defaults.

### After installation

These are skills, not standalone apps. Once installed, the normal flow is to ask the agent to do the work and let it pull in the relevant skill when needed.

Examples:

- `Use MotherDuck skills to connect to my workspace and inspect the schema.`
- `Use the connect, explore, and query skills to validate this analytics query.`
- `Use MotherDuck skills to build a Dive-backed dashboard on these tables.`
- `/motherduck:route migrate this Postgres analytics workload to MotherDuck`

If you installed a single skill manually or through the Skills CLI, you can name it explicitly, but most agents should also discover it automatically from context.

Maintainer note for Gemini gallery discovery:

- keep `gemini-extension.json` at the repo root
- keep the repo public
- add the GitHub topic `gemini-cli-extension` in the repository settings so the Gemini gallery crawler can find it

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

These are the end-to-end use-case skills in the catalog:

- `build-cfa-app` -- build serious customer-facing analytics with isolation and serving boundaries
- `build-dashboard` -- compose one coherent multi-section analytics dashboard
- `build-data-pipeline` -- land, transform, and publish analytics-ready data
- `migrate-to-motherduck` -- move off legacy warehouses and validate cutover
- `enable-self-serve-analytics` -- roll out governed self-serve analytics for internal teams
- `partner-delivery` -- deliver repeatable MotherDuck architectures for consultants and partners

## Skills Overview

| Skill | Layer | Use it when |
|-------|-------|-------------|
| `connect` | Utility | you need to choose the right connection path before writing code or SQL |
| `explore` | Utility | you need to inspect real databases, schemas, tables, columns, views, or shares |
| `query` | Utility | you need to write, validate, or optimize DuckDB SQL against MotherDuck |
| `duckdb-sql` | Utility | you need DuckDB SQL syntax or MotherDuck-specific SQL constraints quickly |
| `load-data` | Workflow | you need to ingest files, cloud objects, HTTP data, or upstream systems into MotherDuck |
| `model-data` | Workflow | you need to design analytical schemas, tables, views, or transformation layers |
| `share-data` | Workflow | you need to publish, consume, or govern MotherDuck shares safely |
| `create-dive` | Workflow | you need to build, theme, preview, save, or update a Dive |
| `ducklake` | Workflow | you need to decide whether DuckLake is appropriate and how to apply it safely |
| `security-governance` | Workflow | you need MotherDuck-specific guidance on security, access, governance, or residency |
| `pricing-roi` | Workflow | you need to frame workload cost drivers, pricing posture, or ROI tradeoffs |
| `build-cfa-app` | Use-case | you are building a customer-facing analytics product on MotherDuck |
| `build-dashboard` | Use-case | you are building one coherent analytics dashboard backed by Dives and tables |
| `build-data-pipeline` | Use-case | you are designing an ingestion-to-serving data pipeline on MotherDuck |
| `migrate-to-motherduck` | Use-case | you are moving from Snowflake, Redshift, Postgres, or dbt-heavy stacks onto MotherDuck |
| `enable-self-serve-analytics` | Use-case | you are rolling out internal self-serve analytics, sharing, and governed dashboards |
| `partner-delivery` | Use-case | you are delivering repeatable multi-client MotherDuck implementations for customers or partners |

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

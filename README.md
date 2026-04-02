<h1><img src="assets/duck_skills.png" alt="MotherDuck Skills" height="80" align="center" /> MotherDuck Skills for AI Agents</h1>

MotherDuck Skills is the public skill catalog for agents building on MotherDuck.

It gives agents practical guidance for the most common work on the platform: connecting to MotherDuck, exploring live data, writing DuckDB SQL, modeling tables, building Dives, and shipping larger workflows like dashboards, migrations, and data pipelines.

The lower-level skills are intentionally not generic data-engineering tutorials. They exist to encode MotherDuck-specific defaults, gotchas, and opinionated workflow choices:

- when to prefer the PG endpoint versus a native DuckDB client
- when DuckDB SQL differs from PostgreSQL habits that would break on MotherDuck
- when native MotherDuck storage should stay the default over DuckLake
- how shares, Dives, read scaling, and customer-facing isolation actually work on MotherDuck

The repo is intentionally opinionated and agent-oriented:

- prefer live schema discovery over invented schemas
- keep utility and workflow `SKILL.md` files short and router-like
- keep deeper guidance in `references/`
- ship runnable examples inside the skill folders
- validate important artifacts against temporary real MotherDuck databases

## Install

Choose one install path per agent.

- want the packaged experience: use the Claude Code, Codex, or Gemini CLI install
- want only a few skills or a cross-agent install: use the Skills CLI
- want full manual control: copy a skill directory directly

Avoid mixing packaged installs and raw skill installs for the same agent unless you are testing packaging behavior.

### Choose an install path

| Goal | Recommended path |
|-------|------------------|
| Use the packaged Claude Code plugin from the repo marketplace | Claude Code plugin install |
| Use the packaged Codex plugin from the repo marketplace | Codex plugin install |
| Install the whole MotherDuck catalog in Gemini CLI | Gemini CLI extension install |
| Install one or two skills in Gemini CLI without the packaged extension | Gemini CLI skills install |
| Install the whole MotherDuck catalog quickly | Skills CLI |
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

After installation, restart Gemini CLI or reload your session. `gemini extensions list` and `gemini skills list` can help confirm the install.

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

The `skills` package is interactive, so use the repo-level install and follow the prompts.

Best practices:

- the default install scope is project-local; use that when the skills should travel with the repo
- add `-g` when you want a personal cross-project install
- use manual per-skill install when you want only one skill from this repo without the full catalog

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

For manual installs, prefer `.agents/skills/<name>` when the skill should be shared with the project. Use `~/.claude/skills/<name>` or `~/.codex/skills/<name>` only for personal cross-project defaults.

### After installation

These are skills, not standalone apps. After install, ask the agent to do the work and let it load the right skill from context.

You can name a skill explicitly if you want, but in most cases a normal request is enough:

- `Use MotherDuck skills to inspect this workspace and validate the query.`
- `Use MotherDuck skills to build a dashboard on these tables.`

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

For most real tasks, start in this order:

1. `connect`
2. `explore`
3. `query`
4. move into the workflow or use-case skill that matches the job

That keeps the agent grounded in the real connection path, schema, and SQL shape before it moves into higher-level orchestration.

This order matters because the lower-level skills are the opinionated foundation. They should add MotherDuck-specific judgment, not reteach generic analytics theory.

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

```text
+---------------------------------------------------------------+
|                           Use Cases                           |
| build-cfa-app | build-dashboard | build-data-pipeline         |
| migrate-to-motherduck | enable-self-serve-analytics           |
| partner-delivery                                            |
+---------------------------------------------------------------+
|                           Workflows                           |
| load-data | model-data | share-data | create-dive             |
| ducklake | security-governance | pricing-roi                  |
+---------------------------------------------------------------+
|                           Utilities                           |
| connect | explore | query | duckdb-sql                        |
+---------------------------------------------------------------+
```

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

In practice, this means:

- utility and workflow skills should stay short, activation-friendly, and explicit about defaults
- detailed mechanics, examples, and edge cases belong in `references/`
- use-case skills should orchestrate lower-level skills rather than duplicating them

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

These are packaged per use-case as paired artifacts:

- a MotherDuck-backed Python artifact used by the existing smoke tests
- a TypeScript companion artifact with the same output contract for app/backend-oriented implementations

Python artifact commands:

```bash
uv run --with duckdb python skills/build-cfa-app/artifacts/customer_routing_example.py
uv run --with duckdb python skills/build-dashboard/artifacts/dashboard_story_example.py
uv run --with duckdb python skills/build-data-pipeline/artifacts/pipeline_stage_example.py
uv run --with duckdb python skills/migrate-to-motherduck/artifacts/migration_validation_example.py
uv run --with duckdb python skills/enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
uv run --with duckdb python skills/partner-delivery/artifacts/client_delivery_example.py
```

Validate the TypeScript companion artifacts:

```bash
uv run scripts/test_typescript_artifacts.py
```

They are not meant to replace production code. They are small patterns that help an agent move from plan to implementation faster.

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
uv run scripts/test_typescript_artifacts.py
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

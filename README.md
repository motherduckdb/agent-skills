<h1><img src="assets/duck_skills.png" alt="MotherDuck Skills" height="80" align="center" /> MotherDuck Skills for AI Agents</h1>

MotherDuck Skills is the public skill catalog for agents and developers building on MotherDuck.

It packages the common work done on the platform: choosing the right connection path, exploring live data, writing DuckDB SQL, using the REST API for administration, building Dives, and shipping larger workflows like dashboards, migrations, pipelines, and customer-facing analytics apps.

The repo is intentionally opinionated. It is a productized set of MotherDuck defaults and workflows.

## Quick Start

- install the repo in the harness you already use
- mention MotherDuck in your prompt and the agent should pick the right skill automatically
- when a remote or local MotherDuck server is active, let the live schema drive the work

See `HARNESSES.md` for the full harness matrix and `docs/install-matrix.md` for copy-paste install commands.

## Supported Harnesses

All main harnesses can use the shared MotherDuck catalog through `npx skills`.
For the major harnesses that support it, this repo also ships native packaged plugin or extension surfaces.

| Harness | Best path | Native packaged surface in this repo |
|-------|-------|-------|
| `Claude Code` | Claude plugin or `npx skills` | `plugins/motherduck-skills-claude/.claude-plugin/plugin.json` |
| `Codex` | Codex plugin or `npx skills` | `.codex-plugin/plugin.json`, `plugins/motherduck-skills` |
| `Gemini CLI` | Gemini extension or Gemini skills install | `gemini-extension.json`, `commands/`, `GEMINI.md` |

## Install

Choose one install path per harness.

### Skills CLI: install all skills

This is the default install path for most agents, including `Codex`, `Claude Code`, and custom agent setups.

Use the non-interactive repo-level install that auto-accepts all prompts and installs the full catalog:

Local (current project):

```bash
npx skills add motherduckdb/agent-skills --skill '*' --yes
```

Global (all projects):

```bash
npx skills add motherduckdb/agent-skills --skill '*' --yes --global
```

To link skills to a specific agent (e.g. Claude Code):

```bash
npx skills add motherduckdb/agent-skills --agent claude-code --skill '*' --yes --global
```

### Claude Code plugin install

```bash
/plugin marketplace add motherduckdb/agent-skills
/plugin install motherduck-skills@motherduck-agent-skills
```

After install, restart Claude Code if it was already running. The skills load automatically and should trigger when relevant.

For local Claude plugin development and validation, use the dedicated package root:

```bash
claude --plugin-dir ./plugins/motherduck-skills-claude
```

### Codex plugin install

1. Clone or open this repo in Codex.
2. Restart Codex if it was already running for the repo.
3. Open `/plugins`.
4. Install **MotherDuck Skills** from the repo marketplace.

### Gemini CLI extension install

Install from GitHub:

```bash
gemini extensions install https://github.com/motherduckdb/agent-skills --consent
```

For local development from a checkout:

```bash
gemini extensions link .
```

### Manual per-skill install

Copy the whole skill directory, not just `SKILL.md`, so any bundled `references/`, `scripts/`, and `artifacts/` remain available.

Global manual install for a specific agent:

```bash
mkdir -p ~/.claude/skills ~/.codex/skills
cp -R skills/motherduck-connect ~/.claude/skills/motherduck-connect
cp -R skills/motherduck-connect ~/.codex/skills/motherduck-connect
```

## Start Here by Task

| If you need to... | Start with... |
|-------|-------|
| connect an app or service to MotherDuck | `motherduck-connect` |
| inspect a live workspace or schema | `motherduck-explore` |
| write or debug analytics SQL | `motherduck-query` |
| check exact DuckDB syntax | `motherduck-duckdb-sql` |
| manage service accounts, tokens, Duckling config, active accounts, or Dive embed sessions with the REST API | `motherduck-rest-api` |
| build a Dive | `motherduck-create-dive` |
| build a dashboard | `motherduck-build-dashboard` |
| design a data pipeline | `motherduck-build-data-pipeline` |
| plan a migration | `motherduck-migrate-to-motherduck` |
| design customer-facing analytics | `motherduck-build-cfa-app` |

## Skills Overview

| Skill | Layer | Use it when |
|-------|-------|-------------|
| `motherduck-connect` | Utility | you need to choose the right connection path before writing code or SQL |
| `motherduck-explore` | Utility | you need to inspect real databases, schemas, tables, columns, views, or shares |
| `motherduck-query` | Utility | you need to write, validate, or optimize DuckDB SQL against MotherDuck |
| `motherduck-duckdb-sql` | Utility | you need DuckDB SQL syntax or MotherDuck-specific SQL constraints quickly |
| `motherduck-rest-api` | Utility | you need to use the REST API for control-plane tasks like service accounts, tokens, Duckling config, active accounts, or Dive embed sessions |
| `motherduck-load-data` | Workflow | you need to ingest files, cloud objects, HTTP data, or upstream systems into MotherDuck |
| `motherduck-model-data` | Workflow | you need to design analytical schemas, tables, views, or transformation layers |
| `motherduck-share-data` | Workflow | you need to publish, consume, or govern MotherDuck shares safely |
| `motherduck-create-dive` | Workflow | you need to build, theme, preview, save, or update a Dive |
| `motherduck-ducklake` | Workflow | you need to decide whether DuckLake is appropriate and how to apply it safely |
| `motherduck-security-governance` | Workflow | you need MotherDuck-specific guidance on security, access, governance, or residency |
| `motherduck-pricing-roi` | Workflow | you need to frame workload cost drivers, pricing posture, or ROI tradeoffs |
| `motherduck-build-cfa-app` | Use-case | you are building a customer-facing analytics product on MotherDuck |
| `motherduck-build-dashboard` | Use-case | you are building one coherent analytics dashboard backed by Dives and tables |
| `motherduck-build-data-pipeline` | Use-case | you are designing an ingestion-to-serving data pipeline on MotherDuck |
| `motherduck-migrate-to-motherduck` | Use-case | you are moving from Snowflake, Redshift, Postgres, or dbt-heavy stacks onto MotherDuck |
| `motherduck-enable-self-serve-analytics` | Use-case | you are rolling out internal self-serve analytics, sharing, and governed dashboards |
| `motherduck-partner-delivery` | Use-case | you are delivering repeatable multi-client MotherDuck implementations for customers or partners |

## Why This Repo Is Opinionated

These skills preserve a few strong defaults:

- DuckDB SQL, not PostgreSQL SQL
- fully qualified table names
- PG endpoint for thin-client interoperability paths
- native DuckDB APIs when local files or hybrid execution matter
- Parquet over CSV when the format is under our control
- native MotherDuck storage unless DuckLake is explicitly required
- structural isolation over query-time tenant filtering for serious customer-facing analytics
- MCP-first exploration and Dive workflows when MotherDuck MCP is available

## For Agents

Use this repo as a routed skill catalog

- Install the plugins or skills matching what you need. Usually, it's better to install the entire plugin, as skills and plugin only use a minimal amount of context (they are not loaded fully in context, just their description)
- `Route work`: start with `motherduck-connect`, then `motherduck-explore`, then `motherduck-query` for narrow technical work; start with the matching use-case skill for end-to-end product work.
- `Use live discovery`: if a remote or local MotherDuck server is active, inspect the real workspace, schema, joins, and date columns before inventing examples or plans.
- `Read next`:
  - `skills/catalog.json`
  - `HARNESSES.md`
  - `CLAUDE.md`
  - `CONTRIBUTING.md`
  - `docs/skill-authoring.md`
  - `docs/skills-sync.md`
- `Validate changes`:
  - `uv run scripts/validate_skills.py`
  - `claude plugin validate ./.claude-plugin/marketplace.json`
  - `claude plugin validate ./plugins/motherduck-skills-claude`
  - `uv run scripts/check_claude_plugin_sync.py`

## Links

- [MotherDuck Documentation](https://motherduck.com/docs/)
- [MotherDuck MCP Server](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-setup/)
- [MotherDuck Dive Gallery](https://motherduck.com/dive-gallery/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckLake](https://ducklake.select/)
- [Agent Skills Specification](https://agentskills.io)

## License

This project is licensed under the [MIT License](LICENSE).

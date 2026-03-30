<h1><img src="assets/duck_skills.png" alt="MotherDuck Skills" height="80" align="center" /> MotherDuck Skills for AI Agents</h1>

Opinionated AI agent skills for building applications with [MotherDuck](https://motherduck.com) -- the serverless, DuckDB-powered cloud data warehouse.

These skills help both users and coding agents make better decisions when working with MotherDuck: how to connect, how to query, how to model data, how to build Dives, and how to ship production patterns like customer-facing analytics and data pipelines.

> This project is public and evolving. MotherDuck, Dives, MCP workflows, and DuckLake continue to improve quickly, so the skills are designed to stay opinionated while still pointing agents toward current product guidance.

## Quick Install

```bash
npx skills add motherduckdb/agent-skills
```

## What Are Skills?

Skills are instruction files that AI coding agents use to understand how to work with MotherDuck. When installed, they give your agent durable knowledge of MotherDuck's connection options, SQL dialect, data loading patterns, product surfaces, and application architecture -- so you can go from prompt to production without constantly correcting the model.

Skills follow the open [Agent Skills specification](https://agentskills.io) and work across tools like Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, and other compatible coding agents.

## The Skill Pyramid

MotherDuck Skills are organized in three layers. Higher layers build on lower ones.

```text
                        USE-CASE
        ┌──────────────────────────────────────────────┐
        │  build-cfa-app                              │
        │  build-dashboard                            │
        │  build-data-pipeline                        │
        │  migrate-to-motherduck                      │
        │  enable-self-serve-analytics                │
        │  partner-delivery                           │
        └─────────────────────┬────────────────────────┘
                              │
                        WORKFLOW
  ┌──────────────────┼────────────────────────────────────────────┐
  │  load-data       │  create-dive                              │
  │  model-data      │  ducklake                                 │
  │  share-data      │  security-governance                      │
  │  pricing-roi     │                                            │
  └─────────┬────────┴───────────────────────┬────────────────────┘
            │                                │
                   UTILITY
          ┌──────────┼─────────────────┼──────────┐
          │ connect  │  query          │ duckdb-sql │
          │          │  explore        │            │
          └──────────┴─────────────────┴────────────┘
```

- **Utility** -- Foundational capabilities: connecting, querying, exploring data, and DuckDB SQL.
- **Workflow** -- Task-specific MotherDuck workflows: loading data, modeling schemas, building Dives, sharing data, and working with DuckLake.
- **Use-case** -- End-to-end application patterns: customer-facing analytics, dashboards, and data pipelines.

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

## How the Skills Work Together

This repo is meant to be used as a system, not just as a list of isolated files.

- `connect`, `query`, `explore`, and `duckdb-sql` form the foundation for everything else.
- `create-dive` builds on exploration and query work rather than replacing it.
- `build-dashboard` composes exploration, query design, and Dive creation into one workflow.
- `build-cfa-app` combines connection, modeling, and serving patterns for product teams embedding analytics into their apps.
- `build-data-pipeline` ties together ingestion, transformation, and publishing decisions.
- `migrate-to-motherduck` is the migration-specific orchestration layer for platform teams moving from existing warehouses or PostgreSQL estates.
- `enable-self-serve-analytics` is the rollout layer for analytics leads who need governed access, fast adoption, and shareable Dives.
- `partner-delivery` packages the repeatable patterns consultants need for multi-client delivery, isolation, and regional deployment choices.

The general flow for most agents is:

1. connect
2. explore
3. query
4. switch to the workflow or use-case skill that matches the job

## Installation

### Local Install

Install the skills into the current project:

```bash
npx skills add motherduckdb/agent-skills --skill '*'
```

### Global Install

Install once for all projects:

```bash
npx skills add motherduckdb/agent-skills --skill '*' --global
```

### Claude Code Plugin

Install directly as a Claude Code plugin:

```bash
/plugin marketplace add motherduckdb/agent-skills
```

### Install a Single Skill

```bash
npx skills add motherduckdb/agent-skills --skill connect
```

### Manual

```bash
git clone https://github.com/motherduckdb/agent-skills.git
```

## Getting Started

1. Create a [MotherDuck account](https://motherduck.com) (free tier available).
2. Create an access token: **Settings > Access Tokens**.
3. Set the environment variable:
   ```bash
   export MOTHERDUCK_TOKEN=<your_token>
   ```
4. Install the skills.
5. Ask your AI agent something concrete.

Examples:

```text
Connect to MotherDuck and show me what databases are available.
```

```text
Explore my analytics database, then create a Dive showing weekly revenue trends.
```

```text
I want to build customer-facing analytics for my SaaS product. Which MotherDuck architecture should I start with?
```

## Prerequisites

- A MotherDuck account ([sign up free](https://motherduck.com))
- A MotherDuck access token
- An AI coding agent that supports the [Agent Skills specification](https://agentskills.io)

## Compatible AI Tools

These skills work with any AI coding agent that supports the Agent Skills spec, including:

- **Claude Code**
- **Codex**
- **Cursor**
- **GitHub Copilot**
- **Gemini CLI**
- **Windsurf**
- **Junie**
- **Kiro**
- **Goose**
- **Roo Code**
- **OpenCode**
- And many others via the Agent Skills ecosystem

## Opinionated By Design

These skills are intentionally opinionated. They encode practical defaults drawn from real MotherDuck usage so your AI agent does not have to guess.

- **The Postgres endpoint is the practical default for many applications.** It works with common PostgreSQL drivers and is especially useful for thin-client, serverless, and interoperability-heavy environments. The `connect` skill also teaches when native DuckDB, `pg_duckdb`, or Wasm are better fits.
- **DuckDB SQL for all queries, not PostgreSQL SQL.** MotherDuck runs DuckDB -- the skills teach the correct dialect and the DuckDB features that matter most in practice.
- **Parquet over CSV** when you control the format.
- **Wide analytical tables over unnecessary normalization** for common analytics and dashboard workloads.
- **3-tier architecture for serious customer-facing analytics** with stronger isolation and cleaner scaling paths.
- **MCP-first workflows for exploration and Dives** when an agent has MotherDuck MCP access.
- **DuckLake is supported, but not assumed.** It belongs in the catalog, but native MotherDuck storage remains the simpler default for most projects.

## Contributing

Contributions are welcome. Whether you are fixing a typo, improving an existing skill, or proposing a new one, we appreciate the help.

1. Fork the repository.
2. Create a feature branch: `git checkout -b my-skill-improvement`.
3. Make your changes and ensure they follow the existing skill structure.
4. Run `uv run scripts/validate_skills.py`.
5. Submit a pull request with a clear description of what changed and why.

Please open an issue first if you are planning a large change -- it helps us coordinate and provide early feedback.

## License

This project is licensed under the [MIT License](LICENSE).

## Links

- [MotherDuck Documentation](https://motherduck.com/docs/)
- [MotherDuck Getting Started](https://motherduck.com/docs/getting-started/)
- [MotherDuck Examples](https://github.com/motherduckdb/motherduck-examples)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckLake](https://ducklake.select/)
- [Agent Skills Specification](https://agentskills.io)
- [MotherDuck MCP Server](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-setup/)

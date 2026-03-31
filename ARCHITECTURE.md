# Repository Architecture

## Purpose

This repository publishes reusable MotherDuck skills for AI agents.

The repo is optimized for:

- app builders
- agent-driven product development
- opinionated MotherDuck workflows

## Core Structure

The catalog is a three-layer dependency graph:

- `utility`: primitives and reference knowledge
- `workflow`: concrete MotherDuck capability and product-surface skills
- `use-case`: end-to-end workflows composed from lower layers

Current catalog:

- Utility: `connect`, `query`, `explore`, `duckdb-sql`
- Workflow: `load-data`, `model-data`, `share-data`, `create-dive`, `ducklake`, `security-governance`, `pricing-roi`
- Use-case: `build-cfa-app`, `build-dashboard`, `build-data-pipeline`, `migrate-to-motherduck`, `enable-self-serve-analytics`, `partner-delivery`

Each skill may also have:

- `references/` for preserved detailed guidance, playbooks, and occasionally a fuller runnable reference project
- `artifacts/` for small runnable examples that demonstrate the core pattern quickly

The repo-level machine-readable index is `skills/catalog.json`, which maps skills to dependencies, references, artifacts, source docs, and live-discovery expectations.

## Invariants

- Utility skills must not declare skill dependencies.
- Workflow skills may depend only on utility skills.
- Use-case skills may depend only on utility and workflow skills.
- SKILL frontmatter stays portable and limited to broadly supported fields like `name`, `description`, and `license`.
- Repo-only skill graph data lives in `skills/catalog.json`, not in SKILL frontmatter.
- The README catalog, `CLAUDE.md` catalog, Claude plugin manifest, Claude marketplace manifest, Codex plugin manifest, and Codex marketplace entry must stay in sync with the `skills/` directory.
- The Codex marketplace must point at the packaged plugin under `plugins/motherduck-skills`, not the repo root.
- `skills/catalog.json` must stay in sync with actual `references/` and `artifacts/` paths.
- The repo stays opinionated; it is not a neutral encyclopedia of all possible MotherDuck patterns.
- Related-skill discovery stays in prose sections like `Related Skills`; we do not add repo-specific frontmatter for that.

## Product Positioning Invariants

- DuckDB SQL is the canonical SQL dialect for all connection paths.
- Connection guidance is scenario-based, not one-size-fits-all.
- Native `md:` workspace connections are the default posture for multi-database discovery, bootstrap flows, and temporary MotherDuck validation environments.
- Dives are MCP-first and should use `get_dive_guide` before save/update flows.
- Use-case skills should begin from the user's live MotherDuck data model when a remote or local server is active.
- DuckLake is supported but opt-in; native MotherDuck storage remains the default posture.
- Artifacts should be local-first where practical, but when the repo claims MotherDuck-specific validation, the corresponding artifact or reference project should also be runnable against temporary real MotherDuck databases.

## Enforcement

`scripts/validate_skills.py` enforces:

- required frontmatter
- no unsupported SKILL frontmatter keys
- valid layer names
- valid dependency targets
- valid dependency direction
- `skills/catalog.json` consistency
- `skills/catalog.json` reference and artifact path integrity
- live-discovery section requirements for use-case skills that declare them
- README and assistant catalog consistency
- Claude and Codex plugin consistency
- Claude marketplace wiring
- Codex marketplace wiring
- packaged Codex plugin sync and non-symlink packaging

`scripts/test_motherduck_artifacts.py` is the runtime verification layer for:

- MotherDuck-backed use-case artifacts
- the full `dlt + dbt + MotherDuck` pipeline reference project
- temporary database cleanup after validation

`scripts/test_codex_plugin.py` is the runtime smoke layer for:

- Codex marketplace discovery
- Codex plugin read/install flows
- installed plugin skill exposure through `skills/list`

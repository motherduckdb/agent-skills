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

## Invariants

- Utility skills must not declare skill dependencies.
- Workflow skills may depend only on utility skills.
- Use-case skills may depend only on utility and workflow skills.
- The README catalog and Claude plugin manifest must stay in sync with the `skills/` directory.
- The repo stays opinionated; it is not a neutral encyclopedia of all possible MotherDuck patterns.

## Product Positioning Invariants

- DuckDB SQL is the canonical SQL dialect for all connection paths.
- Connection guidance is scenario-based, not one-size-fits-all.
- Dives are MCP-first and should use `get_dive_guide` before save/update flows.
- DuckLake is supported but opt-in; native MotherDuck storage remains the default posture.

## Enforcement

`scripts/validate_skills.py` enforces:

- required frontmatter
- valid layer names
- valid dependency targets
- valid dependency direction
- README and plugin catalog consistency

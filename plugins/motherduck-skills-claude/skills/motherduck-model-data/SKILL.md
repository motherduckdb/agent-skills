---
name: motherduck-model-data
description: Design or implement MotherDuck analytical schemas and transformation models, including grain, types, and materialization.
argument-hint: [table-or-model-goal]
license: MIT
---

# Model Data in MotherDuck

## Core Behavior

For multi-model work, keep transformations in reviewable SQL files using the project's existing dbt, SQLMesh, or local conventions. If none exist, use stage directories and a `model_manifest.yml` recording dependencies, materialization, and target database. A single-table request needs only the requested SQL or change.

## Prerequisites

Use the known source schema and connection. Discover missing types, grain, and join keys before implementing; planning can use supplied schema without a live connection.

## Default Posture

- Design for analytical reads, not transactional writes.
- Prefer wide denormalized tables and pre-aggregated serving tables over highly normalized OLTP-style schemas.
- Use fully qualified names and add comments to tables and columns. Preserve stable object names so Guides can reference the intended catalog objects reliably.
- Use `NOT NULL` aggressively; do not assume primary keys or foreign keys are enforced.
- Reuse an existing dbt, SQLMesh, or repo-local modeling convention when one is already present; create the lightweight scaffold only when there is no established project shape.
- Separate `raw`, `staging`, and `analytics` lifecycle stages when the project is non-trivial.

## Workflow

1. Inspect the current source tables and actual column types before designing new models.
2. Choose the target lifecycle stage and grain for each modeled table. Map dependencies between models.
3. Place SQL in the existing project, or use the scaffold reference for a new multi-model project.
4. Author each model as a standalone SQL file. Use explicit types, nullability, comments, and fully qualified names. Decide between a table, CTAS rebuild, or view based on freshness and cost.
5. Record dependencies and materializations in the project's framework or lightweight manifest, not both.
6. For implementation, run the in-scope models and verify grain and row counts; MCP DDL and CTAS require `query_rw`. For an answer, review, or plan, return the requested explanation or SQL without creating a project or mutating the warehouse unless requested.

## References

Read only the reference sections needed for the current task.

- Read `references/MODELING_PLAYBOOK.md` for schema patterns, data-type guidance, CTAS/view decisions, complex types, constraints, project scaffold conventions, and common modeling mistakes.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-duckdb-sql` for type syntax and function details
- `motherduck-query` for executing DDL, rebuilds, and validation queries
- `motherduck-explore` for understanding the source schema before remodeling
- `motherduck-load-data` for ingestion paths that feed the modeled tables
- `motherduck-manage-guides` for durable business definitions and join rules that do not belong in transformation code

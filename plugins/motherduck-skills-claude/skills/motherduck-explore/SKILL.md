---
name: motherduck-explore
description: Discover MotherDuck databases, tables, columns, shares, and sample data to understand an available dataset.
argument-hint: [database-or-workspace]
license: MIT
---

# Explore MotherDuck Data

## Prerequisites

- An established MotherDuck connection (or an active MotherDuck MCP server)

## Default Posture

- Start at the known catalog object; broaden to databases or shares only when the target is unknown.
- Use fully qualified table names once more than one database is attached.
- Check shared databases before concluding that data is unavailable.
- Use the MotherDuck MCP tools (`list_databases`, `list_tables`, `list_columns`, `search_catalog`) when available because they return structured results faster than ad hoc SQL.
- Before business-semantic exploration through MCP, call `get_query_guide`, then read only relevant root Guides and topic branches. Follow `relatedGuides` returned by catalog tools when they govern the objects in scope.
- Record whether a share is filtered and whether an existing Dive is Draft, Ready, Endorsed, or Archived; these attributes change what downstream agents should trust or expect to see.
- Return a concise schema map with table grain, join keys, date columns, and likely measures before moving into modeling or dashboard work.

## Workflow

1. List databases in scope.
2. Load relevant Guide context, then list tables and views in the target database.
3. Inspect columns, types, nullability, and comments before writing queries.
4. Use targeted profiling or `SUMMARIZE` when ranges, cardinality, or null rates affect the answer; avoid broad scans for a catalog lookup.
5. Preview rows, capture grain and join assumptions, and only then move into analytical SQL or modeling work.

## References

Read only the reference sections needed for the current task.

- Read `references/EXPLORATION_PLAYBOOK.md` for the full SQL workflow, share discovery patterns, MCP tool guidance, and common exploration mistakes

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for session setup and authentication
- `motherduck-query` for analytical SQL after the schema is understood
- `motherduck-duckdb-sql` for DuckDB syntax patterns during exploration
- `motherduck-share-data` for creating and consuming shares once shared datasets become part of the workflow
- `motherduck-manage-guides` for reading or maintaining the context attached to discovered objects

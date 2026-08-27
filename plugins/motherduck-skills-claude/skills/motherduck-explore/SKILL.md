---
name: motherduck-explore
description: Discover and explore databases, tables, columns, and data shares in MotherDuck. Use when you need to understand what data is available, preview table contents, or search the data catalog.
argument-hint: [database-or-workspace]
license: MIT
---

# Explore MotherDuck Data

Use this skill when you need to discover what databases, tables, and columns exist in a MotherDuck account; preview and sample data; understand schemas and data types; find shared databases; or search the data catalog.

## Prerequisites

- An established MotherDuck connection (or an active MotherDuck MCP server)

## Default Posture

- Explore top-down: databases, then tables/views, then columns, then statistics, then sample rows.
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
4. Run `SUMMARIZE` on important tables to understand ranges, cardinality, and null rates.
5. Preview rows, capture grain and join assumptions, and only then move into analytical SQL or modeling work.

## Open Next

- Read `references/EXPLORATION_PLAYBOOK.md` for the full SQL workflow, share discovery patterns, MCP tool guidance, and common exploration mistakes

## Related Skills

- `motherduck-connect` for session setup and authentication
- `motherduck-query` for analytical SQL after the schema is understood
- `motherduck-duckdb-sql` for DuckDB syntax patterns during exploration
- `motherduck-share-data` for creating and consuming shares once shared datasets become part of the workflow
- `motherduck-manage-guides` for reading or maintaining the context attached to discovered objects

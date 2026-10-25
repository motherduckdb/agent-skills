---
name: motherduck-explore
description: Find and understand MotherDuck databases, tables, columns, shares, and sample data, including which tables hold a given kind of data. Use first when a MotherDuck workspace or schema is unfamiliar.
argument-hint: [database-or-workspace]
license: MIT
---

# Explore MotherDuck Data

## Prerequisites

- An established MotherDuck connection (or an active MotherDuck MCP server)

## Default Posture

- Start at the known catalog object; broaden to databases or shares only when the target is unknown.
- Prefer fully qualified `"database"."schema"."table"` names; they are required once more than one database or share is attached.
- Check shared databases before concluding that data is unavailable. A share with secure views can hide columns and rows: a missing column in an attached share may be policy, not schema drift.
- Use the MotherDuck MCP tools (`list_databases`, `list_tables`, `list_views`, `list_columns`, `list_macros`, `search_catalog`) when available because they return structured results faster than ad hoc SQL. Check `list_macros` before reimplementing logic; table and scalar macros often encode governed definitions.
- When MotherDuck MCP is available and the SQL answers a business question, call `get_query_guide` first, then read only the relevant Guide topics and validate their claims against the live schema. Follow `relatedGuides` returned by catalog tools when they govern the objects in scope.
- Record whether a share is filtered and whether an existing Dive is Draft, Ready, Endorsed, or Archived; these attributes change what downstream agents should trust or expect to see.
- Return a concise schema map with table grain, join keys, date columns, and likely measures before moving into modeling or dashboard work.

## Workflow

1. List databases in scope.
2. Load relevant Guide context, then list tables and views in the target database.
3. Inspect columns, types, nullability, and comments before writing queries.
4. Use targeted profiling or `SUMMARIZE` when ranges, cardinality, or null rates affect the answer; avoid broad scans for a catalog lookup.
5. Preview rows with `SELECT * ... LIMIT n` or `USING SAMPLE`; on wide tables these read only the row groups they need. Capture grain and join assumptions, and only then move into analytical SQL or modeling work.

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

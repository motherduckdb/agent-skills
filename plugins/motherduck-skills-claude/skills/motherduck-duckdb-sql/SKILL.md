---
name: motherduck-duckdb-sql
description: Look up or repair DuckDB SQL syntax and verify MotherDuck-specific command and feature support.
argument-hint: [syntax-or-error]
license: MIT
---

# DuckDB SQL Reference for MotherDuck

## Source Of Truth

- Prefer current DuckDB SQL docs for language features and function semantics.
- Use current MotherDuck SQL docs for MotherDuck-only commands such as shares, secrets, snapshots, and Dive operations.
- MotherDuck can lag upstream DuckDB releases for client compatibility; check MotherDuck version-lifecycle docs before promising newly released DuckDB syntax or types are available.
- If the connection path matters, verify behavior against the current Postgres-endpoint docs before promising server-mode support.

## Default Posture

- Write DuckDB SQL, not PostgreSQL SQL, even when the client connects through the Postgres endpoint.
- Prefer fully qualified `"database"."schema"."table"` names; they are required once more than one database or share is attached.
- Prefer DuckDB-native constructs when they simplify the query: `GROUP BY ALL`, `QUALIFY`, `UNION BY NAME`, `arg_max`, `EXCLUDE`, and `REPLACE`.
- When porting SQL from another engine, translate functions, date arithmetic, identifier quoting, and type casts explicitly instead of assuming compatibility.
- Verify current MotherDuck support before relying on recently released upstream DuckDB features such as `VARIANT`, native `GEOMETRY`, `MERGE INTO`, or `date_trunc` return-type changes.
- Check whether the statement depends on local files, extension install/load, temporary-table behavior, or other client-only features before claiming it will work in MotherDuck.
- Treat snapshot, restore, and `UNDROP DATABASE` statements as operational SQL with plan-specific retention behavior, not ordinary analytical syntax.
- Treat `INCLUDE_PATTERN` as whole-table/view filtering on a Share. Row filters, hidden columns, and masking use share secure views (`WITH SECURE VIEW ... REPLACES <table> AS (SELECT ...)`, `ALTER SHARE ... ADD|DROP SECURE VIEW`), which are unrelated to DuckDB's `CREATE SECURE VIEW` optimizer barrier.
- Distinguish physical import (`CREATE DATABASE ... FROM '<file-url>'`, including a DuckDB file in cloud storage such as `'s3://bucket/app.db'`) from zero-copy clone sources. Reject filtered shares and shares with secure views as clone sources; use `COPY FROM DATABASE` instead.
- Use role/grant SQL for governed access and audit it with `SHOW ...` statements; do not preserve `ACCESS ORGANIZATION` as the preferred RBAC pattern.
- Treat MotherDuck SQL as an additional surface on top of DuckDB SQL, not a replacement for it.
- MotherDuck adds SQL AI functions: `prompt()` for generated or structured text, `embedding()` for vectors, and `prompt_jev()` for typed classification, scoring, yes/no probabilities, and image bounding boxes. See `motherduck-query` for usage and cost rules.

## Workflow

1. Confirm the connection path and whether the question is about syntax, feature support, or a specific error.
2. Write or repair the statement in DuckDB SQL first.
3. Verify any MotherDuck-only command or server-mode limitation against the current docs.
4. If the user needs exact syntax or function details, open `references/SYNTAX_REFERENCE.md`.

## References

Read only the reference sections needed for the current task.

- Read `references/SYNTAX_REFERENCE.md` for DuckDB data types, friendly SQL features, functions, complex types, and common MotherDuck-specific gotchas.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-query` for writing and validating analytical SQL against live MotherDuck data
- `motherduck-connect` when syntax support depends on PG endpoint versus native DuckDB behavior
- `motherduck-explore` when the problem is really missing schema context rather than missing syntax knowledge

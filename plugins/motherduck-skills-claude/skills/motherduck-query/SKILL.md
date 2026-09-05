---
name: motherduck-query
description: Write, execute, or optimize analytical DuckDB SQL against MotherDuck data.
argument-hint: [query-or-task]
license: MIT
---

# Query MotherDuck

## Prerequisites

- An established MotherDuck connection (or an active MotherDuck MCP server)
- Target database and tables identified

## Default Posture

- When MotherDuck MCP is available and the query answers a business question, call `get_query_guide` before writing SQL. Traverse only relevant topics and validate Guide claims against the live schema.
- Write DuckDB SQL, not PostgreSQL SQL, even when using the PG endpoint.
- Always use fully qualified `"database"."schema"."table"` names.
- Preserve result grain and check join cardinality before optimizing or materializing a query.
- Filter early, aggregate early, and prefer serving tables or summaries for repeated reads.
- Keep SQL obvious, multi-line, and explicit about grain, filters, and output shape.
- Treat DDL, DML, `ATTACH`, `DETACH`, recovery commands such as `CREATE SNAPSHOT`, `ALTER DATABASE ... SET SNAPSHOT`, `UNDROP DATABASE`, and lifecycle commands such as `SHUTDOWN` as writes. Use the MotherDuck MCP `query_rw` tool when the user's change request authorizes the write. Ask for confirmation only when the action is destructive, externally visible, or outside the stated scope.
- Tag long-lived integrations with `custom_user_agent` when the connection path supports it.

## Workflow

1. Confirm the actual tables, columns, and grain before writing SQL.
2. Load relevant Guide context when MCP is available, without treating it as a substitute for schema inspection.
3. Write the query in SQL first, then wrap it in Python or TypeScript only if needed.
4. Use DuckDB-native patterns when they simplify the query; a simple lookup does not need a CTE or a materialization.
5. Verify result shape and key aggregates. Inspect the plan when performance is part of the request or execution shows a problem.
6. Materialize expensive repeated queries into serving tables or light views when warranted.

## References

Read only the reference sections needed for the current task.

- Read `references/QUERY_PLAYBOOK.md` for DuckDB query patterns, exploration SQL, performance rules, common analytical shapes, and common mistakes

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for session setup
- `motherduck-duckdb-sql` for syntax and function reference
- `motherduck-explore` for understanding the source schema before writing queries
- `motherduck-manage-guides` when semantic definitions or reusable query rules need to be read or maintained

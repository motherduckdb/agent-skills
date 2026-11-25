---
name: motherduck-query
description: Write, run, optimize, or troubleshoot DuckDB SQL against MotherDuck, including AI functions such as prompt_jev for in-SQL classification. Use for any SQL that targets MotherDuck, even simple queries, because MotherDuck has its own dialect and naming rules.
license: MIT
---

# Query MotherDuck

## Prerequisites

- An established MotherDuck connection (or an active MotherDuck MCP server)
- Target database and tables identified

## Default Posture

- When MotherDuck MCP is available and the SQL answers a business question, call `get_query_guide` first, then read only the relevant Guide topics and validate their claims against the live schema.
- Write DuckDB SQL, not PostgreSQL SQL, even when using the PG endpoint.
- Prefer fully qualified `"database"."schema"."table"` names; they are required once more than one database or share is attached.
- Preserve result grain and check join cardinality before optimizing or materializing a query.
- Filter early, aggregate early, and prefer serving tables or summaries for repeated reads.
- Keep SQL obvious, multi-line, and explicit about grain, filters, and output shape.
- Treat DDL, DML, `ATTACH`, `DETACH`, recovery commands such as `CREATE SNAPSHOT`, `ALTER DATABASE ... SET SNAPSHOT`, `UNDROP DATABASE`, and lifecycle commands such as `SHUTDOWN` as writes. Use the MotherDuck MCP `query_rw` tool when the user's change request authorizes the write. Ask for confirmation only when the action is destructive, externally visible, or outside the stated scope.
- Tag long-lived integrations with `custom_user_agent` when the connection path supports it; the tag appears per query in the Duckling Overview and in query history.
- For classification, scoring, routing, or yes/no judgments over text or images, use `prompt_jev()`: it returns typed probabilities and labels, bills input tokens only, and batches rows. Use `prompt()` for generated text or open extraction with `struct` or `json_schema`. Both are per-row billable calls: test on a small `LIMIT`, store results in a table, and rerun only `NULL` rows.

## Workflow

1. Confirm the actual tables, columns, and grain before writing SQL.
2. Load relevant Guide context when MCP is available, without treating it as a substitute for schema inspection.
3. Write the query in SQL first, then wrap it in Python or TypeScript only if needed.
4. Use DuckDB-native patterns when they simplify the query; a simple lookup does not need a CTE or a materialization.
5. Verify result shape and key aggregates. When performance is part of the request or execution shows a problem, check `EXPLAIN ANALYZE` and `md_information_schema.query_history` (`wait_time`, `bytes_spilled_to_disk`, `instance_type`) before changing the query or the Duckling size.
6. Materialize expensive repeated queries into serving tables or light views when warranted.

## References

Read only the reference sections needed for the current task.

- Read `references/QUERY_PLAYBOOK.md` for DuckDB query patterns, exploration SQL, performance rules, common analytical shapes, and common mistakes
- Read `references/AI_FUNCTIONS.md` when a query calls `prompt_jev()`, `prompt()`, or `embedding()`
- Read `references/PERFORMANCE.md` when a query is slow, spills, runs out of memory, or a Duckling looks undersized

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for session setup
- `motherduck-duckdb-sql` for syntax and function reference
- `motherduck-explore` for understanding the source schema before writing queries
- `motherduck-manage-guides` when semantic definitions or reusable query rules need to be read or maintained

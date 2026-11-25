# MotherDuck Guidelines for Antigravity

When working with MotherDuck through this plugin and the remote MCP server (`https://api.motherduck.com/mcp`):

- **Discover live schemas first**: Inspect databases, tables, and columns with MotherDuck MCP catalog tools before writing SQL. Never assume or invent table or column names.
- **Consult Guides before authoring**: Call `get_query_guide` before business-semantic MCP queries, and call `get_dive_guide` before `save_dive`, `update_dive`, or `edit_dive_content`.
- **Write DuckDB SQL**: MotherDuck runs DuckDB, not PostgreSQL. Prefer fully qualified `"database"."schema"."table"` references and apply `LIMIT` when previewing unfamiliar tables.
- **Default to read-only queries**: Use read-only queries for exploration and confirm destructive DDL/DML changes (`DROP`, `DELETE`, `TRUNCATE`, or overwriting tables).
- **Never hardcode credentials**: Authenticate via Antigravity's MCP OAuth flow or use `MOTHERDUCK_TOKEN` (or the documented read-scaling variants) from the environment.

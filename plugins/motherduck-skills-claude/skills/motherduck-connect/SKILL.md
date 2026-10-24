---
name: motherduck-connect
description: Set up or troubleshoot MotherDuck connections, authentication, client runtimes, and read scaling.
argument-hint: [app-or-runtime]
license: MIT
---

# Connect to MotherDuck

## Source Of Truth

- Prefer current MotherDuck connection, attach-mode, read-scaling, and multithreading docs.
- If the MotherDuck MCP `ask_docs_question` tool is available, use it first for current connection behavior.
- When it is unavailable, verify guidance against the public docs before making firm claims about connection strings, token types, or read-scaling behavior.

## Default Posture

- Start with the PG endpoint (MotherDuck's Postgres-compatible endpoint) for backend applications, BI tools, and serverless runtimes that want PostgreSQL wire compatibility.
- For BI tools, treat the PG endpoint as the compatibility path for Power BI and Tableau Cloud when current docs list them as supported.
- Use the native DuckDB API when you need local files, hybrid local/cloud execution, or direct DuckDB control.
- Use `md:` workspace connections for multi-database exploration, bootstrap flows, and temporary validation environments.
- Reuse an existing connection, connector, or environment-managed token when the user's context already provides one; do not ask for secrets that can be discovered from the active workspace. When only the MotherDuck MCP server is connected and a one-off local session needs credentials, `get_short_lived_token` returns a temporary token and endpoint details; pass it through the process environment and never write it to files, code, or logs. Deployed services still need a service-account token.
- Start with one connection. Add pooling or read scaling only when real concurrent-read pressure exists.
- For services that should fail over instead of blocking while a Duckling starts, bound native `md:` connects with `connection_timeout` (`md:my_db?connection_timeout=30s`, `MOTHERDUCK_CONNECTION_TIMEOUT`, or `SET motherduck_connection_timeout = '30s'` before the first `ATTACH 'md:'`). It applies to DuckDB clients with the MotherDuck extension, not the PG endpoint or Wasm. Without it, only network retries are bounded.
- Use native DuckDB `custom_user_agent` where supported; for PG endpoint clients, prefer the client's `application_name` setting when available. The tag shows per query in the Duckling Overview, which makes it the quickest way to see which workload is using a Duckling.

## Runtime Selection

Pick the connection method (above) and the runtime separately. The runtime is what actually executes queries: MotherDuck MCP, the MotherDuck CLI, a Python or Node process, or the DuckDB CLI.

For answer, review, or planning requests, inspect the available runtimes and recommend a path without installing anything. Install or configure a runtime only when the user asks to connect, build, or change the application.

Reuse the project’s language, dependencies, and working connection. Prefer MCP for chat-only exploration and the MotherDuck CLI for file-shaped Dive/Flight work or large output. For application code, use its existing runtime; choose a new runtime only when none is established.

Before installing a DuckDB client, check `https://motherduck.com/docs/duckdb-versions.json` and pin a MotherDuck-supported version. Keep an existing compatible pin unless the task requires an upgrade. See the runtime reference for installation examples.

## Workflow

1. Choose the connection path for the workload; keep ingestion and serving paths distinct when their needs differ.
2. Put the MotherDuck token in environment-managed secrets, not in source code.
3. Establish the connection with explicit SSL settings where required.
4. Verify the connection with `SELECT 1 AS connected` and then list reachable tables.
5. If the workload is read-heavy and concurrent, evaluate read scaling and a stable `session_name` per end user.

## References

Read only the reference sections needed for the current task.

- Read `references/CONNECTION_GUIDE.md` for connection-method selection, PG endpoint and native DuckDB examples, token handling, read scaling, attach modes, and common failure modes
- Read `references/RUNTIME_SELECTION.md` for the MCP-vs-Python-vs-Node-vs-CLI decision tree, detection commands, install snippets, and the DuckDB version-pinning workflow

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-explore` for discovering databases, tables, columns, and shares after the connection is established
- `motherduck-query` for executing DuckDB SQL against the connected databases
- `motherduck-duckdb-sql` for DuckDB syntax and function lookup support
- `motherduck-rest-api` for control-plane admin operations; those use `MOTHERDUCK_ADMIN_TOKEN`, which is never used for database connections
- `motherduck-cli` for terminal queries and file-oriented Dive/Flight authoring

# MCP Registry entry for the hosted MotherDuck MCP server

`server.json` is the [MCP Registry](https://registry.modelcontextprotocol.io) entry `io.github.motherduckdb/motherduck`. It describes the hosted MotherDuck MCP server at `https://api.motherduck.com/mcp`, which uses OAuth sign-in.

The local server has its own entry, `io.github.motherduckdb/mcp-server-motherduck`, published from [mcp-server-motherduck](https://github.com/motherduckdb/mcp-server-motherduck).

To publish a change, edit `server.json`, raise its `version` (the registry rejects a version it already has), merge, and run the **Publish MCP Registry entry** workflow from `main`. This version is independent of the skills release version.

# MotherDuck MCP server

The hosted MotherDuck MCP server connects AI assistants and coding agents to [MotherDuck](https://motherduck.com), the cloud data warehouse built on DuckDB. Agents can explore databases and schemas, run DuckDB SQL, and build Dives, Flights, and Guides.

- **Endpoint:** `https://api.motherduck.com/mcp` (Streamable HTTP)
- **Sign-in:** OAuth in the browser. Access follows your MotherDuck permissions. No API key is needed.
- **Documentation:** [MotherDuck MCP server](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-workflows/mcp-setup/)

Add the endpoint as a remote MCP server in your client, then sign in when prompted. GitHub Copilot CLI and Google Antigravity users can install the `motherduck` plugin from this repository instead, which adds the server and the MotherDuck skills together.

To run a server on your own machine against local DuckDB files, use [mcp-server-motherduck](https://github.com/motherduckdb/mcp-server-motherduck).

## Registry entry

`server.json` in this directory is the [MCP Registry](https://registry.modelcontextprotocol.io) entry `io.github.motherduckdb/motherduck`. Maintainers: to publish a change, raise `version` in `server.json`, merge, and run the **Publish MCP Registry entry** workflow from `main`. The version is independent of the skills release version.

# MotherDuck MCP Server Setup

Connect an AI client to the hosted MotherDuck MCP server. Verify client menus against current MotherDuck MCP docs; client UIs change often.

## Server and Auth

- URL: `https://api.motherduck.com/mcp`, HTTP transport.
- OAuth sign-in with the user's MotherDuck account is the default in clients that support it.
- Otherwise send `Authorization: Bearer <token>` with a token from MotherDuck Settings, Access Tokens. Read it from `MOTHERDUCK_TOKEN`; never write the value into a committed config file.
- For enforced read-only access, use a read-scaling token, ideally for a service account. Otherwise rely on the client's tool permissions: set `query_rw` to require approval or block it. `query` is always read-only.

## Clients

Claude Code (local scope by default; add `--scope user` for every project), then run `/mcp`, select MotherDuck, and authenticate:

```bash
claude mcp add --transport http MotherDuck https://api.motherduck.com/mcp
```

Cursor, Windsurf, Zed, and most JSON-configured clients:

```json
{
  "mcpServers": {
    "MotherDuck": { "url": "https://api.motherduck.com/mcp", "type": "http" }
  }
}
```

VS Code with GitHub Copilot, in `.vscode/mcp.json`, then start the server, sign in, and use Agent mode:

```json
{
  "servers": {
    "motherduck": { "type": "http", "url": "https://api.motherduck.com/mcp" }
  }
}
```

Gemini CLI, in `~/.gemini/settings.json` or a project's `.gemini/settings.json`, with `MOTHERDUCK_TOKEN` exported; verify with `gemini mcp list`:

```json
{
  "mcpServers": {
    "motherduck": {
      "httpUrl": "https://api.motherduck.com/mcp",
      "headers": { "Authorization": "Bearer ${MOTHERDUCK_TOKEN}" }
    }
  }
}
```

- Claude web and desktop: add the MotherDuck connector from the connectors settings. On Team and Enterprise plans an organization owner enables it first.
- ChatGPT and Codex: install the MotherDuck app or plugin and connect the account.
- Copilot Studio: add a Model Context Protocol tool with the server URL; choose OAuth for per-user sign-in, or an `Authorization` header with a service-account token (queries are then attributed to that service account).

## Local Server

For local DuckDB files, self-hosting, or custom configuration, use the open-source server in `motherduckdb/mcp-server-motherduck`. Read its README for the current package name and flags instead of assuming them.

## Verify

- Ask the client to list MotherDuck databases and confirm it calls a MotherDuck tool such as `list_databases`.
- In Claude, enable the connector for the conversation if the client answers without calling it.
- Claude Code sessions authenticated with an API key or a third-party provider do not inherit Claude account connectors; add the server with `claude mcp add`.

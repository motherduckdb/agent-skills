# MotherDuck for GitHub Copilot

An [Agent Plugins 1.0](https://agent-plugins.org) package for GitHub Copilot CLI and VS Code. It bundles:

- the MotherDuck skill catalog under `skills/`
- the remote MotherDuck MCP server (`https://api.motherduck.com/mcp`) in `mcp.json`

The MCP server uses OAuth. Copilot opens a browser sign-in the first time the server is used. No token or environment variable is needed.

## Install

```text
/plugin marketplace add motherduckdb/agent-skills
/plugin install motherduck@motherduck-skills
```

## Maintenance

`plugin.json` and `mcp.json` are edited here. `skills/` is generated from the repo-level `skills/` directory:

```bash
uv run scripts/sync_copilot_plugin.py
uv run scripts/check_copilot_plugin_sync.py
```

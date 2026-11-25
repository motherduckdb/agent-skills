# MotherDuck for Google Antigravity

A native [Google Antigravity](https://antigravity.google/docs/plugins) plugin bundling:

- the MotherDuck skill catalog under `skills/`
- the hosted remote MotherDuck MCP server (`https://api.motherduck.com/mcp`) in `mcp_config.json`
- lightweight MCP and DuckDB SQL guardrails in `rules/AGENTS.md`

The MCP server uses OAuth over Streamable HTTP. No local MCP server process or manually copied API token is required.

## Install

Install directly from GitHub with the Antigravity CLI (`agy`):

```bash
agy plugin install https://github.com/motherduckdb/agent-skills/tree/main/plugins/motherduck-skills-antigravity
```

Or from a local checkout:

```bash
agy plugin install ./plugins/motherduck-skills-antigravity
```

Once listed in the Antigravity Partner Marketplace, users can also install **MotherDuck** directly from **Customizations → Marketplace**.

## Connect your MotherDuck account

1. Open **Agent settings → Customizations** (`Cmd+,` on macOS) or run `/mcp` in the Antigravity CLI.
2. Click **Authenticate** next to the plugin's `motherduck` MCP server.
3. Sign in to MotherDuck in your browser and authorize Antigravity.
4. If your browser displays an authorization code, copy and paste it into the authentication field in Antigravity settings and click **Submit**.

## Maintenance

`plugin.json`, `mcp_config.json`, `rules/AGENTS.md`, `assets/logo.svg`, and this `README.md` are edited here. `skills/` is generated from the repo-level `skills/` directory:

```bash
uv run scripts/sync_antigravity_plugin.py
uv run scripts/check_antigravity_plugin_sync.py
agy plugin validate ./plugins/motherduck-skills-antigravity --strict
```

## Partner Marketplace submission

Before submitting to the Antigravity Partner Marketplace (`antigravity-plugins-partners`):

1. Confirm `agy plugin validate ./plugins/motherduck-skills-antigravity --strict` passes with zero errors and zero warnings.
2. Swap `assets/logo.svg` with the official MotherDuck brand SVG if required by brand review (square, transparent padding, legible on light and dark themes).
3. Verify fresh OAuth sign-in, tool discovery (`motherduck_motherduck`), read-only query execution, and token refresh across an Antigravity restart.
4. Submit `https://github.com/motherduckdb/agent-skills/tree/main/plugins/motherduck-skills-antigravity` via the **"Get your plugin in the marketplace"** partner form at https://antigravity.google/docs/plugins.

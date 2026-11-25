# MotherDuck for Google Antigravity

A native [Google Antigravity](https://antigravity.google/docs/plugins) plugin bundling:

- the full MotherDuck skill catalog under `skills/`
- the hosted remote MotherDuck MCP server (`https://api.motherduck.com/mcp`) in `mcp_config.json`
- a dedicated `motherduck-analyst` custom agent and subagent in `agents/motherduck-analyst.md`
- lightweight MCP, Guide, and DuckDB SQL guardrails in `rules/AGENTS.md`

The remote MCP server uses OAuth 2.0 over Streamable HTTP (with PKCE and Dynamic Client Registration). No local MCP server process or manually copied API token is required.

## Install

Install directly from GitHub with the Antigravity CLI (`agy`):

```bash
agy plugin install https://github.com/motherduckdb/agent-skills/tree/main/plugins/motherduck-skills-antigravity
```

Or install from a local checkout:

```bash
agy plugin install ./plugins/motherduck-skills-antigravity
```

Once published in the Antigravity Partner Marketplace (`antigravity-plugins-partners`), users can also install **MotherDuck** directly from **Customizations → Marketplace** or via `agy plugin install motherduck@antigravity-plugins-partners`.

## Connect your MotherDuck account

1. Open **Agent settings → Customizations** (`Cmd+,` on macOS) or run `/plugin` in the Antigravity CLI.
2. Click **Authenticate** (or **Sign in**) next to the plugin's `motherduck` MCP server.
3. Sign in to MotherDuck in your browser and authorize Antigravity.
4. If your browser displays an authorization code, paste it into the authentication field in Antigravity settings and click **Submit**.

## Using the bundled agent

Start a MotherDuck-focused session directly with the bundled specialist agent:

```bash
agy --agent motherduck-analyst
```

Or select **motherduck-analyst** in the Antigravity App agent picker; the primary agent can also delegate MotherDuck warehouse investigation to it automatically as a background subagent.

## Maintenance

`plugin.json`, `mcp_config.json`, `agents/motherduck-analyst.md`, `rules/AGENTS.md`, `assets/logo.svg`, and this `README.md` are edited here. `skills/` is generated from the repo-level `skills/` directory:

```bash
uv run scripts/sync_antigravity_plugin.py
uv run scripts/check_antigravity_plugin_sync.py
agy plugin validate ./plugins/motherduck-skills-antigravity --strict
```

## Partner Marketplace submission

Before submitting to the Antigravity Partner Marketplace (`antigravity-plugins-partners`):

1. Confirm `agy plugin validate ./plugins/motherduck-skills-antigravity --strict` passes with zero errors and zero warnings.
2. Swap `assets/logo.svg` with the official MotherDuck brand SVG if required by brand review (1:1 square, `>= 128x128`, ~10% transparent padding, legible on light and dark themes).
3. Verify fresh OAuth sign-in (allowlisting `https://antigravity.google.com/oauth/callback` if required by the OAuth provider), tool discovery (`motherduck_motherduck`), read-only query execution, and token refresh across an Antigravity restart.
4. Submit `https://github.com/motherduckdb/agent-skills/tree/main/plugins/motherduck-skills-antigravity` via the [Antigravity Marketplace partner intake form](https://forms.gle/2EX5RFYPoJe1UgxR9).

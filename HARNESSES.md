# MotherDuck Skills Harness Matrix

MotherDuck Skills ships one shared skill catalog that the main agent hosts can install through the Skills CLI.
For major harnesses that support it, this repo also ships native plugin, extension, or packaged discovery surfaces.

Use this file to answer two questions quickly:

1. which harnesses are supported here
2. what install or discovery path each harness should use

## Supported Harnesses

| Harness | Best install path | Native surface in this repo | Verify it worked |
|-------|-------|-------|-------|
| `GitHub Copilot CLI` | `/plugin marketplace add motherduckdb/agent-skills` then `/plugin install motherduck@motherduck-skills` | `.github/plugin/marketplace.json`, `plugins/motherduck-skills-copilot` (Agent Plugins 1.0: `plugin.json`, `mcp.json`, `skills/`) | run `/plugin list`, check `/mcp` for the `motherduck` server, and ask Copilot to use `motherduck-connect` |
| `VS Code / GitHub Copilot` | `npx -y skills add motherduckdb/agent-skills --agent github-copilot --skill '*' --yes --global` | shared `skills/` catalog | ask Copilot to use a MotherDuck skill in agent mode |
| `Claude Code` | Claude plugin install or Skills CLI | `.claude-plugin/marketplace.json`, `plugins/motherduck-skills-claude/.claude-plugin/plugin.json` | ask Claude Code to use `motherduck-connect`, inspect the plugin list, or run `claude --plugin-dir ./plugins/motherduck-skills-claude` |
| `Codex` | Codex plugin install or Skills CLI | `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `plugins/motherduck-skills` | open `/plugins` or run the Codex plugin smoke test |
| `Cursor` | Skills CLI or Cursor plugin manifest ingestion | `.cursor-plugin/plugin.json`, `.cursor-plugin/marketplace.json` | reload Cursor and ask it to use `motherduck-connect` |
| `Gemini CLI` | Gemini extension install or Gemini skills install | `gemini-extension.json`, `GEMINI.md`, `commands/motherduck/` | run `gemini extensions list` or `gemini skills list` |

## Default Routing

For narrow work, start with the matching skill. Add connection setup or discovery only when context is missing.

For end-to-end product work, start with the matching use-case skill and load lower-level skills only when it needs them.

## Maintainer Notes

- run `uv run scripts/validate_skills.py` after changing harness docs or packaged surfaces
- the Copilot plugin is named `motherduck`, like its MCP server; the Claude Code, Codex, and Cursor plugins keep the name `motherduck-skills`
- the hosted MotherDuck MCP server is published to the MCP Registry from `mcp-registry/server.json` by the **Publish MCP Registry entry** workflow
- the Copilot package also bundles the remote MotherDuck MCP server (`https://api.motherduck.com/mcp`, OAuth sign-in); run `uv run scripts/sync_copilot_plugin.py` after changing `skills/`
- keep `README.md`, `docs/install-matrix.md`, and this file aligned on the same harness list and install story

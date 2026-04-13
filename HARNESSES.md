# MotherDuck Skills Harness Matrix

MotherDuck Skills ships one shared skill catalog that all main harnesses can install through `npx skills`.
For major harnesses that support it, this repo also ships native plugin, extension, or packaged discovery surfaces.

Use this file to answer two questions quickly:

1. which harnesses are supported here
2. what install or discovery path each harness should use

## Supported Harnesses

| Harness | Best install path | Native surface in this repo | Verify it worked |
|-------|-------|-------|-------|
| `Claude Code` | Claude plugin install or `npx skills` | `plugins/motherduck-skills-claude/.claude-plugin/plugin.json` | ask Claude Code to use `motherduck-connect`, inspect the plugin list, or run `claude --plugin-dir ./plugins/motherduck-skills-claude` |
| `Codex` | Codex plugin install or `npx skills` | `.codex-plugin/plugin.json`, `plugins/motherduck-skills` | open `/plugins` or run the Codex plugin smoke test |
| `Gemini CLI` | Gemini extension install or Gemini skills install | `gemini-extension.json`, `GEMINI.md`, `commands/motherduck/` | run `gemini extensions list` or `gemini skills list` |

## Default Routing

For most narrow technical work, start with `motherduck-connect`, then `motherduck-explore`, then `motherduck-query`.

For end-to-end product work, start with the matching use-case skill and let it orchestrate the lower layers.

## Maintainer Notes

- run `uv run scripts/validate_skills.py` after changing harness docs or packaged surfaces
- keep `README.md`, `docs/install-matrix.md`, and this file aligned on the same harness list and install story

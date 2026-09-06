# Install Matrix

Use this document when you want the fastest copy-paste install route for a specific harness.

All main harnesses can use the shared MotherDuck catalog through the Skills CLI.
The packaged installs below are harness-specific convenience paths for runtimes where this repo also ships a native plugin or extension surface.

## Packaged Installs

| Harness | Install |
|-------|-------|
| `GitHub Copilot CLI` | `/plugin marketplace add motherduckdb/agent-skills` then `/plugin install motherduck-skills@motherduck-skills` |
| `Claude Code` | `/plugin marketplace add motherduckdb/agent-skills` then `/plugin install motherduck-skills@motherduck-skills` |
| `Codex` | `codex plugin marketplace add motherduckdb/agent-skills`, then install **MotherDuck Skills** from `/plugins` |
| `Cursor` | `npx -y skills add motherduckdb/agent-skills --agent cursor --skill '*' --yes --global`; this repo also includes `.cursor-plugin/plugin.json` for Cursor plugin ingestion |
| `Gemini CLI` | `gemini extensions install https://github.com/motherduckdb/agent-skills` |

## Skills CLI Install

Use the [Skills CLI](https://github.com/vercel-labs/skills) with Git and Node.js 22.20+; `npx` runs it without a global installation. This requirement comes from the [current package metadata](https://github.com/vercel-labs/skills/blob/main/package.json).

Install into the current project:

```bash
npx -y skills add motherduckdb/agent-skills --skill '*' --yes
```

Global install:

```bash
npx -y skills add motherduckdb/agent-skills --skill '*' --yes --global
```

Install for every supported agent directory:

```bash
npx -y skills add motherduckdb/agent-skills --all
```

Install for GitHub Copilot / VS Code:

```bash
npx -y skills add motherduckdb/agent-skills --agent github-copilot --skill '*' --yes --global
```

Inspect and install one Copilot skill with GitHub CLI:

```bash
gh skill preview motherduckdb/agent-skills motherduck-connect
gh skill install motherduckdb/agent-skills motherduck-connect --agent github-copilot --scope user
```

Install for Cursor:

```bash
npx -y skills add motherduckdb/agent-skills --agent cursor --skill '*' --yes --global
```

## Manual Per-Skill Install

From a repository checkout, copy the full skill directory, not only `SKILL.md`, to a skill path supported by your agent. For agents that discover `~/.agents/skills`:

```bash
mkdir -p ~/.agents/skills
cp -R skills/motherduck-connect ~/.agents/skills/motherduck-connect
```

See [HARNESSES.md](../HARNESSES.md) for agent-specific discovery paths.

## Updates

- Claude Code / GitHub Copilot CLI: `/plugin update motherduck-skills@motherduck-skills`
- Codex: manage the installed plugin from `/plugins`.
- Gemini CLI: `gemini extensions update motherduck-skills`, then restart the session.
- Skills CLI: `npx -y skills update -g` for global skills, or `npx -y skills update -p` for project skills. These update the installed skills in that scope.

For Gemini automation, `--consent` skips the installation confirmation; it is optional for interactive installs.

## Verification

- `GitHub Copilot CLI`: `/plugin list` shows `motherduck-skills`
- `Claude Code`: plugin shows up and can be invoked on a MotherDuck task
- `Codex`: plugin appears in `/plugins`
- `Cursor`: installed skills appear after reload and can be invoked on a MotherDuck task
- `Gemini CLI`: `gemini extensions list` or `gemini skills list`

For local Claude plugin development, validate the dedicated package directly:

```bash
claude plugin validate ./plugins/motherduck-skills-claude
claude --plugin-dir ./plugins/motherduck-skills-claude
```

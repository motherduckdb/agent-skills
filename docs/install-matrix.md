# Install Matrix

Use this document when you want the fastest copy-paste install route for a specific harness.

All main harnesses can use the shared MotherDuck catalog through `npx skills`.
The packaged installs below are harness-specific convenience paths for runtimes where this repo also ships a native plugin or extension surface.

## Packaged Installs

| Harness | Install |
|-------|-------|
| `Claude Code` | `/plugin marketplace add motherduckdb/agent-skills` then `/plugin install motherduck-skills@motherduck-agent-skills` |
| `Codex` | open this repo in Codex, then install **MotherDuck Skills** from `/plugins` |
| `Gemini CLI` | `gemini extensions install https://github.com/motherduckdb/agent-skills --consent` |

## Skills CLI Install

For harnesses that support the shared skills installer:

If you do not already have the Skills CLI available, install it first:

```bash
npm install -g @fountainai/skills
```

```bash
npx -y skills add motherduckdb/agent-skills --yes
```

Global install:

```bash
npx -y skills add motherduckdb/agent-skills --yes --global
```

## Manual Per-Skill Install

Copy the full skill directory, not only `SKILL.md`.

## Verification

- `Claude Code`: plugin shows up and can be invoked on a MotherDuck task
- `Codex`: plugin appears in `/plugins`
- `Gemini CLI`: `gemini extensions list` or `gemini skills list`

For local Claude plugin development, validate the dedicated package directly:

```bash
claude plugin validate ./plugins/motherduck-skills-claude
claude --plugin-dir ./plugins/motherduck-skills-claude
```

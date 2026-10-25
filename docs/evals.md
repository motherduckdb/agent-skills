# Skill Evals

The golden eval set checks the catalog end to end on real agent harnesses. Each task is a realistic request with:

- `expect_skills`: the skills an agent may load to handle it (routing passes if it loads any of them)
- `must` / `must_not`: regex checks on the final answer, each with the reason it matters

The suite lives in `evals/golden_tasks.json`. `scripts/validate_skills.py` checks it on every run: unique ids, real skill names, compilable patterns.

## Run

Run it from the repo root after syncing the plugin packages (`uv run scripts/sync_claude_plugin.py`):

```bash
uv run scripts/run_skill_evals.py --harness claude --runs 2 --out evals/results/<label>.json
uv run scripts/run_skill_evals.py --harness codex --model <model> --runs 2
uv run scripts/run_skill_evals.py --harness gemini --runs 2
```

- `claude` loads `plugins/motherduck-skills-claude` with `--plugin-dir` in an empty working directory, with only project settings and no MCP servers, so the user's own plugins and `CLAUDE.md` do not leak in. Skill loads come from `Skill` tool calls.
- `codex` installs the packaged plugin into an isolated Codex home, the same way `scripts/test_codex_use_cases.py` does. Skill loads are inferred from `SKILL.md` paths in tool events.
- `gemini` uses the Gemini CLI with the MotherDuck extension already installed. Skill loads are inferred from tool-call events. This adapter is the least verified; check a `--tasks <one-id> --runs 1` run by hand before trusting a full report.

Tasks ask for answers, not actions, so runs need no MotherDuck credentials and change nothing.

## Read the report

- `routing_accuracy`: share of runs that loaded an expected skill
- `run_pass_rate`: share of runs that routed correctly and passed every check
- per-task `passes/runs`, marked `intermittent` when a task passed only some runs

Compare against an earlier report with `--baseline <report.json>`. The `flips` block lists tasks that regressed or improved. Read flips before the aggregate: a merge that keeps the average flat can still break one contract.

## When to run it

- Before and after merging, splitting, or renaming skills, or rewriting a description. Keep the change only if no task regresses.
- When adding a skill or a launch to the catalog, add at least one task that routes to it and checks its key contract.
- Across model families before a release: at least Claude Code plus one of Codex or Gemini CLI.

Runs cost model usage (a full Claude run of 20 tasks × 2 is a few dollars) and are not part of CI.

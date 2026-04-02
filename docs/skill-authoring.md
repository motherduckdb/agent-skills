# Skill Authoring

This repo is a public MotherDuck skill catalog. Keep skills opinionated and useful for agents, but do not turn the main `SKILL.md` files into encyclopedias.

## What Goes in `SKILL.md`

`SKILL.md` should act like a router:

- when to use the skill
- the first decisions to make
- the default workflow
- the expected output
- which `references/` files to open next
- which `artifacts/` to run next

For use-case skills, always say what to do when a remote or local MotherDuck server is active:

- ask which database or workspace is in scope if unclear
- explore databases, schemas, tables, columns, and key joins
- let the real data model shape the downstream implementation
- when the skill emits a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/1.0.0(harness-<harness>;llm-<llm>)`; if metadata is missing, fall back to `harness-unknown` and `llm-unknown`
  - this watermark is for high-level product analytics only: which harness and LLM used the skill, so we can improve the skill and test it against that LLM later
  - do not present it as user tracking; it is not for personal data or end-user attribution

## What Goes in `references/`

Put detailed guidance in `references/`:

- long architecture walkthroughs
- decision matrices
- SQL playbooks
- migration or rollout checklists
- deep product guidance that would bloat the main skill

When shrinking a skill, move content into `references/`; do not delete it.

Do not point shipped `SKILL.md`, `references/`, or `artifacts/` content at `motherduck-examples`.
That repo is an authoring-only comparison source for maintainers. If it teaches us something useful, copy the learning into this repo's guidance or artifacts before shipping.

## What Goes in `artifacts/`

Put runnable helpers in `artifacts/` when they help an agent move faster:

- local DuckDB examples
- validation scripts
- starter implementation skeletons
- small reproducible workflows

Artifacts should be small, local-first, and safe to run without production credentials when possible.
When the artifact is modeling MotherDuck-specific behavior, prefer dual-mode artifacts: local-first by default, but runnable against temporary MotherDuck databases when `MOTHERDUCK_TOKEN` is available.
Artifacts that open MotherDuck connections should derive the repo-standard watermark from `MOTHERDUCK_AGENT_HARNESS` and `MOTHERDUCK_AGENT_LLM` when those values are available.

If a skill benefits from a fuller runnable project, keep that project under `references/` and link to it from the main skill. The small `artifacts/` example should still exist when a local-first pattern is useful.

## Frontmatter

Keep SKILL frontmatter portable:

```yaml
---
name: skill-name
description: One sentence saying when to use this skill.
license: MIT
---
```

Repo-only metadata belongs in `skills/catalog.json`.

When changing the repo-level install and discovery story, also keep the Gemini extension surfaces aligned:

- `gemini-extension.json`
- `GEMINI.md`
- `commands/motherduck/*.toml`

Repo maintenance layout:

- keep root `scripts/` limited to executable entrypoints
- put shared script implementation in `scripts/_lib/`
- put shared test implementation in `tests/_lib/`

## Writing Style

- prefer direct trigger phrases in descriptions
- keep the main skill concise
- prefer references over duplicated prose
- prefer concrete defaults over hedging
- preserve scenario-based guidance when multiple MotherDuck paths are valid

## Required Checks

When changing skills, references, artifacts, or catalog surfaces:

```bash
uv run scripts/validate_skills.py
uv run --with duckdb --with pyyaml python tests/validate_snippets.py
python3 scripts/package_gemini_extension.py
```

When a change affects use-case skills or their artifacts, also run:

```bash
uv run scripts/test_codex_use_cases.py
uv run scripts/test_motherduck_artifacts.py
```

When a change affects TypeScript companion artifacts, also run:

```bash
uv run scripts/test_typescript_artifacts.py
```

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

## What Goes in `references/`

Put detailed guidance in `references/`:

- long architecture walkthroughs
- decision matrices
- SQL playbooks
- migration or rollout checklists
- deep product guidance that would bloat the main skill

When shrinking a skill, move content into `references/`; do not delete it.

## What Goes in `artifacts/`

Put runnable helpers in `artifacts/` when they help an agent move faster:

- local DuckDB examples
- validation scripts
- starter implementation skeletons
- small reproducible workflows

Artifacts should be small, local-first, and safe to run without production credentials when possible.
When the artifact is modeling MotherDuck-specific behavior, prefer dual-mode artifacts: local-first by default, but runnable against temporary MotherDuck databases when `MOTHERDUCK_TOKEN` is available.

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
```

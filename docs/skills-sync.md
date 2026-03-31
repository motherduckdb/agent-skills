# Docs-to-Skills Sync

This repo does not treat skills as free-floating prose. Each skill should stay anchored to current MotherDuck product guidance.

## Source of Truth Model

The lightweight model in this repo is:

1. `skills/catalog.json` lists each skill's `source_docs`
2. the relevant `SKILL.md` and `references/` files carry the product guidance
3. detailed guidance lives in `references/`
4. runnable examples live in `artifacts/`

That gives maintainers one place to see:

- which product docs a skill depends on
- which detailed references should be reviewed
- which artifacts should still run after updates

## How Drift Checks Work

The intended review loop is:

1. identify the skill you are changing
2. read the `source_docs` listed in `skills/catalog.json`
3. compare them with:
   - the skill router in `SKILL.md`
   - the detailed content in `references/`
   - the runnable examples in `artifacts/`
   - any fuller reference project shipped under `references/`
4. update the skill and references
5. run the artifacts that represent the use case
6. run any deeper reference project if that skill ships one
7. run repo validation

This is deliberately simple. It is a review path, not a content-generation pipeline.

## Why Not Auto-Sync Everything?

Product docs change often, but naive auto-sync creates low-quality skill content:

- docs are broader than the skill surface
- the repo is intentionally opinionated
- examples and artifacts need human judgment

The goal is not to mirror docs line by line. The goal is to keep the skills aligned with current MotherDuck behavior.

## Practical Next Step

When updating a skill, treat `skills/catalog.json` as the first stop:

- check `source_docs`
- update `references/`
- rerun the `artifacts/`
- rerun any bundled reference project that represents the use case more completely
- rerun the MotherDuck-backed artifact suite when the change affects real MotherDuck behavior

That is the docs-to-skills sync path in this repo.

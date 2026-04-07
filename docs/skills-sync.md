# Docs-to-Skills Sync

This repo does not treat skills as free-floating prose. Each skill should stay anchored to current MotherDuck product guidance.

## Source of Truth Model

The lightweight model in this repo is:

1. `skills/catalog.json` lists each skill's `source_docs`
2. the relevant `SKILL.md` and `references/` files carry the product guidance
3. detailed guidance lives in `references/`
4. runnable examples live in `artifacts/`
5. packaged plugin surfaces and install docs reflect the same catalog

That gives maintainers one place to see:

- which product docs a skill depends on
- which detailed references should be reviewed
- which artifacts should still run after updates
- which plugin surfaces and install routes should still work after updates
- which Claude-only packaged skill augmentations should still be applied

## How Drift Checks Work

The intended review loop is:

1. identify the skill you are changing
2. read the `source_docs` listed in `skills/catalog.json`
3. compare them with:
   - the skill router in `SKILL.md`
   - the detailed content in `references/`
   - the runnable examples in `artifacts/`
   - the TypeScript companion artifact when the catalog or skill references one
   - any fuller reference project shipped under `references/`
   - optional maintainer-only comparison inputs such as `motherduck-examples`
4. update the skill and references
5. run the artifacts that represent the use case
6. run any deeper reference project if that skill ships one
7. sync the dedicated Claude plugin when the shared skill content changed
8. run repo validation

This is deliberately simple. It is a review path, not a content-generation pipeline.

## Why Not Auto-Sync Everything?

Product docs change often, but naive auto-sync creates low-quality skill content:

- docs are broader than the skill surface
- the repo is intentionally opinionated
- examples and artifacts need human judgment

The goal is not to mirror docs line by line. The goal is to keep the skills aligned with current MotherDuck behavior.

If an external comparison repo helps during authoring, internalize the resulting guidance here. Do not ship references that require the user to have that comparison repo alongside the plugin.

## Practical Next Step

When updating a skill, treat `skills/catalog.json` as the first stop:

- check `source_docs`
- update `references/`
- rerun the `artifacts/`
- rerun `scripts/test_typescript_artifacts.py` when the skill ships TS companion artifacts
- rerun any bundled reference project that represents the use case more completely
- rerun the MotherDuck-backed artifact suite when the change affects real MotherDuck behavior
- rerun `uv run scripts/sync_claude_plugin.py` when the shared catalog changed
- rerun `uv run scripts/check_claude_plugin_sync.py` before you consider the Claude package done
- keep the Skills CLI prerequisite in install docs explicit: `npm install -g @fountainai/skills`

That is the docs-to-skills sync path in this repo.

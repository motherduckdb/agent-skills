# Contributing

This repository publishes reusable MotherDuck skills for AI agents.

Contributions should keep the repo opinionated, low-drift, and grounded in real MotherDuck behavior.

## What to Change

Contributions are welcome for:

- skill content in `skills/*/SKILL.md`
- detailed guidance in `skills/*/references/`
- runnable examples in `skills/*/artifacts/`
- catalog and packaging metadata
- install and validation docs

Keep changes targeted. Prefer small, mechanical updates over broad rewrites.

## Repo Structure

The catalog is a three-layer graph:

- `utility`: `motherduck-connect`, `motherduck-query`, `motherduck-explore`, `motherduck-duckdb-sql`
- `workflow`: `motherduck-load-data`, `motherduck-model-data`, `motherduck-share-data`, `motherduck-create-dive`, `motherduck-ducklake`, `motherduck-security-governance`, `motherduck-pricing-roi`
- `use-case`: `motherduck-build-cfa-app`, `motherduck-build-dashboard`, `motherduck-build-data-pipeline`, `motherduck-migrate-to-motherduck`, `motherduck-enable-self-serve-analytics`, `motherduck-partner-delivery`

Important source-of-truth files:

- `skills/*/SKILL.md`
- `skills/catalog.json`
- `README.md`
- `HARNESSES.md`
- `ARCHITECTURE.md`
- `docs/skill-authoring.md`
- `docs/skills-sync.md`
- `docs/install-matrix.md`
- `CLAUDE.md`
- `.claude-plugin/marketplace.json`
- `plugins/motherduck-skills-claude/.claude-plugin/plugin.json`
- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

## Repo Shape

Each skill folder can contain:

- `SKILL.md` -- the concise router the agent should load first
- `references/` -- preserved detailed guidance and playbooks
- `artifacts/` -- runnable local examples or helpers

Some use-case skills also ship a fuller runnable reference project under `references/` when the local artifact is intentionally smaller than the real workflow.

In practice, this means:

- utility and workflow skills should stay short, activation-friendly, and explicit about defaults
- detailed mechanics, examples, and edge cases belong in `references/`
- use-case skills should orchestrate lower-level skills rather than duplicating them

The machine-readable index lives at `skills/catalog.json` and tracks:

- skill names and descriptions
- layer and dependencies
- reference files
- runnable artifacts
- source docs
- whether a use-case should begin with live MotherDuck discovery

## Runnable Use-Case Artifacts

These are packaged per use-case as paired artifacts:

- a MotherDuck-backed Python artifact used by the existing smoke tests
- a TypeScript companion artifact with the same output contract for app/backend-oriented implementations

Python artifact commands:

```bash
uv run --with duckdb python skills/motherduck-build-cfa-app/artifacts/customer_routing_example.py
uv run --with duckdb python skills/motherduck-build-dashboard/artifacts/dashboard_story_example.py
uv run --with duckdb python skills/motherduck-build-data-pipeline/artifacts/pipeline_stage_example.py
uv run --with duckdb python skills/motherduck-migrate-to-motherduck/artifacts/migration_validation_example.py
uv run --with duckdb python skills/motherduck-enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
uv run --with duckdb python skills/motherduck-partner-delivery/artifacts/client_delivery_example.py
```

Validate the TypeScript companion artifacts:

```bash
uv run scripts/test_typescript_artifacts.py
```

They are not meant to replace production code. They are small patterns that help an agent move from plan to implementation faster.

To run the whole artifact suite against temporary real MotherDuck databases with your token:

```bash
uv run scripts/test_motherduck_artifacts.py
```

That suite:

- runs all six use-case artifacts against temporary MotherDuck databases
- runs the full `dlt + dbt + MotherDuck` reference pipeline
- drops the temporary databases afterward

For a fuller MotherDuck pipeline example, `motherduck-build-data-pipeline` also includes:

```bash
cd skills/motherduck-build-data-pipeline/references/dlt-dbt-motherduck-project
export MOTHERDUCK_TOKEN=...
export MOTHERDUCK_PIPELINE_DB=md_skills_pipeline_demo
uv sync --python 3.12
uv run python pipeline/run_all.py
uv run python pipeline/cleanup.py
```

## Contribution Workflow

1. Fork the repository.
2. Create a branch.
3. Make the skill, reference, artifact, catalog, or plugin-surface change.
4. Run the validators.
5. Open a PR with a clear explanation of what changed and why.

## Editing Guidelines

- Keep shared source skills portable. Claude-only metadata such as `argument-hint` belongs in the dedicated Claude package sync layer, not in `skills/`.
- Do not point shipped skill content at `motherduck-examples`; internalize useful guidance into this repo first.
- If you shrink a skill, move preserved detail into `references/` rather than deleting it.
- If a change affects real MotherDuck behavior, update the runnable artifact or reference project, not just the prose.
- Preserve the layer graph:
  - utility skills cannot depend on other skills
  - workflow skills can depend only on utility skills
  - use-case skills can depend only on utility and workflow skills

## Validation

Run these when changing skills, catalogs, manifests, or docs:

```bash
uv run scripts/validate_skills.py
claude plugin validate ./.claude-plugin/marketplace.json
claude plugin validate ./plugins/motherduck-skills-claude
uv run scripts/sync_claude_plugin.py
uv run scripts/check_claude_plugin_sync.py
uv run --with duckdb --with pyyaml python tests/validate_snippets.py
```

Run these when changing TypeScript companion artifacts or guidance that claims the TS artifacts are runnable:

```bash
uv run scripts/test_typescript_artifacts.py
```

Run these when changing artifact behavior, reference projects, or any guidance that claims to be validated against real MotherDuck:

```bash
uv run scripts/test_motherduck_artifacts.py
```

Run these when changing use-case output contracts or use-case reference guidance:

```bash
uv run scripts/test_codex_use_cases.py
```

Optional deeper benchmark:

```bash
uv run scripts/benchmark_motherduck_artifacts.py --runs 2
```

## More Context

For repo-specific authoring and drift rules:

- `docs/skill-authoring.md`
- `docs/skills-sync.md`
- `ARCHITECTURE.md`

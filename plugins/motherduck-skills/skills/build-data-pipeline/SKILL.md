---
name: build-data-pipeline
description: Build an end-to-end data pipeline with MotherDuck. Use when someone is designing a workflow that ingests external data, transforms it with DuckDB SQL, and produces analytics-ready tables or visualizations.
license: MIT
---

# Build a Data Pipeline with MotherDuck

Use this skill when the user needs an ingestion-to-serving workflow, not just a single load step.

This is a use-case skill. It orchestrates `connect`, `load-data`, `model-data`, `query`, `share-data`, and `ducklake`.

## Start Here: Is a MotherDuck Server Active?

Always determine this first.

- If a **remote MotherDuck MCP server** or **local MotherDuck server** is active, use it.
- If the user already knows the destination database, confirm it before designing stages.
- Explore the live environment:
  - current databases and schemas
  - raw, staging, and analytics boundaries if they already exist
  - source tables, target tables, and table grain
  - key columns, date fields, and join keys

Use that discovery to decide whether the pipeline is:

- landing into an empty workspace
- extending an existing warehouse layout
- publishing into an existing analytics model

If no server is active, ask for source shape and target shape before drafting the pipeline.

## Use This Skill When

- The user needs ingestion plus transformation plus serving output.
- The work spans raw landing, curation, and publication.
- The user needs a stage-by-stage pipeline pattern rather than one command.

## Pipeline Defaults

- batch over streaming
- raw landing before curation
- explicit raw -> staging -> analytics boundaries
- bulk ingest paths over row-by-row writes
- native MotherDuck storage unless DuckLake is explicitly required

## Workflow

1. Confirm whether live MotherDuck discovery is available.
2. Inspect the current workspace and target data model.
3. Define raw, staging, and analytics boundaries.
4. Ingest raw data.
5. Deduplicate, type, and promote into staging.
6. Materialize analytics-ready outputs.
7. Validate counts and business metrics before publishing downstream assets.

## Output

The output of this skill should be:

- the stage layout
- the ingestion method
- the transformation sequence
- the serving tables or views
- the validation checks

## References

- `references/dlt-dbt-motherduck-project/` -- fully runnable MotherDuck reference project using `dlt`, `dbt-duckdb`, and validation queries
- `references/PIPELINE_IMPLEMENTATION_GUIDE.md` -- preserved detailed pipeline guidance that used to live in this skill
- `../load-data/references/INGESTION_PATTERNS.md` -- lower-level ingestion patterns

## Runnable Artifact

- `artifacts/pipeline_stage_example.py` -- local DuckDB example that lands raw data, deduplicates it, and publishes analytics output across raw/staging/analytics databases
- `references/dlt-dbt-motherduck-project/` -- end-to-end MotherDuck example that bootstraps the target database, lands raw data with `dlt`, builds staging and analytics models with `dbt`, and validates the final mart

Run it with:

```bash
uv run --with duckdb python skills/build-data-pipeline/artifacts/pipeline_stage_example.py
```

Run the same stage pattern against temporary MotherDuck databases:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/build-data-pipeline/artifacts/pipeline_stage_example.py
```

For the full MotherDuck project:

```bash
cd skills/build-data-pipeline/references/dlt-dbt-motherduck-project
export MOTHERDUCK_TOKEN=...
export MOTHERDUCK_PIPELINE_DB=md_skills_pipeline_demo
uv sync --python 3.12
uv run python pipeline/run_all.py
uv run python pipeline/cleanup.py
```

## Verified Notes

- Bootstrap the target MotherDuck database before running `dlt`. The `motherduck` destination does not create the database for you.
- Keep this stack on Python 3.11 or 3.12 for now. The tested `dbt-duckdb` path here was not reliable on Python 3.14.
- If you want exact schema names like `raw`, `staging`, and `analytics` in dbt, override `generate_schema_name`.
- When a long-lived Python process loads data and a separate `dbt` subprocess builds models, run post-build validation in a fresh process or refresh database state before reading new relations.

## Related Skills

- `connect` -- choose the right connection path
- `load-data` -- ingestion mechanics
- `model-data` -- shape the analytics layer
- `query` -- write transformations and validations
- `share-data` -- publish curated outputs
- `ducklake` -- only when open-table-format storage is a real requirement

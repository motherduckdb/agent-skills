# Execution Reference

Read this for example execution or an explicit structured-output request. These fixtures illustrate the pattern; they are not the user’s dataset or a prerequisite for ordinary work.

## Structured Output

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.
This is mainly for automated tests, regression checks, or downstream tooling that needs a stable machine-readable shape. Normal human-facing use of the skill can stay in prose unless JSON is explicitly requested.

Use this exact top-level shape when JSON is requested:

```json
{
  "summary": {},
  "assumptions": [],
  "implementation_plan": [],
  "validation_plan": [],
  "risks": []
}
```

## Runnable Artifact

- `artifacts/pipeline_stage_example.py` -- MotherDuck-backed Python example that stages a Parquet extract, lands it into raw, deduplicates it, and publishes analytics output across raw/staging/analytics databases
- `artifacts/pipeline_stage_example.ts` -- TypeScript companion artifact with the same stage layout and output contract
- `references/dlt-dbt-motherduck-project/` -- end-to-end MotherDuck example that bootstraps the target database, lands raw data with `dlt`, builds staging and analytics models with `dbt`, and validates the final mart

From the repository root, run it with (for an installed skill, substitute its absolute artifact path):

```bash
uv run --with duckdb python skills/motherduck-build-data-pipeline/artifacts/pipeline_stage_example.py
```

Run the same stage pattern against temporary MotherDuck databases:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/motherduck-build-data-pipeline/artifacts/pipeline_stage_example.py
```

From a checkout of this repository, validate the TypeScript companion artifacts:

```bash
uv run scripts/test_typescript_artifacts.py
```

For the full MotherDuck project:

```bash
cd skills/motherduck-build-data-pipeline/references/dlt-dbt-motherduck-project
export MOTHERDUCK_TOKEN=...
export MOTHERDUCK_PIPELINE_DB=md_skills_pipeline_demo
uv sync --python 3.12
uv run python pipeline/run_all.py
uv run python pipeline/cleanup.py
```

## Verified Notes

- Bootstrap the target MotherDuck database before running `dlt`. The `motherduck` destination does not create the database for you.
- Use Python 3.11 or 3.12 to reproduce this reference project; its tested `dbt-duckdb` path did not run reliably on Python 3.14.
- If you want exact schema names like `raw`, `staging`, and `analytics` in dbt, override `generate_schema_name`.
- When a long-lived Python process loads data and a separate `dbt` subprocess builds models, run post-build validation in a fresh process or refresh database state before reading new relations.

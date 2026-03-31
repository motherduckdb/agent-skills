# dlt + dbt + MotherDuck Reference Project

This is a minimal end-to-end pipeline reference for the `build-data-pipeline` skill.

It captures the pipeline shape that this repo repeatedly verified against real MotherDuck runs:

- `dlt` for the raw loading step
- `dbt-duckdb` for staging and analytics modeling
- Python validation and cleanup around the workflow

The example is deliberately small and fully runnable:

- `dlt` lands raw JSONL data in MotherDuck
- `dbt` models staging and analytics relations in the same MotherDuck database
- Python validation checks the final outputs

## Why One Database

The main skill recommends separate lifecycle stages. For this reference project, the simplest runnable shape is one MotherDuck database with explicit schemas:

- `raw`
- `staging`
- `analytics`

That keeps the dbt project small and avoids extra attach configuration. When the pipeline grows and stage boundaries matter operationally, split the stages into separate MotherDuck databases and use dbt `attach`.

## Verified Constraints

These are based on a real local run against MotherDuck:

- Bootstrap the MotherDuck database before `dlt` runs. The `motherduck` destination does not create the target database for you.
- Use Python 3.11 or 3.12 for this stack. `dbt-duckdb` did not run correctly on Python 3.14 in this environment.
- Keep `dbt` concurrency at `threads: 1` for a small MotherDuck project like this.
- Override `generate_schema_name` so dbt uses exact schema names instead of `main_<schema>`.
- Run post-build validation in a fresh process. A long-lived local DuckDB process may not immediately see schemas written by a separate `dbt` subprocess.

## Files

- `pipeline/bootstrap.py`: creates the MotherDuck database and schemas
- `pipeline/load_raw.py`: loads raw data into MotherDuck with `dlt`
- `pipeline/run_all.py`: runs bootstrap, load, dbt build, and validation
- `pipeline/validate.py`: asserts row counts and final mart output
- `dbt_project.yml`, `profiles.yml`, `models/`, `macros/`: dbt project
- `data/*.jsonl`: tiny input dataset

## Run It

Set credentials:

```bash
export MOTHERDUCK_TOKEN=...
export MOTHERDUCK_PIPELINE_DB=md_skills_pipeline_demo
```

Install dependencies with a supported Python:

```bash
uv sync --python 3.12
```

Run the whole pipeline:

```bash
uv run python pipeline/run_all.py
```

Drop the temporary MotherDuck database when you are done:

```bash
uv run python pipeline/cleanup.py
```

Run the steps individually if you want to inspect them:

```bash
uv run python pipeline/bootstrap.py
uv run python pipeline/load_raw.py
DBT_PROFILES_DIR=. uv run dbt build
uv run python pipeline/validate.py
```

## Expected Output

After a successful run, the final mart contains three rows:

| customer_id | customer_name     | order_count | total_amount |
|-------------|-------------------|-------------|--------------|
| c1          | Acme Rockets      | 2           | 155.00       |
| c2          | Birch Analytics   | 1           | 75.00        |
| c3          | Cedar Logistics   | 1           | 200.00       |

The staging model also proves two common pipeline patterns:

- deduplicate by latest `updated_at`
- filter analytics output to `PAID` orders only

## Real MotherDuck Test Posture

This project is intended to run against a real MotherDuck database, not just local DuckDB.

- use a temporary `MOTHERDUCK_PIPELINE_DB` for validation runs
- bootstrap the database first
- run validation after `dbt build`
- drop the temporary database with `pipeline/cleanup.py` after the run

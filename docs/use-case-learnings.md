# Use-Case Learnings

This document captures the durable lessons from repeatedly building and testing the six use-case skills in this repo through the Codex plugin and the runnable MotherDuck artifacts.

## Distribution Rules

- Shipped skills, references, and artifacts must be self-contained.
- Do not tell plugin users to look at `motherduck-examples`.
- `motherduck-examples` is an authoring input only:
  - use it when drafting or revising artifacts in this repo
  - use it when sanity-checking implementation posture
  - internalize the resulting guidance here before shipping

## Use-Case Output Rules

- When a caller asks for structured JSON, the skill should return raw JSON only.
- Do not wrap requested JSON in Markdown fences.
- Use-case tests should validate the output structure mechanically rather than relying on manual spot checks.

## MotherDuck Execution Rules

- Validate use-case artifacts against real temporary MotherDuck databases, not just local DuckDB.
- Clean up temporary MotherDuck databases after every test run.
- Watermark native DuckDB `md:` connections with the repo-standard `custom_user_agent`.

## Artifact Design Rules

- Keep a small local-first artifact for each use case.
- When the use case claims real MotherDuck behavior, make the artifact dual-mode so it can run against MotherDuck too.
- Prefer a small runnable artifact plus one deeper reference project over bloating the top-level skill.

## Pipeline Learnings

- Prefer Parquet or other bulk landing paths over row-by-row inserts.
- Bootstrap the target MotherDuck database before running loaders that assume it already exists.
- For the bundled `dlt + dbt` reference project, stay on Python 3.11 or 3.12 for now.
- Override dbt schema naming when exact `raw`, `staging`, and `analytics` schema names matter.

## Use-Case Planning Learnings

- Start from the live MotherDuck database or workspace whenever discovery is available.
- Keep the first implementation slice narrow and runnable.
- Default to structural isolation for customer-facing or multi-client work.
- Keep self-serve rollouts opinionated: first audience, first asset, first governed dataset.

## Runtime Learnings

- Full use-case generation through Codex is materially slower than the MotherDuck artifact suite.
- Use dedicated runtime checks for both:
  - plugin installation and skill exposure
  - use-case output structure
  - MotherDuck-backed artifact execution
- Treat the runtime loop as two tiers:
  - quick inner-loop checks: `validate_skills.py`, snippet validation, and targeted artifact runs
  - slower regression checks: `test_codex_use_cases.py` and the full MotherDuck artifact suite

---
name: motherduck-build-data-pipeline
description: Build ingestion-to-serving pipelines on MotherDuck, including stage boundaries, transformations, and publication.
argument-hint: [pipeline-goal]
license: MIT
---

# Build a Data Pipeline with MotherDuck

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Pipeline Defaults

- batch over streaming
- raw landing before curation
- explicit raw -> staging -> analytics boundaries
- bulk ingest paths over row-by-row writes
- idempotent stage rebuilds or append contracts before scheduled automation
- verify the MotherDuck-supported DuckDB client version before recommending upstream-only write, checkpoint, or lakehouse features
- native MotherDuck storage unless DuckLake is explicitly required
- MotherDuck CLI for Flight source and large file-shaped output when the agent has a shell; MCP for chat-only operation
- a `flights` Guide for reusable scheduling, naming, secret, and ingestion conventions when the organization has them

## Workflow

1. Inspect the available MotherDuck server or supplied source and target context.
2. Inspect the current workspace and target data model.
3. Define raw, staging, and analytics boundaries.
4. Ingest raw data.
5. Deduplicate, type, and promote into staging.
6. Materialize analytics-ready outputs.
7. Validate counts, freshness, uniqueness, and business metrics before publishing downstream assets.
8. When durable context is part of delivery, capture stable business definitions and operating caveats in referenced Guides; keep executable transformation logic in source control.

Match execution to the request: answer, review, or planning work returns the requested pipeline artifacts; build or change work creates the requested in-scope files and warehouse objects and validates them. Ask before destructive actions, unrelated external writes, or a material expansion of scope.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.6.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- the stage layout
- the ingestion method
- the transformation sequence
- the serving tables or views
- the validation checks

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/dlt-dbt-motherduck-project/` -- fully runnable MotherDuck reference project using `dlt`, `dbt-duckdb`, and validation queries
- `references/PIPELINE_IMPLEMENTATION_GUIDE.md` -- stage design, transformation sequencing, and ingestion-to-serving examples
- `../motherduck-load-data/references/INGESTION_PATTERNS.md` -- lower-level ingestion patterns

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [pipeline_stage_example.py](artifacts/pipeline_stage_example.py)
- [pipeline_stage_example.ts](artifacts/pipeline_stage_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` -- choose the right connection path
- `motherduck-load-data` -- ingestion mechanics
- `motherduck-model-data` -- shape the analytics layer
- `motherduck-query` -- write transformations and validations
- `motherduck-share-data` -- publish curated outputs
- `motherduck-ducklake` -- only when open-table-format storage is a real requirement

---
name: motherduck-load-data
description: Load files, object storage, dataframes, or external databases into MotherDuck using an appropriate bulk ingestion path.
argument-hint: [source-and-target]
license: MIT
---

# Load Data into MotherDuck

## Source Of Truth

- Prefer current MotherDuck loading, cloud-storage, and Postgres-endpoint loading docs first.
- Use `CREATE SECRET` and cloud-storage docs for protected-object-store workflows.
- Use the DuckDB database upload docs when the source is an existing local `.duckdb`, `.ddb`, or attached DuckDB database.
- Keep the loading advice aligned with MotherDuck's documented posture:
  - batch over streaming
  - Parquet over CSV when you control the format
  - dataframe, `COPY`, CTAS, or `INSERT ... SELECT` over row-by-row inserts
  - native MotherDuck storage first unless DuckLake is explicitly required

## Default Posture

- Start by classifying the source: object storage or HTTPS, local file or local DuckDB, in-memory rows, or an external database.
- Prefer `CREATE TABLE AS SELECT` for first loads and `INSERT INTO ... SELECT` for appends.
- For whole DuckDB databases, use `CREATE OR REPLACE DATABASE remote_name FROM CURRENT_DATABASE()`, an attached local database, a local file path from a native client, or a remote `.duckdb` file URL such as S3. Remote and local file imports physically copy data into MotherDuck; database/share clone sources are zero-copy.
- Use Parquet for durable bulk movement whenever you control the source format.
- Treat the Postgres endpoint as a thin-client path for server-side remote reads, not for local-file or extension-driven ingestion.
- Bootstrap the target MotherDuck database first when the ingestion tool does not create it automatically.
- Keep raw landing minimally transformed; do typing, deduplication, and business logic in staging or modeling steps.
- Keep source storage close to the MotherDuck region when you control placement.

## Workflow

1. Identify where the source data actually lives.
2. Choose the loading path:
   - object storage or HTTPS: remote read into MotherDuck
   - local file or local DuckDB: use a DuckDB client path
   - remote DuckDB database file: use `CREATE DATABASE ... FROM '<cloud-url>'` with the required cloud secret
   - in-memory rows: Arrow or dataframe bulk load first, batched inserts only as a fallback
   - external database: use the appropriate scan or replication path from a DuckDB-capable environment
3. Land the data into a raw or staging table with minimal transformation.
4. Validate row counts, types, and a few business aggregates immediately after the load.
5. Promote into modeled tables only when the request includes transformation; a load request is complete after its destination data is validated.

For answer, review, or planning requests, recommend the loading path without mutating data. For load or implementation requests, perform the requested in-scope write and validation; ask before destructive replacement or a broader external write.

## References

Read only the reference sections needed for the current task.

- Read `references/INGESTION_PATTERNS.md` for format-specific options, cloud-storage secrets, Postgres-endpoint loading tradeoffs, Python dataframe paths, and advanced ingestion patterns.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for choosing between the Postgres endpoint and a DuckDB client path
- `motherduck-explore` for inspecting destination databases and validating landed tables
- `motherduck-query` for writing CTAS, append, and validation SQL
- `motherduck-model-data` for promoting landed data into staging and analytics tables
- `motherduck-ducklake` only when object-storage-backed lakehouse storage is an explicit requirement
- `motherduck-cli` when a shell-based load should stream structured output to files

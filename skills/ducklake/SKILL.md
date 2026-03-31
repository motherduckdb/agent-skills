---
name: ducklake
description: Decide when DuckLake is the right fit and how to use it on MotherDuck. Use when evaluating open-table-format storage, object storage-backed databases, or DuckLake-specific capabilities such as BYOB, time travel, maintenance functions, and file-level ingestion.
license: MIT
---

# Use DuckLake on MotherDuck

Use this skill when the storage question is bigger than "where should this table live?" and the answer may involve an open table format, object storage, snapshot-aware operations, or DuckLake-specific maintenance and ingestion behavior.

For reusable language patterns, see `references/typescript.md` and `references/python.md`.

## Source Of Truth

- Prefer current MotherDuck DuckLake docs first, then the underlying DuckLake extension docs only when they help explain behavior.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep the storage guidance aligned with the documented product posture:
  - native MotherDuck first
  - DuckLake is preview and opt-in
  - managed vs BYOB vs own-compute modes are distinct
  - maintenance is explicit, not automatic

This skill is intentionally opinionated for MotherDuck, but it is grounded in the official DuckLake extension code and DuckLake / DuckDB documentation. That matters because DuckLake has three distinct layers:

1. the DuckLake specification
2. the DuckDB `ducklake` extension
3. MotherDuck's productized DuckLake offering

Do not blur those together. The raw DuckDB extension can do more than a given hosted product deployment may expose.

## Default Position

Start with native MotherDuck storage unless there is a concrete reason not to.

Use DuckLake when you explicitly need one or more of these:

- open table format semantics
- object-storage-backed data layout
- direct control over file layout, snapshot retention, and maintenance
- the ability to register existing Parquet files into a lakehouse catalog
- a hybrid path where some databases remain warehouse-native and some graduate to lakehouse storage

Do not adopt DuckLake because it sounds more scalable or more modern.

## MotherDuck-Specific Position

For MotherDuck users, the strong default is still native MotherDuck storage.

Why:

- simpler operating model
- stronger default ergonomics
- faster reads for many ordinary analytical workloads
- fewer storage and metadata decisions

MotherDuck's public DuckLake docs explicitly say native MotherDuck storage is often 2x-10x faster than DuckLake for reads, including both cold and hot runs. That is the main reason not to move normal warehouse workloads onto DuckLake by default.

Use DuckLake on MotherDuck only when the architecture really benefits from:

- object storage as the source of truth
- open table format posture
- BYOB or lakehouse-oriented interoperability
- file-aware maintenance and ingestion flows

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** when the DuckLake task is operational:
  - maintenance jobs
  - ingestion scripts
  - data migration tooling
  - snapshot inspection and validation
- Prefer **TypeScript/Javascript** when the DuckLake task is product-facing:
  - provisioning workflows
  - platform control planes
  - app configuration and orchestration
- Avoid pushing file-layout or maintenance logic into browser or frontend code. DuckLake operations belong in backend or data-engineering surfaces.

## TypeScript/Javascript Starter

```ts
import { DuckDBInstance } from "@duckdb/node-api";

const instance = await DuckDBInstance.create();
const connection = await instance.connect();
await connection.run("LOAD md");
await connection.run(`SET motherduck_token='${process.env.MOTHERDUCK_TOKEN}'`);
await connection.run("ATTACH 'md:'");

// Run DuckLake SQL only from backend or automation code.
```

## Python Starter

```python
import os
import duckdb

conn = duckdb.connect()
conn.sql("LOAD md")
conn.sql(f"SET motherduck_token='{os.environ['MOTHERDUCK_TOKEN']}'")
conn.sql("ATTACH 'md:'")

# Run DuckLake SQL here after verifying the MotherDuck surface supports it.
conn.close()
```

## What DuckLake Actually Is

DuckLake is an open lakehouse format built around:

- a transactional catalog database for metadata
- Parquet files for table data

Unlike file-oriented lake formats that keep metadata in manifests or metadata files, DuckLake stores metadata in SQL tables. That gives it a very SQL-native operational surface.

In the official DuckDB extension, DuckLake supports:

- reads and writes through normal SQL
- snapshots and time travel
- schema evolution without rewriting existing files
- `MERGE INTO` upserts
- partitioning
- sorted-table metadata
- change-data style inspection between snapshots
- compaction and cleanup functions
- direct registration of existing Parquet files

## Mental Model: Spec vs Extension vs MotherDuck

### DuckLake specification

Defines what the format can represent:

- snapshots
- schema versions
- file metadata
- partition metadata
- sort metadata
- change metadata

### DuckDB `ducklake` extension

Implements a concrete SQL surface for working with DuckLake from DuckDB:

- `ATTACH 'ducklake:...'`
- `ALTER TABLE ... SET PARTITIONED BY`
- `ALTER TABLE ... SET SORTED BY`
- `CALL ducklake_merge_adjacent_files(...)`
- `FROM ducklake_snapshots(...)`
- `CALL ducklake_add_data_files(...)`

### MotherDuck

May expose DuckLake through product-specific database creation and management flows. Do not assume every raw DuckDB extension operation is available with identical syntax in MotherDuck.

## When DuckLake Is a Good Fit

Choose DuckLake deliberately when:

- data should live in object storage instead of warehouse-native storage
- you need open table format behavior
- you need to register external Parquet files into a managed catalog
- you care about snapshot history and explicit file maintenance
- you are building a hybrid architecture where metadata operations matter
- you want the option to use your own compute against DuckLake metadata

Good examples:

- very large append-heavy analytical datasets on object storage
- lakehouse ingestion where files already exist and should not be copied
- file-aware ETL where compaction, rewrite, and cleanup are planned maintenance steps
- multi-system architectures where catalog-backed lake data is a requirement

## When Native MotherDuck Is Better

Stay with native MotherDuck storage when:

- the workload is a normal analytical warehouse workload
- the team wants the fewest moving parts
- read performance and simplicity matter more than open-format posture
- you do not need object-storage-backed tables
- the dataset is mainly powering dashboards, apps, or team analytics rather than lakehouse workflows

If the argument for DuckLake is vague, stay native.

## Choose the Operating Mode

| Need | Path |
|---|---|
| Easiest evaluation in MotherDuck | fully managed DuckLake |
| Your own bucket, MotherDuck-managed query path | BYOB with MotherDuck compute |
| Your own compute against DuckLake metadata | own-compute DuckLake pattern |
| Local or self-managed DuckDB usage | DuckDB extension with `ATTACH` |

## Official DuckDB Extension Connection Model

With the raw DuckDB extension, the fundamental connection primitive is `ATTACH`.

DuckDB-catalog-backed DuckLake:

```sql
ATTACH 'ducklake:metadata.ducklake' AS my_ducklake (DATA_PATH 'data_files/');
USE my_ducklake;
```

Postgres-catalog-backed DuckLake:

```sql
ATTACH 'ducklake:postgres:dbname=ducklake_catalog host=localhost' AS my_ducklake
  (DATA_PATH 's3://my-bucket/my-data/');
USE my_ducklake;
```

Read-only attach:

```sql
ATTACH 'ducklake:postgres:dbname=ducklake_catalog host=localhost' AS my_ducklake
  (READ_ONLY);
```

### Catalog database choices

Per official docs:

- DuckDB catalog: simplest, but single-client
- SQLite catalog: local multi-client
- PostgreSQL catalog: multi-user / remote-friendly
- MySQL catalog: mentioned by docs, but the extension docs still say MySQL catalogs are not fully supported

That last point is important. Do not recommend MySQL casually without version-specific verification.

## MotherDuck-Oriented Connection Model

MotherDuck’s public docs frame DuckLake as a database type and managed product surface rather than as raw `ATTACH` syntax.

Typical MotherDuck examples look like:

```sql
CREATE DATABASE my_ducklake (TYPE DUCKLAKE);
```

or:

```sql
CREATE DATABASE my_ducklake (
  TYPE DUCKLAKE,
  DATA_PATH 's3://my-bucket/my-prefix/'
);
```

When writing a MotherDuck-facing skill or workflow:

- use MotherDuck syntax and product constraints first
- use raw DuckLake extension details to reason about behavior and limitations
- do not tell users to manage MotherDuck DuckLake as though it were only a local DuckDB extension
- keep BYOB object storage in the same region as the target MotherDuck region when you control the bucket placement
- do not assume MotherDuck performs file maintenance for you automatically

## Important Attach and Creation Options

The official extension surface supports several important options:

- `DATA_PATH`
- `READ_ONLY`
- `CREATE_IF_NOT_EXISTS`
- `DATA_INLINING_ROW_LIMIT`
- `ENCRYPTED`
- `METADATA_CATALOG`
- `METADATA_PATH`
- `METADATA_SCHEMA`
- `METADATA_PARAMETERS`
- `OVERRIDE_DATA_PATH`
- `SNAPSHOT_VERSION`
- `SNAPSHOT_TIME`
- `AUTOMATIC_MIGRATION`

Important behavior from the code and docs:

- if no DuckLake exists and `READ_ONLY` is used, attach fails
- `SNAPSHOT_VERSION` / `SNAPSHOT_TIME` imply read-only behavior
- `OVERRIDE_DATA_PATH` changes the active write/read path for the current connection only
- with `OVERRIDE_DATA_PATH`, data under the original path is not queryable in that connection
- existing catalogs can require automatic migration when extension/catalog versions diverge

## Core Capabilities

### 1. Time travel

DuckLake supports querying historical database state by snapshot id or timestamp.

Query at a specific snapshot:

```sql
SELECT * FROM tbl AT (VERSION => 3);
```

Query at a specific timestamp:

```sql
SELECT * FROM tbl AT (TIMESTAMP => now() - INTERVAL '1 week');
```

Attach a catalog at a historical snapshot:

```sql
ATTACH 'ducklake:metadata.duckdb' AS my_ducklake (SNAPSHOT_VERSION 3);
```

### 2. Schema evolution

DuckLake supports schema evolution without rewriting all existing files.

Supported patterns include:

```sql
ALTER TABLE tbl ADD COLUMN new_column INTEGER;
ALTER TABLE tbl ADD COLUMN nested_struct.new_field INTEGER;
ALTER TABLE tbl DROP COLUMN new_column;
ALTER TABLE tbl DROP COLUMN nested_struct.old_field;
ALTER TABLE tbl RENAME old_name TO new_name;
ALTER TABLE tbl RENAME nested_struct.old_field TO new_field_name;
ALTER TABLE tbl RENAME TO tbl_new_name;
```

This includes nested-field evolution inside `STRUCT` columns.

### 3. Upserts

DuckLake does not rely on primary keys for upserts. Use `MERGE INTO`.

```sql
MERGE INTO Stock AS s
USING Buy AS b
ON s.item_id = b.item_id
WHEN MATCHED THEN UPDATE SET balance = balance + b.volume
WHEN NOT MATCHED THEN INSERT VALUES (b.item_id, b.volume);
```

Do not recommend `INSERT ... ON CONFLICT` for DuckLake.

### 4. Partitioning

DuckLake tables can be partitioned by user-defined partition keys. New data is written using the current partitioning layout; old data keeps the layout it was written with.

```sql
ALTER TABLE events SET PARTITIONED BY (event_date);
```

Important implications:

- partitioning affects new writes, not historical files
- partition metadata is stored in DuckLake metadata
- Hive-style folder patterns are the default for partitioned data
- `hive_file_pattern` can be configured off if needed

### 5. Sorted tables

DuckLake supports logical sort definitions:

```sql
ALTER TABLE events SET SORTED BY (event_time ASC);
ALTER TABLE events SET SORTED BY (event_time ASC, event_type DESC);
```

Expressions are allowed:

```sql
ALTER TABLE events SET SORTED BY (date_trunc('hour', event_time) ASC);
```

Critical nuance:

- sorting applies during compaction and inlined-data flushing
- direct inserts are not automatically re-sorted at write time
- if you need sorted inserts immediately, use `ORDER BY` in the insert query

### 6. Data inlining

DuckLake supports inlining small changes directly into metadata tables instead of creating tiny Parquet files.

This applies to:

- small inserts
- small deletes

Important official behavior:

- data inlining is enabled by default in the official stable docs with a low row threshold
- MotherDuck may expose its own defaults and knobs
- inlined data behaves like normal table data from a query perspective

Examples:

```sql
SET ducklake_default_data_inlining_row_limit = 50;
```

```sql
CALL my_ducklake.set_option('data_inlining_row_limit', 100);
```

Use data inlining for:

- many tiny batch inserts
- frequent small delete operations
- workloads where tiny-file proliferation would otherwise become a maintenance problem

### 7. File registration

One of DuckLake’s most distinctive capabilities is registering existing Parquet files without copying them:

```sql
CALL ducklake_add_data_files('my_ducklake', 'people', 'people.parquet');
```

Important rules from official docs and tests:

- DuckLake does not copy the file; it just registers it
- ownership transfers conceptually to DuckLake for maintenance purposes
- later maintenance operations may delete or rewrite those files
- missing columns error unless `allow_missing => true`
- extra columns error unless `ignore_extra_columns => true`
- type compatibility is validated
- Hive partitioning can be inferred when requested

Examples:

```sql
CALL ducklake_add_data_files('my_ducklake', 'people', 'people.parquet', allow_missing => true);
CALL ducklake_add_data_files('my_ducklake', 'people', 'people.parquet', ignore_extra_columns => true);
```

This is a strong reason to choose DuckLake when external Parquet files already exist and you want them queryable through a catalog without rewriting them.

### 8. Snapshot and change inspection

DuckLake exposes metadata and change functions for introspection:

- `ducklake_snapshots`
- `ducklake_current_snapshot`
- `ducklake_last_committed_snapshot`
- `ducklake_table_info`
- `ducklake_table_insertions`
- `ducklake_table_deletions`
- `ducklake_table_changes`
- `ducklake_list_files`
- `ducklake_settings`
- `ducklake_options`

Example:

```sql
FROM my_ducklake.table_changes('tbl', 3, 4)
ORDER BY snapshot_id;
```

Use these when:

- auditing what changed between snapshots
- debugging ingestion and maintenance behavior
- building lineage or data-diff tooling
- investigating which files currently back a table

### 9. Maintenance operations

DuckLake requires explicit maintenance thinking. The official extension exposes:

- `ducklake_flush_inlined_data`
- `ducklake_merge_adjacent_files`
- `ducklake_rewrite_data_files`
- `ducklake_expire_snapshots`
- `ducklake_cleanup_old_files`
- `ducklake_delete_orphaned_files`
- `CHECKPOINT`

Practical guidance from official docs:

- merge adjacent files when small-file accumulation hurts efficiency
- expire snapshots only when you intentionally want to reduce historical retention
- clean up files after expiring snapshots if you want storage reclaimed
- rewrite files when many deletes are degrading read performance
- use `CHECKPOINT` to bundle periodic maintenance patterns

Do not pitch DuckLake without also owning maintenance behavior.

## Configuration Surface

The official extension supports both DuckDB-level settings and persistent DuckLake-scoped options.

DuckDB-level settings include:

- `ducklake_max_retry_count`
- `ducklake_retry_wait_ms`
- `ducklake_retry_backoff`
- `ducklake_default_data_inlining_row_limit`

DuckLake-scoped persistent options include:

- `data_inlining_row_limit`
- `parquet_compression`
- `parquet_version`
- `parquet_compression_level`
- `parquet_row_group_size`
- `parquet_row_group_size_bytes`
- `hive_file_pattern`
- `target_file_size`
- `require_commit_message`
- `rewrite_delete_threshold`
- `delete_older_than`
- `expire_older_than`
- `auto_compact`
- `encrypted`
- `per_thread_output`

Examples:

```sql
SET ducklake_max_retry_count = 100;
SET ducklake_retry_backoff = 2;
```

```sql
CALL my_ducklake.set_option('parquet_compression', 'zstd');
CALL my_ducklake.set_option('parquet_compression', 'zstd', schema => 'analytics');
CALL my_ducklake.set_option('parquet_compression', 'zstd', table_name => 'events');
FROM my_ducklake.options();
FROM my_ducklake.settings();
```

Scope priority is:

1. table
2. schema
3. global
4. default

## Concurrency and Conflict Resolution

DuckLake uses snapshot ids and metadata-level conflict detection.

High-level behavior from official docs:

- concurrent non-conflicting changes can often be retried automatically
- logical conflicts abort the transaction
- retry behavior is configurable

Common conflict categories:

- concurrent schema conflicts
- create/drop conflicts on the same object
- writes against tables altered or dropped by another transaction
- deletes or compaction colliding with other table changes

This means DuckLake is not "just Parquet files plus SQL". It has a real concurrency model, and that is part of its value.

## Unsupported and Risky Areas

### Unsupported by the DuckLake specification

Per official docs, do not rely on:

- indexes
- enforced primary keys
- enforced unique constraints
- foreign keys
- sequences
- `VARINT`
- `BITSTRING`
- `UNION`

Also not currently supported by the spec, though some may come later:

- user-defined types
- fixed-size arrays
- enums
- variant types
- generated columns
- non-literal default expressions such as `DEFAULT now()`
- full `DROP ... CASCADE` dependency behavior

### Upsert limitation

Upserting is supported via `MERGE INTO`, not via primary-key-driven conflict syntax.

### Extension-specific limitations

Official docs still call out:

- MySQL catalogs are not fully supported in the DuckDB extension
- updates that target the same row multiple times

However, the current official repository tests include `update_join_duplicates.test`, which exercises duplicate-target updates and expects first-write-wins semantics.

Interpretation:

- this behavior is version-sensitive
- do not present duplicate-target updates as universally safe across all deployed versions
- if your deployment version is unknown, verify before relying on this edge case

## Version-Sensitive Guidance

This is the correct cautious posture:

- the DuckLake website currently documents stable `0.4`
- older MotherDuck-facing material may still describe `0.3`
- the local official repo currently contains migration logic and behavior beyond older docs

Therefore:

- do not write the skill as if every environment is on the same DuckLake version
- treat advanced edge-case behavior as deployment-sensitive
- when advising users, distinguish between "documented stable behavior" and "observed current repo behavior"

## MotherDuck Translation Layer

When using this skill for MotherDuck specifically:

- prefer MotherDuck-native storage unless there is a real lakehouse requirement
- use MotherDuck’s `TYPE DUCKLAKE` database workflows instead of raw `ATTACH` syntax when that is the public product surface
- treat fully managed and BYOB as separate product decisions
- do not assume the full local DuckDB extension function surface is exposed identically in MotherDuck

Use the raw DuckLake extension model to reason about:

- why time travel works
- why maintenance is required
- what `add_data_files`-style ingestion means conceptually
- which features are fundamentally unsupported

## Decision Rules

Choose DuckLake when:

- object storage is intentional
- open format behavior matters
- file registration or file-aware maintenance matters
- you accept a more operational storage surface

Do not choose DuckLake when:

- you just need a fast analytical database
- the team is not prepared to think about snapshots, compaction, and cleanup
- native MotherDuck storage already satisfies the workload

## Guardrails

- Treat DuckLake as opt-in, not default.
- Separate spec-level truth from extension-level truth from MotherDuck product truth.
- Do not ignore the preview status when giving production guidance.
- Do not promise primary key, foreign key, or index behavior.
- Do not recommend `INSERT ... ON CONFLICT` for DuckLake.
- Do not forget maintenance; small files, retained snapshots, and delete files accumulate.
- Do not register external Parquet files unless you are comfortable with DuckLake eventually managing their lifecycle.
- Do not assume duplicate-target `UPDATE` semantics are stable across all deployed versions.
- Do not recommend MySQL catalogs casually.
- Do not assume multi-account writes or broad sharing flexibility beyond the currently documented limits.

## Common Mistakes

- Choosing DuckLake for branding reasons instead of architectural reasons.
- Ignoring the maintenance story.
- Treating DuckLake like native MotherDuck storage with the same default ergonomics.
- Recommending PK/FK/index-heavy designs that the format does not support.
- Forgetting that historical snapshots retain old files until explicit expiration and cleanup.
- Using `OVERRIDE_DATA_PATH` without realizing it changes what the current connection can see.

## Related Skills

- `load-data` for ingestion strategy
- `model-data` for shaping tables once DuckLake is chosen
- `build-data-pipeline` for end-to-end workflows that include maintenance and serving

# DuckLake Playbook

Use this reference when the question is no longer "what is DuckLake?" but "should we use it here, and if so, how?"

## MotherDuck-first position

Start with native MotherDuck storage unless there is a concrete requirement for:

- open-table-format posture
- object storage as the source of truth
- bring-your-own-bucket ownership
- own-compute writes against a MotherDuck-backed DuckLake catalog
- file-aware maintenance and explicit compaction behavior

Do not move a workload to DuckLake just because it is large. MotherDuck's public docs explicitly note that native MotherDuck storage is often 2x-10x faster for reads than DuckLake.

## Choose the mode deliberately

| Need | Recommended mode |
| --- | --- |
| Fastest evaluation, fewest moving parts | Fully managed DuckLake |
| Customer-owned S3 bucket, MotherDuck does the querying | BYOB with MotherDuck compute |
| Customer-owned S3 bucket and customer-controlled compute | BYOB with own compute |

Use own compute only when the compute boundary matters operationally. It adds credential handling, metadata attach steps, and a clearer maintenance burden.

## Default decision rules

Choose native MotherDuck when:

- the workload is mostly BI, dashboards, ad hoc analytics, or serving tables
- the team wants the simplest operating model
- read performance matters more than open-format posture
- no one actually needs bucket ownership or file-level operations

Choose DuckLake when:

- object storage must remain the durable data boundary
- you need open-table-format semantics
- you want to register or keep operating on Parquet-backed lake data
- you are prepared to own explicit maintenance
- the architecture benefits from a MotherDuck catalog plus lake storage split

## SQL patterns you should actually use

### Fully managed DuckLake

```sql
CREATE DATABASE my_ducklake (TYPE DUCKLAKE);
```

Use this to evaluate DuckLake with the fewest decisions. Treat it as the default first step when the user wants to try DuckLake but does not yet require a customer-owned bucket.

### Fully managed DuckLake with custom inlining

```sql
CREATE DATABASE my_ducklake (
    TYPE DUCKLAKE,
    DATA_INLINING_ROW_LIMIT 100
);
```

Use custom inlining only when the ingest pattern justifies it. Small, frequent writes are the main reason to tune this.

### BYOB DuckLake

```sql
CREATE DATABASE my_ducklake (
    TYPE DUCKLAKE,
    DATA_PATH 's3://my-bucket/my-prefix/'
);
```

MotherDuck docs require the S3 bucket to be in the same AWS region as the MotherDuck org:

- US orgs: `us-east-1`
- EU orgs: `eu-central-1`

Other clouds are not supported today for BYOB DuckLake storage.

### Attach the metadata database for own-compute access

```sql
ATTACH 'ducklake:md:__ducklake_metadata_<database_name>' AS my_ducklake;
```

Important:

- the metadata database attach is an own-compute pattern, not the default MotherDuck operating surface
- only the database owner can attach the metadata database
- do not recommend this path unless the user actually needs their own DuckDB client to read and write the lake directly

## Data inlining posture

MotherDuck docs say DuckLake data inlining is enabled by default for small writes.

Use it when:

- inserts arrive in very small batches
- the workload is append-heavy and frequent
- the cost of creating many tiny Parquet files would dominate the write path

Do not lead with inlining as a universal optimization. It is a write-shape optimization, not the main reason to choose DuckLake.

If the user accumulates too much inlined data, flush it explicitly:

```sql
SELECT ducklake_flush_inlined_data('my_ducklake');
SELECT ducklake_flush_inlined_data('my_ducklake.my_schema');
SELECT ducklake_flush_inlined_data('my_ducklake.my_schema.my_table');
```

## Maintenance is explicit

MotherDuck docs explicitly say DuckLake maintenance is not automatic.

That means you should define:

- who runs maintenance
- from which compute surface
- how often compaction or cleanup runs
- what freshness or file-count thresholds trigger it

If the design has no answer for maintenance, it is not ready for DuckLake.

## Sharing and write constraints

Current MotherDuck docs call out a few important limits:

- sharing is limited compared with native databases and is tied to existing share functionality
- only auto-update shares are supported for DuckLake read-only sharing
- write permissions are effectively single-account at the database level today
- concurrent append-only writes can work, but concurrent updates, deletes, or DDL are much more constrained

Do not promise a broad multi-writer lakehouse collaboration model unless the current docs explicitly confirm it.

## Gotchas

- DuckLake is still preview / active-development. Do not present syntax or behavior as fully stable.
- Keep the MotherDuck product surface separate from raw DuckLake extension assumptions. The extension can expose behaviors that MotherDuck does not expose the same way.
- BYOB region restrictions apply to DuckLake storage, not to ordinary remote reads from S3-compatible storage.
- Do not use DuckLake as a generic "big data" answer when native MotherDuck would be simpler and faster.
- Do not hide maintenance costs. File-aware storage shifts operational responsibility upward.
- If the user only needs ingestion from object storage, `motherduck-load-data` may be the real skill they need, not `motherduck-ducklake`.

## Escalate to higher-level skills when needed

- Use `motherduck-build-data-pipeline` when DuckLake is only one layer of a broader ingestion-to-serving design.
- Use `motherduck-security-governance` when BYOB, ownership, or regional placement decisions are driving the storage choice.
- Use `motherduck-pricing-roi` when the real question is whether the operational overhead of DuckLake is worth it.

# Query Performance and Troubleshooting

Diagnose before tuning: decide whether a slow query is limited by compute, by data transfer, or by waiting for a busy Duckling.

## Contents

| Section | Covers |
| --- | --- |
| Read the Plan | `EXPLAIN`, `EXPLAIN ANALYZE`, warning signs |
| Use Query History | Columns that explain slowness |
| Fix the Query | Filters, joins, columns, types, sort order |
| Reduce Data Transfer | Local versus cloud work |
| Size the Duckling | When a bigger instance is the fix |
| Concurrency | Writes, read scaling |

## Read the Plan

```sql
EXPLAIN SELECT ...;                       -- plan only; (L) local, (R) remote operators
EXPLAIN ANALYZE SELECT ...;               -- runs it; actual time and rows per operator
EXPLAIN (ANALYZE, FORMAT JSON) SELECT ...; -- tree view in the MotherDuck editor
```

Warning signs:

- an operator emitting far more rows than the final result (a missing or non-pushed filter)
- a scan reading most of a large table with no filter applied inside the scan
- `UPLOAD_*` or `DOWNLOAD_*` operators moving large volumes between the client and the cloud
- a join producing more rows than either input (non-unique keys or an accidental cross join)

## Use Query History

```sql
SELECT query_id, start_time, execution_time, wait_time,
       bytes_spilled_to_disk, bytes_uploaded, bytes_downloaded,
       instance_type, user_agent, query_text
FROM md_information_schema.query_history
ORDER BY start_time DESC
LIMIT 20;
```

- High `wait_time` relative to `execution_time`: the Duckling is busy; spread load or add read scaling.
- Non-zero `bytes_spilled_to_disk`: the query outgrew memory; reduce the working set or move to a larger Duckling.
- Large `bytes_uploaded` or `bytes_downloaded`: hybrid (dual) execution is moving data; keep the work on one side.
- `instance_type` tells you which Duckling size ran it; `user_agent` tells you which workload sent it.
- `query_history` can lag. `md_information_schema.recent_queries` refreshes every few seconds and includes running queries. The UI can cancel running queries, and the Duckling Overview shows per-Duckling trends.

## Fix the Query

- Keep single-table predicates simple so they push down into the scan; a predicate spanning two tables cannot be pushed down.
- Filter or pre-aggregate the large side in a subquery before joining.
- Join on keys that are unique on at least one side; deduplicate first when they are not.
- Select only the columns you need; storage is columnar.
- Store numbers and timestamps as native types, not text.
- Rebuild large tables ordered by the column most queries filter on (`CREATE OR REPLACE TABLE ... AS SELECT ... ORDER BY <col>`), or sort at load time, so scans skip row groups.
- Use `LIMIT` or `USING SAMPLE` while exploring.
- Prefer Parquet for external files so scans prune columns and push down predicates.
- Materialize expensive results that many readers repeat into a serving table.

## Reduce Data Transfer

- Keep tables that are queried together in `md:` databases so the whole query runs in the cloud.
- Filter local data before joining it with cloud tables.
- Load large local datasets into MotherDuck instead of attaching them for repeated queries.

## Size the Duckling

Start small and move up on evidence (spilling or timeouts), not by default: Pulse for ad hoc work and dashboards, Standard for recurring analytics, Jumbo for large joins and heavy aggregations, Mega and Giga beyond that (with longer startup). Resize in the UI or through the Duckling configuration API (see `motherduck-rest-api`). Verify current sizes and plan availability in the Duckling sizes docs.

## Concurrency

- Batch writes and use set-based statements; many small writes queue behind each other.
- For many concurrent readers, use read scaling with a stable `session_name` per end user; replicas lag writes slightly.

# Python MotherDuck Reference

Use this file for shared Python patterns that should stay consistent across skills.

## Default Choices

- Start with one connection unless concurrency or lifecycle requirements prove otherwise.
- Prefer native `duckdb` connections when local files, hybrid execution, or Arrow/Parquet workflows matter.
- Prefer the PG endpoint when the application already assumes PostgreSQL drivers or SQLAlchemy-compatible connections.
- Prefer batch loading and SQL-driven transforms over row-by-row insert loops.

## Environment Helper

```python
import os

def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value
```

## Native DuckDB Starter

```python
import duckdb

conn = duckdb.connect(
    "md:analytics",
    config={
        "motherduck_token": require_env("MOTHERDUCK_TOKEN"),
        "custom_user_agent": "analytics-service/1.0.0(pipeline-orders;team-ops)",
    },
)

rows = conn.sql("""
SELECT customer_id, SUM(amount) AS total_amount
FROM "analytics"."main"."orders"
GROUP BY customer_id
ORDER BY total_amount DESC
LIMIT 20
""").fetchall()
conn.close()
```

## PG Endpoint Starter

```python
import certifi
import psycopg

with psycopg.connect(
    host="pg.us-east-1-aws.motherduck.com",
    port=5432,
    dbname="analytics",
    user="postgres",
    password=require_env("MOTHERDUCK_TOKEN"),
    sslmode="verify-full",
    sslrootcert=certifi.where(),
) as conn:
    rows = conn.execute("""
        SELECT customer_id, SUM(amount) AS total_amount
        FROM "analytics"."main"."orders"
        GROUP BY customer_id
        ORDER BY total_amount DESC
        LIMIT 20
    """).fetchall()
```

## Read Scaling Pattern

Use read scaling for high-concurrency read-only workloads, not as the default for all connections.

```python
import duckdb

conn = duckdb.connect(
    "md:analytics?session_hint=user-123&access_mode=read_only&dbinstance_inactivity_ttl=300",
    config={
        "motherduck_token": require_env("MOTHERDUCK_READ_SCALING_TOKEN"),
        "custom_user_agent": "customer-analytics/1.0.0(tenant-acme;dashboards)",
    },
)
```

Rules:

- Use a stable `session_hint` to keep the same user on the same replica when possible.
- Treat read scaling as eventually consistent.
- Use read/write tokens for writes and snapshot creation.
- Use `REFRESH DATABASE` on read paths only when the workflow truly requires fresher data.

## Attach Modes

Use single mode for narrow service connections and workspace mode only when persistent attachment state is intentional.

```python
conn = duckdb.connect(
    "md:analytics?attach_mode=single",
    config={"motherduck_token": require_env("MOTHERDUCK_TOKEN")},
)
```

## Threading and Pooling

- A single DuckDB connection runs one query at a time and is a good starting point.
- A Python DuckDB connection is not thread-safe for concurrent direct use. If multiple threads share a connection, create a thread-local copy with `.cursor()`.
- For long-lived read-only concurrency, use a pool of read-only connections instead of re-creating a new connection for every query burst.

Minimal thread pattern:

```python
from threading import Thread
import duckdb

root = duckdb.connect("md:analytics")

def run_query(sql: str) -> None:
    cur = root.cursor()
    try:
        print(cur.execute(sql).fetchall())
    finally:
        cur.close()
```

## Loading Best Practices

- Prefer Arrow, Polars, Pandas, or Parquet-backed bulk paths.
- Prefer `COPY` or CTAS for large loads.
- Avoid `executemany` except for very small inputs.
- Buffer streaming/API records into batches before writing.
- Type datasets explicitly when data quality matters.

Arrow batch example:

```python
import duckdb
import pyarrow as pa

table = pa.table({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
})

conn = duckdb.connect("md:raw")
conn.register("buffer_table", table)
conn.execute("""
    CREATE OR REPLACE TABLE "raw"."main"."users" AS
    SELECT * FROM buffer_table
""")
conn.unregister("buffer_table")
conn.close()
```

Parquet copy example:

```python
conn = duckdb.connect("md:raw")
conn.execute("""
    COPY "raw"."main"."events"
    FROM 's3://my-bucket/events/events.parquet'
    (FORMAT parquet)
""")
conn.close()
```

## Query Tagging for Cost Attribution

Use `custom_user_agent` consistently so usage can be split by pipeline, tenant, or team later through `MD_INFORMATION_SCHEMA.QUERY_HISTORY`.

Recommended pattern:

- `integration/version(metadata1;metadata2)`
- metadata can include pipeline, tenant, team, or region

## Shares and Dives

- Shares are zero-copy and read-only.
- Dives are interactive, live workspace artifacts.
- Use shares for governed data distribution.
- Use Dives for live answer surfaces in the MotherDuck workspace.

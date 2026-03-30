---
name: load-data
description: Load and ingest data into MotherDuck from files, cloud storage, HTTP, or other databases. Use when importing CSV, Parquet, JSON, Excel files or setting up data ingestion from S3, GCS, Azure, or external sources.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: workflow
  language_focus: "typescript|javascript|python"
  depends_on:
    - connect
    - query
    - explore
---

# Load Data into MotherDuck

Use this skill when importing data into MotherDuck from local files, cloud storage (S3, GCS, Azure), HTTP URLs, or external databases. Start here before building queries or models on new data.

For reusable language patterns, see `references/typescript.md` and `references/python.md`.

## Source Of Truth

- Prefer current MotherDuck loading, connection, and cloud-storage docs first.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep guidance aligned with MotherDuck's documented posture:
  - batch over streaming
  - Parquet over CSV when you control the format
  - dataframe or `COPY`-style bulk paths over row-by-row inserts
  - native storage first unless DuckLake or BYOB requirements are explicit

## Prerequisites

- MotherDuck connection established (see `connect` skill)
- Target database created (see `explore` skill to discover existing databases)
- For cloud storage: appropriate credentials configured (see `references/INGESTION_PATTERNS.md`)

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** for most ingestion work. It is the default language for:
  - ETL scripts
  - dlt or notebook-driven ingestion
  - batch jobs
  - file preparation and validation
- Prefer **TypeScript/Javascript** when ingestion is part of:
  - backend product flows
  - event or API ingestion services
  - internal admin tools
- If the user needs both:
  - use Python for heavy ingest and data shaping
  - use TypeScript/Javascript for service orchestration, product integration, and user-facing control paths

## TypeScript/Javascript Starter

```ts
import pg from "pg";

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "raw",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

await client.connect();
await client.query(`
  CREATE OR REPLACE TABLE "raw"."main"."events" AS
  SELECT * FROM read_parquet('s3://my-bucket/events/*.parquet')
`);
await client.end();
```

## Python Starter

```python
import duckdb

conn = duckdb.connect("md:raw")
conn.sql("""
CREATE OR REPLACE TABLE "raw"."main"."events" AS
SELECT * FROM read_parquet('s3://my-bucket/events/*.parquet')
""")
conn.close()
```

## Opinionated Guidance

- **Prefer Parquet over CSV.** Parquet is columnar, compressed, and preserves types. CSV requires type inference, delimiter detection, and encoding guesses. When you control the source format, always choose Parquet.
- **Use `CREATE TABLE AS SELECT` (CTAS) for initial loads.** It infers the schema and creates the table in one step. Do not create an empty table then INSERT unless you need explicit type control.
- **Use `INSERT INTO ... SELECT` for appending** new data to an existing table.
- **Always preview data before loading.** Run `SELECT ... LIMIT 10` on the source to verify structure, types, and data quality before creating a table.
- **Use fully qualified table names** for every target table: `"database"."schema"."table"`.
- **Treat MotherDuck as batch-oriented for ingestion.** Buffer API or event traffic and write in batches instead of streaming row-by-row directly into analytical tables.
- **Prefer Arrow/dataframe bulk paths or `COPY`** over `executemany`. Row-by-row inserts are the slow path and should be reserved for tiny inputs only.
- **Keep transactions bounded.** Size batches so the write finishes comfortably instead of trying to push an unbounded single transaction.
- **Keep source storage region close to the target MotherDuck region** when you control object storage placement.

## Ingestion Defaults

Use these defaults unless the workload proves they are wrong:

1. Land data in a raw table with minimal transformation.
2. Use Parquet, Arrow, or staged cloud files for bulk movement.
3. Batch API or event ingestion in memory or queues before writing.
4. Validate row counts and core aggregates immediately after each load.
5. Move into curated staging or analytics tables only after the raw landing succeeds.

---

## Quick Start

```sql
-- Load CSV from a URL
CREATE TABLE "my_db"."main"."sales" AS
SELECT * FROM read_csv('https://example.com/sales.csv');

-- Load Parquet from S3
CREATE TABLE "my_db"."main"."events" AS
SELECT * FROM read_parquet('s3://my-bucket/data/events.parquet');
```

---

## Loading by Format

### CSV

```sql
-- Basic CSV load with auto-detection
CREATE TABLE "my_db"."main"."customers" AS
SELECT * FROM read_csv('https://example.com/customers.csv');

-- CSV with explicit options
CREATE TABLE "my_db"."main"."transactions" AS
SELECT * FROM read_csv('s3://bucket/transactions.csv',
    delim = '|',
    header = true,
    dateformat = '%m/%d/%Y',
    null_padding = true,
    auto_detect = true
);

-- CSV with explicit column types
CREATE TABLE "my_db"."main"."products" AS
SELECT * FROM read_csv('data.csv',
    columns = {
        'id': 'INTEGER',
        'name': 'VARCHAR',
        'price': 'DECIMAL(10,2)',
        'created_at': 'TIMESTAMP'
    }
);
```

### Parquet (Preferred)

Parquet is the fastest format. It preserves types, supports predicate pushdown, and compresses well.

```sql
-- Single file
CREATE TABLE "my_db"."main"."orders" AS
SELECT * FROM read_parquet('s3://bucket/orders.parquet');

-- Multiple files with glob
CREATE TABLE "my_db"."main"."logs" AS
SELECT * FROM read_parquet('s3://bucket/logs/year=2024/**/*.parquet');

-- With hive partitioning
CREATE TABLE "my_db"."main"."partitioned_data" AS
SELECT * FROM read_parquet('s3://bucket/data/**/*.parquet',
    hive_partitioning = true
);
```

### JSON

```sql
-- Auto-detected JSON
CREATE TABLE "my_db"."main"."api_responses" AS
SELECT * FROM read_json('https://api.example.com/data.json');

-- Newline-delimited JSON (NDJSON)
CREATE TABLE "my_db"."main"."events" AS
SELECT * FROM read_json('s3://bucket/events.ndjson',
    format = 'newline_delimited'
);

-- JSON with explicit schema
CREATE TABLE "my_db"."main"."records" AS
SELECT * FROM read_json('data.json',
    columns = {'id': 'INTEGER', 'payload': 'JSON', 'timestamp': 'TIMESTAMP'}
);
```

### Excel

```sql
-- Load first sheet (default)
CREATE TABLE "my_db"."main"."budget" AS
SELECT * FROM read_excel('s3://bucket/budget.xlsx');

-- Load a specific sheet by name
CREATE TABLE "my_db"."main"."q4_forecast" AS
SELECT * FROM read_excel('s3://bucket/budget.xlsx', sheet = 'Q4 Forecast');
```

---

## Loading from Cloud Storage

```sql
-- S3
SELECT * FROM read_parquet('s3://bucket/path/*.parquet');

-- GCS
SELECT * FROM read_parquet('gs://bucket/path/*.parquet');

-- Azure Blob Storage
SELECT * FROM read_parquet('azure://container/path/*.parquet');

-- HTTPS
SELECT * FROM read_parquet('https://host/path/file.parquet');
```

### Multi-File Loads with Glob Patterns

```sql
-- All Parquet files in a directory
CREATE TABLE "my_db"."main"."all_events" AS
SELECT * FROM read_parquet('s3://bucket/events/*.parquet');

-- Recursive glob across subdirectories
CREATE TABLE "my_db"."main"."all_logs" AS
SELECT * FROM read_parquet('s3://bucket/logs/**/*.parquet');

-- Hive-partitioned data with partition column extraction
CREATE TABLE "my_db"."main"."partitioned" AS
SELECT * FROM read_parquet('s3://bucket/data/year=2024/**/*.parquet',
    hive_partitioning = true
);

-- Include source filename as a column
CREATE TABLE "my_db"."main"."with_source" AS
SELECT * FROM read_parquet('s3://bucket/data/*.parquet', filename = true);
```

---

## Loading Patterns

### Full Load (CTAS)

```sql
CREATE TABLE "my_db"."main"."sales" AS
SELECT * FROM read_parquet('s3://bucket/sales.parquet');
```

### Schema-First Load

Use when you need strict type control or want to reject malformed rows.

```sql
CREATE TABLE "my_db"."main"."orders" (
    order_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    amount DECIMAL(12, 2),
    order_date DATE,
    status VARCHAR
);

INSERT INTO "my_db"."main"."orders"
SELECT * FROM read_csv('s3://bucket/orders.csv');
```

### Append

```sql
INSERT INTO "my_db"."main"."orders"
SELECT * FROM read_csv('s3://bucket/new_orders_march.csv');
```

### Python Bulk Insert via Arrow

Use this over `executemany` when data already exists in memory.

```python
import duckdb
import pyarrow as pa

table = pa.table({
    "id": [1, 2, 3],
    "email": ["a@example.com", "b@example.com", "c@example.com"],
})

conn = duckdb.connect("md:raw")
conn.register("incoming_batch", table)
conn.execute("""
CREATE OR REPLACE TABLE "raw"."main"."users" AS
SELECT * FROM incoming_batch
""")
conn.unregister("incoming_batch")
conn.close()
```

### Python COPY Pattern

Use this for staged Parquet files or object storage sources.

```python
import duckdb

conn = duckdb.connect("md:raw")
conn.execute("""
COPY "raw"."main"."events"
FROM 's3://my-bucket/events/events.parquet'
(FORMAT parquet)
""")
conn.close()
```

### Replace

```sql
CREATE OR REPLACE TABLE "my_db"."main"."daily_snapshot" AS
SELECT * FROM read_parquet('s3://bucket/snapshot/latest.parquet');
```

### Selective Columns

```sql
CREATE TABLE "my_db"."main"."order_summary" AS
SELECT order_id, customer_id, amount, order_date
FROM read_parquet('s3://bucket/orders_full.parquet');
```

### Filtered Load

```sql
CREATE TABLE "my_db"."main"."recent_orders" AS
SELECT * FROM read_parquet('s3://bucket/orders.parquet')
WHERE order_date >= '2024-01-01';
```

---

## Data Validation Before Loading

Always validate source data before creating tables.

```sql
-- Preview rows
SELECT * FROM read_csv('s3://bucket/data.csv') LIMIT 10;

-- Check row count
SELECT count(*) FROM read_csv('s3://bucket/data.csv');

-- Inspect inferred schema
DESCRIBE SELECT * FROM read_csv('s3://bucket/data.csv');

-- Check for nulls and data quality
SELECT
    count(*) AS total_rows,
    count(*) FILTER (WHERE customer_id IS NULL) AS null_customer_ids,
    count(*) FILTER (WHERE amount IS NULL) AS null_amounts,
    min(order_date) AS earliest_date,
    max(order_date) AS latest_date
FROM read_csv('s3://bucket/data.csv');
```

---

## PG Endpoint Limitation

The MotherDuck PG endpoint does NOT support local file access. `read_csv('/local/path/file.csv')` fails because queries execute on the MotherDuck server, not your local machine.

To load local files:

1. **Upload to cloud storage first** (S3, GCS, Azure), then load via URL.
2. **Use the native DuckDB API** (`md:` protocol) for local file access.
3. **Use the MotherDuck web UI** drag-and-drop upload for ad-hoc loads.

```python
# Native DuckDB API -- supports local file access
import duckdb
conn = duckdb.connect("md:my_database")
conn.sql("""
    CREATE TABLE "my_database"."main"."local_data" AS
    SELECT * FROM read_csv('/path/to/local/file.csv')
""")
conn.close()
```

---

## ETL Tool Integrations

For ongoing replication from production databases, use a managed ETL tool instead of manual file loads.

| Tool | Best For | Sources |
|------|----------|---------|
| **Fivetran** | Enterprise, managed connectors | PostgreSQL, MySQL, Salesforce, Stripe, 300+ |
| **Airbyte** | Open-source, self-hosted option | PostgreSQL, MySQL, MongoDB, APIs, 350+ |
| **Estuary** | Real-time CDC | PostgreSQL, MySQL, MongoDB |
| **dlt** | Python-native, lightweight | APIs, databases, files |
| **Streamkap** | Low-latency CDC | PostgreSQL, MySQL, MongoDB |

These tools handle schema changes, incremental syncs, and CDC automatically. Prefer them over manual export/import for any source that updates continuously.

---

## Key Rules

- **Prefer Parquet** for best performance. Use CSV only when Parquet is not available.
- **Always preview data before loading** with `SELECT ... LIMIT 10` and `DESCRIBE`.
- **Use fully qualified table names** for every target: `"database"."schema"."table"`.
- **Test with SELECT before CREATE TABLE AS.** Verify data looks correct before committing.
- **Use CTAS for initial loads** and `INSERT INTO ... SELECT` for appending.
- **Use `CREATE OR REPLACE TABLE`** for full refresh -- never DROP then CREATE (non-atomic).
- **Batch loads over streaming.** MotherDuck is optimized for batch analytics, not row-level inserts.
- **Avoid `executemany` except for tiny inputs.** Prefer Arrow/dataframe registration, staged Parquet, or `COPY`.
- **Configure credentials before loading** from private cloud storage (see `references/INGESTION_PATTERNS.md`).

---

## Common Mistakes

### Loading via PG endpoint and expecting local file access

The PG endpoint runs queries on the MotherDuck server. Local paths like `/tmp/data.csv` do not exist there. Upload to cloud storage or use the native DuckDB API.

### Loading CSV without checking delimiter or encoding

```sql
-- Wrong: assumes defaults, breaks on pipe-delimited files
CREATE TABLE t AS SELECT * FROM read_csv('data.csv');

-- Right: preview first, then specify options
SELECT * FROM read_csv('data.csv') LIMIT 5;
CREATE TABLE t AS SELECT * FROM read_csv('data.csv', delim = '|');
```

### Not previewing data before creating tables

Skipping validation creates tables with wrong types, garbled data, or missing columns. Always run `DESCRIBE` and `LIMIT 10` before CTAS.

### Using INSERT for initial loads instead of CTAS

```sql
-- Slower: requires schema definition + separate insert
CREATE TABLE t (id INT, name VARCHAR, amount DECIMAL(10,2));
INSERT INTO t SELECT * FROM read_parquet('data.parquet');

-- Better: CTAS does both in one step
CREATE TABLE t AS SELECT * FROM read_parquet('data.parquet');
```

### Forgetting hive_partitioning for partitioned datasets

```sql
-- Wrong: partition columns (year, month) missing from result
SELECT * FROM read_parquet('s3://bucket/data/**/*.parquet') LIMIT 5;

-- Right: partition columns extracted into regular columns
SELECT * FROM read_parquet('s3://bucket/data/**/*.parquet',
    hive_partitioning = true) LIMIT 5;
```

### Loading all columns when only a few are needed

```sql
-- Wasteful: loads 50 columns when you only need 3
CREATE TABLE t AS SELECT * FROM read_parquet('wide_table.parquet');

-- Better: select only what you need
CREATE TABLE t AS SELECT id, name, revenue FROM read_parquet('wide_table.parquet');
```

---

## Related Skills

- `connect` -- Establish a MotherDuck connection
- `query` -- Execute DuckDB SQL queries against MotherDuck databases
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup
- `explore` -- Discover databases, tables, columns, and data shares
- `model-data` -- Transform and model data within MotherDuck

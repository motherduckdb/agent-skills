# Ingestion Patterns Reference

Advanced reference for data ingestion into MotherDuck. Covers format-specific options, cloud authentication, table formats (Delta Lake, Iceberg), large dataset strategies, and database replication patterns.

---

## Choose the client path first

Before choosing a file format or SQL shape, choose the ingestion surface:

- **Node.js with `@duckdb/node-api`** is a native DuckDB client path
- **Python with `duckdb`** is a native DuckDB client path
- **Node.js with `pg`**, **Python with `psycopg`**, or any other PostgreSQL driver talking to MotherDuck is a **Postgres-endpoint thin client path**

That distinction matters more than the programming language itself.

### Native DuckDB client paths

Treat these as full DuckDB-capable ingestion surfaces.

Use them when you need:

- local-file `COPY`
- loading from local DuckDB files
- dataframe or Arrow registration
- `CREATE SECRET`
- extension-backed reads
- local execution behavior such as `MD_RUN = LOCAL`

In practice:

- Node.js `@duckdb/node-api` and Python `duckdb` can use the richer DuckDB ingestion patterns
- these paths are the default when the data starts on local disk, in memory, or in a local DuckDB workflow

### Postgres-endpoint thin client paths

Treat these as SQL submission paths, not as full DuckDB clients.

Use them when:

- the environment already speaks PostgreSQL
- the source files already live in object storage or HTTPS
- the app only needs to send SQL to MotherDuck

Do not expect the PG endpoint to behave like a native DuckDB client. It is best for:

- `CREATE TABLE AS SELECT` from remote files with `MD_RUN = REMOTE`
- `INSERT INTO ... SELECT` from remote files with `MD_RUN = REMOTE`
- explicit multi-row `INSERT` batches when the source exists only in application memory

Do not use the PG endpoint for:

- local-file `COPY`
- `CREATE SECRET`
- local DuckDB attachments
- extension install/load workflows
- local execution paths

### Best-practice decision guide

| Situation | Best path |
| --- | --- |
| Local file on disk | Native DuckDB client |
| Dataframe or Arrow buffer in memory | Native DuckDB client |
| Existing Node.js service already built on PostgreSQL drivers | PG endpoint, but prefer remote-read CTAS or batched multi-row inserts |
| Existing Python service already built on PostgreSQL drivers | PG endpoint, but prefer remote-read CTAS or batched multi-row inserts |
| Files already in S3, GCS, R2, Azure, or HTTPS | PG endpoint or native DuckDB client; default to remote-read SQL |
| Need `CREATE SECRET` before loading | Native DuckDB client first, then PG endpoint is optional |

### SQL patterns for the PG endpoint

Preferred remote-read pattern:

```sql
CREATE OR REPLACE TABLE "my_db"."ingest"."orders_stage" AS
SELECT *
FROM read_parquet(
    's3://bucket/orders/*.parquet',
    MD_RUN = REMOTE
);
```

Preferred publish-after-stage pattern:

```sql
CREATE OR REPLACE TABLE "my_db"."main"."orders_curated" AS
SELECT
    order_id,
    customer_id,
    order_ts,
    total_amount
FROM "my_db"."ingest"."orders_stage";
```

If the source exists only in application memory, use larger multi-row batches instead of one-row-at-a-time inserts:

```sql
INSERT INTO "my_db"."main"."orders_batch" VALUES
  (1, 'a', 10.0),
  (2, 'b', 20.0),
  (3, 'c', 30.0);
```

For the PG endpoint, think in classic thin-client terms:

- fewer round trips
- larger batches
- append into staging first
- transactions that stay comfortably bounded

If you find yourself trying to simulate a local DuckDB ingestion workflow over the PG wire, switch to a native DuckDB client path instead.

---

## CSV Advanced Options

Use these parameters when `read_csv()` auto-detection fails or produces incorrect results.

```sql
SELECT * FROM read_csv('file.csv',
    -- Delimiters and quoting
    delim = ',',              -- Column delimiter (default: auto-detected)
    quote = '"',              -- Quote character (default: '"')
    escape = '"',             -- Escape character inside quotes (default: '"')

    -- Header and row handling
    header = true,            -- First row is column names (default: auto-detected)
    skip = 0,                 -- Number of rows to skip at the start
    null_padding = true,      -- Pad rows with fewer columns with NULLs
    ignore_errors = false,    -- Skip rows that fail to parse

    -- Type inference
    auto_detect = true,       -- Auto-detect types (default: true)
    all_varchar = false,      -- Read all columns as VARCHAR (disable type inference)
    sample_size = 20480,      -- Number of rows to sample for type inference

    -- Explicit column definitions
    columns = {               -- Override auto-detected types
        'id': 'INTEGER',
        'name': 'VARCHAR',
        'amount': 'DECIMAL(10,2)'
    },

    -- Date and time formats
    dateformat = '%Y-%m-%d',
    timestampformat = '%Y-%m-%d %H:%M:%S',

    -- Multi-file options
    filename = true,          -- Add source filename as a column
    union_by_name = true      -- Match columns by name across files (not position)
);
```

### Common CSV Scenarios

```sql
-- Pipe-delimited
SELECT * FROM read_csv('data.txt', delim = '|') LIMIT 10;

-- Tab-delimited (TSV)
SELECT * FROM read_csv('data.tsv', delim = '\t') LIMIT 10;

-- No header row
SELECT * FROM read_csv('data.csv', header = false) LIMIT 10;

-- Skip metadata rows at the top of the file
SELECT * FROM read_csv('report.csv', skip = 3, header = true) LIMIT 10;

-- Inconsistent column counts (ragged CSV)
SELECT * FROM read_csv('ragged.csv', null_padding = true) LIMIT 10;

-- Multiple CSV files with different column orders
CREATE TABLE "my_db"."main"."combined" AS
SELECT * FROM read_csv('s3://bucket/exports/*.csv', union_by_name = true);

-- Custom date format
CREATE TABLE "my_db"."main"."dated" AS
SELECT * FROM read_csv('data.csv', dateformat = '%d/%m/%Y');
```

### Force All Columns to VARCHAR for Manual Casting

When auto-detection produces wrong types, load everything as strings and cast manually:

```sql
CREATE TABLE "my_db"."main"."raw_import" AS
SELECT * FROM read_csv('messy_data.csv', all_varchar = true);

CREATE TABLE "my_db"."main"."clean_import" AS
SELECT
    CAST(id AS INTEGER) AS id,
    name,
    CAST(amount AS DECIMAL(10,2)) AS amount,
    strptime(date_str, '%m/%d/%Y')::DATE AS order_date
FROM "my_db"."main"."raw_import";
```

---

## Parquet Advanced Options

```sql
SELECT * FROM read_parquet('file.parquet',
    hive_partitioning = true,   -- Extract partition keys from directory structure
    filename = true,            -- Add source filename as a column
    union_by_name = true        -- Match columns by name across files
);
```

### Hive-Partitioned Datasets

Hive partitioning encodes column values in the directory path (e.g., `year=2024/month=01/data.parquet`).

```sql
-- Directory structure:
-- s3://bucket/data/year=2023/month=01/part-001.parquet
-- s3://bucket/data/year=2024/month=01/part-001.parquet

CREATE TABLE "my_db"."main"."partitioned_data" AS
SELECT * FROM read_parquet('s3://bucket/data/**/*.parquet',
    hive_partitioning = true
);
-- Result includes 'year' and 'month' as regular INTEGER columns
```

### Combining Files with Different Schemas

When source files have evolved schemas (added columns over time):

```sql
CREATE TABLE "my_db"."main"."merged" AS
SELECT * FROM read_parquet('s3://bucket/exports/*.parquet',
    union_by_name = true
);
-- Missing columns are filled with NULL
```

---

## JSON Advanced Options

```sql
SELECT * FROM read_json('file.json',
    format = 'auto',           -- 'auto', 'array', 'unstructured', 'newline_delimited'
    auto_detect = true,        -- Auto-detect schema (default: true)
    columns = {                -- Override auto-detected types
        'id': 'INTEGER',
        'payload': 'JSON',
        'tags': 'VARCHAR[]'
    },
    maximum_depth = -1,        -- Max nesting depth (-1 = unlimited)
    sample_size = 20480,       -- Rows to sample for schema inference
    filename = true,           -- Add source filename as a column
    union_by_name = true       -- Match columns by name across files
);
```

### JSON Format Types

```sql
-- Standard JSON array: [{"id": 1}, {"id": 2}]
SELECT * FROM read_json('users.json', format = 'array');

-- Newline-delimited JSON (NDJSON): one JSON object per line
SELECT * FROM read_json('events.ndjson', format = 'newline_delimited');
```

### Deeply Nested JSON

Load as raw JSON and extract fields with DuckDB JSON functions:

```sql
CREATE TABLE "my_db"."main"."raw_api" AS
SELECT * FROM read_json('api_response.json', maximum_depth = 2);

SELECT
    data->>'$.user.id' AS user_id,
    data->>'$.user.name' AS user_name,
    data->'$.user.addresses' AS addresses
FROM "my_db"."main"."raw_api";
```

---

## Cloud Storage Authentication

### S3

**Option 1: Environment Variables (Recommended)**

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
export AWS_SESSION_TOKEN="..."  # Optional: for temporary credentials
```

**Option 2: CREATE SECRET**

```sql
CREATE SECRET my_s3_secret (
    TYPE S3,
    KEY_ID 'AKIA...',
    SECRET '...',
    REGION 'us-east-1'
);
```

**Option 3: IAM Role (EC2 / ECS / Lambda)**

DuckDB uses the instance metadata service automatically when an IAM role is attached. No credentials needed.

### GCS

**Option 1: Service Account Key**

```sql
CREATE SECRET my_gcs_secret (
    TYPE GCS,
    KEY_ID 'GOOG...',
    SECRET '...'
);
```

**Option 2: gcloud CLI (Local Development)**

```bash
gcloud auth application-default login
```

**Option 3: Workload Identity (GKE)** -- automatic, no configuration needed.

### Azure Blob Storage

**Option 1: Connection String**

```sql
CREATE SECRET my_azure_secret (
    TYPE AZURE,
    CONNECTION_STRING 'DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net'
);
```

**Option 2: Service Principal**

```sql
CREATE SECRET my_azure_secret (
    TYPE AZURE,
    PROVIDER CREDENTIAL_CHAIN,
    ACCOUNT_NAME 'mystorageaccount'
);
```

**Option 3: Environment Variables**

```bash
export AZURE_STORAGE_ACCOUNT="mystorageaccount"
export AZURE_STORAGE_KEY="..."
```

### Public Buckets

No credentials needed:

```sql
SELECT * FROM read_parquet('s3://public-bucket/data.parquet') LIMIT 10;
SELECT * FROM read_parquet('https://data.example.com/public/data.parquet') LIMIT 10;
```

---

## Delta Lake Ingestion

Requires the pre-installed `delta` extension.

```sql
CREATE TABLE "my_db"."main"."delta_data" AS
SELECT * FROM delta_scan('s3://bucket/delta-table/');

-- Preview and filter
SELECT * FROM delta_scan('s3://bucket/delta-table/') LIMIT 10;
DESCRIBE SELECT * FROM delta_scan('s3://bucket/delta-table/');

CREATE TABLE "my_db"."main"."recent_delta" AS
SELECT * FROM delta_scan('s3://bucket/delta-table/')
WHERE created_at >= '2024-01-01';
```

---

## Iceberg Ingestion

Requires the pre-installed `iceberg` extension.

```sql
CREATE TABLE "my_db"."main"."iceberg_data" AS
SELECT * FROM iceberg_scan('s3://bucket/iceberg-table/');

SELECT * FROM iceberg_scan('s3://bucket/iceberg-table/') LIMIT 10;

CREATE TABLE "my_db"."main"."iceberg_subset" AS
SELECT user_id, event_type, event_time
FROM iceberg_scan('s3://bucket/iceberg-table/');
```

---

## Large Dataset Strategies

### Filter During Load

```sql
CREATE TABLE "my_db"."main"."orders_2024" AS
SELECT * FROM read_parquet('s3://bucket/orders/**/*.parquet',
    hive_partitioning = true
)
WHERE year = 2024;
```

### Partition Load by Date

```sql
CREATE TABLE "my_db"."main"."q1_2024" AS
SELECT * FROM read_parquet('s3://bucket/data/year=2024/month=01/*.parquet',
    hive_partitioning = true);

INSERT INTO "my_db"."main"."q1_2024"
SELECT * FROM read_parquet('s3://bucket/data/year=2024/month=02/*.parquet',
    hive_partitioning = true);
```

### Select Only Needed Columns

Parquet's columnar format means unselected columns are never read from disk:

```sql
CREATE TABLE "my_db"."main"."narrow" AS
SELECT user_id, event_type, timestamp, revenue
FROM read_parquet('s3://bucket/wide_events.parquet');
```

### Use COPY for Bulk Operations

```sql
COPY "my_db"."main"."orders" FROM 's3://bucket/orders.csv' (FORMAT CSV, HEADER true);
COPY "my_db"."main"."events" FROM 's3://bucket/events.parquet' (FORMAT PARQUET);
```

### COPY TO (Export)

```sql
COPY "my_db"."main"."orders" TO 's3://bucket/export/orders.parquet' (FORMAT PARQUET);

COPY (
    SELECT customer_id, SUM(amount) AS total
    FROM "my_db"."main"."orders"
    GROUP BY customer_id
) TO 's3://bucket/export/totals.parquet' (FORMAT PARQUET);

COPY "my_db"."main"."events" TO 's3://bucket/export/events' (
    FORMAT PARQUET,
    PARTITION_BY (year, month)
);
```

---

## Database Replication Patterns

### PostgreSQL to MotherDuck

**Option 1: Managed ETL (Recommended).** Use Fivetran, Airbyte, or Estuary for continuous CDC replication. These handle schema changes, soft deletes, and incremental updates automatically.

**Option 2: pg_dump + Load (One-time or Periodic)**

```bash
psql -d mydatabase -c "COPY orders TO STDOUT WITH CSV HEADER" > orders.csv
```

```sql
CREATE TABLE "my_db"."main"."orders" AS
SELECT * FROM read_csv('s3://staging-bucket/orders.csv');
```

**Option 3: Direct PostgreSQL Attach (native DuckDB API only)**

```sql
ATTACH 'dbname=mydb user=myuser host=pg-host.example.com' AS pg_source (TYPE POSTGRES);

CREATE TABLE "my_db"."main"."orders" AS
SELECT * FROM pg_source.public.orders;
```

Note: The `postgres` extension is not pre-installed on MotherDuck. This works only via a local DuckDB instance.

### MySQL to MotherDuck

**Option 1: Managed ETL.** Use Fivetran, Airbyte, or Streamkap.

**Option 2: mysqldump + Load**

```bash
mysql -u user -p -e "SELECT * FROM orders" --batch --raw mydatabase > orders.tsv
```

```sql
CREATE TABLE "my_db"."main"."orders" AS
SELECT * FROM read_csv('s3://staging-bucket/orders.tsv', delim = '\t');
```

**Option 3: Direct MySQL Attach (native DuckDB API only)**

```sql
ATTACH 'host=mysql-host user=myuser password=mypass database=mydb' AS mysql_src (TYPE MYSQL);
CREATE TABLE "my_db"."main"."customers" AS
SELECT * FROM mysql_src.customers;
```

Note: The `mysql` extension is not pre-installed on MotherDuck. This works only via a local DuckDB instance.

### MongoDB to MotherDuck

Use Airbyte, Estuary, or Streamkap for MongoDB CDC. There is no direct DuckDB connector for MongoDB.

### API Sources to MotherDuck

Use **dlt** (data load tool) for REST API ingestion:

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="api_ingest",
    destination="motherduck",
    dataset_name="api_data"
)

data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
pipeline.run(data, table_name="users")
```

---

## Troubleshooting

### "No files found" error

Verify the path and credentials. S3 paths are case-sensitive.

```sql
SELECT * FROM read_parquet('s3://bucket/path/*.parquet') LIMIT 1;
```

### Type mismatch on INSERT

Compare source and target schemas, then cast explicitly:

```sql
DESCRIBE SELECT * FROM read_csv('source.csv');
DESCRIBE SELECT * FROM "my_db"."main"."target_table";

INSERT INTO "my_db"."main"."target_table"
SELECT
    CAST(id AS INTEGER),
    CAST(amount AS DECIMAL(10,2)),
    CAST(date_str AS DATE)
FROM read_csv('source.csv');
```

### CSV parsing errors

Use `ignore_errors` to skip malformed rows, then check what was lost:

```sql
CREATE TABLE "my_db"."main"."clean_data" AS
SELECT * FROM read_csv('messy.csv', ignore_errors = true);

SELECT count(*) AS source_rows FROM read_csv('messy.csv', all_varchar = true);
SELECT count(*) AS loaded_rows FROM "my_db"."main"."clean_data";
```

### Slow loads from cloud storage

- Prefer Parquet over CSV.
- Select only needed columns instead of `SELECT *`.
- Filter during load with WHERE.
- Load in batches by partition key for very large datasets.

### Encoding issues

If the CSV contains non-UTF-8 characters, load as `all_varchar = true` and handle encoding in a transformation step, or convert the file to UTF-8 before loading.

<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Build a Data Pipeline with MotherDuck

Use this skill when designing an end-to-end workflow that moves data from raw sources through transformation stages into analytics-ready output. This is a use-case skill -- it ties together lower-level skills into a complete pipeline.

## Source Of Truth

- Prefer current MotherDuck loading, connection, tagging, and storage docs first.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep the pipeline guidance aligned with the documented posture:
  - batch over streaming
  - raw landing before curation
  - Parquet and bulk paths over row-by-row inserts
  - native MotherDuck storage first unless DuckLake is explicitly required

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** as the default language for pipeline implementation:
  - ingestion jobs
  - transformation runners
  - notebook validation
  - orchestration glue
- Prefer **TypeScript/Javascript** when the pipeline connects directly to:
  - backend services
  - event ingestion APIs
  - product-side control planes
- If the user asks for implementation code, bias toward Python unless their existing stack is clearly Node.js.

## TypeScript/Javascript Orchestration Starter

```ts
import pg from "pg";
import { readFile } from "node:fs/promises";

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "staging",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

await client.connect();
for (const file of ["01_ingest.sql", "02_transform.sql", "03_publish.sql"]) {
  await client.query(await readFile(`sql/pipeline/${file}`, "utf8"));
}
await client.end();
```

## Prerequisites

- MotherDuck connection established (see `connect` skill)
- Familiarity with data ingestion patterns (see `load-data` skill)
- Understanding of schema design (see `model-data` skill)
- Ability to write transformation queries (see `query` skill)

## Runnable Reference Project

For a fully runnable example in this repo, start with:

- `references/dlt-dbt-motherduck-project/`

That reference project is intentionally small and verified against a real MotherDuck run. It combines:

- `dlt` for raw loading
- `dbt-duckdb` for staging and analytics models
- Python validation for output checks

Operational notes from that verified example:

- bootstrap the target MotherDuck database before running `dlt`; the `motherduck` destination does not create the database for you
- keep this stack on Python 3.11 or 3.12 for now; the tested `dbt-duckdb` path here was not reliable on Python 3.14
- if you want exact schema names like `raw`, `staging`, and `analytics` in dbt, override `generate_schema_name`; otherwise dbt defaults may append the target schema name

## Verified Delivery Defaults

The repeated repo runs point to a stable pipeline posture:

- prefer Parquet or other bulk landing paths over row inserts
- keep explicit `raw`, `staging`, and `analytics` boundaries even in small examples
- ship one small MotherDuck-backed artifact plus one deeper runnable reference project
- measure and validate the pipeline with real MotherDuck runs rather than relying on local-only examples
- bootstrap the target MotherDuck database before loaders that assume it already exists

---

## Pipeline Architecture

Every pipeline follows four stages. Do not skip stages.

For code examples and execution:

- default to **Python** for the pipeline runner
- show **TypeScript/Javascript** only when the pipeline is embedded in an existing Node.js service or control plane

```
Source --> Raw --> Staging --> Analytics/Serve
```

- **Source:** External data -- files, cloud storage (S3, GCS, Azure), APIs, databases.
- **Raw:** Append-only landing data preserved as close to the source as practical.
- **Staging:** Cleaned, typed, deduplicated intermediate tables.
- **Analytics/Serve:** Analytics-ready tables, views, Dives, or shares for downstream consumption.

Separating stages ensures you never lose raw data, can debug transformations independently, and can rebuild downstream assets from raw or staging at any time.

---

## Step 1: Design the Target Schema

Start from the end -- what does the analytics team need? Design output tables first, then work backward.

For production pipelines, prefer a multi-database structure to enforce stage separation:

```sql
CREATE DATABASE IF NOT EXISTS raw;       -- Append-only ingested data
CREATE DATABASE IF NOT EXISTS staging;   -- Cleaned and deduplicated data
CREATE DATABASE IF NOT EXISTS analytics; -- Denormalized, business-ready tables
```

Design wide, denormalized analytics tables (see `model-data` skill). Pre-join dimensions so analysts do not need to write joins.

For a minimal dbt project, one MotherDuck database with explicit `raw`, `staging`, and `analytics` schemas is also acceptable. That keeps the project small while preserving stage boundaries in the relation names.

---

## Step 2: Ingest Raw Data into Raw

Use `load-data` skill patterns. Land data in `raw` as-is -- no transformations at this stage.

```sql
CREATE OR REPLACE TABLE "raw"."main"."orders_landing" AS
SELECT * FROM read_parquet('s3://bucket/orders/*.parquet');

CREATE OR REPLACE TABLE "raw"."main"."customers_landing" AS
SELECT * FROM read_csv('s3://bucket/customers/customers.csv');
```

Use `CREATE OR REPLACE TABLE` for idempotent full refreshes. Validate after loading:

```sql
SELECT 'orders_landing' AS table_name, count(*) AS row_count FROM "raw"."main"."orders_landing"
UNION ALL
SELECT 'customers_landing', count(*) FROM "raw"."main"."customers_landing";
```

Operational defaults:

- buffer API or event traffic before writing analytical tables
- prefer staged Parquet, Arrow/dataframes, or `COPY`
- tag long-lived workloads with `custom_user_agent`; for repo use-case builds, use `agent-skills/1.0.0(harness-<harness>;llm-<llm>)`
- keep write transactions comfortably bounded instead of unbounded monoliths

---

## Step 3: Promote Into Staging and Write Transformation Queries

Apply transformations in order: deduplicate, cast types, join, aggregate. Use CTEs for readability.

### Deduplication

```sql
CREATE OR REPLACE TABLE "staging"."main"."orders_deduped" AS
SELECT * FROM "raw"."main"."orders_landing"
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) = 1;
```

For composite keys, partition by the full key:

```sql
CREATE OR REPLACE TABLE "staging"."main"."order_lines_deduped" AS
SELECT * FROM "raw"."main"."order_lines_landing"
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id, line_item_id
    ORDER BY updated_at DESC
) = 1;
```

### Type Casting and Normalization

```sql
CREATE OR REPLACE TABLE "staging"."main"."orders_clean" AS
SELECT
    order_id,
    CAST(order_date AS DATE) AS order_date,
    customer_id,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DECIMAL(18,2)) AS unit_price,
    CAST(quantity * unit_price AS DECIMAL(18,2)) AS total_amount,
    UPPER(TRIM(status)) AS status
FROM "staging"."main"."orders_deduped"
WHERE order_id IS NOT NULL;
```

### Joining Across Sources

```sql
CREATE OR REPLACE TABLE "analytics"."main"."orders" AS
SELECT
    o.order_id, o.order_date, o.customer_id,
    c.customer_name, c.segment AS customer_segment,
    p.product_name, p.category AS product_category,
    o.quantity, o.unit_price, o.total_amount, c.region
FROM "staging"."main"."orders_clean" o
LEFT JOIN "raw"."main"."customers_landing" c ON o.customer_id = c.customer_id
LEFT JOIN "raw"."main"."products_landing" p ON o.product_id = p.product_id;
COMMENT ON TABLE "analytics"."main"."orders" IS 'Denormalized order data with customer and product attributes';
```

### Aggregation

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_revenue" AS
SELECT
    order_date, region, product_category,
    COUNT(*) AS order_count, SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value, COUNT(DISTINCT customer_id) AS unique_customers
FROM "analytics"."main"."orders"
GROUP BY ALL;
COMMENT ON TABLE "analytics"."main"."daily_revenue" IS 'Daily revenue by region and product category from orders';
COMMENT ON COLUMN "analytics"."main"."daily_revenue"."total_revenue" IS 'SUM(total_amount) from analytics.main.orders';
COMMENT ON COLUMN "analytics"."main"."daily_revenue"."avg_order_value" IS 'AVG(total_amount) from analytics.main.orders';
COMMENT ON COLUMN "analytics"."main"."daily_revenue"."unique_customers" IS 'COUNT(DISTINCT customer_id) from analytics.main.orders';
```

---

## Step 4: Materialize Analytics Tables

Use CTAS for expensive aggregations queried repeatedly. Use views for lightweight, always-current logic.

```sql
-- Materialized: expensive computation
CREATE OR REPLACE TABLE "analytics"."main"."customer_lifetime_value" AS
SELECT
    customer_id, customer_name, customer_segment,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(total_amount) AS lifetime_revenue,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date
FROM "analytics"."main"."orders"
GROUP BY ALL;
COMMENT ON TABLE "analytics"."main"."customer_lifetime_value" IS 'Customer lifetime value metrics from orders';
COMMENT ON COLUMN "analytics"."main"."customer_lifetime_value"."total_orders" IS 'COUNT(DISTINCT order_id) from analytics.main.orders';
COMMENT ON COLUMN "analytics"."main"."customer_lifetime_value"."lifetime_revenue" IS 'SUM(total_amount) from analytics.main.orders';
COMMENT ON COLUMN "analytics"."main"."customer_lifetime_value"."first_order_date" IS 'MIN(order_date) from analytics.main.orders';
COMMENT ON COLUMN "analytics"."main"."customer_lifetime_value"."last_order_date" IS 'MAX(order_date) from analytics.main.orders';

-- View: always-current, lightweight
CREATE OR REPLACE VIEW "analytics"."main"."recent_orders" AS
SELECT * FROM "analytics"."main"."orders"
WHERE order_date >= current_date - INTERVAL 30 DAY;
COMMENT ON VIEW "analytics"."main"."recent_orders" IS 'Orders from the last 30 days from analytics.main.orders';
```

---

## Step 5: Validate Data Quality

Run validation checks between every pipeline stage. Never skip validation.

```sql
-- Row count sanity check across stages
SELECT 'raw.orders_landing' AS table_name, count(*) AS row_count
    FROM "raw"."main"."orders_landing"
UNION ALL
SELECT 'staging.orders_deduped', count(*) FROM "staging"."main"."orders_deduped"
UNION ALL
SELECT 'analytics.orders', count(*) FROM "analytics"."main"."orders";

-- NULL check on required columns
SELECT
    count(*) FILTER (WHERE order_id IS NULL) AS null_order_ids,
    count(*) FILTER (WHERE customer_id IS NULL) AS null_customer_ids,
    count(*) FILTER (WHERE total_amount IS NULL) AS null_amounts
FROM "analytics"."main"."orders";

-- Uniqueness check
SELECT order_id, count(*) AS cnt FROM "analytics"."main"."orders"
GROUP BY order_id HAVING cnt > 1;

-- Range validation
SELECT MIN(order_date) AS earliest, MAX(order_date) AS latest,
    count(*) FILTER (WHERE total_amount < 0) AS negative_amounts
FROM "analytics"."main"."orders";
```

---

## Step 6: Serve Results

```sql
-- Views for common query patterns
CREATE OR REPLACE VIEW "analytics"."main"."top_customers" AS
SELECT customer_id, customer_name, lifetime_revenue
FROM "analytics"."main"."customer_lifetime_value"
ORDER BY lifetime_revenue DESC LIMIT 100;
COMMENT ON VIEW "analytics"."main"."top_customers" IS 'Top 100 customers by lifetime revenue from customer_lifetime_value';
```

- Use the `create-dive` skill for interactive visualizations powered by analytics tables.
- Use the `share-data` skill to distribute databases to teams or partners:

```sql
CREATE SHARE IF NOT EXISTS analytics_share FROM analytics (
    ACCESS ORGANIZATION, VISIBILITY DISCOVERABLE, UPDATE AUTOMATIC
);
```

Before sharing, make sure the serving tables are curated and documented. Shares are zero-copy and easy to distribute, so be deliberate about what database boundary you are publishing.

---

## Incremental Load Patterns

Full refreshes work for small-to-medium datasets. For large or frequently updated datasets, use incremental patterns.

```sql
-- Append new data only
INSERT INTO "raw"."main"."orders_landing"
SELECT * FROM read_parquet('s3://bucket/orders/date=2024-03-24/*.parquet')
WHERE order_date > (SELECT MAX(order_date) FROM "raw"."main"."orders_landing");

-- Upsert: load into temp table, delete old rows, insert new
CREATE OR REPLACE TEMP TABLE new_orders AS
SELECT * FROM read_parquet('s3://bucket/orders/latest/*.parquet');

DELETE FROM "raw"."main"."orders_landing"
WHERE order_id IN (SELECT order_id FROM new_orders);

INSERT INTO "raw"."main"."orders_landing"
SELECT * FROM new_orders;

-- Incremental aggregation: rebuild only affected date range
DELETE FROM "analytics"."main"."daily_revenue"
WHERE order_date >= (SELECT MAX(order_date) - INTERVAL 3 DAY FROM "raw"."main"."orders_landing");

INSERT INTO "analytics"."main"."daily_revenue"
SELECT order_date, region, product_category,
    COUNT(*) AS order_count, SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value, COUNT(DISTINCT customer_id) AS unique_customers
FROM "analytics"."main"."orders"
WHERE order_date >= (SELECT MAX(order_date) - INTERVAL 3 DAY FROM "raw"."main"."orders_landing")
GROUP BY ALL;
```

---

## Complete Pipeline Example

End-to-end: CSV ingest, deduplicate, join, aggregate, validate, create views, share.

```sql
-- 1. Create databases
CREATE DATABASE IF NOT EXISTS raw;
CREATE DATABASE IF NOT EXISTS staging;
CREATE DATABASE IF NOT EXISTS analytics;

-- 2. Ingest raw data
CREATE OR REPLACE TABLE "raw"."main"."sales_landing" AS
SELECT * FROM read_csv('s3://acme-data/sales/sales_2024.csv');

CREATE OR REPLACE TABLE "raw"."main"."customers_landing" AS
SELECT * FROM read_csv('s3://acme-data/customers/customers.csv');

-- 3. Deduplicate
CREATE OR REPLACE TABLE "staging"."main"."sales_deduped" AS
SELECT * FROM "raw"."main"."sales_landing"
QUALIFY ROW_NUMBER() OVER (PARTITION BY sale_id ORDER BY updated_at DESC) = 1;

-- 4. Transform and join
CREATE OR REPLACE TABLE "analytics"."main"."sales" AS
SELECT s.sale_id, s.sale_date, s.product_name, s.quantity, s.unit_price,
    CAST(s.quantity * s.unit_price AS DECIMAL(18,2)) AS total_amount,
    c.customer_name, c.segment, c.region
FROM "staging"."main"."sales_deduped" s
LEFT JOIN "raw"."main"."customers_landing" c ON s.customer_id = c.customer_id;
COMMENT ON TABLE "analytics"."main"."sales" IS 'Denormalized sales with customer attributes';

-- 5. Aggregate
CREATE OR REPLACE TABLE "analytics"."main"."revenue_summary" AS
SELECT date_trunc('month', sale_date) AS month, region, segment,
    COUNT(*) AS sale_count, SUM(total_amount) AS total_revenue,
    COUNT(DISTINCT customer_name) AS unique_customers
FROM "analytics"."main"."sales" GROUP BY ALL;
COMMENT ON TABLE "analytics"."main"."revenue_summary" IS 'Monthly revenue summary by region and segment from sales';
COMMENT ON COLUMN "analytics"."main"."revenue_summary"."total_revenue" IS 'SUM(total_amount) from analytics.main.sales';
COMMENT ON COLUMN "analytics"."main"."revenue_summary"."unique_customers" IS 'COUNT(DISTINCT customer_name) from analytics.main.sales';

-- 6. Validate
SELECT count(*) FILTER (WHERE sale_id IS NULL) AS null_ids,
    count(*) FILTER (WHERE total_amount < 0) AS negative_amounts
FROM "analytics"."main"."sales";

SELECT sale_id, count(*) AS cnt FROM "analytics"."main"."sales"
GROUP BY sale_id HAVING cnt > 1;

-- 7. Serve
CREATE OR REPLACE VIEW "analytics"."main"."monthly_revenue" AS
SELECT month, SUM(total_revenue) AS revenue, SUM(unique_customers) AS customers
FROM "analytics"."main"."revenue_summary" GROUP BY month ORDER BY month;
COMMENT ON VIEW "analytics"."main"."monthly_revenue" IS 'Monthly total revenue and customer counts rolled up from revenue_summary';
COMMENT ON COLUMN "analytics"."main"."monthly_revenue"."revenue" IS 'SUM(total_revenue) from analytics.main.revenue_summary';
COMMENT ON COLUMN "analytics"."main"."monthly_revenue"."customers" IS 'SUM(unique_customers) from analytics.main.revenue_summary';

-- 8. Share
CREATE SHARE IF NOT EXISTS analytics_share FROM analytics (
    ACCESS ORGANIZATION, VISIBILITY DISCOVERABLE, UPDATE AUTOMATIC
);
```

---

## Scheduling Considerations

MotherDuck does not have built-in scheduling. Use external schedulers: cron, GitHub Actions, Dagster, Airflow, or Prefect.

Store SQL transformations in version-controlled `.sql` files. Execute them from a scheduled script:

```python
# pipeline.py -- run via cron, Airflow, or GitHub Actions
import psycopg2, certifi, os
from pathlib import Path

def run_pipeline():
    conn = psycopg2.connect(
        host="pg.us-east-1-aws.motherduck.com", port=5432,
        dbname="staging", user="postgres",
        password=os.environ["MOTHERDUCK_TOKEN"],
        sslmode="verify-full", sslrootcert=certifi.where(),
    )
    conn.autocommit = True
    for step in sorted(Path("sql/pipeline").glob("*.sql")):
        print(f"Running {step.name}...")
        conn.cursor().execute(step.read_text())
    conn.close()

if __name__ == "__main__":
    run_pipeline()
```

Number files to enforce execution order (`01_ingest.sql`, `02_dedupe.sql`, etc.). Each file should be idempotent -- use `CREATE OR REPLACE` so re-running is safe.

---

## Key Rules

- **Separate lifecycle stages explicitly.** Production default: `raw`, `staging`, and `analytics` as separate databases. Minimal dbt projects may use one database with `raw`, `staging`, and `analytics` schemas.
- **Land data in `raw` before curation.** Preserve source-like tables so downstream rebuilds stay simple.
- **Validate data between every pipeline stage.** Row counts, NULL checks, uniqueness, range validation.
- **Preserve raw data.** Never transform during ingestion. Rebuild downstream tables from staging.
- **Materialize only what needs fast repeated access.** Use views for lightweight, always-current logic.
- **Use `CREATE OR REPLACE` for idempotent rebuilds.** Every pipeline step should be safe to re-run.
- **Version control all SQL transformations.** Store `.sql` files in git, not in ad-hoc query editors.
- **Deduplicate before building analytics tables.** Raw sources often contain duplicates.
- **Use fully qualified table names** in every statement: `"database"."schema"."table"`.
- **Tag long-lived pipeline runners with `custom_user_agent`.** This makes workload attribution and cost analysis possible later. For repo use-case builds, use `agent-skills/1.0.0(harness-<harness>;llm-<llm>)`.

---

## Common Mistakes

### Loading and transforming in a single step

Combining ingestion with transformation loses the raw data. If a bug is discovered later, you must re-ingest from the external source.

```sql
-- Wrong: raw data is lost
CREATE TABLE "analytics"."main"."orders" AS
SELECT order_id, UPPER(status) AS status FROM read_parquet('s3://bucket/orders.parquet');

-- Right: ingest raw first, then transform
CREATE TABLE "raw"."main"."orders_landing" AS
SELECT * FROM read_parquet('s3://bucket/orders.parquet');
CREATE TABLE "analytics"."main"."orders" AS
SELECT order_id, UPPER(status) AS status FROM "raw"."main"."orders_landing";
```

### Not deduplicating before analytics tables

Raw sources frequently contain duplicates from retries, overlapping file loads, or CDC replication. Without deduplication, aggregations produce inflated numbers.

### Forgetting data validation between stages

Skipping validation means bad data propagates silently. A NULL customer ID in staging becomes an orphaned order in analytics and an incorrect revenue number in a dashboard.

### Using DROP TABLE then CREATE TABLE instead of CREATE OR REPLACE

`DROP` then `CREATE` is non-atomic -- queries fail during the gap. Use `CREATE OR REPLACE TABLE` for atomic replacement.

### Over-aggregating and losing detail

Pre-aggregating to monthly granularity when analysts later need hourly or daily breakdowns forces a pipeline rebuild. Ask what the finest useful grain is before choosing -- for some use cases that is hourly, for others event-level. Keep that grain as the base table and build coarser rollups (daily, weekly, monthly) on top. When in doubt, preserve more detail -- it is easy to aggregate up but impossible to disaggregate down.

---

## Related Skills

- `connect` -- Establish a MotherDuck connection
- `load-data` -- Ingest data from files, cloud storage, and external sources
- `model-data` -- Design database schemas and data models
- `query` -- Execute DuckDB SQL queries and transformations
- `explore` -- Discover databases, tables, columns, and shares
- `create-dive` -- Build interactive visualizations from analytics tables
- `share-data` -- Distribute analytics databases to teams and partners

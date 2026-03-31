---
name: model-data
description: Design database schemas and data models in MotherDuck. Use when creating tables, choosing data types, defining relationships, or restructuring data for analytics workloads.
license: MIT
---

# Model Data in MotherDuck

Use this skill when creating tables, designing schemas, choosing data types, defining relationships between tables, or restructuring data for analytical workloads.

## Prerequisites

- MotherDuck connection established (see `connect` skill)
- Familiarity with DuckDB data types and SQL syntax (see `duckdb-sql` skill)

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** examples when schema design is tied to:
  - ETL or ELT jobs
  - dbt-like modeling work
  - notebooks and one-off migration scripts
- Prefer **TypeScript/Javascript** examples when schema design is tied to:
  - product backends
  - analytics APIs
  - customer-facing analytics control planes
- In both languages, keep DDL as explicit SQL checked into the repo rather than generated dynamically at runtime unless there is a strong reason not to.
- If the user asks for table design and code together, model the schema in SQL first, then show how Python or TypeScript/Javascript executes it.

## TypeScript/Javascript Starter

```ts
import pg from "pg";

const ddl = `
  CREATE OR REPLACE TABLE "analytics"."main"."daily_metrics" AS
  SELECT date_trunc('day', event_timestamp) AS day,
         event_type,
         COUNT(*) AS event_count
  FROM "raw"."main"."events"
  GROUP BY ALL
`;

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "analytics",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

await client.connect();
await client.query(ddl);
await client.end();
```

## Python Starter

```python
import duckdb

ddl = """
CREATE OR REPLACE TABLE "analytics"."main"."daily_metrics" AS
SELECT date_trunc('day', event_timestamp) AS day,
       event_type,
       COUNT(*) AS event_count
FROM "raw"."main"."events"
GROUP BY ALL
"""

conn = duckdb.connect("md:analytics")
conn.sql(ddl)
conn.close()
```

---

## Schema Design Principles

MotherDuck is an OLAP (Online Analytical Processing) system. Design every schema for read-heavy analytical queries, not transactional writes.

- **Prefer wide, denormalized tables** over highly normalized schemas. Joins are expensive at scale; pre-joining data into fewer, wider tables accelerates analytical queries.
- **Pre-aggregate where possible.** Materialized summary tables are cheap to store and dramatically speed up dashboards and reports.
- **Use descriptive snake_case names** for all tables and columns. Avoid abbreviations that sacrifice clarity (e.g., `customer_lifetime_value` not `cust_ltv`).
- **Add comments to every table and column.** Comments are the primary discovery mechanism in MotherDuck -- they appear in catalog searches and exploration tools.
- **Use fully qualified names** in all DDL statements: `"database"."schema"."table"`.

---

## CREATE TABLE Patterns

### Basic Table Creation

```sql
CREATE TABLE "my_db"."main"."events" (
    event_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    properties JSON,
    created_at TIMESTAMP DEFAULT current_timestamp
);
COMMENT ON TABLE "my_db"."main"."events" IS 'Raw user interaction events from the web and mobile apps';
COMMENT ON COLUMN "my_db"."main"."events".event_type IS 'One of: pageview, click, purchase, signup';
COMMENT ON COLUMN "my_db"."main"."events".properties IS 'Event-specific metadata as JSON (varies by event_type)';
```

### CREATE TABLE AS SELECT (CTAS)

Materialize query results into a new table. Use CTAS for building denormalized analytical tables from raw sources.

```sql
CREATE TABLE "analytics"."main"."order_summary" AS
SELECT o.customer_id, c.customer_name, c.segment,
    COUNT(*) AS total_orders, SUM(o.amount) AS total_revenue,
    AVG(o.amount) AS avg_order_value,
    MIN(o.order_date) AS first_order_date, MAX(o.order_date) AS last_order_date
FROM "raw"."main"."orders" o
JOIN "raw"."main"."customers" c ON o.customer_id = c.customer_id
GROUP BY ALL;
COMMENT ON TABLE "analytics"."main"."order_summary" IS 'Pre-aggregated customer order metrics, refreshed daily';
```

### CREATE OR REPLACE TABLE

Use `CREATE OR REPLACE` for idempotent table rebuilds in data pipelines.

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_metrics" AS
SELECT date_trunc('day', event_timestamp) AS day, event_type,
    COUNT(*) AS event_count, COUNT(DISTINCT user_id) AS unique_users
FROM "raw"."main"."events" GROUP BY ALL;
```

---

## Data Type Selection Guide

Choose types deliberately. Wrong type choices cause precision loss, poor query performance, and lost functionality.

| Use Case | Recommended Type | Avoid | Why |
|---|---|---|---|
| IDs and keys | VARCHAR | INTEGER | VARCHAR handles UUIDs, external IDs, and avoids overflow limits |
| Money/currency | DECIMAL(18,2) | FLOAT/DOUBLE | Floating point causes rounding errors in financial calculations |
| Timestamps | TIMESTAMP or TIMESTAMPTZ | VARCHAR | VARCHAR loses time arithmetic, comparisons, and truncation |
| Booleans | BOOLEAN | INTEGER 0/1 | BOOLEAN is self-documenting and type-safe |
| Categories (<50 values) | VARCHAR | ENUM | ENUM is inflexible when new categories appear |
| Free text | VARCHAR | TEXT | Both are identical in DuckDB; VARCHAR is idiomatic |
| Semi-structured data | JSON or STRUCT | VARCHAR | Lose query capability with plain strings |
| Lists of values | LIST type (e.g., `VARCHAR[]`) | Comma-separated VARCHAR | Lists support indexing, filtering, and unnesting |
| Nested objects | STRUCT | Flattened columns | STRUCT preserves hierarchy when structure is consistent |
| Date only (no time) | DATE | TIMESTAMP | DATE is more precise in intent and avoids midnight ambiguity |
| Large integers (>2B) | BIGINT or HUGEINT | INTEGER | INTEGER overflows at ~2.1 billion |

---

## Schema Organization

### Multi-Database Pattern

Separate databases by data lifecycle stage. This is the recommended pattern for any non-trivial project.

```sql
CREATE DATABASE IF NOT EXISTS raw;       -- Ingested source data, append-only
CREATE DATABASE IF NOT EXISTS staging;   -- Cleaned, validated, deduplicated data
CREATE DATABASE IF NOT EXISTS analytics; -- Denormalized, pre-aggregated, business-ready
```

### Schema Usage

Use the `main` schema unless you have a specific reason for multiple schemas. DuckDB defaults to `main`, and most tools expect it.

```sql
CREATE TABLE "analytics"."main"."revenue_by_region" ( ... );

-- Use a custom schema only for logical grouping within a single database
CREATE SCHEMA IF NOT EXISTS "analytics"."marketing";
CREATE TABLE "analytics"."marketing"."campaign_performance" ( ... );
```

---

## Analytical Modeling Patterns

### Pattern 1: Wide Denormalized Table (Recommended Default)

A single table per domain with all relevant attributes pre-joined. Simplest pattern, fastest for most analytical queries.

```sql
CREATE TABLE "analytics"."main"."orders_wide" AS
SELECT o.order_id, o.order_date, o.amount, o.status,
    c.customer_name, c.segment, c.region,
    p.product_name, p.category, p.unit_price
FROM "raw"."main"."orders" o
JOIN "raw"."main"."customers" c ON o.customer_id = c.customer_id
JOIN "raw"."main"."order_items" oi ON o.order_id = oi.order_id
JOIN "raw"."main"."products" p ON oi.product_id = p.product_id;
COMMENT ON TABLE "analytics"."main"."orders_wide" IS 'Denormalized order data with customer and product attributes';
```

Use this pattern when:
- Analysts query the same joined dataset repeatedly
- The table has fewer than ~100 columns
- Data freshness requirements allow periodic rebuilds

### Pattern 2: Star Schema

Fact tables store measurable events; dimension tables store descriptive attributes. Use when dimension tables are shared across multiple fact tables.

```sql
-- Dimension tables: descriptive attributes with NOT NULL on key columns
CREATE TABLE "analytics"."main"."dim_customers" (
    customer_id VARCHAR NOT NULL, customer_name VARCHAR NOT NULL,
    segment VARCHAR, region VARCHAR, created_at TIMESTAMP
);
COMMENT ON TABLE "analytics"."main"."dim_customers" IS 'Customer dimension with current attributes';

CREATE TABLE "analytics"."main"."dim_products" (
    product_id VARCHAR NOT NULL, product_name VARCHAR NOT NULL,
    category VARCHAR, subcategory VARCHAR, unit_price DECIMAL(18,2)
);
COMMENT ON TABLE "analytics"."main"."dim_products" IS 'Product catalog dimension';

-- Date dimension generated from a series
CREATE TABLE "analytics"."main"."dim_dates" AS
SELECT date::DATE AS date_key, EXTRACT(YEAR FROM date) AS year,
    EXTRACT(QUARTER FROM date) AS quarter, EXTRACT(MONTH FROM date) AS month,
    dayname(date) AS day_name, dayofweek(date) IN (0, 6) AS is_weekend
FROM generate_series(DATE '2020-01-01', DATE '2030-12-31', INTERVAL 1 DAY) AS t(date);

-- Fact table: measurable events at the grain of one order line
CREATE TABLE "analytics"."main"."fact_orders" (
    order_id VARCHAR NOT NULL, customer_id VARCHAR NOT NULL,
    order_date DATE NOT NULL, product_id VARCHAR NOT NULL,
    quantity INTEGER NOT NULL, unit_price DECIMAL(18,2) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL
);
COMMENT ON TABLE "analytics"."main"."fact_orders" IS 'Order line-level fact table';
```

### Pattern 3: Materialized Summary Tables

Pre-compute common aggregations. Rebuild periodically instead of computing on the fly. Use for dashboard queries, expensive reports, and metrics that change infrequently.

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_revenue_summary" AS
SELECT date_trunc('day', order_date) AS day, region, category,
    COUNT(*) AS order_count, SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value, COUNT(DISTINCT customer_id) AS unique_customers
FROM "analytics"."main"."fact_orders" f
JOIN "analytics"."main"."dim_customers" c USING (customer_id)
JOIN "analytics"."main"."dim_products" p USING (product_id)
GROUP BY ALL;
COMMENT ON TABLE "analytics"."main"."daily_revenue_summary" IS 'Daily revenue by region and category, rebuilt nightly';
```

---

## Views vs Tables

### Use Views for Reusable Logic

Views always reflect the latest underlying data. Use them for query logic that should stay current without manual refreshes.

```sql
CREATE VIEW "analytics"."main"."daily_revenue" AS
SELECT
    date_trunc('day', order_date) AS day,
    SUM(total_amount) AS revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM "analytics"."main"."fact_orders"
GROUP BY ALL;

COMMENT ON VIEW "analytics"."main"."daily_revenue" IS 'Daily revenue and unique customer counts, always current';
```

### Use Tables (CTAS) for Materialized Results

Tables store computed results for fast repeated access. Use when the underlying query is expensive and the data does not need to be real-time.

```sql
CREATE OR REPLACE TABLE "analytics"."main"."monthly_cohort_retention" AS
WITH first_purchase AS (
    SELECT customer_id, date_trunc('month', MIN(order_date)) AS cohort_month
    FROM "analytics"."main"."fact_orders" GROUP BY customer_id
)
SELECT f.cohort_month,
    date_diff('month', f.cohort_month, date_trunc('month', o.order_date)) AS months_since_first,
    COUNT(DISTINCT o.customer_id) AS active_customers
FROM first_purchase f
JOIN "analytics"."main"."fact_orders" o ON f.customer_id = o.customer_id
GROUP BY ALL;
```

### Decision Guide

| Criterion | Use VIEW | Use TABLE (CTAS) |
|---|---|---|
| Must reflect latest data | Yes | No |
| Query is fast (<1s) | Yes | Either |
| Query is expensive (>5s) | No | Yes |
| Accessed many times per day | No | Yes |
| Source data changes frequently | Yes | Rebuild periodically |

---

## Complex Types for Semi-Structured Data

### STRUCT: Fixed Schema Nested Objects

Use STRUCT when you know the exact fields and types at design time.

```sql
CREATE TABLE "my_db"."main"."customers" (
    customer_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    address STRUCT(street VARCHAR, city VARCHAR, state VARCHAR, zip VARCHAR, country VARCHAR),
    created_at TIMESTAMP DEFAULT current_timestamp
);

-- Query nested fields with dot notation
SELECT customer_id, address.city, address.state
FROM "my_db"."main"."customers" WHERE address.country = 'US';
```

### LIST: Variable-Length Arrays

Use LIST for ordered collections of the same type.

```sql
CREATE TABLE "my_db"."main"."articles" (
    article_id VARCHAR NOT NULL, title VARCHAR NOT NULL, tags VARCHAR[], scores INTEGER[]
);

SELECT title, tags[1] AS primary_tag, list_contains(tags, 'analytics') AS is_analytics
FROM "my_db"."main"."articles";

-- Unnest lists into rows
SELECT article_id, UNNEST(tags) AS tag FROM "my_db"."main"."articles";
```

### MAP and JSON

Use MAP when keys are dynamic but values share a type. Use JSON when the structure varies across rows entirely.

```sql
-- MAP: dynamic key-value pairs
CREATE TABLE "my_db"."main"."feature_flags" (
    user_id VARCHAR NOT NULL, flags MAP(VARCHAR, BOOLEAN)
);
SELECT user_id, flags['dark_mode'] AS dark_mode_enabled FROM "my_db"."main"."feature_flags";

-- JSON: fully dynamic structure
CREATE TABLE "my_db"."main"."api_responses" (
    request_id VARCHAR NOT NULL, endpoint VARCHAR NOT NULL,
    response_body JSON, received_at TIMESTAMP DEFAULT current_timestamp
);
SELECT request_id, response_body->>'$.status' AS status,
    response_body->'$.data.items' AS items
FROM "my_db"."main"."api_responses";
```

### Complex Type Selection Guide

| Scenario | Type | Reason |
|---|---|---|
| Address with known fields | STRUCT | Fixed schema, dot-notation access |
| Tags on a blog post | VARCHAR[] (LIST) | Variable-length, same type |
| User preferences (unknown keys) | MAP(VARCHAR, VARCHAR) | Dynamic keys, uniform value type |
| Third-party API payload | JSON | Structure varies per response |

---

## ALTER TABLE Patterns

Modify existing tables without recreating them.

```sql
-- Add a column
ALTER TABLE "my_db"."main"."customers" ADD COLUMN loyalty_tier VARCHAR;

-- Add a column with a default value
ALTER TABLE "my_db"."main"."orders" ADD COLUMN currency VARCHAR DEFAULT 'USD';

-- Drop a column
ALTER TABLE "my_db"."main"."customers" DROP COLUMN legacy_code;

-- Rename a column
ALTER TABLE "my_db"."main"."customers" RENAME COLUMN email TO email_address;

-- Rename a table
ALTER TABLE "my_db"."main"."customers" RENAME TO clients;
```

---

## Constraints

DuckDB constraints are partially enforced. Understand what is enforced and what is informational.

| Constraint | Enforced? | Behavior |
|---|---|---|
| NOT NULL | Yes | Rejects NULL inserts and updates |
| PRIMARY KEY | No | Informational only -- duplicates are allowed |
| UNIQUE | No | Informational only -- duplicates are allowed |
| CHECK | No | Informational only -- invalid values are allowed |
| FOREIGN KEY | No | Not supported |

**Use NOT NULL as the primary constraint mechanism.** It is the only constraint that DuckDB enforces at write time.

Declare PRIMARY KEY for documentation purposes -- it signals intent to readers and tools -- but never assume it prevents duplicates.

```sql
CREATE TABLE "my_db"."main"."users" (
    user_id VARCHAR NOT NULL,  -- enforced
    email VARCHAR NOT NULL,    -- enforced
    display_name VARCHAR,      -- nullable is intentional
    PRIMARY KEY (user_id)      -- informational only, NOT enforced
);
```

---

## Key Rules

- **Design for analytics (reads), not transactions (writes).** Favor denormalized, wide tables over highly normalized schemas.
- **Prefer wide tables over joins** for data that analysts query repeatedly.
- **Always add table and column comments.** Comments power discovery via `search_catalog` and `explore`.
- **Use fully qualified names** in all DDL: `"database"."schema"."table"`.
- **Use VARCHAR for IDs**, DECIMAL for money, TIMESTAMP for times, BOOLEAN for flags.
- **Use NOT NULL liberally.** It is the only enforced constraint and prevents bad data at the source.
- **Use CTAS and CREATE OR REPLACE** for idempotent, rebuildable analytical tables.
- **Separate databases by lifecycle**: `raw`, `staging`, `analytics`.

---

## Common Mistakes

- **Over-normalizing.** Applying OLTP normalization patterns (3NF, junction tables everywhere) to an OLAP system. MotherDuck is optimized for scanning wide tables, not joining many small ones.
- **Using FLOAT/DOUBLE for monetary values.** Floating point arithmetic causes rounding errors. Use `DECIMAL(18,2)` for all financial data.
- **Forgetting comments on tables and columns.** Without comments, data discovery relies entirely on column names, which are often ambiguous.
- **Assuming PRIMARY KEY is enforced.** It is informational only in DuckDB. Duplicate rows will be silently inserted. Deduplicate data in your pipeline, not via constraints.
- **Creating too many small tables.** A single wide table with 30 columns outperforms 6 joined tables of 5 columns each for analytical queries.
- **Using VARCHAR for timestamps.** Storing `'2024-01-15 14:30:00'` as VARCHAR loses date arithmetic, comparisons, and `date_trunc` functionality. Use TIMESTAMP.
- **Skipping the multi-database pattern.** Mixing raw ingestion data and analytical outputs in the same database makes it difficult to manage freshness, permissions, and rebuild logic.

---

## Related Skills

- `duckdb-sql` -- DuckDB data types, functions, and syntax reference
- `query` -- Execute DDL and analytical queries against MotherDuck
- `explore` -- Discover and inspect existing schemas, tables, and columns
- `load-data` -- Ingest data from files, URLs, and external sources into tables

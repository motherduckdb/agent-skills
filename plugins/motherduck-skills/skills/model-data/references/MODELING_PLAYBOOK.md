# Modeling Playbook

Reference for analytical schema design, data-type selection, CTAS and view patterns, complex types, and DuckDB constraint behavior in MotherDuck.

## SQL-First Modeling Posture

- Keep model definitions as explicit SQL DDL or CTAS statements, not dynamic code generation.
- Make grain, lifecycle stage, and output shape obvious in the SQL itself.
- Prefer checked-in SQL that can be reviewed, rebuilt, and rerun.
- Use comments, fully qualified names, and explicit data types so the model remains understandable outside the application code that executes it.

### SQL Starter

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_metrics" AS
SELECT
    date_trunc('day', event_timestamp) AS day,
    event_type,
    COUNT(*) AS event_count
FROM "raw"."main"."events"
GROUP BY ALL;
```

## Schema Design Principles

- MotherDuck is an OLAP system. Design for read-heavy analytical queries.
- Prefer wide, denormalized tables over highly normalized schemas.
- Pre-aggregate where possible.
- Use descriptive snake_case names.
- Add comments to every table and column.
- Use fully qualified names in all DDL statements.

## `CREATE TABLE` Patterns

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

### `CREATE TABLE AS SELECT`

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

### `CREATE OR REPLACE TABLE`

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_metrics" AS
SELECT date_trunc('day', event_timestamp) AS day, event_type,
    COUNT(*) AS event_count, COUNT(DISTINCT user_id) AS unique_users
FROM "raw"."main"."events" GROUP BY ALL;
```

## Data Type Selection Guide

| Use Case | Recommended Type | Avoid | Why |
|---|---|---|---|
| IDs and keys | VARCHAR | INTEGER | Handles UUIDs and external IDs |
| Money | DECIMAL(18,2) | FLOAT/DOUBLE | Avoids rounding errors |
| Timestamps | TIMESTAMP or TIMESTAMPTZ | VARCHAR | Preserves date arithmetic |
| Booleans | BOOLEAN | INTEGER 0/1 | Clear intent |
| Categories | VARCHAR | ENUM | More flexible |
| Free text | VARCHAR | TEXT | Same semantics in DuckDB |
| Semi-structured data | JSON or STRUCT | VARCHAR | Preserves queryability |
| Lists | LIST | Comma-separated VARCHAR | Supports indexing and unnesting |
| Nested objects | STRUCT | Flattened columns | Preserves hierarchy |
| Date only | DATE | TIMESTAMP | Clearer semantics |
| Large integers | BIGINT or HUGEINT | INTEGER | Avoids overflow |

## Schema Organization

### Multi-Database Pattern

```sql
CREATE DATABASE IF NOT EXISTS raw;
CREATE DATABASE IF NOT EXISTS staging;
CREATE DATABASE IF NOT EXISTS analytics;
```

### Schema Usage

Use the `main` schema unless you have a specific reason for multiple schemas.

```sql
CREATE TABLE "analytics"."main"."revenue_by_region" ( ... );

CREATE SCHEMA IF NOT EXISTS "analytics"."marketing";
CREATE TABLE "analytics"."marketing"."campaign_performance" ( ... );
```

## Analytical Modeling Patterns

### Pattern 1: Wide Denormalized Table

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

### Pattern 2: Star Schema

```sql
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

CREATE TABLE "analytics"."main"."dim_dates" AS
SELECT date::DATE AS date_key, EXTRACT(YEAR FROM date) AS year,
    EXTRACT(QUARTER FROM date) AS quarter, EXTRACT(MONTH FROM date) AS month,
    dayname(date) AS day_name, dayofweek(date) IN (0, 6) AS is_weekend
FROM generate_series(DATE '2020-01-01', DATE '2030-12-31', INTERVAL 1 DAY) AS t(date);

CREATE TABLE "analytics"."main"."fact_orders" (
    order_id VARCHAR NOT NULL, customer_id VARCHAR NOT NULL,
    order_date DATE NOT NULL, product_id VARCHAR NOT NULL,
    quantity INTEGER NOT NULL, unit_price DECIMAL(18,2) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL
);
COMMENT ON TABLE "analytics"."main"."fact_orders" IS 'Order line-level fact table';
```

### Pattern 3: Materialized Summary Tables

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

## Views vs Tables

### Use Views for Reusable Logic

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

## Complex Types for Semi-Structured Data

### `STRUCT`

```sql
CREATE TABLE "my_db"."main"."customers" (
    customer_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    address STRUCT(street VARCHAR, city VARCHAR, state VARCHAR, zip VARCHAR, country VARCHAR),
    created_at TIMESTAMP DEFAULT current_timestamp
);

SELECT customer_id, address.city, address.state
FROM "my_db"."main"."customers" WHERE address.country = 'US';
```

### `LIST`

```sql
CREATE TABLE "my_db"."main"."articles" (
    article_id VARCHAR NOT NULL, title VARCHAR NOT NULL, tags VARCHAR[], scores INTEGER[]
);

SELECT title, tags[1] AS primary_tag, list_contains(tags, 'analytics') AS is_analytics
FROM "my_db"."main"."articles";

SELECT article_id, UNNEST(tags) AS tag FROM "my_db"."main"."articles";
```

### `MAP` and `JSON`

```sql
CREATE TABLE "my_db"."main"."feature_flags" (
    user_id VARCHAR NOT NULL, flags MAP(VARCHAR, BOOLEAN)
);
SELECT user_id, flags['dark_mode'] AS dark_mode_enabled FROM "my_db"."main"."feature_flags";

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
| Address with known fields | STRUCT | Fixed schema |
| Tags on a blog post | `VARCHAR[]` | Variable-length list |
| User preferences with unknown keys | `MAP(VARCHAR, VARCHAR)` | Dynamic keys |
| Third-party API payload | JSON | Structure varies |

## `ALTER TABLE` Patterns

```sql
ALTER TABLE "my_db"."main"."customers" ADD COLUMN loyalty_tier VARCHAR;
ALTER TABLE "my_db"."main"."orders" ADD COLUMN currency VARCHAR DEFAULT 'USD';
ALTER TABLE "my_db"."main"."customers" DROP COLUMN legacy_code;
ALTER TABLE "my_db"."main"."customers" RENAME COLUMN email TO email_address;
ALTER TABLE "my_db"."main"."customers" RENAME TO clients;
```

## Constraints

| Constraint | Enforced? | Behavior |
|---|---|---|
| NOT NULL | Yes | Rejects NULL writes |
| PRIMARY KEY | No | Informational only |
| UNIQUE | No | Informational only |
| CHECK | No | Informational only |
| FOREIGN KEY | No | Not supported |

Use `NOT NULL` as the primary constraint mechanism.

```sql
CREATE TABLE "my_db"."main"."users" (
    user_id VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    display_name VARCHAR,
    PRIMARY KEY (user_id)
);
```

## Key Rules

- Design for analytics, not OLTP.
- Prefer wide tables over repeated joins for common analytical access paths.
- Always add table and column comments.
- Use fully qualified names in all DDL.
- Use `VARCHAR` for IDs, `DECIMAL` for money, `TIMESTAMP` for times, and `BOOLEAN` for flags.
- Use `NOT NULL` liberally.
- Use CTAS and `CREATE OR REPLACE` for rebuildable analytical tables.
- Separate lifecycle stages across databases.

## Common Mistakes

- Over-normalizing
- Using floating point types for money
- Forgetting table and column comments
- Assuming `PRIMARY KEY` is enforced
- Creating too many small tables
- Using `VARCHAR` for timestamps
- Skipping the multi-database lifecycle pattern

---
name: query
description: Execute DuckDB SQL queries against MotherDuck databases. Use when running analytics, aggregations, transformations, or any SQL operation. Covers query best practices, CTEs, window functions, QUALIFY, and performance optimization.
license: MIT
---

# Query MotherDuck

Use this skill when executing SQL queries for analytics, aggregations, transformations, or data exploration against MotherDuck databases.

For reusable language patterns, see `references/typescript.md` and `references/python.md`.

## Prerequisites

- MotherDuck connection established (see `connect` skill)
- Target database and tables exist (see `explore` skill to discover available data)

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** examples when the user is:
  - running analytics scripts
  - building transformations
  - validating results in notebooks
  - orchestrating data workflows
- Prefer **TypeScript/Javascript** examples when the user is:
  - querying from backend APIs
  - serving analytics to a web application
  - building internal tools or admin surfaces
- In both languages:
  - parameterize values instead of interpolating strings
  - keep SQL in multi-line strings with obvious formatting
  - return pre-aggregated results to the application layer
- If the user is asking about query shape rather than code execution, answer in SQL first and only then show the language wrapper.

## Compute and Storage Posture

- Filter early and aggregate early so less data moves through expensive stages.
- Prefer curated tables, views, or pre-aggregated summary tables for repeated dashboards and app-serving queries.
- Use `LIMIT` or aggregates during exploration; do not scan wide raw tables blindly when a smaller preview will answer the question.
- Tag long-lived integrations with `custom_user_agent` so query history can attribute cost and workload shape later.
- When validating multi-database patterns in the native DuckDB API, use a workspace connection (`md:`) and fully qualified `database.schema.table` names.

## TypeScript/Javascript Starter

```ts
import pg from "pg";

const pool = new pg.Pool({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "analytics",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

const sql = `
  SELECT customer_id, SUM(amount) AS total_spent
  FROM "analytics"."main"."orders"
  WHERE order_date >= $1
  GROUP BY customer_id
  ORDER BY total_spent DESC
  LIMIT 20
`;

const { rows } = await pool.query(sql, ["2025-01-01"]);
```

## Python Starter

```python
import os
import certifi
import psycopg

sql = """
SELECT customer_id, SUM(amount) AS total_spent
FROM "analytics"."main"."orders"
WHERE order_date >= %s
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 20
"""

with psycopg.connect(
    host="pg.us-east-1-aws.motherduck.com",
    port=5432,
    dbname="analytics",
    user="postgres",
    password=os.environ["MOTHERDUCK_TOKEN"],
    sslmode="verify-full",
    sslrootcert=certifi.where(),
) as conn:
    rows = conn.execute(sql, ("2025-01-01",)).fetchall()
```

---

## 1. Always Use Fully Qualified Table Names

Reference every table as `"database"."schema"."table"`. The default schema is `main`.

```sql
-- Correct: fully qualified
SELECT * FROM "my_db"."main"."orders" LIMIT 10;

-- WRONG: unqualified table name -- fails with multiple databases attached
SELECT * FROM orders;
```

Use double quotes for identifiers, single quotes for string literals.

---

## 2. Query Structure Best Practices

### Use CTEs Over Subqueries

CTEs improve readability and DuckDB auto-materializes identical CTEs, so repeated references cost nothing extra.

```sql
-- Good: CTEs with early filtering
WITH completed_orders AS (
    SELECT customer_id, amount
    FROM "analytics"."main"."orders"
    WHERE status = 'completed'
),
customer_totals AS (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM completed_orders
    GROUP BY customer_id
)
SELECT customer_id, total_spent
FROM customer_totals
WHERE total_spent > 1000;
```

### Filter Early

Push filters into the earliest CTE to reduce data volume before aggregations and joins.

### Pre-Aggregate for Repeated Reads

If the same expensive aggregation powers a dashboard, API, or frequent report, materialize it into a table or a light view instead of recomputing the full raw scan on every request.

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_revenue" AS
SELECT
    order_date,
    region,
    SUM(amount) AS total_amount
FROM "analytics"."main"."orders"
GROUP BY ALL;
```

### Use arg_max / arg_min Instead of Window Functions for "Most Recent" Queries

```sql
SELECT
    customer_id,
    arg_max(order_date, order_date) AS latest_order_date,
    arg_max(amount, order_date) AS latest_amount
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

`arg_max(value, order_col)` returns `value` from the row where `order_col` is highest. This avoids materializing the full window function result.

### Patterns to Avoid

- **Correlated subqueries** -- rewrite as joins or CTEs
- **Cartesian joins** -- always include a join condition
- **Unnecessary ORDER BY on intermediate CTEs** -- sort only the final result
- **SELECT * in production queries** -- list only the columns you need
- **Raw-table rescans for app-serving endpoints** -- publish a serving table or view instead

---

## 3. DuckDB SQL Patterns

### FROM-First Queries

Omit `SELECT *` for quick exploration:

```sql
FROM "my_db"."main"."users" WHERE active = true LIMIT 10;
```

Equivalent to `SELECT * FROM "my_db"."main"."users" WHERE active = true LIMIT 10;`.

### GROUP BY ALL

Automatically groups by every non-aggregated column:

```sql
SELECT category, region, SUM(sales) AS total_sales
FROM "my_db"."main"."transactions"
GROUP BY ALL;
```

### QUALIFY -- Filter Window Function Results

`QUALIFY` filters rows based on window function results without wrapping in a subquery. Use it instead of `WHERE` for window function conditions.

```sql
-- Top 1 order per customer by date
SELECT customer_id, order_date, amount
FROM "analytics"."main"."orders"
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;
```

```sql
-- Top 3 products per category by revenue
SELECT category, product_name, revenue
FROM "analytics"."main"."products"
QUALIFY RANK() OVER (PARTITION BY category ORDER BY revenue DESC) <= 3;
```

### EXCLUDE and REPLACE

Remove or transform columns without listing every column:

```sql
SELECT * EXCLUDE (internal_id, debug_flag) FROM "my_db"."main"."events";
SELECT * REPLACE (UPPER(name) AS name) FROM "my_db"."main"."customers";
SELECT * EXCLUDE (raw_payload) REPLACE (LOWER(email) AS email) FROM "my_db"."main"."users";
```

### Column Alias Reuse

DuckDB allows aliases in WHERE, GROUP BY, and HAVING:

```sql
SELECT price * quantity AS total
FROM "my_db"."main"."line_items"
WHERE total > 100;
```

### PIVOT

Transform rows into columns:

```sql
PIVOT "analytics"."main"."sales"
ON quarter
USING SUM(revenue)
GROUP BY region;
```

Result: one row per region with columns `Q1`, `Q2`, `Q3`, `Q4`.

### UNPIVOT

Transform columns into rows:

```sql
UNPIVOT "analytics"."main"."quarterly_report"
ON Q1, Q2, Q3, Q4
INTO NAME quarter VALUE revenue;
```

### UNION BY NAME

Combine tables with different column orders or partially overlapping schemas:

```sql
SELECT * FROM "db1"."main"."events_2023"
UNION BY NAME
SELECT * FROM "db1"."main"."events_2024";
```

Matches columns by name, not position. Missing columns become NULL.

### List Comprehensions

Transform list elements inline:

```sql
SELECT [x * 2 FOR x IN scores] AS doubled_scores
FROM "my_db"."main"."students";
```

### Function Chaining

Chain string (and other) functions:

```sql
SELECT name.upper().replace(' ', '_') AS clean_name
FROM "my_db"."main"."customers";
```

---

## 4. Schema Exploration Queries

Use these queries to understand your data before writing analytics.

### List All Databases

```sql
SELECT alias AS database_name, type
FROM MD_ALL_DATABASES();
```

### List Tables in a Database

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'my_db';
```

### Get Column Details

```sql
SELECT column_name, data_type, is_nullable, comment
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND table_name = 'orders';
```

### Quick Statistics

```sql
SUMMARIZE "my_db"."main"."orders";
```

Returns min, max, count, null count, unique count, and percentiles for every column.

---

## 5. Performance Optimization

### Filter Early in CTEs, Not at the End

Move WHERE clauses to the earliest possible CTE. Reducing row count before joins and aggregations is the single biggest optimization.

### Use Aggregate Functions Over Window Functions

Window functions materialize the entire result set. Prefer aggregate alternatives:

| Instead of | Use |
|---|---|
| `ROW_NUMBER() ... = 1` for latest row | `arg_max(value, order_col)` |
| `FIRST_VALUE() OVER (...)` | `arg_min(value, order_col)` |
| Window SUM for running total (when only final value needed) | Plain `SUM()` |

### Avoid SELECT * in Production

List only the columns you need. DuckDB uses columnar storage -- fewer columns means less data scanned.

### Use EXPLAIN to Understand Query Plans

```sql
EXPLAIN SELECT customer_id, SUM(amount)
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

In MotherDuck, the plan shows `(L)` for local operations and `(R)` for remote (cloud) operations. Push filters before remote scans for best performance.

### Avoid Functions on the Left Side of WHERE

Functions on filtered columns prevent predicate pushdown:

```sql
-- Bad: prevents pushdown
WHERE YEAR(order_date) = 2024

-- Good: enables pushdown
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
```

---

## 6. Common Query Patterns

### Top N Per Group

```sql
SELECT category, product_name, revenue
FROM "analytics"."main"."products"
QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) <= 5;
```

### Deduplication

Keep only the most recent row per key:

```sql
SELECT *
FROM "analytics"."main"."raw_events"
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at DESC) = 1;
```

### Running Totals

```sql
SELECT order_date, daily_revenue,
    SUM(daily_revenue) OVER (ORDER BY order_date) AS cumulative_revenue
FROM (
    SELECT order_date, SUM(amount) AS daily_revenue
    FROM "analytics"."main"."orders"
    GROUP BY order_date
);
```

### Year-over-Year Comparison

```sql
WITH monthly AS (
    SELECT EXTRACT(YEAR FROM order_date) AS yr,
           EXTRACT(MONTH FROM order_date) AS mo,
           SUM(amount) AS revenue
    FROM "analytics"."main"."orders"
    WHERE order_date >= '2023-01-01'
    GROUP BY ALL
)
SELECT curr.mo AS month, curr.revenue AS revenue_2024,
       prev.revenue AS revenue_2023,
       ROUND(100.0 * (curr.revenue - prev.revenue) / prev.revenue, 1) AS yoy_pct
FROM monthly curr
JOIN monthly prev ON curr.mo = prev.mo
WHERE curr.yr = 2024 AND prev.yr = 2023
ORDER BY curr.mo;
```

### Conditional Aggregation with FILTER

```sql
SELECT
    customer_id,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'returned') AS returned_orders,
    SUM(amount) FILTER (WHERE status = 'completed') AS completed_revenue
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

---

## 7. Key Rules

- Use **DuckDB SQL syntax**, never PostgreSQL SQL -- even when connected via the Postgres endpoint.
- Always use **fully qualified table names**: `"database"."schema"."table"`.
- Use **CTEs** for readability and to benefit from DuckDB's auto-materialization.
- Use **QUALIFY** to filter window function results -- never wrap in a subquery.
- Use **GROUP BY ALL** to avoid repeating non-aggregated column lists.
- Use **arg_max / arg_min** for "most recent" or "first" value queries instead of window functions.
- Use **FILTER** for conditional aggregation instead of CASE WHEN inside aggregate functions.

---

## 8. Common Mistakes

- **Using PostgreSQL-specific syntax** -- `ILIKE`, `::text`, `NOW()` may not behave identically. Consult `duckdb-sql` skill for correct syntax.
- **Forgetting fully qualified table names** -- unqualified names fail when multiple databases are attached.
- **Using WHERE to filter window functions** -- use QUALIFY instead. `WHERE` cannot reference window function results.
- **Over-using ORDER BY on intermediate results** -- sorting is expensive; sort only the final output.
- **Applying functions on WHERE column side** -- `WHERE LOWER(name) = 'foo'` prevents pushdown. Store normalized data or use generated columns.
- **Installing extensions at runtime** -- MotherDuck supports only the 12 pre-installed extensions. Do not run `INSTALL` or `LOAD` for unsupported extensions.

---

## Related Skills

- `connect` -- establish a MotherDuck connection
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup
- `explore` -- discover databases, tables, columns, and shares

# Query Playbook

Reference for writing DuckDB SQL against MotherDuck, choosing the right query patterns, and avoiding common analytical-query mistakes.

## SQL-First Posture

- Keep the query logic in SQL rather than pushing grouping, filtering, and reshaping into the caller.
- Write multi-line SQL with explicit aliases, explicit grain, and explicit fully qualified table names.
- Leave value binding to the caller, but keep the SQL itself obvious and production-readable.
- Return pre-aggregated results when the workload is a repeated dashboard, app-serving endpoint, or shared analytical surface.

## Compute and Storage Posture

- Filter early and aggregate early.
- Prefer curated tables, views, or pre-aggregated summary tables for repeated dashboards and app-serving queries.
- Use `LIMIT` or aggregates during exploration.
- Tag long-lived integrations with `custom_user_agent` so query history can attribute cost and workload shape later.
- When validating multi-database patterns in the native DuckDB API, use a workspace connection (`md:`) and fully qualified names.

## SQL Starter

```sql
SELECT
    customer_id,
    SUM(amount) AS total_spent
FROM "analytics"."main"."orders"
WHERE order_date >= DATE '2025-01-01'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 20;
```

## Always Use Fully Qualified Table Names

```sql
SELECT * FROM "my_db"."main"."orders" LIMIT 10;
```

Use double quotes for identifiers and single quotes for string literals.

## Query Structure Best Practices

### Use CTEs Over Subqueries

```sql
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

### Pre-Aggregate for Repeated Reads

Creating or replacing tables changes state. When the runner is MCP, use `query_rw` only after the user explicitly asks for the table change and confirms what will be modified.

```sql
CREATE OR REPLACE TABLE "analytics"."main"."daily_revenue" AS
SELECT
    order_date,
    region,
    SUM(amount) AS total_amount
FROM "analytics"."main"."orders"
GROUP BY ALL;
```

### Use `arg_max` / `arg_min` for Most-Recent Queries

```sql
SELECT
    customer_id,
    arg_max(order_date, order_date) AS latest_order_date,
    arg_max(amount, order_date) AS latest_amount
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

### Patterns to Avoid

- correlated subqueries
- cartesian joins
- unnecessary `ORDER BY` in intermediate CTEs
- `SELECT *` in production queries
- raw-table rescans for app-serving endpoints

## Duckling Lifecycle Commands

Use lifecycle commands only for operational control after the user has explicitly asked to stop a Duckling or optimize batch/CI cost.

```sql
SHUTDOWN;
SHUTDOWN TERMINATE (REASON 'batch complete');
```

- `SHUTDOWN` registers a graceful shutdown and lets running work complete.
- `SHUTDOWN TERMINATE` interrupts running queries and should be reserved for stuck or explicitly force-stopped Ducklings.
- Both are subject to the minimum billing period documented for Duckling compute.
- In MCP, lifecycle commands require `query_rw` and explicit user confirmation.

## Recovery Commands

Use database recovery commands only when the user explicitly wants to preserve, clone, restore, or recover database state. Snapshot retention and point-in-time recovery support are plan-specific, so verify the current data-recovery docs before promising a window.

```sql
CREATE SNAPSHOT release_cutover OF analytics;

CREATE DATABASE analytics_restore FROM analytics (
    SNAPSHOT_NAME 'release_cutover'
);

ALTER DATABASE analytics SET SNAPSHOT TO (
    SNAPSHOT_NAME 'release_cutover'
);

UNDROP DATABASE analytics;
```

In MCP, these are write operations and require `query_rw` plus explicit confirmation.

## DuckDB SQL Patterns

### `FROM`-First Queries

```sql
FROM "my_db"."main"."users" WHERE active = true LIMIT 10;
```

### `GROUP BY ALL`

```sql
SELECT category, region, SUM(sales) AS total_sales
FROM "my_db"."main"."transactions"
GROUP BY ALL;
```

### `QUALIFY`

```sql
SELECT customer_id, order_date, amount
FROM "analytics"."main"."orders"
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;
```

```sql
SELECT category, product_name, revenue
FROM "analytics"."main"."products"
QUALIFY RANK() OVER (PARTITION BY category ORDER BY revenue DESC) <= 3;
```

### `EXCLUDE` and `REPLACE`

```sql
SELECT * EXCLUDE (internal_id, debug_flag) FROM "my_db"."main"."events";
SELECT * REPLACE (UPPER(name) AS name) FROM "my_db"."main"."customers";
SELECT * EXCLUDE (raw_payload) REPLACE (LOWER(email) AS email) FROM "my_db"."main"."users";
```

### Column Alias Reuse

```sql
SELECT price * quantity AS total
FROM "my_db"."main"."line_items"
WHERE total > 100;
```

### `PIVOT`

```sql
PIVOT "analytics"."main"."sales"
ON quarter
USING SUM(revenue)
GROUP BY region;
```

### `UNPIVOT`

```sql
UNPIVOT "analytics"."main"."quarterly_report"
ON Q1, Q2, Q3, Q4
INTO NAME quarter VALUE revenue;
```

### `UNION BY NAME`

```sql
SELECT * FROM "db1"."main"."events_2023"
UNION BY NAME
SELECT * FROM "db1"."main"."events_2024";
```

### List Comprehensions

```sql
SELECT [x * 2 FOR x IN scores] AS doubled_scores
FROM "my_db"."main"."students";
```

### Function Chaining

```sql
SELECT name.upper().replace(' ', '_') AS clean_name
FROM "my_db"."main"."customers";
```

## Schema Exploration Queries

```sql
SELECT alias AS database_name, type
FROM MD_ALL_DATABASES();
```

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'my_db';
```

```sql
SELECT column_name, data_type, is_nullable, comment
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND table_name = 'orders';
```

```sql
SUMMARIZE "my_db"."main"."orders";
```

## Performance Optimization

- Filter early in CTEs, not at the end.
- Prefer aggregate alternatives when a window function is not required.
- Avoid `SELECT *` in production.
- Use `EXPLAIN` to understand plans.
- Avoid functions on the left side of `WHERE` when pushdown matters.

### `EXPLAIN`

```sql
EXPLAIN SELECT customer_id, SUM(amount)
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

### Predicate Pushdown Example

```sql
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
```

## Common Query Patterns

### Top N Per Group

```sql
SELECT category, product_name, revenue
FROM "analytics"."main"."products"
QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) <= 5;
```

### Deduplication

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

### Conditional Aggregation with `FILTER`

```sql
SELECT
    customer_id,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'returned') AS returned_orders,
    SUM(amount) FILTER (WHERE status = 'completed') AS completed_revenue
FROM "analytics"."main"."orders"
GROUP BY customer_id;
```

## Key Rules

- Use DuckDB SQL syntax, never PostgreSQL SQL.
- Always use fully qualified table names.
- Use CTEs for readability and DuckDB-friendly planning.
- Use `QUALIFY` to filter window-function results.
- Use `GROUP BY ALL` to avoid duplicated grouping lists.
- Use `arg_max` and `arg_min` for latest/first-value patterns where applicable.
- Use `FILTER` for conditional aggregation.

## Common Mistakes

- Using PostgreSQL-specific syntax
- Forgetting fully qualified table names
- Using `WHERE` to filter window functions instead of `QUALIFY`
- Over-using intermediate `ORDER BY`
- Applying functions on the filtered column side of `WHERE`
- Installing extensions at runtime

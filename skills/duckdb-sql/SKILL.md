---
name: duckdb-sql
description: DuckDB SQL syntax reference for MotherDuck. Use when you need to look up DuckDB-specific syntax, data types, functions, extensions, or resolve SQL errors. Covers friendly SQL, complex types, pre-installed extensions, and MotherDuck-specific SQL.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: utility
  language_focus: "typescript|javascript|python"
  depends_on: []
---

# DuckDB SQL Reference for MotherDuck

Use this skill when you need to look up DuckDB-specific syntax, data types, functions, or extensions — or when debugging SQL errors against MotherDuck. This is a reference skill with no dependencies.

## Critical Rule

**Always write DuckDB SQL, NEVER PostgreSQL SQL** — even when connecting through the MotherDuck Postgres endpoint. The PG endpoint speaks the PostgreSQL wire protocol but executes DuckDB SQL on the server. PostgreSQL-specific functions, syntax, and system catalogs do not work.

## Language Focus: TypeScript/Javascript and Python

- This skill is language-agnostic at the SQL layer, but its main consumers in this repo should be:
  - **Python** data and pipeline code
  - **TypeScript/Javascript** backend and product code
- When explaining syntax, prefer examples that drop directly into Python triple-quoted strings or TypeScript template strings.
- When the user asks for a full application snippet:
  - show DuckDB SQL first
  - then wrap it in Python or TypeScript/Javascript second
- Warn against:
  - PostgreSQL-only syntax leaking into TS/JS apps using the PG endpoint
  - Python or JS code trying to compensate for SQL that should be written correctly in DuckDB instead

## String Embedding Pattern

Use clean multi-line SQL strings in both languages.

```ts
const sql = `
  SELECT strftime(date_trunc('month', created_at), '%Y-%m') AS month,
         COUNT(*) AS events
  FROM "analytics"."main"."events"
  GROUP BY 1
  ORDER BY 1
`;
```

```python
sql = """
SELECT strftime(date_trunc('month', created_at), '%Y-%m') AS month,
       COUNT(*) AS events
FROM "analytics"."main"."events"
GROUP BY 1
ORDER BY 1
"""
```

---

## Friendly SQL Quick Reference

DuckDB extends standard SQL with several convenience features collectively known as "Friendly SQL."

### FROM-First Queries

```sql
FROM orders WHERE status = 'shipped';  -- Equivalent to SELECT * FROM ...
```

### SELECT Without FROM

```sql
SELECT 1 + 1 AS result;
```

### Alias Reuse in WHERE, GROUP BY, HAVING

```sql
SELECT price * quantity AS total, category
FROM line_items
WHERE total > 100
GROUP BY category;
```

### GROUP BY ALL / ORDER BY ALL

```sql
SELECT category, region, SUM(sales) AS total_sales FROM revenue GROUP BY ALL;
SELECT * FROM my_table ORDER BY ALL;
```

### UNION BY NAME

```sql
SELECT name, age FROM employees_us
UNION BY NAME
SELECT age, name, department FROM employees_eu;
```

---

## Column Selection

### EXCLUDE

```sql
SELECT * EXCLUDE (password_hash, ssn) FROM users;
```

### REPLACE

```sql
SELECT * REPLACE (UPPER(name) AS name, ROUND(salary, 0) AS salary) FROM employees;
```

### COLUMNS Pattern

```sql
SELECT COLUMNS('sales_.*') FROM quarterly_data;        -- Regex column match
SELECT AVG(COLUMNS('metric_.*')) FROM measurements;    -- Aggregate matched columns
```

---

## QUALIFY Clause

Filter rows based on window function results without a subquery:

```sql
-- Top 2 products by sales in each category
SELECT category, product, sales
FROM products
QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) <= 2;

-- Most recent order per customer
SELECT customer_id, order_date, amount
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;
```

---

## Complex Data Types

### Lists

Variable-length arrays. **1-indexed.**

```sql
SELECT [1, 2, 3] AS nums;
SELECT nums[1] AS first;           -- 1  (1-indexed!)
SELECT nums[1:2] AS slice;         -- [1, 2]
SELECT list_append(nums, 4);       -- [1, 2, 3, 4]
SELECT UNNEST([10, 20, 30]) AS val; -- Expands to 3 rows

-- List comprehensions
SELECT [x * 2 FOR x IN [1, 2, 3]]; -- [2, 4, 6]
SELECT [x FOR x IN list_col IF x > 5] FROM t;
```

### Structs

Named fields with fixed schema:

```sql
SELECT {'name': 'Alice', 'age': 30} AS person;
SELECT person.name;                -- 'Alice'
SELECT person['age'];              -- 30
```

### Maps

Key-value pairs with uniform types:

```sql
SELECT MAP([1, 2], ['one', 'two']) AS m;
SELECT m[1];                       -- 'one'
```

### JSON

Use the `json` extension (pre-installed):

```sql
SELECT '{"user": "alice", "score": 99}'::JSON AS data;
SELECT data->>'user';              -- 'alice' (returns text)
SELECT data->'$.score';            -- 99 (returns JSON)
```

### Function Chaining

Call string/list methods with dot syntax:

```sql
SELECT 'DuckDB'.replace('Duck', 'Goose').upper(); -- 'GOOSEDB'
SELECT 'hello world'.split(' ').list_sort();       -- ['hello', 'world']
```

### Slicing (1-indexed)

```sql
SELECT 'DuckDB'[1:4];             -- 'Duck'
SELECT [10, 20, 30, 40][2:3];     -- [20, 30]
```

---

## Date/Time Operations

```sql
SELECT strptime('2023-07-23', '%Y-%m-%d')::TIMESTAMP;              -- Parse string
SELECT strftime(NOW(), '%Y-%m-%d %H:%M:%S');                        -- Format
SELECT EXTRACT(YEAR FROM DATE '2023-07-23');                         -- 2023
SELECT date_trunc('month', TIMESTAMP '2023-07-23 14:30:00');        -- 2023-07-01
SELECT DATE '2023-07-23' + INTERVAL 30 DAY;                         -- Arithmetic
SELECT date_diff('day', DATE '2023-01-01', DATE '2023-07-23');      -- 203
SELECT current_date, current_timestamp, NOW();
```

---

## Type Conversion

```sql
-- Implicit conversion
SELECT '42' + 1;                    -- 43 (string to integer)

-- Explicit casting
SELECT CAST(3.14 AS INTEGER);      -- 3
SELECT '42'::INTEGER;               -- 42
SELECT CAST(col AS DOUBLE) FROM t;

-- Safe casting (returns NULL on failure instead of error)
SELECT TRY_CAST('abc' AS INTEGER);  -- NULL
```

---

## Aggregation Shortcuts

### arg_max / arg_min

Get the value of one column at the row where another column is max/min — avoids complex window functions:

```sql
-- Most recent status per customer (no window function needed)
SELECT customer_id, arg_max(status, updated_at) AS latest_status
FROM orders
GROUP BY customer_id;

-- Cheapest product name per category
SELECT category, arg_min(product_name, price) AS cheapest
FROM products
GROUP BY category;
```

### PIVOT

```sql
PIVOT monthly_sales
ON month
USING SUM(revenue)
GROUP BY product;
```

### UNPIVOT

```sql
UNPIVOT quarterly_data
ON q1, q2, q3, q4
INTO NAME quarter VALUE revenue;
```

---

## Pre-installed Extensions

MotherDuck has exactly 12 pre-installed extensions. **You cannot install additional extensions at runtime.**

| Extension | Purpose |
|-----------|---------|
| `azure` | Read/write Azure Blob Storage |
| `delta` | Read Delta Lake tables |
| `ducklake` | DuckLake catalog support |
| `encodings` | Additional encoding support |
| `excel` | Read/write Excel files |
| `httpfs` | Read files over HTTP/S3/GCS |
| `iceberg` | Read Apache Iceberg tables |
| `icu` | Unicode collation and timezone support |
| `json` | JSON parsing and extraction |
| `parquet` | Read/write Parquet files |
| `spatial` | Geospatial types and functions (GEOMETRY, ST_*) |
| `h3` | Uber H3 hexagonal grid system |

---

## MotherDuck-Specific SQL

### Schema Exploration

```sql
-- List all databases
SELECT alias AS database_name, type FROM MD_ALL_DATABASES();

-- List tables in a database
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'my_db';

-- List views
SELECT database_name, schema_name, view_name, sql
FROM duckdb_views()
WHERE database_name = 'my_db';

-- Column metadata
SELECT column_name, data_type, is_nullable, comment
FROM duckdb_columns()
WHERE database_name = 'my_db' AND table_name = 'my_table';

-- Quick statistics
SUMMARIZE my_table;
```

### Dives (Interactive Data Apps)

```sql
-- Create a Dive
SELECT MD_CREATE_DIVE('dive_title', 'prompt or description');

-- Update Dive content
SELECT MD_UPDATE_DIVE_CONTENT('dive_id', 'updated prompt');
```

### Data Sharing

```sql
-- Create a share
CREATE SHARE my_share FROM my_database (
  ACCESS ORGANIZATION,
  VISIBILITY DISCOVERABLE,
  UPDATE MANUAL
);

-- List shares you own
LIST SHARES;

-- Push a new snapshot to a manual share
UPDATE SHARE my_share;

-- Drop a share
DROP SHARE my_share;

-- Consumer: info about shares shared with you
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;

-- Owner: info about your shares
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;

-- Consumer: attach a share URL
ATTACH 'md:_share/birds/e9ads7-dfr32-41b4-a230-bsadgfdg32tfa' AS birds;
```

---

## Unsupported in MotherDuck (vs Local DuckDB)

These features work in local DuckDB but are **not available** on MotherDuck:

- **Custom Python/native UDFs** — user-defined functions cannot be registered
- **Custom/community extensions** — only the 12 pre-installed extensions are available
- **Runtime extension installation** — `INSTALL` and `LOAD` statements are blocked
- **Some SET configuration statements** — certain DuckDB configuration options are restricted
- **Server-side database attachments** — attaching arbitrary databases from the server file system

---

## Common Mistakes

### 1. Using PostgreSQL syntax

```sql
-- WRONG: PostgreSQL system catalog
SELECT * FROM pg_catalog.pg_tables;

-- RIGHT: DuckDB system functions
SELECT * FROM duckdb_tables();

-- WRONG: PostgreSQL function
SELECT to_char(date_col, 'YYYY-MM-DD');

-- RIGHT: DuckDB function
SELECT strftime(date_col, '%Y-%m-%d');
```

### 2. Trying to install extensions at runtime

```sql
-- WRONG: Will fail on MotherDuck
INSTALL spatial;
LOAD spatial;

-- RIGHT: Extensions are pre-installed — just use them
SELECT ST_Point(40.7, -74.0);
```

### 3. Forgetting 1-based indexing

```sql
-- WRONG: 0-based (returns NULL or unexpected result)
SELECT my_list[0];
SELECT 'DuckDB'[0:3];

-- RIGHT: 1-based indexing
SELECT my_list[1];       -- First element
SELECT 'DuckDB'[1:4];   -- 'Duck'
```

### 4. Confusing NULL handling

```sql
SELECT NULL = NULL;                  -- NULL (not TRUE!)
SELECT NULL IS NULL;                 -- TRUE
SELECT COALESCE(nullable_col, 'default') FROM t;  -- Use COALESCE/IFNULL
```

### 5. Using FROM with expressions that do not need it

```sql
-- WRONG                              -- RIGHT
SELECT 1 + 1 FROM dual;              SELECT 1 + 1 AS result;
```

---

## Related Skills

- **`query`** — Execute SQL queries against MotherDuck databases
- **`explore`** — Discover databases, tables, columns, and shares

See `references/SYNTAX_REFERENCE.md` for the complete function and data type reference.

---
name: explore
description: Discover and explore databases, tables, columns, and data shares in MotherDuck. Use when you need to understand what data is available, preview table contents, or search the data catalog.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: utility
  language_focus: "typescript|javascript|python"
  depends_on: []
---

# Explore MotherDuck Data

Use this skill when you need to discover what databases, tables, and columns exist in a MotherDuck account; preview and sample data; understand schemas and data types; find shared databases; or search the data catalog.

## Prerequisites

Establish a MotherDuck connection before exploring data. See the `connect` skill for setup instructions.

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** when exploration is part of:
  - notebook work
  - profiling source data before modeling
  - batch validation scripts
- Prefer **TypeScript/Javascript** when exploration is part of:
  - API endpoints
  - admin tools
  - schema discovery in product or developer tooling
- In Python, it is fine to fetch small result sets into DataFrames for inspection after the SQL is correct.
- In TypeScript/Javascript, keep exploration server-side and return compact summaries rather than pushing raw catalog output into a frontend.

## TypeScript/Javascript Starter

```ts
import pg from "pg";

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "analytics",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

await client.connect();
const databases = await client.query(`SELECT alias, type FROM MD_ALL_DATABASES()`);
const tables = await client.query(`
  SELECT database_name, schema_name, table_name, comment
  FROM duckdb_tables()
  WHERE database_name = 'analytics'
`);
await client.end();
```

## Python Starter

```python
import duckdb

conn = duckdb.connect("md:analytics")
databases = conn.sql("SELECT alias, type FROM MD_ALL_DATABASES()").fetchall()
columns = conn.sql("""
    SELECT column_name, data_type, comment
    FROM duckdb_columns()
    WHERE database_name = 'analytics'
      AND table_name = 'orders'
""").fetchall()
conn.close()
```

## Exploration Workflow

Always explore data top-down. Follow these steps in order:

1. **List databases** to see what is available.
2. **List tables** in the target database.
3. **Inspect columns** and their types for the target table.
4. **Run SUMMARIZE** to get statistics and understand data distributions.
5. **Sample rows** to see actual data values.

Do not skip steps. Understanding the schema before querying prevents wasted effort and incorrect assumptions.

---

## Step 1: List Databases

Retrieve all databases attached to the current session, including both owned and shared databases.

```sql
SELECT alias AS database_name, type
FROM MD_ALL_DATABASES();
```

The `type` column indicates whether a database is local, cloud, or shared. Pay attention to shared databases -- they often contain data you need but might overlook.

---

## Step 2: List Tables in a Database

Once you identify the target database, list its tables.

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'my_database';
```

Read the `comment` column. Table comments often describe the contents and purpose of the table, saving you from unnecessary exploration.

### List Views

Views may contain pre-built logic and curated datasets. Always check for views alongside tables.

```sql
SELECT database_name, schema_name, view_name, comment, sql
FROM duckdb_views()
WHERE database_name = 'my_database';
```

The `sql` column contains the view definition. Inspect it to understand the transformations applied.

---

## Step 3: Inspect Columns and Types

Examine the structure of a specific table before querying it.

```sql
SELECT column_name, data_type, comment, is_nullable
FROM duckdb_columns()
WHERE database_name = 'my_database'
  AND table_name = 'my_table';
```

Pay attention to:
- **data_type**: Know whether a column is a `VARCHAR`, `INTEGER`, `TIMESTAMP`, `STRUCT`, `LIST`, or another type before writing filters or aggregations.
- **is_nullable**: Nullable columns require `NULL`-safe comparisons and may need `COALESCE` in aggregations.
- **comment**: Column-level comments describe semantics that the column name alone may not convey.

---

## Step 4: Get Quick Statistics with SUMMARIZE

Run `SUMMARIZE` before writing any analytical query. It provides a comprehensive statistical overview of every column in a single call.

```sql
SUMMARIZE "my_database"."main"."my_table";
```

`SUMMARIZE` returns one row per column with these fields:

| Field | Description |
|---|---|
| `column_name` | Name of the column |
| `column_type` | Data type |
| `min` | Minimum value |
| `max` | Maximum value |
| `approx_unique` | Approximate number of distinct values |
| `avg` | Average (numeric columns) |
| `std` | Standard deviation (numeric columns) |
| `q25` | 25th percentile |
| `q50` | Median (50th percentile) |
| `q75` | 75th percentile |
| `count` | Total non-null count |
| `null_percentage` | Percentage of null values |

Use this output to understand value ranges, detect null-heavy columns, estimate cardinality for joins, and identify potential data quality issues -- all before writing a single analytical query.

---

## Step 5: Preview Data

Sample actual rows to see real values and verify your understanding of the schema.

```sql
FROM "my_database"."main"."my_table" LIMIT 10;
```

Always use fully qualified table names (`database.schema.table`) to avoid ambiguity when multiple databases are attached.

---

## Working with Shares

Shared databases are read-only databases that other MotherDuck users have shared with you. They behave like regular databases once attached. Always check for available shares -- they may contain exactly the data you need.

### List Shares Available to You

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

This returns share names, URLs, owners, and metadata. Use the URL to attach shares.

### List Your Owned Shares

```sql
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;
```

### Attach a Shared Database

```sql
ATTACH '<share_url>' AS shared_db;
```

Replace `<share_url>` with the URL from the `SHARED_WITH_ME` query. Choose a meaningful alias that describes the data.

### Refresh Shared Data

Shared databases may be updated by their owners. Refresh to get the latest data.

```sql
REFRESH DATABASE shared_db;
```

### Query Shared Data

Once attached, query shared tables like any other table.

```sql
FROM shared_db.main.my_table LIMIT 10;
```

---

## MCP Tools Available

When using the MotherDuck MCP server, prefer these tools for exploration tasks. They are purpose-built, require no SQL, and return structured results.

| Tool | Purpose |
|---|---|
| `list_databases` | List all attached databases |
| `list_tables` | List tables in a specific database |
| `list_columns` | List columns and types for a specific table |
| `search_catalog` | Search across the entire data catalog by keyword |
| `list_shares` | List available data shares |
| `query` | Execute read-only SQL queries |
| `ask_docs_question` | Ask questions about DuckDB and MotherDuck documentation |

Use `search_catalog` when you do not know which database or table contains the data you need. It searches across all databases and returns matching tables and columns.

Use `ask_docs_question` when you need clarification on DuckDB SQL syntax, MotherDuck-specific features, or supported functions.

---

## Advanced Exploration Patterns

### Find Tables Matching a Pattern

Search across all databases for tables with names containing a keyword.

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE table_name LIKE '%sales%';
```

### Find Columns of a Specific Type

Locate all timestamp columns in a database, useful for identifying time-series data.

```sql
SELECT table_name, column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND data_type = 'TIMESTAMP';
```

### Get Table Row Counts

Estimate the size of tables before running expensive queries.

```sql
SELECT table_name, estimated_size
FROM duckdb_tables()
WHERE database_name = 'my_db'
ORDER BY estimated_size DESC;
```

### Find Columns by Name Across Tables

Locate a specific column (e.g., `customer_id`) across all tables in a database to understand join relationships.

```sql
SELECT table_name, column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND column_name LIKE '%customer%';
```

### Explore Nested and Complex Types

For columns with `STRUCT`, `LIST`, or `MAP` types, preview values to understand their structure.

```sql
SELECT complex_column
FROM "my_db"."main"."my_table"
LIMIT 5;
```

Then unnest if needed:

```sql
SELECT UNNEST(list_column)
FROM "my_db"."main"."my_table"
LIMIT 20;
```

---

## Key Rules

- **Explore top-down**: databases, then tables, then columns. Never jump straight to querying.
- **Run SUMMARIZE before writing queries** to understand data distributions, null rates, and value ranges.
- **Use fully qualified table names** (`database.schema.table`) in all queries to avoid ambiguity.
- **Check shared databases** before concluding that data is unavailable. Shared databases are easy to miss.
- **Read comments** on tables and columns. They contain context that column names alone do not provide.
- **Use MCP tools when available**. They are faster and return structured results optimized for exploration.

---

## Common Mistakes

- **Querying tables without checking the schema first.** This leads to wrong assumptions about column names, types, and nullability. Always inspect columns before writing filters or aggregations.
- **Missing shared databases.** Shared databases do not appear in standard `duckdb_tables()` output until attached. Always run `SHARED_WITH_ME` to check for available shares.
- **Not using SUMMARIZE to understand data quality.** Skipping `SUMMARIZE` means you miss null rates, value ranges, and cardinality -- all critical for writing correct queries.
- **Using unqualified table names.** When multiple databases are attached, unqualified names cause ambiguity errors or silently resolve to the wrong table.
- **Ignoring views.** Views often contain pre-built transformations and curated datasets. Always check `duckdb_views()` alongside `duckdb_tables()`.

---

## Related Skills

- `connect` -- Set up and manage MotherDuck connections.
- `query` -- Execute SQL queries against MotherDuck data.
- `duckdb-sql` -- DuckDB SQL syntax reference and patterns.
- `share-data` -- Create and manage data shares.

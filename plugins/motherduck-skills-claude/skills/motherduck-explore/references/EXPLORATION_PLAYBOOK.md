# Exploration Playbook

Reference for discovering databases, tables, columns, views, shares, and data quality signals in MotherDuck.

## Language Focus

- Prefer **Python** when exploration is part of notebook work, profiling source data before modeling, or batch validation scripts.
- Prefer **TypeScript/Javascript** when exploration is part of API endpoints, admin tools, or schema discovery inside developer tooling.
- In Python, small result sets can be fetched into DataFrames after the SQL is correct.
- In TypeScript/Javascript, keep exploration server-side and return compact summaries instead of raw catalog dumps.

### TypeScript/Javascript Starter

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

### Python Starter

```python
import duckdb

conn = duckdb.connect("md:")
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

1. List databases to see what is available.
2. List tables in the target database.
3. Inspect columns and types for the target table.
4. Run `SUMMARIZE` to get statistics.
5. Sample rows to see actual values.

## Step 1: List Databases

```sql
SELECT alias AS database_name, type
FROM MD_ALL_DATABASES();
```

## Step 2: List Tables in a Database

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'my_database';
```

### List Views

```sql
SELECT database_name, schema_name, view_name, comment, sql
FROM duckdb_views()
WHERE database_name = 'my_database';
```

## Step 3: Inspect Columns and Types

```sql
SELECT column_name, data_type, comment, is_nullable
FROM duckdb_columns()
WHERE database_name = 'my_database'
  AND table_name = 'my_table';
```

Pay attention to:

- `data_type`
- `is_nullable`
- `comment`

## Step 4: Get Quick Statistics with `SUMMARIZE`

```sql
SUMMARIZE "my_database"."main"."my_table";
```

`SUMMARIZE` returns one row per column with min, max, approximate distinct counts, percentiles, counts, and null percentages.

## Step 5: Preview Data

```sql
FROM "my_database"."main"."my_table" LIMIT 10;
```

When exploring several MotherDuck databases in one session, prefer a workspace connection (`md:`).

## Working with Shares

### List Shares Available to You

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

### List Your Owned Shares

```sql
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;
```

### Attach a Shared Database

```sql
ATTACH '<share_url>' AS shared_db;
```

### Refresh Shared Data

```sql
REFRESH DATABASE shared_db;
```

### Query Shared Data

```sql
FROM shared_db.main.my_table LIMIT 10;
```

## MCP Tools Available

When using the MotherDuck MCP server, prefer:

| Tool | Purpose |
|---|---|
| `list_databases` | List attached databases |
| `list_tables` | List tables in a database |
| `list_columns` | List columns and types |
| `search_catalog` | Search the data catalog |
| `list_shares` | List available data shares |
| `motherduck-query` | Execute read-only SQL |
| `ask_docs_question` | Clarify product or SQL behavior |

Use `search_catalog` when you do not know which database or table contains the data you need.

## Advanced Exploration Patterns

### Find Tables Matching a Pattern

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE table_name LIKE '%sales%';
```

### Find Columns of a Specific Type

```sql
SELECT table_name, column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND data_type = 'TIMESTAMP';
```

### Get Table Row Counts

```sql
SELECT table_name, estimated_size
FROM duckdb_tables()
WHERE database_name = 'my_db'
ORDER BY estimated_size DESC;
```

### Find Columns by Name Across Tables

```sql
SELECT table_name, column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'my_db'
  AND column_name LIKE '%customer%';
```

### Explore Nested and Complex Types

```sql
SELECT complex_column
FROM "my_db"."main"."my_table"
LIMIT 5;
```

```sql
SELECT UNNEST(list_column)
FROM "my_db"."main"."my_table"
LIMIT 20;
```

## Key Rules

- Explore top-down: databases, then tables, then columns.
- Run `SUMMARIZE` before writing analytical queries.
- Use fully qualified table names.
- Check shared databases before concluding data is unavailable.
- Read table and column comments.
- Use MCP tools when available.

## Common Mistakes

- Querying tables without checking the schema first
- Missing shared databases
- Skipping `SUMMARIZE`
- Using unqualified table names
- Ignoring views that already contain curated logic

---
name: connect
description: Connect to MotherDuck from any application. Use when setting up database connectivity via the Postgres endpoint (recommended), pg_duckdb, native DuckDB API, or JDBC. Covers connection strings, authentication, SSL, and environment variable configuration.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: utility
  language_focus: "typescript|javascript|python"
  depends_on: []
---

# Connect to MotherDuck

Use this skill when establishing database connectivity from any application, script, or service to MotherDuck. Start here before running queries or loading data.

For reusable language patterns, see `references/typescript.md` and `references/python.md`.

## Source Of Truth

- Prefer current MotherDuck connection, attach-mode, read-scaling, and multithreading docs.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first for current connection behavior.
- When it is unavailable, verify guidance against the public docs before making firm claims about connection strings, token types, or read-scaling behavior.

## Choose a Connection Method

Pick one. Do not mix methods in the same application.

```
Is this a backend app or script?
├── Yes ─── Do you need hybrid local/cloud execution?
│           ├── No  ──> PG Endpoint (DEFAULT — start here)
│           └── Yes ──> Native DuckDB API (md: protocol)
├── Extending an existing PostgreSQL database?
│           └── Yes ──> pg_duckdb
└── Browser-only analytics under 1GB?
            └── Yes ──> DuckDB-WASM
```

**Use the PG endpoint for backend applications that already want PostgreSQL wire compatibility.** It requires no DuckDB installation and works with standard PostgreSQL drivers. If the runtime can use DuckDB directly and you need local files, hybrid execution, or tighter DuckDB control, use the native DuckDB API instead.

## Operational Defaults

- Start with **one connection**. A single DuckDB or MotherDuck connection already executes one query at a time efficiently.
- Add **connection pooling** only for long-lived read-only concurrency or queue-style backends.
- Add **read scaling** only when many concurrent read-only users on the same account are actually the bottleneck.
- Use **single attach mode** for narrow app or BI connections that should not persist attachment changes.
- Use **workspace mode** only when the client intentionally wants shared, persistent attachment state across sessions.

---

## Prerequisites

1. A MotherDuck account (sign up at https://motherduck.com)
2. A MotherDuck access token
3. A database created in MotherDuck

## Language Focus: TypeScript/Javascript and Python

- Prefer **TypeScript/Javascript** examples when the user is building:
  - backend APIs in Node.js
  - serverless functions
  - Next.js or Express applications
  - customer-facing analytics products
- Prefer **Python** examples when the user is building:
  - data pipelines
  - notebooks
  - backend services in FastAPI
  - ETL, orchestration, or ad-hoc operational scripts
- For Node backends, default to:
  - `pg` for the PG endpoint
  - `@duckdb/node-api` for native DuckDB API usage
- For Python, default to:
  - `psycopg` or SQLAlchemy on the PG endpoint
  - `duckdb` for native DuckDB API usage
- When both languages are plausible, choose the example that matches the user's runtime and deployment surface rather than the one that is shortest.

## Typed Environment Pattern

Use small helpers so connection setup fails early and clearly.

```ts
function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing env var: ${name}`);
  return value;
}
```

```python
import os

def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value
```

---

## Step 1: Set the Environment Variable

Store the token in an environment variable. NEVER hardcode tokens in source code.

```bash
export MOTHERDUCK_TOKEN="<your_token>"
```

Add this to your shell profile (`.bashrc`, `.zshrc`) or your deployment environment's secret manager (AWS Secrets Manager, Vault, Doppler, etc.).

---

## Step 2: Connect via PG Endpoint (Default)

### Connection String

```
postgresql://postgres:<MOTHERDUCK_TOKEN>@pg.us-east-1-aws.motherduck.com:5432/<database>?sslmode=verify-full&sslrootcert=system
```

Use the regional hostname that matches the target MotherDuck deployment. For example, public docs also show regional hosts such as `pg.eu-central-1-aws.motherduck.com`.

### Connection Components

| Component   | Value                                      | Notes                          |
|-------------|--------------------------------------------|---------------------------------|
| **Host**    | `pg.us-east-1-aws.motherduck.com`          | Example regional host; verify the target region |
| **Port**    | `5432`                                     | Standard PostgreSQL port       |
| **User**    | `postgres`                                 | Fixed value, do not change     |
| **Password**| Your MotherDuck access token               | Use env var, never hardcode    |
| **Database**| Your MotherDuck database name              | e.g., `my_database`           |
| **SSL**     | `sslmode=verify-full`                      | Required, not optional         |

### Python (psycopg2)

```python
import psycopg2
import certifi
import os

conn = psycopg2.connect(
    host="pg.us-east-1-aws.motherduck.com",
    port=5432,
    dbname="my_database",
    user="postgres",
    password=os.environ["MOTHERDUCK_TOKEN"],
    sslmode="verify-full",
    sslrootcert=certifi.where(),
)

cur = conn.cursor()
cur.execute("SELECT * FROM my_table LIMIT 10")
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()
```

Install dependencies: `pip install psycopg2-binary certifi`

### Node.js (pg)

```javascript
import pg from "pg";

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  database: "my_database",
  ssl: { rejectUnauthorized: true },
});

await client.connect();
const { rows } = await client.query("SELECT * FROM my_table LIMIT 10");
console.log(rows);
await client.end();
```

Install dependencies: `npm install pg`

### JDBC

```
jdbc:postgresql://pg.us-east-1-aws.motherduck.com:5432/my_database?user=postgres&password=<MOTHERDUCK_TOKEN>&sslmode=verify-full
```

Use the standard PostgreSQL JDBC driver (`org.postgresql.Driver`). SSL is required.

### Python (SQLAlchemy)

```python
import os
from sqlalchemy import create_engine, text

token = os.environ["MOTHERDUCK_TOKEN"]
engine = create_engine(
    f"postgresql+psycopg2://postgres:{token}@pg.us-east-1-aws.motherduck.com:5432/my_database",
    connect_args={"sslmode": "verify-full", "sslrootcert": __import__("certifi").where()},
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM my_table LIMIT 10"))
    for row in result:
        print(row)
```

---

## Step 3: Verify the Connection

Run a simple query to confirm connectivity:

```sql
SELECT 1 AS connected;
```

Then verify you can reach your data:

```sql
SELECT table_name FROM duckdb_tables() WHERE database_name = 'my_database';
```

---

## Native DuckDB API Alternative

Use only when you need dual execution (hybrid local/cloud queries) or direct DuckDB features not available via the PG endpoint (local file access, extensions, SET statements).

### Python

```python
import duckdb
import os

# Token from environment variable (recommended)
conn = duckdb.connect("md:my_database")

# Or explicitly (less preferred)
conn = duckdb.connect(f"md:my_database?motherduck_token={os.environ['MOTHERDUCK_TOKEN']}")

result = conn.sql("SELECT * FROM my_table LIMIT 10")
result.show()
conn.close()
```

Install: `pip install duckdb`

### Node.js (@duckdb/node-api)

```javascript
import { DuckDBInstance } from "@duckdb/node-api";

const instance = await DuckDBInstance.create("md:my_database?attach_mode=single", {
  motherduck_token: process.env.MOTHERDUCK_TOKEN,
  custom_user_agent: "my-service/1.0.0(api;analytics)",
});
const connection = await instance.connect();

const result = await connection.run('SELECT * FROM "my_database"."main"."my_table" LIMIT 10');
console.log(result);
```

Install: `npm install @duckdb/node-api`

### JDBC (Native DuckDB)

```
jdbc:duckdb:md:my_database?motherduck_token=<MOTHERDUCK_TOKEN>
```

Requires the DuckDB JDBC driver (`org.duckdb.DuckDBDriver`), not the PostgreSQL driver.

---

## Authentication

### Token Types

| Token Type          | Use Case                                  | Access Level           |
|---------------------|-------------------------------------------|------------------------|
| **Read/Write**      | Application backends, data pipelines      | Full read and write    |
| **Read Scaling**    | High-concurrency read workloads, CFA apps | Read-only, distributed across replicas |

### Create a Service Token

1. Go to **MotherDuck UI > Settings > Access Tokens**
2. Click **Create token**
3. Select the token type (Read/Write or Read Scaling)
4. Set an optional expiration date
5. Copy the token immediately -- it is shown only once

### Token Best Practices

- Store tokens in environment variables or a secrets manager. NEVER commit tokens to version control.
- Use **service accounts** for production applications, not personal tokens.
- Set expiration dates on tokens. Rotate tokens on a regular cadence (e.g., every 90 days).
- Use **Read Scaling tokens** for read-heavy workloads to distribute load across replicas.
- Revoke compromised tokens immediately via the MotherDuck UI.
- Scope each service to its own token so that revoking one does not break others.

---

## Read Scaling and Session Affinity

Use read scaling for **high-concurrency read-only** workloads on the same account, such as customer-facing analytics, BI traffic, or many simultaneous dashboard users.

- Read scaling replicas are **eventually consistent**.
- Use a stable `session_hint` per end user, session, or tenant-facing request path.
- Prefer `access_mode=read_only` on read-only serving connections.
- If the workflow needs stricter freshness after a write, use `CREATE SNAPSHOT` on the writer and `REFRESH DATABASE` on readers.

### Python

```python
import duckdb
import os

conn = duckdb.connect(
    "md:my_database?session_hint=user-123&access_mode=read_only&dbinstance_inactivity_ttl=300",
    config={
        "motherduck_token": os.environ["MOTHERDUCK_READ_SCALING_TOKEN"],
        "custom_user_agent": "customer-analytics/1.0.0(tenant-acme;dashboards)",
    },
)
```

### Node.js

```javascript
import { DuckDBInstance } from "@duckdb/node-api";

const db = await DuckDBInstance.create(
  "md:my_database?session_hint=user-123&access_mode=read_only&dbinstance_inactivity_ttl=300",
  {
    motherduck_token: process.env.MOTHERDUCK_READ_SCALING_TOKEN,
    custom_user_agent: "customer-analytics/1.0.0(tenant-acme;dashboards)",
  }
);
```

## Attach Modes

- `md:` or `md:my_database` uses **workspace mode** and persists attachment changes across sessions.
- `md:my_database?attach_mode=single` uses **single mode** and keeps the session scoped to one database without persisting attach/detach changes.
- For services, APIs, and BI clients, prefer **single mode** unless persistent multi-database workspace state is intentional.

---

## Key Rules

- **ALWAYS write DuckDB SQL, not PostgreSQL SQL** -- even when connecting via the PG endpoint. The PG endpoint translates the wire protocol, not the SQL dialect.
- **SSL is required** for the PG endpoint. Omitting SSL configuration causes connection failures.
- **No PostgreSQL-specific features** via the PG endpoint: `pg_*` functions, indexes, sequences, stored procedures, `LISTEN`/`NOTIFY`, and advisory locks are not supported.
- **The PG endpoint does NOT support local file access or dual execution.** Use the native DuckDB API for hybrid local/cloud queries.
- **Use fully qualified table names** when querying across databases: `"database"."schema"."table"`.
- **Do not install extensions at runtime** in MotherDuck. Only pre-installed extensions are available: azure, delta, ducklake, encodings, excel, httpfs, iceberg, icu, json, parquet, spatial, h3.
- **Tag production workloads with `custom_user_agent`.** This makes downstream cost attribution and workload analysis far easier.

---

## Common Mistakes

### Writing PostgreSQL SQL instead of DuckDB SQL

Wrong:
```sql
-- PostgreSQL syntax: NOT supported
SELECT * FROM my_table WHERE created_at::date = CURRENT_DATE;
SELECT array_agg(name) FROM users GROUP BY department;
CREATE INDEX idx_name ON my_table(name);
```

Right:
```sql
-- DuckDB SQL
SELECT * FROM my_table WHERE CAST(created_at AS DATE) = current_date;
SELECT list(name) FROM users GROUP BY department;
-- DuckDB does not use explicit indexes; it optimizes automatically
```

### Hardcoding tokens

Wrong:
```python
conn = psycopg2.connect(
    password="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # NEVER do this
)
```

Right:
```python
conn = psycopg2.connect(
    password=os.environ["MOTHERDUCK_TOKEN"]
)
```

### Using ORM features that generate PostgreSQL-specific SQL

ORMs like Django ORM, Prisma, or TypeORM may auto-generate `CREATE INDEX`, `pg_*` catalog queries, or PostgreSQL-specific type casts. Test ORM-generated SQL against MotherDuck before deploying. Prefer ORMs that allow raw SQL or custom dialects (SQLAlchemy with `text()` works well).

### Forgetting SSL configuration

Wrong:
```python
# Missing SSL -- connection will fail
conn = psycopg2.connect(
    host="pg.us-east-1-aws.motherduck.com",
    port=5432,
    dbname="my_database",
    user="postgres",
    password=os.environ["MOTHERDUCK_TOKEN"],
)
```

Right:
```python
conn = psycopg2.connect(
    host="pg.us-east-1-aws.motherduck.com",
    port=5432,
    dbname="my_database",
    user="postgres",
    password=os.environ["MOTHERDUCK_TOKEN"],
    sslmode="verify-full",
    sslrootcert=certifi.where(),
)
```

### Using the PG endpoint for local file access

The PG endpoint runs queries on the MotherDuck server. It cannot access files on your local machine. Use the native DuckDB API (`md:` protocol) for hybrid queries that reference local files.

### Pooling before it is needed

The docs recommend starting simple. If a single connection meets the latency and throughput target, keep it. Add pooling only for long-lived read-only concurrency, and combine it with read-only access plus read scaling when the workload is truly concurrent.

### Skipping session_hint on read scaling

Without a stable `session_hint`, requests from the same user can bounce between replicas, which weakens cache affinity and consistency. Use a durable value such as a user id, tenant id, or session id hash.

---

## PG Endpoint Limitations vs Native DuckDB API

| Capability                          | PG Endpoint | Native DuckDB API |
|-------------------------------------|-------------|-------------------|
| SQL dialect                         | DuckDB SQL  | DuckDB SQL        |
| Local file access                   | No          | Yes               |
| Dual execution (hybrid local/cloud) | No          | Yes               |
| `SET` configuration statements      | Restricted  | Full support      |
| DDL/DML                             | Limited     | Full support      |
| SSL                                 | Required    | Optional          |
| DuckDB installation required        | No          | Yes               |
| Works with any PG driver            | Yes         | No (DuckDB SDK)   |

---

## Related Skills

- `query` -- Execute DuckDB SQL queries against MotherDuck databases
- `explore` -- Discover databases, tables, columns, and data shares
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup

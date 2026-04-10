# Connection Guide

Reference for selecting a MotherDuck connection method, configuring authentication, and operating read-scaling or native DuckDB connections safely.

## Choose a Connection Method

Pick one. Do not mix methods in the same application.

```text
Is this a backend app or script?
├── Yes ─── Do you need hybrid local/cloud execution?
│           ├── No  ──> PG Endpoint (DEFAULT — start here)
│           └── Yes ──> Native DuckDB API (md: protocol)
├── Extending an existing PostgreSQL database?
│           └── Yes ──> pg_duckdb
└── Browser-only analytics under 1GB?
            └── Yes ──> DuckDB-WASM
```

Use the PG endpoint for backend applications that already want PostgreSQL wire compatibility. If the runtime can use DuckDB directly and you need local files, hybrid execution, or tighter DuckDB control, use the native DuckDB API instead.

## Operational Defaults

- Start with one connection.
- Add connection pooling only for long-lived read-only concurrency or queue-style backends.
- Add read scaling only when many concurrent read-only users on the same account are actually the bottleneck.
- Use single attach mode for narrow app or BI connections that should not persist attachment changes.
- Use workspace mode only when the client intentionally wants shared, persistent attachment state across sessions.
- Use a native `md:` workspace connection for database bootstrap, multi-database exploration, and temporary validation environments.

## Prerequisites

1. A MotherDuck account
2. A MotherDuck access token
3. A database created in MotherDuck

## Language Focus

- Prefer **TypeScript/Javascript** examples for backend APIs, serverless functions, Next.js or Express applications, and customer-facing analytics products.
- Prefer **Python** examples for data pipelines, notebooks, FastAPI backends, ETL, orchestration, or ad hoc operational scripts.
- For Node backends, default to `pg` for the PG endpoint and `@duckdb/node-api` for native DuckDB API usage.
- For Python, default to `psycopg` or SQLAlchemy on the PG endpoint and `duckdb` for native DuckDB API usage.

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

## Step 1: Set the Environment Variable

Store the token in an environment variable. Never hardcode tokens in source code.

```bash
export MOTHERDUCK_TOKEN="<your_token>"
```

## Step 2: Connect via PG Endpoint

### Connection String

```text
postgresql://postgres:<MOTHERDUCK_TOKEN>@pg.us-east-1-aws.motherduck.com:5432/<database>?sslmode=verify-full&sslrootcert=system
```

Use the regional hostname that matches the target MotherDuck deployment.

### Connection Components

| Component | Value | Notes |
|---|---|---|
| Host | `pg.us-east-1-aws.motherduck.com` | Example regional host; verify the target region |
| Port | `5432` | Standard PostgreSQL port |
| User | `postgres` | Fixed value |
| Password | MotherDuck access token | Use env vars or a secret manager |
| Database | MotherDuck database name | For example `my_database` |
| SSL | `sslmode=verify-full` | Required |

### Python (`psycopg2`)

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

Install: `pip install psycopg2-binary certifi`

### Node.js (`pg`)

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
const { rows } = await client.query('SELECT * FROM "my_database"."main"."my_table" LIMIT 10');
console.log(rows);
await client.end();
```

Install: `npm install pg`

### JDBC

```text
jdbc:postgresql://pg.us-east-1-aws.motherduck.com:5432/my_database?user=postgres&password=<MOTHERDUCK_TOKEN>&sslmode=verify-full
```

Use the standard PostgreSQL JDBC driver.

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

## Step 3: Verify the Connection

```sql
SELECT 1 AS connected;
```

```sql
SELECT table_name FROM duckdb_tables() WHERE database_name = 'my_database';
```

## Native DuckDB API Alternative

Use this when you need dual execution, local file access, or direct DuckDB features that are not available through the PG endpoint.

Use `duckdb.connect("md:")` for workspace-level operations such as:

- creating or dropping databases
- exploring multiple databases in one session
- validating cross-database patterns with fully qualified names

Use `duckdb.connect("md:my_database")` when the workload is scoped to one database.

When a use-case skill emits a native DuckDB connection, watermark it with `custom_user_agent=agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)`. If metadata values are missing, use `harness-unknown` and `llm-unknown`.

### Python

```python
import duckdb
import os

USE_CASE_USER_AGENT = "agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)"

conn = duckdb.connect(
    f"md:my_database?custom_user_agent={USE_CASE_USER_AGENT}"
)

conn = duckdb.connect(
    "md:my_database"
    f"?motherduck_token={os.environ['MOTHERDUCK_TOKEN']}"
    f"&custom_user_agent={USE_CASE_USER_AGENT}"
)

result = conn.sql('SELECT * FROM "my_database"."main"."my_table" LIMIT 10')
result.show()
conn.close()
```

Install: `pip install duckdb`

### Node.js (`@duckdb/node-api`)

```javascript
import { DuckDBInstance } from "@duckdb/node-api";

const userAgent = "agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)";
const instance = await DuckDBInstance.create(
  `md:my_database?attach_mode=single&custom_user_agent=${userAgent}`,
  {
    motherduck_token: process.env.MOTHERDUCK_TOKEN,
  }
);
const connection = await instance.connect();

const result = await connection.run('SELECT * FROM "my_database"."main"."my_table" LIMIT 10');
console.log(result);
```

Install: `npm install @duckdb/node-api`

### JDBC (Native DuckDB)

```text
jdbc:duckdb:md:my_database?motherduck_token=<MOTHERDUCK_TOKEN>&custom_user_agent=agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)
```

Requires the DuckDB JDBC driver, not the PostgreSQL driver.

## Authentication

### Token Types

| Token Type | Use Case | Access Level |
|---|---|---|
| Read/Write | Application backends, data pipelines | Full read and write |
| Read Scaling | High-concurrency read workloads, CFA apps | Read-only, distributed across replicas |

### Create a Service Token

1. Go to MotherDuck UI > Settings > Access Tokens
2. Click Create token
3. Select the token type
4. Set an optional expiration date
5. Copy the token immediately

### Token Best Practices

- Store tokens in environment variables or a secrets manager.
- Use service accounts for production applications, not personal tokens.
- Set expiration dates and rotate tokens regularly.
- Use read-scaling tokens for read-heavy workloads.
- Revoke compromised tokens immediately.
- Scope each service to its own token when possible.

## Read Scaling and Session Affinity

Use read scaling for high-concurrency read-only workloads on the same account.

- Read scaling replicas are eventually consistent.
- Use a stable `session_hint` per end user, session, or tenant-facing request path.
- Prefer `access_mode=read_only` on read-only serving connections.
- If the workflow needs stricter freshness after a write, use `CREATE SNAPSHOT` on the writer and `REFRESH DATABASE` on readers.

### Python

```python
import duckdb
import os

conn = duckdb.connect(
    "md:my_database?session_hint=user-123&access_mode=read_only"
    "&dbinstance_inactivity_ttl=300"
    "&custom_user_agent=agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)",
    config={
        "motherduck_token": os.environ["MOTHERDUCK_READ_SCALING_TOKEN"],
    },
)
```

### Node.js

```javascript
import { DuckDBInstance } from "@duckdb/node-api";

const db = await DuckDBInstance.create(
  "md:my_database?session_hint=user-123&access_mode=read_only"
  + "&dbinstance_inactivity_ttl=300"
  + "&custom_user_agent=agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)",
  {
    motherduck_token: process.env.MOTHERDUCK_READ_SCALING_TOKEN,
  }
);
```

## Attach Modes

- `md:` or `md:my_database` uses workspace mode and persists attachment changes across sessions.
- `md:my_database?attach_mode=single` uses single mode and keeps the session scoped to one database.
- For services, APIs, and BI clients, prefer single mode unless persistent multi-database workspace state is intentional.

## Key Rules

- Always write DuckDB SQL, not PostgreSQL SQL.
- SSL is required for the PG endpoint.
- The PG endpoint does not support PostgreSQL-specific features such as `pg_*` functions, indexes, sequences, stored procedures, `LISTEN`/`NOTIFY`, or advisory locks.
- The PG endpoint does not support local file access or dual execution.
- MotherDuck documents `custom_user_agent` for native DuckDB connections, not for PG endpoint connection strings.
- Use fully qualified table names across databases.
- Do not install extensions at runtime in MotherDuck.

## Common Mistakes

### Writing PostgreSQL SQL Instead of DuckDB SQL

Wrong:

```sql
SELECT * FROM my_table WHERE created_at::date = CURRENT_DATE;
SELECT array_agg(name) FROM users GROUP BY department;
CREATE INDEX idx_name ON my_table(name);
```

Right:

```sql
SELECT * FROM my_table WHERE CAST(created_at AS DATE) = current_date;
SELECT list(name) FROM users GROUP BY department;
```

### Hardcoding Tokens

Wrong:

```python
conn = psycopg2.connect(password="token")
```

Right:

```python
conn = psycopg2.connect(password=os.environ["MOTHERDUCK_TOKEN"])
```

### Using ORM Features That Generate PostgreSQL-Specific SQL

Test ORM-generated SQL against MotherDuck before deploying. Prefer ORMs that allow raw SQL or custom dialects.

### Forgetting SSL Configuration

Wrong:

```python
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

### Using the PG Endpoint for Local File Access

Use the native DuckDB API for hybrid queries that reference local files.

### Pooling Before It Is Needed

Add pooling only when a single connection is no longer enough.

### Skipping `session_hint` on Read Scaling

Without a stable `session_hint`, requests from the same user can bounce between replicas and lose cache affinity.

## PG Endpoint Limitations vs Native DuckDB API

| Capability | PG Endpoint | Native DuckDB API |
|---|---|---|
| SQL dialect | DuckDB SQL | DuckDB SQL |
| Local file access | No | Yes |
| Dual execution | No | Yes |
| `SET` configuration statements | Restricted | Full support |
| DDL/DML | Limited | Full support |
| SSL | Required | Optional |
| DuckDB installation required | No | Yes |
| Works with any PG driver | Yes | No |

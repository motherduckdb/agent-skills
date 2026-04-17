# CFA Architecture Reference

Detailed architecture patterns, complete code examples, and scaling playbook for building customer-facing analytics applications on MotherDuck.

---

## Choose the Connection Posture First

There are two valid backend shapes for customer-facing analytics on MotherDuck:

- **Thin-client / backend API**: the browser talks to your backend, and the backend talks to MotherDuck through the PG endpoint. This is the practical default for most product teams because it fits existing API stacks, auth middleware, and connection-pooling patterns.
- **Native DuckDB backend**: the backend already runs on `duckdb` or `@duckdb/node-api`, and uses MotherDuck through the native API. Use this when the service also needs local files, hybrid local/cloud execution, or direct DuckDB control.

This reference leads with the thin-client 3-tier pattern because it is the most common multi-tenant production shape. Keep the native backend path in play when the application is already DuckDB-native.

---

## 3-Tier Architecture Diagram

```
┌──────────┐     ┌──────────────┐     ┌─────────────────────────┐
│ Browser  │────>│ Backend API  │────>│ MotherDuck              │
│ (React/  │<────│ (FastAPI/    │<────│                         │
│  Vue/etc)│     │  Express)    │     │ Duckling A (customer_a) │
└──────────┘     │              │     │   Primary + Replica x4  │
                 │ 1. Auth      │     │                         │
                 │ 2. Route     │     │ Duckling B (customer_b) │
                 │ 3. Validate  │     │   Primary + Replica x4  │
                 │ 4. Execute   │     │                         │
                 └──────────────┘     │ Duckling C (customer_c) │
                                      │   Primary + Replica x8  │
                                      └─────────────────────────┘
```

Each Duckling is an isolated DuckDB instance. The primary handles writes; read replicas handle CFA query traffic via Read Scaling tokens. The backend authenticates each request, routes to the correct customer Duckling, validates the query, and returns results.

---

## Complete Python Backend Example (FastAPI + psycopg2)

A production-ready backend that routes customer queries to their isolated MotherDuck databases.

```python
"""
CFA Backend -- FastAPI + psycopg2
Routes authenticated customer requests to per-customer MotherDuck databases.

Install: pip install fastapi uvicorn psycopg2-binary certifi pyjwt
Run:     uvicorn cfa_backend:app --host 0.0.0.0 --port 8000
"""

import os
import json
from contextlib import contextmanager
from typing import Any

import certifi
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import jwt

app = FastAPI(title="CFA Analytics API")

# --- Configuration ---

# Customer registry: maps customer_id to database and Read Scaling token.
# In production, load this from a secrets manager (AWS Secrets Manager, Vault).
CUSTOMER_REGISTRY: dict[str, dict[str, str]] = {
    "acme": {
        "database": "customer_acme",
        "read_token": os.environ.get("ACME_READ_TOKEN", ""),
        "write_token": os.environ.get("ACME_WRITE_TOKEN", ""),
    },
    "globex": {
        "database": "customer_globex",
        "read_token": os.environ.get("GLOBEX_READ_TOKEN", ""),
        "write_token": os.environ.get("GLOBEX_WRITE_TOKEN", ""),
    },
}

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
MD_HOST = "pg.us-east-1-aws.motherduck.com"
MD_PORT = 5432

# --- Allowed query patterns ---
# In production, maintain an allowlist of query templates or use parameterized queries.
ALLOWED_PREFIXES = ("SELECT", "WITH", "FROM", "SUMMARIZE", "DESCRIBE")


# --- Auth ---

def get_customer_id(authorization: str = Header(...)) -> str:
    """Extract and validate customer_id from JWT token."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        customer_id = payload.get("customer_id")
        if customer_id not in CUSTOMER_REGISTRY:
            raise HTTPException(status_code=403, detail="Unknown customer")
        return customer_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- Database ---

@contextmanager
def get_connection(customer_id: str, write: bool = False):
    """Get a psycopg2 connection to the customer's MotherDuck database."""
    customer = CUSTOMER_REGISTRY[customer_id]
    token = customer["write_token"] if write else customer["read_token"]
    conn = psycopg2.connect(
        host=MD_HOST,
        port=MD_PORT,
        dbname=customer["database"],
        user="postgres",
        password=token,
        sslmode="verify-full",
        sslrootcert=certifi.where(),
    )
    try:
        yield conn
    finally:
        conn.close()


def validate_query(sql: str) -> None:
    """Reject queries that are not read-only SELECT statements."""
    normalized = sql.strip().upper()
    if not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT, WITH, FROM, SUMMARIZE, and DESCRIBE queries are allowed",
        )


# --- API ---

class QueryRequest(BaseModel):
    sql: str
    params: list[Any] | None = None


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


@app.post("/query", response_model=QueryResponse)
def run_query(
    request: QueryRequest,
    customer_id: str = Depends(get_customer_id),
):
    """Execute a read-only query against the customer's MotherDuck database."""
    validate_query(request.sql)

    with get_connection(customer_id) as conn:
        cur = conn.cursor()
        try:
            cur.execute(request.sql, request.params)
            columns = [desc[0] for desc in cur.description]
            rows = [list(row) for row in cur.fetchall()]
            return QueryResponse(columns=columns, rows=rows, row_count=len(rows))
        except psycopg2.Error as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cur.close()


@app.get("/health")
def health():
    return {"status": "ok"}
```

### Key design decisions in this example:

- **Read Scaling tokens** are used for the `/motherduck-query` endpoint. Write tokens are reserved for data ingestion and data transformation.
- **Query validation** rejects non-SELECT statements. In production, use a more sophisticated allowlist or parameterized query templates.
- **Connections are not pooled.** For higher throughput, add connection pooling with `psycopg2.pool.ThreadedConnectionPool` or switch to `psycopg` (v3) with async support.
- **JWT authentication** maps each request to a `customer_id`. Replace with your product's auth system.

---

## Node.js Backend Example (Express + pg)

The same pattern as the Python example, implemented in Node.js. Install: `npm install express pg jsonwebtoken`

```javascript
import express from "express";
import pg from "pg";
import jwt from "jsonwebtoken";

const app = express();
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || "change-me-in-production";
const CUSTOMER_REGISTRY = {
  acme: {
    database: "customer_acme",
    readToken: process.env.ACME_READ_TOKEN || "",
  },
  globex: {
    database: "customer_globex",
    readToken: process.env.GLOBEX_READ_TOKEN || "",
  },
};

function authenticate(req, res, next) {
  try {
    const token = (req.headers.authorization || "").replace("Bearer ", "");
    const payload = jwt.verify(token, JWT_SECRET);
    if (!CUSTOMER_REGISTRY[payload.customer_id])
      return res.status(403).json({ error: "Unknown customer" });
    req.customerId = payload.customer_id;
    next();
  } catch {
    return res.status(401).json({ error: "Invalid token" });
  }
}

app.post("/query", authenticate, async (req, res) => {
  const { sql, params } = req.body;
  if (!sql) return res.status(400).json({ error: "Missing sql field" });

  const allowed = ["SELECT", "WITH", "FROM", "SUMMARIZE", "DESCRIBE"];
  if (!allowed.some((p) => sql.trim().toUpperCase().startsWith(p)))
    return res.status(400).json({ error: "Read-only queries only" });

  const customer = CUSTOMER_REGISTRY[req.customerId];
  const client = new pg.Client({
    host: "pg.us-east-1-aws.motherduck.com",
    port: 5432,
    user: "postgres",
    password: customer.readToken,
    database: customer.database,
    ssl: { rejectUnauthorized: true },
  });

  try {
    await client.connect();
    const result = await client.query(sql, params || []);
    res.json({
      columns: result.fields.map((f) => f.name),
      rows: result.rows,
      row_count: result.rowCount,
    });
  } catch (err) {
    res.status(400).json({ error: err.message });
  } finally {
    await client.end();
  }
});

app.listen(process.env.PORT || 8000);
```

For production, replace `new pg.Client()` with a per-customer `pg.Pool` for connection reuse.

---

## 1.5-Tier Architecture with DuckDB-Wasm

### When to Use

Use the 1.5-tier pattern only when ALL of these conditions are true:

- Datasets are under 1GB per user.
- The use case is a read-only dashboard (no writes from the browser).
- You do not need strict, server-enforced data isolation.
- You accept that the token is visible in the browser (lower security).

### How It Works

```
┌──────────────────────────────────────────────────┐
│                 BROWSER                           │
│                                                   │
│  ┌─────────────┐    ┌─────────────────────────┐  │
│  │ DuckDB-Wasm │───>│ MotherDuck (via md:)     │  │
│  │ (in-browser) │<───│ per-customer database    │  │
│  └─────────────┘    └─────────────────────────┘  │
│                                                   │
│  - Queries execute locally in the browser         │
│  - Data syncs from MotherDuck to Wasm instance    │
│  - Sub-millisecond latency for cached data        │
│  - No backend server needed                       │
└──────────────────────────────────────────────────┘
```

### Limitations and Tradeoffs

| Aspect | 1.5-Tier | 3-Tier |
|---|---|---|
| Latency | Ultra-low (local execution) | Low (network round-trip) |
| Data size per user | <1GB practical limit | No practical limit |
| Token security | Token visible in browser | Token stays on server |
| Data isolation | Relies on per-user tokens | Per-database structural isolation |
| Write support | Limited | Full |
| Backend required | No | Yes |
| Concurrency scaling | N/A (client-side) | Read Scaling replicas |

**Do not use 1.5-tier for production CFA with sensitive data.** The token is visible in the browser, and there is no server-side query validation layer.

---

## Service Account Management

### Creating Service Accounts

1. Go to **MotherDuck UI > Settings > Service Accounts**.
2. Click **Create Service Account**.
3. Name the account descriptively: `svc_<customer_slug>` (e.g., `svc_acme`).
4. Assign the service account access to the customer's database.
5. Generate tokens for the service account.

### Token Types and When to Use Each

| Token Type | Purpose | Use In CFA |
|---|---|---|
| **Read Scaling** | Distribute read queries across replicas | CFA query endpoint (primary use) |
| **Read/Write** | Full read and write access to the database | Backend data ingestion only |

**Rule: use Read Scaling tokens for CFA query endpoints when the workload is concurrent and read-heavy.** Read/Write tokens are for data pipelines that load data into customer databases and for other writer workflows.

### Token Rotation Strategy

Set 90-day expiration on all tokens. At day 80, generate a new token and store it in the secrets manager. At day 85, verify the application uses the new token. At day 90, the old token expires. Automate this with your secrets manager's rotation feature. Revoke compromised tokens immediately -- do not wait for expiration.

---

## Scaling Playbook

### Phase 1: Launch (1-50 customers)

- **One Duckling per customer.** Each customer gets a separate database and service account.
- **Start simple on reads.** Add read scaling only when concurrency is real; the default pool size is 4 replicas and can be increased up to 16 as a soft limit.
- **Single backend instance.** One API server routes requests to customer databases.
- **Monitor:** Query latency (p50, p95, p99), error rates, connection counts.

### Phase 2: Growth (50-500 customers)

- **Increase read scaling capacity for high-traffic customers.** Identify customers with the most concurrent users and scale their replica pools.
- **Add connection pooling.** Use `psycopg2.pool.ThreadedConnectionPool` (Python) or `pg.Pool` (Node.js) to reuse connections.
- **Multiple backend instances behind a load balancer.** Scale the API layer horizontally.
- **Automate customer provisioning.** Script database creation, service account setup, and token generation.
- **Monitor:** Per-customer query volume, replica utilization, connection pool saturation.

### Phase 3: Scale (500+ customers)

- **Scale read replicas for top-tier customers.** The highest-traffic customers may need the documented soft limit or a higher limit coordinated with support.
- **Tiered customer configs.** Group customers by usage tier (free, pro, enterprise) with different replica counts and query rate limits.
- **Per-customer rate limiting.** Protect the system from runaway query volume by enforcing per-customer request limits.
- **Dedicated backend pools.** Route enterprise customers to dedicated backend instances for guaranteed capacity.
- **Monitor:** Per-customer cost, replica lag, query queue depth, overall system utilization.

### Scaling Decision Matrix

| Signal | Action |
|---|---|
| p95 query latency > 2s | Add read replicas for affected customers |
| Connection pool exhausted | Increase pool size or add backend instances |
| Replica lag beyond freshness target | Investigate write volume; consider `CREATE SNAPSHOT` |
| Single customer > 50% of total traffic | Move to dedicated backend pool |
| Provisioning takes > 5 min manually | Automate with scripts or API |

---

## Multi-Tenant Data Loading Patterns

### Loading Data Per Customer

Each customer has its own database. Load data into the correct database using the customer's Read/Write token.

```python
def load_customer_data(customer_id: str, data_path: str):
    """Load data into a customer's MotherDuck database."""
    customer = CUSTOMER_REGISTRY[customer_id]
    conn = psycopg2.connect(
        host="pg.us-east-1-aws.motherduck.com",
        port=5432,
        dbname=customer["database"],
        user="postgres",
        password=customer["write_token"],  # Use Write token for ingestion
        sslmode="verify-full",
        sslrootcert=certifi.where(),
    )
    try:
        cur = conn.cursor()
        # Rebuild the analytics table from fresh data
        cur.execute(f"""
            CREATE OR REPLACE TABLE "main"."analytics_events" AS
            SELECT * FROM read_parquet('{data_path}')
        """)
        conn.commit()
        # Create a snapshot so read replicas pick up the new data
        cur.execute("CREATE SNAPSHOT")
        conn.commit()
    finally:
        conn.close()
```

### Scheduling Data Refreshes

Use a task scheduler (cron, Airflow, Dagster, Prefect) to refresh customer data on a cadence.

```python
# Example: Airflow-style pseudocode for per-customer data refresh

def refresh_all_customers():
    """Refresh analytics data for every customer."""
    for customer_id, config in CUSTOMER_REGISTRY.items():
        data_path = f"s3://data-lake/{customer_id}/latest/*.parquet"
        load_customer_data(customer_id, data_path)
        print(f"Refreshed data for {customer_id}")

# Schedule: run daily at 02:00 UTC
# In Airflow: @daily with a PythonOperator
# In cron:    0 2 * * * python refresh_customers.py
```

### Handling Schema Evolution Across Customers

When the analytics schema changes, apply the change to every customer database. Use idempotent DDL patterns.

```sql
-- Add a new column to every customer's analytics_events table.
-- Run this against each customer database.

ALTER TABLE "main"."analytics_events"
    ADD COLUMN IF NOT EXISTS session_id VARCHAR;

-- If the column requires backfilling:
UPDATE "main"."analytics_events"
    SET session_id = 'unknown'
    WHERE session_id IS NULL;
```

Automate schema migrations by iterating over all customer databases, connecting with each customer's Write token, and executing the migration SQL. Wrap each customer's migration in a try/except to continue on failure and log which customers succeeded or failed.

### Data Loading Best Practices

- **Use `CREATE OR REPLACE TABLE ... AS SELECT` for full refreshes.** This is idempotent and atomic.
- **Use Parquet format for source data.** Parquet is columnar, compressed, and loads significantly faster than CSV.
- **Load only needed columns.** Select specific columns during load to reduce transfer and storage.
- **Create a snapshot after loading.** Run `CREATE SNAPSHOT` so read replicas pick up the new data promptly.
- **Pre-aggregate during load.** Build summary tables at load time rather than aggregating at query time. This keeps CFA query latency under 1 second.
- **Use the `motherduck-load-data` skill patterns** for format-specific options (CSV, JSON, Parquet, Delta Lake, Iceberg).

---

## Connection Pooling

For production, use per-customer connection pools instead of creating a new connection per request.

**Python:** Use `psycopg2.pool.ThreadedConnectionPool` with `minconn=2, maxconn=10` per customer. Store pools in a dictionary keyed by `customer_id`. Call `pool.getconn()` before each query and `pool.putconn(conn)` in a `finally` block.

**Node.js:** Use `pg.Pool` with `max: 10, idleTimeoutMillis: 30000` per customer. Store pools in a `Map` keyed by `customerId`. Call `pool.connect()` to get a client and `client.release()` in a `finally` block.

In both cases, create the pool lazily on first request for each customer.

---

## Monitoring and Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|---|---|---|
| Query latency p50 | <200ms | >500ms |
| Query latency p95 | <1s | >2s |
| Query latency p99 | <2s | >5s |
| Error rate | <0.1% | >1% |
| Connection pool utilization | <70% | >90% |

Log every CFA query with `customer_id`, `duration_ms`, `row_count`, and error details. Use structured logging (JSON) so metrics can be aggregated per customer.

---

## Troubleshooting

### Connection refused or timeout

- Verify the host is `pg.us-east-1-aws.motherduck.com` and port is `5432`.
- Confirm SSL is enabled (`sslmode=verify-full`).
- Check that the token is valid and not expired.
- Verify the database name is correct and the service account has access.

### Query returns stale data after a write

- Read Scaling tokens route to replicas, which are eventually consistent.
- Run `CREATE SNAPSHOT` on the writer connection after the write completes.
- Run `REFRESH DATABASE <db_name>` on the reader connection to force a sync.

### High query latency

- Check if the customer's data needs pre-aggregation. Build summary tables during data loading.
- Verify the query uses column selection (not `SELECT *`).
- Check replica count -- increase read replicas for high-concurrency customers.
- Use `EXPLAIN` to inspect the query plan and identify bottlenecks.

### Connection pool exhaustion

- Increase the pool `maxconn` setting.
- Reduce query execution time by pre-aggregating data.
- Add per-customer rate limiting to prevent runaway query volume.
- Scale the backend horizontally with additional API instances.

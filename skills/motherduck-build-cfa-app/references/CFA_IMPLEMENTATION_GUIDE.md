<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Build a Customer-Facing Analytics App

Use this skill when embedding analytics directly into your product for external users -- customers, partners, or end users who need to query their own data through your application. Customer-facing analytics (CFA) requires sub-second query latency, high concurrency, strict per-customer data isolation, and predictable performance under load.

This is a use-case skill. It ties together `motherduck-connect`, `motherduck-model-data`, `motherduck-query`, `motherduck-load-data`, and `motherduck-explore` into a production architecture.

## Source Of Truth

- Prefer current MotherDuck docs for service accounts, connection paths, read scaling, and the Hypertenancy product guidance.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep the CFA guidance aligned with the documented posture:
  - structural isolation first
  - dedicated compute or service-account boundaries where blast radius matters
  - read scaling for truly concurrent read-heavy workloads
  - native storage first unless an explicit DuckLake requirement exists

## Verified Delivery Defaults

The repeated repo runs point to a stable CFA posture:

- start from the live MotherDuck workspace or target database before picking a serving pattern
- default to a 3-tier app with an API layer between the browser and MotherDuck
- default to structural isolation such as per-customer databases or service-account boundaries
- use native DuckDB `md:` connections when the backend needs direct MotherDuck control
- keep any PostgreSQL-compatible path as an integration tactic, not the primary CFA architecture

## Validation Signals

Use these signals for testing, review, and regression checks. They are not an instruction to include a separate "Validation Signals" section in normal user-facing replies.

- run `artifacts/customer_routing_example.py` against temporary MotherDuck databases
- verify the result reports `routing_mode` as `per-customer database namespace`
- verify separate customer database names are present in the `backend.databases` payload
- treat any shared-database shortcut as a regression unless the task explicitly calls for it

## Language Focus: TypeScript/Javascript and Python

- Prefer **TypeScript/Javascript** for:
  - the backend API layer in Node.js
  - Next.js, Express, or serverless app integration
  - product-side auth, routing, and request shaping
- Prefer **Python** for:
  - FastAPI backends
  - analytics-heavy backend services
  - provisioning or operational scripts around the app
- For customer-facing analytics, default to showing both when useful:
  - TypeScript/Javascript for the product request path
  - Python for operational or backend alternatives

## Prerequisites

- MotherDuck connection established (see `motherduck-connect` skill)
- Data model designed (see `motherduck-model-data` skill)
- Familiarity with DuckDB SQL (see `motherduck-query` skill)

---

## What Is Customer-Facing Analytics

CFA means your product exposes analytics capabilities to external users. Unlike internal BI dashboards, CFA has hard requirements:

- **Sub-second latency.** Users expect interactive speed. Queries returning in 2-5 seconds feel broken.
- **High concurrency.** Hundreds or thousands of users querying simultaneously.
- **Per-customer data isolation.** Customer A must never see Customer B's data. This is a security requirement, not a nice-to-have.
- **Predictable performance.** One customer's heavy query must not degrade another customer's experience.

MotherDuck's Hypertenancy architecture addresses all four requirements with per-customer or per-workload compute boundaries, dedicated ducklings, and read scaling when the serving workload is highly concurrent.

---

## Choose an Architecture

Use the 3-tier architecture for production CFA. The other options exist for specific, narrower use cases.

```
Production CFA (recommended):
  Browser ──> Backend API ──> MotherDuck (per-customer databases)

Lightweight dashboards only (<1GB per user):
  Browser (DuckDB-Wasm) ──> MotherDuck

Simple multi-tenant (weak isolation, low security):
  Browser ──> Backend API ──> MotherDuck (single database, tenant_id filtering)
```

### 3-Tier Architecture (Default for Production)

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐
│ Browser  │────>│ Backend API  │────>│  MotherDuck     │
│ (React/  │<────│ (FastAPI/    │<────│  (per-customer  │
│  Vue/etc)│     │  Express)    │     │   databases)    │
└──────────┘     └──────────────┘     └─────────────────┘
```

- Per-customer service accounts and databases provide strong data isolation.
- Backend handles authentication, authorization, and query routing.
- Add Read Scaling tokens for high-concurrency read workloads.
- Tokens never leave the backend. The browser talks only to your API.

### 1.5-Tier Architecture (DuckDB-Wasm)

Use only when datasets are under 1GB per user and the use case is a lightweight, read-only dashboard. The browser runs DuckDB-Wasm and connects directly to MotherDuck. No backend needed, but data isolation is harder to enforce and datasets must be small enough for browser-side execution.

### Embedded Dives

Embedded Dives sit between a standalone Dive and a full CFA app:

- good for read-only live dashboards inside an existing site or product
- backend still creates the embed session
- browser receives only the short-lived session string
- not a substitute for a full app backend when you need customer-specific routing, richer write paths, or tighter policy enforcement

If the requirement is "show a live MotherDuck dashboard inside our product," this can be enough. If the requirement is "serve each customer through our own application contract and backend controls," stay with the 3-tier CFA architecture.

### Single Service Account (Weak Isolation)

One service account, one database, data filtered by `tenant_id` in every query. Less secure because a bug in query construction can leak data across tenants. Use only for internal tools or low-sensitivity analytics where simplicity outweighs isolation.

**For anything customer-facing, use the 3-tier architecture.** The rest of this skill assumes the 3-tier pattern.

---

## Step-by-Step: Build a 3-Tier CFA App

### Step 1: Design Per-Customer Schema

Create one database per customer. This is the strongest isolation model -- each customer's data lives in a completely separate namespace with its own compute resources.

Use the `motherduck-model-data` skill for schema design within each customer database.

```sql
-- Create a database for each customer
CREATE DATABASE customer_acme;
CREATE DATABASE customer_globex;

-- Create analytics tables in each customer database
CREATE TABLE "customer_acme"."main"."analytics_events" (
    event_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR NOT NULL,
    properties JSON,
    created_at TIMESTAMP DEFAULT current_timestamp
);
COMMENT ON TABLE "customer_acme"."main"."analytics_events"
    IS 'Raw analytics events for customer Acme Corp';

-- Repeat the same schema for each customer
CREATE TABLE "customer_globex"."main"."analytics_events" (
    event_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR NOT NULL,
    properties JSON,
    created_at TIMESTAMP DEFAULT current_timestamp
);
```

Use a consistent naming convention: `customer_<slug>` for database names. This makes routing straightforward.

### Step 2: Create Service Accounts

Create service accounts per customer or per workload boundary when isolation, sizing, or revocation blast radius matters. Service accounts can be created in the MotherDuck UI or programmatically via the Admin API.

### TypeScript backend shape

For Node.js or TypeScript services, use a backend-only pattern:

- authenticate the end user in your app
- map the user to the correct customer database or service account
- execute DuckDB SQL from the server
- never expose MotherDuck tokens in the browser

1. Go to **MotherDuck UI > Settings > Service Accounts**.
2. Create a service account for each customer (e.g., `svc_acme`, `svc_globex`).
3. Generate a **Read Scaling token** for each service account only when the CFA workload is read-heavy and concurrent.
4. Generate a **Read/Write token** only for accounts that need write access (data ingestion).
5. Store all tokens in a secrets manager (AWS Secrets Manager, HashiCorp Vault, Doppler). Never store tokens in application config files or environment variables on shared machines.

### Step 3: Connect the Backend to MotherDuck

Use the `motherduck-connect` skill patterns. Each incoming customer request routes to that customer's database using their dedicated token. Choose the connection approach that fits your backend.

#### Option A: Native DuckDB (recommended for Python backends)

Native DuckDB gives full SQL support, cross-database queries, and no driver translation. Use this for FastAPI, Flask, or any Python service.

```python
# Python backend example (FastAPI + duckdb)
import duckdb

CFA_USER_AGENT = "agent-skills/<latest-available-skills-version>(harness-<harness>;llm-<llm>)"

def get_customer_connection(customer_db: str, customer_token: str):
    """Create a native DuckDB connection to a customer's MotherDuck database."""
    return duckdb.connect(
        f"md:{customer_db}?motherduck_token={customer_token}"
        f"&custom_user_agent={CFA_USER_AGENT}"
    )
```

Install: `pip install duckdb`

#### Option B: PG Endpoint (for existing PostgreSQL stacks)

Use the PG endpoint when your backend already has PostgreSQL drivers, connection pooling, or runs in a serverless environment where installing native DuckDB is impractical.

```ts
// TypeScript backend example (Express + pg)
import pg from "pg";

function getCustomerPool(database: string, token: string) {
  return new pg.Pool({
    host: "pg.us-east-1-aws.motherduck.com",
    port: 5432,
    database,
    user: "postgres",
    password: token,
    ssl: { rejectUnauthorized: true },
  });
}
```

```python
# Python backend example (FastAPI + psycopg2)
import psycopg2
import certifi

def get_customer_connection(customer_db: str, customer_token: str):
    """Create a PG endpoint connection to a customer's MotherDuck database."""
    return psycopg2.connect(
        host="pg.us-east-1-aws.motherduck.com",
        port=5432,
        dbname=customer_db,
        user="postgres",
        password=customer_token,
        sslmode="verify-full",
        sslrootcert=certifi.where()
    )
```

Install: `pip install psycopg2-binary certifi`

### Step 4: Implement Query Routing

Map each authenticated customer to their database name and token. Execute queries against the correct customer database and return results to the frontend.

```python
# Customer registry -- in production, load from secrets manager
CUSTOMER_REGISTRY = {
    "acme": {
        "database": "customer_acme",
        "token": os.environ["ACME_MD_TOKEN"],
    },
    "globex": {
        "database": "customer_globex",
        "token": os.environ["GLOBEX_MD_TOKEN"],
    },
}

def execute_customer_query(customer_id: str, query: str):
    """Route a query to the correct customer database."""
    customer = CUSTOMER_REGISTRY[customer_id]
    conn = get_customer_connection(customer["database"], customer["token"])
    try:
        cur = conn.cursor()
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return {"columns": columns, "rows": rows}
    finally:
        conn.close()
```

```ts
const CUSTOMER_REGISTRY = {
  acme: { database: "customer_acme", token: process.env.ACME_MD_TOKEN! },
  globex: { database: "customer_globex", token: process.env.GLOBEX_MD_TOKEN! },
};

async function executeCustomerQuery(customerId: keyof typeof CUSTOMER_REGISTRY, sql: string, values: unknown[] = []) {
  const customer = CUSTOMER_REGISTRY[customerId];
  const pool = getCustomerPool(customer.database, customer.token);
  const result = await pool.query(sql, values);
  await pool.end();
  return result.rows;
}
```

Validate and sanitize all queries before execution. Never pass raw user input directly to `cur.execute()`. Use parameterized queries or an allowlist of permitted query templates.

### Step 5: Set Up Read Scaling

Enable read scaling for each customer's service account when concurrent read workloads justify it.

- **Default flock limit:** read scaling starts with a maximum default flock size of 16 replicas, adjustable via support.
- **Use Read Scaling tokens** to distribute load across replicas automatically.
- **Read Scaling tokens are read-only.** Write operations require a Read/Write token.
- **Use `session_hint` on native DuckDB connections** so repeated requests from the same end user land on the same replica when possible.

| Token Type | Use Case | Concurrency | Write Access |
|---|---|---|---|
| Read/Write | Data ingestion, schema changes | Single writer | Yes |
| Read Scaling | CFA query workloads | Distributed across replicas | No |

**Use Read Scaling tokens for concurrent CFA read paths.** Reserve Read/Write tokens for backend data loading processes, schema changes, and other writer workflows.

### Step 6: Handle Consistency

Read replicas are eventually consistent. There is typically a lag between a write and its visibility on replicas. For most CFA workloads this is acceptable -- analytics data is inherently slightly behind real-time.

When you need strict consistency after a write (e.g., after a data load completes and a customer should see the new data immediately):

```sql
-- On the writer connection (Read/Write token):
-- After loading new data, create a snapshot
CREATE SNAPSHOT;

-- On the reader side, refresh to pick up the snapshot:
REFRESH DATABASE customer_acme;
```

Use this pattern sparingly. For most CFA use cases, eventual consistency with a few seconds of delay is sufficient and performs better.

---

## Hypertenancy Explained

Hypertenancy is MotherDuck's multi-tenant architecture. It provides stronger isolation than traditional shared-database multi-tenancy.

- **Each customer gets a dedicated DuckDB instance ("Duckling").** Customer workloads run on separate compute. One customer's expensive query cannot slow down another customer.
- **No resource contention.** CPU, memory, and I/O are isolated per customer. Performance is predictable regardless of how many tenants exist.
- **Independent scaling.** High-traffic customers can get more compute or read replicas without affecting other customers' configurations.
- **Database-level isolation.** Each customer's data lives in a separate database. There is no shared table with a `tenant_id` column -- the isolation is structural, not query-dependent.

This model eliminates the "noisy neighbor" problem that plagues shared-database multi-tenant architectures.

---

## Read Scaling Deep Dive

Read scaling distributes read queries across multiple replicas of a customer's Duckling instance.

- **Default flock size is capped at 16 replicas** unless support adjusts it.
- **Eventually consistent.** Replicas sync from the primary with a delay. This delay is acceptable for analytics workloads.
- **Automatic load distribution.** When using a Read Scaling token, MotherDuck routes queries across available replicas automatically.
- **Session affinity matters.** When using native DuckDB connections, pass a stable `session_hint` so the same user stays on the same replica when possible.
- **No query rewrite is required.** The main change is token type and connection configuration, not a new SQL dialect.

### When to Use CREATE SNAPSHOT and REFRESH DATABASE

| Scenario | Action |
|---|---|
| Routine analytics queries | Do nothing -- eventual consistency is fine |
| After a batch data load | `CREATE SNAPSHOT` on writer, then `REFRESH DATABASE` on reader |
| User just uploaded data and expects to see it | `CREATE SNAPSHOT` + `REFRESH DATABASE` |
| Dashboard refreshes every 5 minutes | Do nothing -- replicas will catch up within seconds |

---

## Security

Per-customer databases are the foundation of CFA security. Follow these rules without exception.

- **Per-customer databases eliminate cross-tenant data leakage by design.** There is no query that can accidentally return another customer's data because the data is in a different database entirely.
- **Use service accounts with minimum permissions.** CFA query endpoints need Read Scaling tokens only. Do not use Read/Write tokens for serving queries.
- **Never expose MotherDuck tokens to the frontend.** Tokens stay in the backend. The browser communicates with your API, which holds the tokens server-side.
- **Validate all queries before execution.** Even with per-customer isolation, validate that incoming queries are well-formed and within allowed patterns. Use parameterized queries or an allowlist of query templates.
- **Rotate tokens on a regular cadence.** Set expiration dates on all service tokens and rotate them every 90 days or sooner.
- **Revoke tokens immediately if compromised.** Use the MotherDuck UI to revoke tokens. Generate new tokens and update your secrets manager.

---

## Key Rules

- **Use the 3-tier architecture for production CFA.** Backend API between browser and MotherDuck. No exceptions for customer-facing products.
- **One database per customer for isolation.** This is a security requirement. Do not use a single database with `tenant_id` filtering for CFA.
- **Use the PG endpoint for backend connectivity.** It works with any PostgreSQL driver. No DuckDB installation needed on the backend.
- **Use Read Scaling tokens for concurrent reads.** Reserve Read/Write tokens for data ingestion only.
- **Keep serving tables lean and pre-aggregated.** Do not push raw multi-billion-row scans through end-user request paths if a curated serving table can answer the question.
- **Never expose service tokens to the frontend.** Tokens live in the backend. The browser never sees them.
- **Write DuckDB SQL, not PostgreSQL SQL.** Even when connecting via the PG endpoint. See `motherduck-duckdb-sql` skill.
- **Pre-aggregate data for dashboard queries.** Use materialized summary tables (see `motherduck-model-data` skill) to keep query latency under 1 second.

---

## Common Mistakes

### Using a single database with tenant_id filtering

Wrong approach: one shared database where every query includes `WHERE tenant_id = :customer_id`. A single missing filter clause leaks data across tenants. This is a security vulnerability, not a design tradeoff.

Right approach: one database per customer. Data isolation is structural and cannot be bypassed by a query bug.

### Exposing MotherDuck tokens to the frontend

Wrong approach: sending the MotherDuck token to the browser so it can query directly.

Right approach: the backend holds all tokens. The browser sends requests to your API, which executes queries server-side and returns results.

### Not enabling read scaling before launch

If you launch with Read/Write tokens serving all CFA queries, you have no concurrency scaling. Add read scaling before launch if the expected traffic is genuinely concurrent and read-heavy; otherwise keep the simpler path until the workload proves it is needed.

### Using Read/Write tokens for read-heavy workloads

Read/Write tokens route to the primary instance. Read Scaling tokens distribute load across replicas. Using the wrong token type means all read traffic hits a single instance.

### Assuming strong consistency with read replicas

Read replicas are eventually consistent. If your application writes data and immediately queries for it via a Read Scaling token, the write may not be visible yet. Use `CREATE SNAPSHOT` + `REFRESH DATABASE` when strict consistency is required after a write. When using native DuckDB connections, pair this with a stable `session_hint`.

### Skipping query validation

Even with per-customer database isolation, validate all incoming queries. Malformed or excessively expensive queries can consume resources. Use parameterized queries, query templates, or an allowlist to control what the CFA endpoint can execute.

---

## Related Skills

- `motherduck-connect` -- Establish a MotherDuck connection and authenticate via PG endpoint or native API
- `motherduck-model-data` -- Design per-customer schemas and denormalized analytical tables
- `motherduck-query` -- Execute DuckDB SQL queries, CTEs, and performance optimization
- `motherduck-explore` -- Discover databases, tables, columns, and data shares
- `motherduck-load-data` -- Ingest data from files, APIs, and cloud storage into customer databases

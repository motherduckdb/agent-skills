# TypeScript and Javascript MotherDuck Reference

Use this file for shared TypeScript/Javascript patterns that should stay consistent across skills.

## Default Choices

- Start with the simplest connection path that fits the runtime.
- Prefer the PG endpoint for thin backend services that already use PostgreSQL drivers.
- Prefer native DuckDB APIs when the service needs local file access, hybrid local/cloud execution, or richer DuckDB control.
- Prefer one connection first. Add pooling only after concurrency or lifecycle requirements are clear.

## Environment Helper

```ts
export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing env var: ${name}`);
  return value;
}
```

## PG Endpoint Starter

Use this for backend APIs, queues, and admin services that want PostgreSQL wire compatibility.

```ts
import pg from "pg";

const pool = new pg.Pool({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "analytics",
  user: "postgres",
  password: requireEnv("MOTHERDUCK_TOKEN"),
  ssl: { rejectUnauthorized: true },
});

const sql = `
  SELECT customer_id, SUM(amount) AS total_amount
  FROM "analytics"."main"."orders"
  WHERE order_date >= $1
  GROUP BY customer_id
  ORDER BY total_amount DESC
  LIMIT 20
`;

const { rows } = await pool.query(sql, ["2025-01-01"]);
```

## Native DuckDB Starter

Use this when the service needs hybrid execution or direct DuckDB control.

```ts
import { DuckDBInstance } from "@duckdb/node-api";

const db = await DuckDBInstance.create("md:analytics", {
  motherduck_token: requireEnv("MOTHERDUCK_TOKEN"),
  custom_user_agent: "my-service/1.0.0(api;analytics)",
});

const con = await db.connect();
const result = await con.run(`
  SELECT COUNT(*) AS total_rows
  FROM "analytics"."main"."orders"
`);
```

## Read Scaling Pattern

Use read scaling only for many concurrent read-only queries on the same account.

```ts
import { DuckDBInstance } from "@duckdb/node-api";

const db = await DuckDBInstance.create(
  "md:analytics?session_hint=user-123&access_mode=read_only&dbinstance_inactivity_ttl=300",
  {
    motherduck_token: requireEnv("MOTHERDUCK_READ_SCALING_TOKEN"),
    custom_user_agent: "customer-analytics/1.0.0(tenant-acme;dashboards)",
  }
);
```

Rules:

- Use a stable `session_hint` per end user, session, or tenant-facing request path.
- Treat read scaling replicas as eventually consistent.
- Keep read-only serving on read scaling tokens; keep writes on read/write tokens.
- Do not add read scaling before concurrency is the real problem.

## Attach Modes

Use workspace mode only when the application intentionally wants persistent attachment state.
Use single mode for narrow service connections and BI-style flows.

```ts
const db = await DuckDBInstance.create("md:analytics?attach_mode=single", {
  motherduck_token: requireEnv("MOTHERDUCK_TOKEN"),
});
```

## Query Tagging for Cost Attribution

Tag integrations and workload slices with `custom_user_agent`.

```ts
const db = await DuckDBInstance.create("md:analytics", {
  motherduck_token: requireEnv("MOTHERDUCK_TOKEN"),
  custom_user_agent: "etl-runner/2.3.1(pipeline-orders;team-data-platform)",
});
```

Use the same tag format consistently:

- `integration/version(metadata1;metadata2)`
- keep the integration and version parts free of spaces
- use metadata for pipeline name, tenant, team, or region

## Loading Best Practices

- Prefer Parquet over CSV when you control the source format.
- Prefer batch loads over row-by-row inserts.
- For API or event ingestion, buffer records and write in batches.
- Use CTAS or `COPY` for bulk loads instead of `executemany`-style insert loops.
- Keep transactions sized so loads finish comfortably, not as one giant unbounded write.

Example bulk load:

```ts
await pool.query(`
  CREATE OR REPLACE TABLE "raw"."main"."events" AS
  SELECT * FROM read_parquet('s3://my-bucket/events/*.parquet')
`);
```

## Shares and Dives

- Shares are zero-copy and read-only.
- Dives are live workspace artifacts that can be shared.
- Use shares when consumers need the data.
- Use Dives when consumers need a live answer surface inside MotherDuck.

---
name: share-data
description: Create and manage MotherDuck data shares for zero-copy data distribution. Use when sharing databases with team members, other organizations, or making data publicly available.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: workflow
  language_focus: "typescript|javascript|python"
  depends_on:
    - connect
    - explore
    - query
---

# Share Data with MotherDuck

Use this skill when distributing data to team members, partners, or the public without copying. Shares are read-only, zero-copy database clones: they create metadata references to the source database, not physical copies of the data.

For reusable language patterns, see `references/typescript.md` and `references/python.md`.

## Source Of Truth

- Prefer the current MotherDuck sharing docs and SQL reference first.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it before falling back to public docs.
- Keep the sharing model aligned with the documented behavior:
  - zero-copy and metadata-only
  - database-granularity sharing
  - read-only recipients
  - owner-controlled update mode

## Prerequisites

- MotherDuck connection established (see `connect` skill)
- A database with data to share (see `explore` skill to discover existing databases)
- Appropriate permissions to create shares on the source database

## Language Focus: TypeScript/Javascript and Python

- Prefer **Python** when automating:
  - recurring share creation
  - validation scripts
  - operational checks on shared datasets
- Prefer **TypeScript/Javascript** when the share workflow is part of:
  - partner or customer provisioning services
  - admin surfaces
  - app-side delivery tooling
- In both languages, treat shares as provisioning operations and keep the share SQL explicit and auditable.

## TypeScript/Javascript Starter

```ts
import pg from "pg";

const createShareSql = `
  CREATE SHARE IF NOT EXISTS partner_share FROM analytics (
    ACCESS RESTRICTED,
    VISIBILITY HIDDEN,
    UPDATE MANUAL
  )
`;

const client = new pg.Client({
  host: "pg.us-east-1-aws.motherduck.com",
  port: 5432,
  database: "analytics",
  user: "postgres",
  password: process.env.MOTHERDUCK_TOKEN,
  ssl: { rejectUnauthorized: true },
});

await client.connect();
await client.query(createShareSql);
await client.end();
```

## Python Starter

```python
import duckdb

conn = duckdb.connect("md:analytics")
conn.sql("""
CREATE SHARE IF NOT EXISTS partner_share FROM analytics (
  ACCESS RESTRICTED,
  VISIBILITY HIDDEN,
  UPDATE MANUAL
)
""")
conn.close()
```

---

## What Shares Are

A share is a read-only reference to a MotherDuck database. When you create a share, MotherDuck records share metadata pointing at the source database. No bytes are copied. Recipients attach the share and query it as a read-only clone in their own workspace.

Key properties:
- **Read-only**: Recipients can SELECT, but never INSERT, UPDATE, or DELETE.
- **Zero-copy**: No data duplication. The share itself incurs no additional storage cost.
- **Database-granularity**: Shares are created from databases, not arbitrary subsets of tables.
- **Owner-controlled updates**: Use `UPDATE MANUAL` for explicit snapshots or `UPDATE AUTOMATIC` for periodic propagation.
- **Access-controlled**: Restrict who can attach the share by organization, ACL, or share URL pattern.

---

## Sharing Workflow

Follow these steps in order:

1. **Choose the database to share.** Identify the source database containing the data you want to distribute.
2. **Decide access level and visibility.** Determine who should be able to attach the share and whether it should appear in share listings.
3. **Create the share.** Run the `CREATE SHARE` statement with the appropriate options.
4. **Distribute the share URL when needed.** Discoverable internal shares may be easy to find in the UI; hidden or partner-facing shares require the URL.
5. **Recipients attach and query.** Recipients use `ATTACH` with the share URL or the provided share reference and query the data directly.

---

## Create a Share

```sql
CREATE SHARE IF NOT EXISTS my_data_share FROM my_database (
  ACCESS ORGANIZATION,
  VISIBILITY DISCOVERABLE,
  UPDATE MANUAL
);
```

This creates a share named `my_data_share` from `my_database` that is visible to anyone in your organization, discoverable, and manual-update by default.

---

## Access Levels

Choose the access level that matches your distribution model. Default to the most restrictive level that meets your needs.

| Level | Who Can Access | Use Case |
|---|---|---|
| ORGANIZATION | Anyone in your MotherDuck organization | Internal team sharing |
| RESTRICTED | Specific users you grant access to | Named-recipient sharing and internal ACLs |
| UNRESTRICTED | Anyone with the share URL | Public datasets |

**Use ORGANIZATION for internal sharing.** It requires no per-user grants and automatically covers new team members.

**Use RESTRICTED for named users inside your organization.** Grant access with `GRANT READ ON SHARE ... TO ...` when you need an ACL instead of broad organization access.

**Use UNRESTRICTED only for truly public or deliberate link-based distribution.** Anyone who obtains the URL can attach and query the data. Never use UNRESTRICTED for sensitive, proprietary, or PII-containing data.

---

## Visibility Options

Visibility controls whether the share is easy for users to find. Access level still controls who can read it.

| Visibility | Behavior |
|---|---|
| DISCOVERABLE | Appears in the UI and other discovery surfaces for users who have access |
| HIDDEN | Only accessible via direct URL |

**Use DISCOVERABLE by default.** It makes shares easy to find and reduces "I didn't know that data existed" problems.

**Use HIDDEN when the share contains sensitive data** or when you want to control distribution strictly through direct URL sharing.

---

## Update Modes

Update mode determines whether the share reflects a frozen snapshot or always-current data.

| Mode | Behavior |
|---|---|
| MANUAL | Share reflects the last explicit published snapshot; run `UPDATE SHARE` to refresh |
| AUTOMATIC | Share updates automatically after source database changes propagate |

**Use MANUAL for point-in-time snapshots.** This is the right choice when recipients need a stable, reproducible dataset -- for example, a quarterly report or a versioned data product. Recipients always see the same data until you explicitly refresh.

**Use AUTOMATIC for always-current data.** This is the right choice when recipients need fresh data without a manual publish step. Treat it as periodic propagation rather than instant synchronization.

---

## Creating Shares for Common Scenarios

### Internal Team Share (Most Common)

Share a curated analytics database with your organization:

```sql
CREATE SHARE IF NOT EXISTS analytics_share FROM analytics_db (
  ACCESS ORGANIZATION,
  VISIBILITY DISCOVERABLE,
  UPDATE AUTOMATIC
);
```

### Named-Recipient Share

Share results with a controlled ACL:

```sql
CREATE SHARE IF NOT EXISTS partner_results FROM partner_deliverables (
  ACCESS RESTRICTED,
  VISIBILITY HIDDEN,
  UPDATE MANUAL
);
```

Grant access explicitly:

```sql
GRANT READ ON SHARE partner_results TO duck1, duck2;
```

### Link-Based External Share

Make data available through a direct share URL:

```sql
CREATE SHARE IF NOT EXISTS partner_benchmark FROM benchmark_data (
  ACCESS UNRESTRICTED,
  VISIBILITY HIDDEN,
  UPDATE MANUAL
);
```

---

## Managing Shares

### List All Shares You Own

```sql
LIST SHARES;
```

```sql
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;
```

`LIST SHARES` lists shares created by the current user. For shares from other users, use `MD_INFORMATION_SCHEMA.SHARED_WITH_ME`.

### List Shares Shared With You

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

### Manually Refresh a Share

Use this when the share has `UPDATE MANUAL` and the source data has changed.

```sql
UPDATE SHARE my_data_share;
```

After refreshing, tell recipients to run `REFRESH DATABASE` on their attached clone if they need the new snapshot immediately.

### Modify Recipient Access

For restricted shares, grant or revoke access explicitly:

```sql
GRANT READ ON SHARE my_data_share TO user_1, user_2;
REVOKE READ ON SHARE my_data_share FROM user_3;
```

### Delete a Share

Remove a share permanently. Recipients lose access immediately.

```sql
DROP SHARE my_data_share;
```

Dropping a share does not affect the source database. It only removes the share reference.

---

## Consuming Shares (Recipient Side)

### Attach a Shared Database

```sql
ATTACH '<share_url>' AS partner_data;
```

Replace `<share_url>` with the URL provided by the share owner. Choose a meaningful alias that describes the data.

### Refresh to Get Latest Updates

When the share owner updates a MANUAL share, refresh to pull the latest snapshot:

```sql
REFRESH DATABASE partner_data;
```

### Query Shared Data

Once attached, query shared tables like any other database. Use fully qualified names.

```sql
SELECT * FROM partner_data.main.customers LIMIT 10;
```

```sql
-- Join shared data with your own tables
SELECT
    c.customer_id,
    c.name,
    o.order_total
FROM partner_data.main.customers c
JOIN my_db.main.orders o ON c.customer_id = o.customer_id;
```

### See What Is Shared with You

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

This returns share names, URLs, owners, and metadata. Use the URL to attach shares you have not yet attached.

---

## Discovering Shares

### Find Shares by URL

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME
WHERE url = '<share_url>';
```

### Browse All Shares You Own

```sql
LIST SHARES;
```

### Explore a Shared Database After Attaching

Once a share is attached, explore it like any other database:

```sql
-- List tables in the shared database
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'partner_data';

-- Inspect columns
SELECT column_name, data_type, comment
FROM duckdb_columns()
WHERE database_name = 'partner_data'
  AND table_name = 'customers';

-- Get statistics
SUMMARIZE partner_data.main.customers;
```

---

## Use Cases

- **Cross-team analytics**: Share curated datasets between data engineering, analytics, and product teams. Use ORGANIZATION access with AUTOMATIC updates so everyone always sees the latest data.
- **Partner data exchange**: Share results with named users via RESTRICTED access and `GRANT READ ON SHARE`, or use a hidden URL pattern when distribution is link-based. Use MANUAL updates to control exactly what version partners see.
- **Public datasets**: Make open data available to anyone with UNRESTRICTED access. Treat link distribution deliberately and do not use it for sensitive datasets.
- **Data products**: Build curated, versioned datasets for consumption. Use MANUAL updates to create explicit versions and refresh on a defined cadence.
- **Reproducible analysis**: Share a frozen snapshot of the data used in a specific analysis. Use MANUAL updates and HIDDEN visibility. Recipients always see the exact data the analysis was built on.

---

## Key Rules

- **Shares are read-only.** Recipients cannot modify source data. This is a feature, not a limitation -- it guarantees data integrity.
- **Zero-copy means no storage cost** for the share itself. The only storage cost is the source database and any retained data there.
- **Use MANUAL update mode for point-in-time snapshots.** This gives you explicit control over what recipients see.
- **Use AUTOMATIC update mode for always-current data.** Recipients see changes after normal propagation without an explicit publish step.
- **Use ORGANIZATION access for internal sharing.** It is the simplest and most maintainable option for team distribution.
- **Use RESTRICTED access for named recipients and ACL-style control.** Never use UNRESTRICTED for data that should not be public.
- **Use DISCOVERABLE visibility by default.** Only use HIDDEN when the share contains sensitive data or you need strict distribution control.
- **Always notify recipients after running `UPDATE SHARE`** on a MANUAL share. They may need to run `REFRESH DATABASE` to see the changes immediately.
- **Use fully qualified table names** when querying shared databases to avoid ambiguity with local tables.
- **Use shares for governed data distribution, not writable collaboration.** Recipients cannot modify shared databases.

---

## Common Mistakes

### Expecting recipients to write to shared databases

Shares are read-only. Recipients cannot INSERT, UPDATE, DELETE, or CREATE tables in a shared database. If a recipient needs to modify or extend shared data, they should copy it into their own database first:

```sql
CREATE TABLE my_db.main.local_copy AS
SELECT * FROM partner_data.main.customers;
```

### Using UNRESTRICTED access for sensitive data

UNRESTRICTED means anyone with the URL can access the data. Never use this for proprietary, internal, or PII-containing datasets. Use RESTRICTED or ORGANIZATION instead.

### Treating shares like row-level security

Shares operate at the database level. If you need per-customer or per-user isolation, publish separate databases or move to customer-facing analytics patterns with stronger structural isolation. Do not imply a share is a substitute for query-time row entitlements.

### Forgetting to UPDATE SHARE with MANUAL mode

With MANUAL update mode, the share reflects data at creation time. If the source database changes, recipients see stale data until you explicitly refresh:

```sql
-- Owner runs this to push new data to the share
UPDATE SHARE my_data_share;
```

Without this step, recipients continue querying the original snapshot indefinitely.

### Not using REFRESH DATABASE on the consumer side

Even after the share owner runs `UPDATE SHARE`, recipients must refresh their attached copy to see the update:

```sql
-- Recipient runs this to pull the latest share snapshot
REFRESH DATABASE partner_data;
```

Without this step, the recipient's local attachment still points to the previous snapshot.

### Dropping a share without notifying recipients

When you drop a share, recipients lose access immediately. Their queries against the shared database start failing. Always communicate deprecation plans before dropping a share. Consider setting a deprecation window and notifying all known recipients.

### Not exploring shared data before querying

Shared databases can have unfamiliar schemas. Always explore the structure before writing queries:

```sql
-- Check what tables exist
SELECT table_name FROM duckdb_tables()
WHERE database_name = 'partner_data';

-- Inspect columns before querying
SELECT column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'partner_data'
  AND table_name = 'customers';
```

---

## Related Skills

- `connect` -- Establish a MotherDuck connection and authenticate
- `explore` -- Discover databases, tables, columns, and data shares
- `query` -- Execute DuckDB SQL queries against MotherDuck databases
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup

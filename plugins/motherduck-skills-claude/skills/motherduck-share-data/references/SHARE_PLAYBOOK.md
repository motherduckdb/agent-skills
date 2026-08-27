# Share Playbook

Reference for creating, operating, and consuming MotherDuck shares safely.

## Contents

| Section | Covers |
| --- | --- |
| What Shares Are | Read-only, zero-copy semantics with optional table/view filtering |
| SQL-First Posture | Shares as explicit, auditable SQL operations |
| Default Workflow | Owner-to-consumer sequence |
| SQL Workflow Template | Copyable end-to-end owner and consumer SQL |
| Create a Share | `CREATE SHARE` options |
| Table-Level Security | `INCLUDE_PATTERN`, preview, alter, and limitations |
| Access Levels | ORGANIZATION vs RESTRICTED vs UNRESTRICTED |
| Role Grants | Governed user and role access |
| Visibility Options | DISCOVERABLE vs HIDDEN |
| Update Modes | MANUAL vs AUTOMATIC |
| Common Share Patterns | Internal, named-recipient, link-based external |
| Operating Shares | List, refresh, grant/revoke, drop |
| Consuming Shares | Attach, refresh, query shared data |
| Discovering and Exploring Shares | Find shares and inspect attached schemas |
| Use Cases | Distribution patterns by scenario |
| Key Rules | Sharing defaults in one list |
| Common Mistakes | Frequent share failures and fixes |

## What Shares Are

A share is a read-only reference to a MotherDuck database. When you create a share, MotherDuck records share metadata pointing at the source database. No bytes are copied. Recipients attach the share and query its exposed catalog as a read-only database in their own workspace.

Key properties:

- **Read-only**: recipients can `SELECT`, but never `INSERT`, `UPDATE`, or `DELETE`
- **Zero-copy**: no data duplication; the share itself incurs no additional storage cost
- **Database-backed**: every share has one source database; an optional `INCLUDE_PATTERN` exposes only selected tables and views
- **Owner-controlled updates**: use `UPDATE MANUAL` for explicit snapshots or `UPDATE AUTOMATIC` for periodic propagation
- **Access-controlled**: restrict who can attach the share by organization, ACL, or share URL pattern

## SQL-First Posture

- Keep share creation and maintenance as explicit SQL, even when the caller is an application or provisioning tool.
- Make access, visibility, update mode, and any include pattern explicit in every `CREATE SHARE`.
- Treat share operations as auditable database changes, not as hidden driver logic.
- Use SQL to verify the share state after every create, update, grant, revoke, or attach step.

## Default Workflow

1. Choose the source database to share.
2. Decide access level, table/view scope, visibility, and freshness requirements.
3. Preview and validate any include pattern against the live catalog.
4. Create the share with explicit options and read its stored state back.
5. Grant restricted access to users or roles and distribute the URL if the share is hidden or external.
6. Have recipients attach and verify the visible catalog before querying it.
7. For manual shares, run `UPDATE SHARE` on the owner side and `REFRESH DATABASE` on the consumer side.

## SQL Workflow Template

Use this sequence as the default shape:

```sql
-- owner side
CREATE SHARE IF NOT EXISTS partner_share FROM analytics (
  ACCESS RESTRICTED,
  VISIBILITY HIDDEN,
  UPDATE MANUAL,
  INCLUDE_PATTERN 'reporting.*, main.orders'
);

GRANT READ ON SHARE partner_share TO ROLE partner_analyst, USER duck1;

LIST SHARES;
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;

-- later, when publishing a new manual snapshot
UPDATE SHARE partner_share;

-- consumer side
ATTACH '<share_url>' AS partner_data;
REFRESH DATABASE partner_data;

SELECT * FROM "partner_data"."main"."customers" LIMIT 10;
```

## Create a Share

```sql
CREATE SHARE IF NOT EXISTS my_data_share FROM my_database (
  ACCESS RESTRICTED,
  VISIBILITY DISCOVERABLE,
  UPDATE AUTOMATIC,
  INCLUDE_PATTERN 'analytics.*, main.dim_*'
);

GRANT READ ON SHARE my_data_share TO ROLE analyst;
```

This creates a share named `my_data_share` from `my_database`, exposes the selected tables and views, and grants the governed audience through a role. Always state access, visibility, update mode, and filtering policy explicitly.

## Table-Level Security

`INCLUDE_PATTERN` is a comma-separated list of `schema.table` patterns. It controls what every recipient of that share can see. It does not filter rows or mask columns.

Preview a pattern against the source database before applying it when the preview function is available in the current MotherDuck version. At minimum, inspect the live schemas, tables, and views and verify that every pattern matches an intended object; validation is all-or-nothing and a pattern that matches nothing fails the statement.

Create a filtered share:

```sql
CREATE SHARE finance_share FROM warehouse (
  ACCESS RESTRICTED,
  UPDATE AUTOMATIC,
  INCLUDE_PATTERN 'finance.*, main.calendar'
);
```

Change or remove the filter without changing the share URL:

```sql
ALTER SHARE finance_share SET INCLUDE_PATTERN 'finance.reporting_*, main.calendar';
ALTER SHARE finance_share RESET INCLUDE_PATTERN;
```

The three stored states are distinct:

| State | Effect |
|---|---|
| `NULL` / `RESET INCLUDE_PATTERN` | Exposes the whole source database |
| Empty pattern list | Exposes no tables or views; the default schema still exists |
| One or more patterns | Exposes matching tables and views |

Read the stored value from `LIST SHARES` or `MD_INFORMATION_SCHEMA.OWNED_SHARES`. Changes reach held-open consumers on the next update cycle; detach and reattach when immediate verification matters.

Limitations:

- Filtered shares require native MotherDuck storage. DuckLake shares can be unfiltered; Iceberg catalogs cannot be shared.
- A filtered share cannot be the source of `CREATE DATABASE ... FROM` or a wholesale `COPY DATABASE`. Copy its visible tables with `COPY FROM DATABASE` instead.
- Patterns select tables and views only. Macros, sequences, and types follow schema visibility; objects in the default schema may remain visible.
- Visible view or macro definitions can name hidden objects even though the hidden data remains unreadable.

## Access Levels

Choose the access level that matches your distribution model. Default to the most restrictive level that meets your needs.

| Level | Who Can Access | Use Case |
|---|---|---|
| ORGANIZATION | Anyone in your MotherDuck organization | Internal team sharing |
| RESTRICTED | Specific users you grant access to | Named-recipient sharing and internal ACLs |
| UNRESTRICTED | Anyone with the share URL | Public datasets |

Prefer `RESTRICTED` plus role grants for internal sharing. Use `ORGANIZATION` only for deliberate legacy organization-wide access; current RBAC guidance prefers granting the share to the `explorer` role instead.

Use `RESTRICTED` for named users when you need an ACL instead of broad organization access. Grant access with `GRANT READ ON SHARE ... TO ...`.

Use `UNRESTRICTED` only for truly public or deliberate link-based distribution. Never use it for sensitive, proprietary, or PII-containing data.

## Role Grants

Grant a restricted share to the lowest role that should receive it. Roles that inherit that role receive the grant too.

```sql
CREATE ROLE IF NOT EXISTS finance;
GRANT ROLE explorer TO ROLE finance;
GRANT READ ON SHARE finance_share TO ROLE finance;

SHOW GRANTS ON SHARE finance_share;
SHOW USERS OF ROLE finance;
```

Grants decide who can attach a share; `INCLUDE_PATTERN` decides what every grantee of that share can see. If two audiences need different subsets, create two shares with different patterns and grant each share to the appropriate role.

## Visibility Options

Visibility controls whether the share is easy for users to find. Access level still controls who can read it.

| Visibility | Behavior |
|---|---|
| DISCOVERABLE | Appears in the UI and other discovery surfaces for users who have access |
| HIDDEN | Only accessible via direct URL |

Use `DISCOVERABLE` by default. It reduces "I didn't know that data existed" problems.

Use `HIDDEN` when the share contains sensitive data or when you want to control distribution strictly through direct URL sharing.

## Update Modes

Update mode determines whether the share reflects a frozen snapshot or always-current data.

| Mode | Behavior |
|---|---|
| MANUAL | Share reflects the last explicit published snapshot; run `UPDATE SHARE` to refresh |
| AUTOMATIC | Share updates automatically after source database changes propagate |

Use `MANUAL` for point-in-time snapshots, versioned data products, and reproducible analysis.

Use `AUTOMATIC` for always-current data. Treat it as periodic propagation rather than instant synchronization.

The implicit default is client-version-sensitive: DuckDB 1.5.5 and later default an omitted mode to `UPDATE AUTOMATIC`, while older supported clients retain their earlier behavior. Keep the mode explicit in durable SQL so the publication contract does not change with the client version.

## Common Share Patterns

### Internal Team Share

```sql
CREATE SHARE IF NOT EXISTS analytics_share FROM analytics_db (
  ACCESS RESTRICTED,
  VISIBILITY DISCOVERABLE,
  UPDATE AUTOMATIC
);

GRANT READ ON SHARE analytics_share TO ROLE explorer;
```

### Named-Recipient Share

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

```sql
CREATE SHARE IF NOT EXISTS partner_benchmark FROM benchmark_data (
  ACCESS UNRESTRICTED,
  VISIBILITY HIDDEN,
  UPDATE MANUAL
);
```

## Operating Shares

### List All Shares You Own

```sql
LIST SHARES;
```

```sql
FROM MD_INFORMATION_SCHEMA.OWNED_SHARES;
```

`LIST SHARES` lists shares created by the current user. For shares from other users, use `MD_INFORMATION_SCHEMA.SHARED_WITH_ME` (see Consuming Shares).

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

## Consuming Shares

### Attach a Shared Database

```sql
ATTACH '<share_url>' AS partner_data;
```

Replace `<share_url>` with the URL provided by the share owner. Choose a meaningful alias that describes the data.

### Refresh to Get Latest Updates

When the share owner updates a manual share, refresh to pull the latest snapshot:

```sql
REFRESH DATABASE partner_data;
```

### Query Shared Data

Once attached, query shared tables like any other database. Use fully qualified names.

```sql
SELECT * FROM "partner_data"."main"."customers" LIMIT 10;
```

```sql
SELECT
    c.customer_id,
    c.name,
    o.order_total
FROM "partner_data"."main"."customers" c
JOIN "my_db"."main"."orders" o ON c.customer_id = o.customer_id;
```

### See What Is Shared With You

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME;
```

This returns share names, URLs, owners, and metadata. Use the URL to attach shares you have not yet attached.

## Discovering and Exploring Shares

### Find Shares by URL

```sql
FROM MD_INFORMATION_SCHEMA.SHARED_WITH_ME
WHERE url = '<share_url>';
```

### Explore a Shared Database After Attaching

Once a share is attached, explore it like any other database:

```sql
SELECT database_name, schema_name, table_name, comment
FROM duckdb_tables()
WHERE database_name = 'partner_data';
```

```sql
SELECT column_name, data_type, comment
FROM duckdb_columns()
WHERE database_name = 'partner_data'
  AND table_name = 'customers';
```

```sql
SUMMARIZE "partner_data"."main"."customers";
```

## Use Cases

- **Cross-team analytics**: share curated datasets between data engineering, analytics, and product teams. Use a restricted share granted to the appropriate roles with `AUTOMATIC` updates.
- **Partner data exchange**: share results with named users via `RESTRICTED` access and `GRANT READ ON SHARE`, or use a hidden URL when distribution is link-based. Use `MANUAL` updates to control exactly what version partners see.
- **Public datasets**: make open data available to anyone with `UNRESTRICTED` access. Treat link distribution deliberately and do not use it for sensitive datasets.
- **Data products**: build curated, versioned datasets for consumption. Use `MANUAL` updates to create explicit versions and refresh on a defined cadence.
- **Reproducible analysis**: share a frozen snapshot of the data used in a specific analysis. Use `MANUAL` updates and `HIDDEN` visibility.

## Key Rules

- Shares are read-only.
- Zero-copy means no storage duplication for the share itself.
- Use `MANUAL` update mode for snapshots and `AUTOMATIC` for always-current delivery.
- Prefer restricted shares and role grants for internal sharing.
- Use `INCLUDE_PATTERN` only for whole-table/view filtering; use separate shares when audiences need different subsets.
- Use `RESTRICTED` for named recipients and ACL-style control.
- Use `DISCOVERABLE` by default and `HIDDEN` when distribution should stay controlled.
- Notify recipients after `UPDATE SHARE` on manual shares because they may need `REFRESH DATABASE`.
- Use fully qualified table names when querying shared databases.
- Use shares for governed distribution, not writable collaboration.

## Common Mistakes

### Expecting Recipients to Write to Shared Databases

Shares are read-only. If a recipient needs to modify or extend shared data, they should copy it into their own database first:

```sql
CREATE TABLE "my_db"."main"."local_copy" AS
SELECT * FROM "partner_data"."main"."customers";
```

### Using Unrestricted Access for Sensitive Data

`UNRESTRICTED` means anyone with the URL can access the data. Never use this for proprietary, internal, or PII-containing datasets.

### Treating Table-Level Security Like Row-Level Security

`INCLUDE_PATTERN` selects whole tables and views. If you need row-level, column-level, per-customer, or per-user isolation, publish separate databases/shares or move to customer-facing analytics patterns with stronger structural isolation.

### Forgetting to Update a Manual Share

With `MANUAL` update mode, recipients see stale data until you explicitly refresh:

```sql
UPDATE SHARE my_data_share;
```

### Forgetting to Refresh on the Consumer Side

Even after the owner updates the share, recipients must refresh their attached copy:

```sql
REFRESH DATABASE partner_data;
```

### Dropping a Share Without Notifying Recipients

When you drop a share, recipients lose access immediately. Communicate a deprecation window before removing a share that other people rely on.

### Not Exploring Shared Data Before Querying

Always inspect the shared schema before writing downstream queries:

```sql
SELECT table_name
FROM duckdb_tables()
WHERE database_name = 'partner_data';
```

```sql
SELECT column_name, data_type
FROM duckdb_columns()
WHERE database_name = 'partner_data'
  AND table_name = 'customers';
```

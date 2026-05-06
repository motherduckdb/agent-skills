# Pricing and ROI Playbook

Reference for framing MotherDuck pricing, workload cost drivers, and ROI discussions without overpromising or hardcoding stale commercial details.

## When To Use

- The user asks about pricing, spend, invoices, budget caps, or plan fit.
- The user is comparing MotherDuck with another warehouse or lakehouse from a cost perspective.
- The user wants a pilot or rollout framed in ROI terms.

## SQL-First Cost Attribution Posture

- Connect pricing to workload shape, isolation boundaries, and compute ownership, not to programming language.
- Use `custom_user_agent` to tag the workload, pipeline, tenant, or internal service that issued the queries.
- Use service accounts deliberately when you need a stable billing and attribution boundary.
- Use SQL over `MD_INFORMATION_SCHEMA.QUERY_HISTORY` and storage views for internal reporting or chargeback.

## How To Answer

Work through these questions in order:

1. What workload shape is being priced?
2. What team size or consumption pattern matters?
3. What alternative is the user comparing against?
4. Is the real concern raw cost, procurement risk, or operational overhead?

## Cost Framing Checklist

- Separate storage, compute, and operational complexity.
- Identify whether the workload is exploratory, BI-style, app-serving, or pipeline-heavy.
- Call out architecture choices that change cost shape:
  - PG endpoint vs native DuckDB API
  - single shared database vs per-customer isolation
  - Dive/dashboard serving vs exported results
  - native MotherDuck storage vs DuckLake
- Explain what the user can validate with a small pilot before making a larger commitment.

## Best Practice for Compute Attribution

MotherDuck's public docs explicitly support tagging workloads with `custom_user_agent` and then grouping query activity in `MD_INFORMATION_SCHEMA.QUERY_HISTORY`.

Use this when the team needs to answer:

- which workflow caused this spend
- which pipeline or integration is responsible for the bill
- which tenant or customer should receive internal chargeback
- whether a cost spike came from BI, ingestion, app-serving, or one-off analyst work

Important:

- `QUERY_HISTORY` is currently a Business-plan, admin-only, preview feature
- this is an internal accounting pattern, not a native MotherDuck chargeback feature

### Tagging convention

MotherDuck docs recommend a convention like:

- `integration`
- `integration/version`
- `integration/version(workload,team)`
- `customerportal/version(tenant42,eucentral1)`

Keep the first metadata slot stable if you want to roll usage up by one workload or tenant label later.

### SQL to inspect tagged workload activity

```sql
WITH tagged_queries AS (
  SELECT
    start_time,
    end_time,
    user_name,
    instance_type,
    user_agent,
    regexp_extract(user_agent, '^(?:[^ ]+ ){2}(.+)$', 1) AS custom_tag
  FROM MD_INFORMATION_SCHEMA.QUERY_HISTORY
  WHERE regexp_matches(user_agent, '^(?:[^ ]+ ){2}.+$')
),
parsed AS (
  SELECT
    start_time,
    end_time,
    user_name,
    instance_type,
    custom_tag,
    regexp_extract(custom_tag, '^([^/( ]+)', 1) AS integration_name,
    nullif(split_part(regexp_extract(custom_tag, '\\(([^)]*)\\)', 1), ',', 1), '') AS workload_name
  FROM tagged_queries
)
SELECT
  integration_name,
  coalesce(workload_name, 'unlabeled') AS workload_name,
  user_name,
  instance_type,
  count(*) AS queries,
  sum(date_diff('second', start_time, end_time)) AS total_elapsed_seconds
FROM parsed
GROUP BY ALL
ORDER BY total_elapsed_seconds DESC;
```

Use this when the goal is to distinguish app-serving workloads from pipelines, dashboards, internal notebooks, or one specific tenant-facing integration.

## Service Accounts as Billing Boundaries

Service accounts matter for pricing and ROI because they are not just auth objects. In MotherDuck's hypertenancy model, each user or service account gets its own Duckling boundary. That makes service accounts a practical way to separate:

- production vs staging
- ingestion vs serving
- one customer vs another customer
- one internal team or workload class vs another

When a workload is run through a dedicated service account, that service account shows up as `QUERY_HISTORY.USER_NAME`. This gives the team a straightforward SQL handle for grouping usage by owner boundary.

This is also the cleanest pattern when the downstream application wants to map MotherDuck usage back to end customers. A per-customer or per-environment service account gives you a stable unit that can be joined to your own billing or account model outside MotherDuck.

### SQL to roll up usage by service account

```sql
SELECT
  user_name,
  instance_type,
  count(*) AS queries,
  sum(date_diff('second', start_time, end_time)) AS tracked_elapsed_seconds
FROM MD_INFORMATION_SCHEMA.QUERY_HISTORY
WHERE start_time >= date_trunc('month', now())
GROUP BY ALL
ORDER BY tracked_elapsed_seconds DESC;
```

This is the simplest starting point for understanding whether:

- one service account is driving most of the spend
- a specific environment needs a different Duckling size
- a customer-facing workload should be split into more isolated service accounts

## Internal Chargeback and Customer Billing

The public docs support two useful patterns:

1. Tag workloads with `custom_user_agent` to distinguish pipelines, dashboards, internal tools, or individual tenants.
2. Use service accounts to create a stronger compute and ownership boundary when you need clearer attribution.

That leads to two common internal models:

- **Workload chargeback**: allocate cost across pipelines, BI, dashboards, and application-serving surfaces
- **Tenant or customer chargeback**: allocate cost to a customer-facing service account or a tagged tenant workload

### SQL to estimate tracked usage share by workload

```sql
WITH tagged_queries AS (
  SELECT
    start_time,
    end_time,
    regexp_extract(user_agent, '^(?:[^ ]+ ){2}(.+)$', 1) AS custom_tag
  FROM MD_INFORMATION_SCHEMA.QUERY_HISTORY
  WHERE start_time >= date_trunc('month', now())
    AND regexp_matches(user_agent, '^(?:[^ ]+ ){2}.+$')
),
workload_usage AS (
  SELECT
    coalesce(
      nullif(split_part(regexp_extract(custom_tag, '\\(([^)]*)\\)', 1), ',', 1), ''),
      regexp_extract(custom_tag, '^([^/( ]+)', 1)
    ) AS workload_name,
    sum(date_diff('second', start_time, end_time)) AS elapsed_seconds
  FROM tagged_queries
  GROUP BY 1
),
totals AS (
  SELECT sum(elapsed_seconds) AS total_elapsed_seconds
  FROM workload_usage
)
SELECT
  workload_name,
  elapsed_seconds,
  elapsed_seconds::double / nullif(total_elapsed_seconds, 0) AS tracked_usage_share
FROM workload_usage, totals
ORDER BY tracked_usage_share DESC;
```

Apply the resulting share to an external invoice only as an internal accounting convention. Do not present this as MotherDuck's official billing breakdown.

## Storage and Lifecycle Visibility

For storage-driven pricing discussions, use the storage lifecycle views rather than only looking at current visible table size.

```sql
SELECT
  user_name,
  database_name,
  active_bytes,
  historical_bytes,
  retained_for_clone_bytes,
  failsafe_bytes
FROM MD_INFORMATION_SCHEMA.STORAGE_INFO
ORDER BY active_bytes DESC;
```

This is especially important when the user is confused by:

- historical retention costs
- clone- or share-related retained bytes
- why deleted data is not immediately absent from billing

## Public Pricing Structure To Reference

The public pricing page currently frames MotherDuck around:

- Lite
- Business
- Enterprise
- instance types: Pulse, Standard, Jumbo, Mega, Giga
- optional read-scaling replicas
- snapshot retention, query history, and plan-specific commercial features

Use the current pricing page for exact numbers. Do not hardcode numbers in durable answers unless you have verified them in the current turn.

## Compute and Storage Realities To Call Out

- Pulse is usage-based and fits bursty or smaller read-heavy work well.
- Standard, Jumbo, Mega, and Giga are wall-clock metered instance types with cooldown behavior. Their cooldown periods are configurable from 1 minute to 24 hours; Pulse does not accept `cooldown_seconds`.
- For batch or CI/CD workloads, `SHUTDOWN` can skip idle cooldown after work completes, while `SHUTDOWN TERMINATE` force-stops running work. Both still have the documented minimum billing period.
- Storage billing is for compressed MotherDuck-managed storage plus retained recoverability windows, not just the current visible table size.
- Shares are zero-copy and do not add storage cost by themselves.
- Data kept in the customer's own object store for DuckLake or BYOB-style patterns is not billed as MotherDuck-managed storage.

## How To Map Workload To Cost Shape

- Pulse:
  - lightweight, bursty, ad-hoc work
  - high-volume read-only workloads can also fit when the unit size is small enough
- Standard:
  - common warehouse work
  - routine loads, transforms, and engineering tasks
- Jumbo:
  - larger transformations, complex joins, heavier concurrent workloads
- Mega and Giga:
  - unusually heavy transformations or high-complexity workloads
- Read Scaling:
  - BI dashboards and read-only workloads with concurrency pressure

## ROI Questions That Matter

- What systems does MotherDuck replace or simplify?
- Does the team avoid maintaining a larger warehouse cluster or extra replicas?
- Does Hypertenancy reduce the need for custom isolation infrastructure?
- Do service accounts create a cleaner way to map compute spend back to workloads, teams, or customers?
- Does `pg_duckdb` avoid a full warehouse migration in phase one?
- Does read scaling let the team separate dashboard concurrency from write-heavy paths?
- Does DuckLake add value, or would it add unnecessary complexity compared with managed storage?

## ROI Guidance

Frame ROI with concrete categories:

- faster initial delivery
- lower operational overhead
- simpler app or dashboard architecture
- fewer systems to integrate and maintain
- faster internal or external access to analytics

## Plan-Aware Talking Points

- Business is publicly positioned for production analytics, with more users, unlimited service accounts, read-scaling replicas, 90-day snapshot retention, query history, support from MotherDuck experts, and a 99.9% availability SLA.
- Current public materials say Dives are available on all plans, while Embedded Dives are positioned as Business-plan functionality.
- Enterprise is publicly positioned for larger-scale deployments with custom commercial terms, fixed-cost capacity pricing, and AWS PrivateLink connectivity.
- Trust and compliance can matter to ROI because security review friction, support level, and procurement constraints affect total adoption cost.

## What Not To Do

- Do not invent custom discounts, annual terms, or enterprise commitments.
- Do not promise lower total cost than another system without workload evidence.
- Do not treat a pricing question as purely technical when it is really about predictability, procurement, or downside risk.
- Do not make up pricing numbers, savings claims, or contract terms.

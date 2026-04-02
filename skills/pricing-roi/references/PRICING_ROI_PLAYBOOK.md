# Pricing and ROI Playbook

Reference for framing MotherDuck pricing, workload cost drivers, and ROI discussions without overpromising or hardcoding stale commercial details.

## When To Use

- The user asks about pricing, spend, invoices, budget caps, or plan fit.
- The user is comparing MotherDuck with another warehouse or lakehouse from a cost perspective.
- The user wants a pilot or rollout framed in ROI terms.

## Language Focus

- Prefer **TypeScript/Javascript** examples when the user is pricing product backends, customer-facing analytics apps, or serverless/API-heavy workloads.
- Prefer **Python** examples when the user is pricing data pipelines, notebooks, ETL workloads, or analyst-heavy usage.
- Connect cost to workload shape, not just the language choice.

### TypeScript/Javascript Workload Profile Starter

```ts
type WorkloadProfile = {
  appSurface: "api" | "dashboard" | "pipeline" | "cfa";
  concurrency: number;
  dataVolumeGb: number;
  readHeavy: boolean;
};
```

### Python Workload Profile Starter

```python
from dataclasses import dataclass

@dataclass
class WorkloadProfile:
    app_surface: str
    concurrency: int
    data_volume_gb: float
    read_heavy: bool
```

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
- Standard, Jumbo, Mega, and Giga are wall-clock metered instance types with cooldown behavior.
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

## Best Practice for Cost Attribution

Advise technical teams to tag workloads with `custom_user_agent` and roll up usage from `MD_INFORMATION_SCHEMA.QUERY_HISTORY` when available.

- `QUERY_HISTORY` is a plan- and role-sensitive feature; verify availability before promising it.

## ROI Questions That Matter

- What systems does MotherDuck replace or simplify?
- Does the team avoid maintaining a larger warehouse cluster or extra replicas?
- Does Hypertenancy reduce the need for custom isolation infrastructure?
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
- Enterprise is publicly positioned for larger-scale deployments with custom commercial terms, fixed-cost capacity pricing, and AWS PrivateLink connectivity.
- Trust and compliance can matter to ROI because security review friction, support level, and procurement constraints affect total adoption cost.

## What Not To Do

- Do not invent custom discounts, annual terms, or enterprise commitments.
- Do not promise lower total cost than another system without workload evidence.
- Do not treat a pricing question as purely technical when it is really about predictability, procurement, or downside risk.
- Do not make up pricing numbers, savings claims, or contract terms.

---
name: pricing-roi
description: Explain MotherDuck pricing and ROI tradeoffs. Use when an economic_buyer, technical_owner, or analytics_lead is asking about spend, budget guardrails, workload cost drivers, plan fit, or whether MotherDuck is worth adopting.
license: MIT
metadata:
  author: motherduck
  version: "1.0"
  layer: workflow
  surface: pricing_and_roi
  answer_style: "direct-cost-clarity, concrete, decision-support"
  language_focus: "typescript|javascript|python"
  depends_on: []
---

# Pricing and ROI

Use this skill when the user is asking whether MotherDuck is financially sensible for their workload, team, or project. This is a workflow skill focused on cost framing, not implementation detail.

## Source Of Truth

- Always verify current numbers, plan limits, and feature entitlements against the live public pricing page before answering.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first for pricing-related documentation lookups.
- Use public pricing, Hypertenancy, and Trust & Security pages for:
  - plan structure
  - instance types
  - read scaling
  - snapshot retention
  - security/commercial differentiators

## When To Use

- The user asks about pricing, spend, invoices, budget caps, or plan fit.
- The user is comparing MotherDuck with another warehouse or lakehouse from a cost perspective.
- The user wants a pilot or rollout framed in ROI terms.

## Language Focus: TypeScript/Javascript and Python

- This skill is not primarily about code, but language choice still affects ROI.
- Prefer **TypeScript/Javascript** examples when the user is pricing:
  - product backends
  - customer-facing analytics apps
  - serverless or API-heavy workloads
- Prefer **Python** examples when the user is pricing:
  - data pipelines
  - notebooks
  - ETL workloads
  - analyst or data-science-heavy usage
- Connect cost to workload shape, not just to the programming language itself.

## TypeScript/Javascript Workload Profile Starter

```ts
type WorkloadProfile = {
  appSurface: "api" | "dashboard" | "pipeline" | "cfa";
  concurrency: number;
  dataVolumeGb: number;
  readHeavy: boolean;
};
```

## Python Workload Profile Starter

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
- optional read scaling replicas
- snapshot retention, query history, and plan-specific commercial features

Use the current pricing page for exact numbers. Do not hardcode numbers in a durable answer unless the user explicitly wants the current public list and you have verified it that turn.

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
  - loads, transforms, and routine engineering tasks
- Jumbo:
  - larger transformations, complex joins, heavier concurrent workloads
- Mega and Giga:
  - unusually heavy transformations or high-complexity workloads
- Read Scaling:
  - use for BI dashboards and read-only workloads with concurrency pressure

## Best Practice for Cost Attribution

Advise technical teams to tag workloads with `custom_user_agent` and roll up usage from `MD_INFORMATION_SCHEMA.QUERY_HISTORY` when available. This is the cleanest documented way to split spend by integration, pipeline, tenant, or team.

- `QUERY_HISTORY` is a plan- and role-sensitive feature; verify availability before promising it.

The point of the answer is not to memorize plan marketing. It is to map the user's workload to the right cost bucket.

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
- Do not promise a lower total cost than another system without workload evidence.
- Do not treat a pricing question as purely technical; many are really about predictability, procurement, or downside risk.

Do not make up pricing numbers, savings claims, or contract terms. If the exact commercial answer is unknown, say what needs confirmation from current pricing or sales.

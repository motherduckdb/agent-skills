<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Enable Self-Serve Analytics

Use this skill when a team wants broad internal access to analytics without turning every question into a central data-team ticket. This is a use-case skill focused on governed rollout, not just chart creation.

## Source Of Truth

- Prefer MotherDuck public docs and product pages for Dives, sharing, pricing, and read scaling.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first.
- When it is unavailable, use the public Dives, pricing, and Hypertenancy pages plus the docs site.

## Verified Delivery Defaults

The repeated repo runs point to a stable self-serve rollout posture:

- pick one audience first instead of launching broadly
- publish one governed dataset before expanding the surface area
- make the first asset a MotherDuck-native answer surface such as a Dive
- keep ownership, sharing, and editing boundaries explicit from the first rollout slice

## When To Use

- The user wants internal teams to explore data and answer their own questions.
- The user needs a rollout plan for Dives, dashboards, or shared analytical datasets.
- The user is trying to balance adoption with clear access boundaries.

## Language Focus: TypeScript/Javascript and Python

- Prefer **TypeScript/TSX** when the rollout artifact is a Dive, dashboard, or UI-facing analytics surface.
- Prefer **Python** when the rollout artifact is:
  - data curation
  - dataset publishing
  - metric validation
  - onboarding automation
- The usual split is:
  - Python for trusted dataset creation
  - TypeScript/TSX for the user-facing analytical surface

## TypeScript/TSX Starter

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";

export default function TeamKpiView() {
  const { data } = useSQLQuery(`
    SELECT team, COUNT(*) AS total_accounts
    FROM "analytics"."main"."customer_health"
    GROUP BY 1
    ORDER BY total_accounts DESC
  `);
  const rows = Array.isArray(data) ? data : [];
  return <pre>{JSON.stringify(rows, null, 2)}</pre>;
}
```

## Python Dataset Starter

```python
import duckdb

USE_CASE_USER_AGENT = "agent-skills/1.0.0(harness-codex;llm-gpt-5.4)"

conn = duckdb.connect(f"md:analytics?custom_user_agent={USE_CASE_USER_AGENT}")
conn.sql("""
CREATE OR REPLACE VIEW "analytics"."main"."customer_health" AS
SELECT team, account_id, status, arr
FROM "analytics"."main"."accounts"
WHERE status IS NOT NULL
""")
conn.close()
```

## Rollout Workflow

1. Pick the first team and first use case.
2. Prepare one clean analytical dataset.
3. Build one shareable Dive or dashboard around that dataset.
4. Define who can read, edit, and share.
5. Expand only after the first workflow is stable and understood.

## Public Product Anchors To Use

- Dives are interactive visualizations created on top of live MotherDuck queries.
- Dives persist in the MotherDuck workspace alongside SQL and data.
- MotherDuck positions Dives for the long tail of questions that do not justify a full dashboard, not as a replacement for every BI workflow.
- Dives are shareable and live.
- Read scaling is the official answer when dashboard or BI traffic becomes read-heavy and concurrent.
- Shares are zero-copy, read-only database-level distribution, so publish only curated databases rather than raw internal workspaces.

## What Good Self-Serve Looks Like

- one obvious entry point
- a small number of trusted datasets
- KPI definitions that are stable and documented
- default filters and views that match how the business works
- sharing patterns that do not expose more than intended

## What To Publish First

Start with one of these:

- one curated KPI dashboard in a Dive
- one trusted analytical view for a single department
- one share for a team that already knows how to query

Do not start by exposing raw tables across the whole organization.

## Recommended Sequence

### Step 1: Curate The Data

- use `explore` to discover source tables
- use `query` to confirm metrics and dimensions
- use `model-data` to publish a wide, analytics-ready table or view

### Step 2: Publish The First Asset

- use `create-dive` for the first interactive dashboard
- use `share-data` when a downstream team needs governed access to the data itself

### Step 2a: Choose Between Dives And Shares

- Use a Dive when:
  - the audience needs a ready-made answer surface
  - filters, drill-downs, and live refresh matter
  - the question is recurring but not important enough for a full BI program
- Use a share when:
  - the consuming team wants direct SQL access
  - the audience is another data team or power users
  - the output should be reusable in another tool or workflow

### Step 3: Expand With Guardrails

- define who owns metric changes
- avoid too many near-duplicate dashboards; flag similarities
- standardize filters, labels, and naming
- expand by use case, not by dumping every table on every team

## Scale Guidance

- If a self-serve rollout becomes read-heavy, add read scaling instead of over-provisioning a single path for everyone.
- If the rollout becomes customer-facing rather than internal, switch to `build-cfa-app` patterns instead of stretching a self-serve setup too far.
- If the organization wants a governed catalog of reusable visual assets, lean into Dives plus a small number of curated shares.
- If teams want direct SQL access, publish a clean share boundary and document ownership rather than pointing users at raw staging tables.

## What Not To Promise

- Do not imply Dives replace the team's existing BI tool for every use case.
- Do not imply broad self-serve succeeds without a curated semantic layer or trusted data model.

The output of this skill should be a rollout plan with a first asset, first audience, and clear guardrails.

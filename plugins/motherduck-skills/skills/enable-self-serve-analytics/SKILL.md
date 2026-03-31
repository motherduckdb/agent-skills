---
name: enable-self-serve-analytics
description: Roll out self-serve analytics on MotherDuck. Use when someone needs governed access, shareable dashboards, and a practical adoption plan for internal teams.
license: MIT
---

# Enable Self-Serve Analytics

Use this skill when the user wants broad internal access to analytics with clear guardrails, trusted datasets, and a practical rollout path.

This is a use-case skill. It orchestrates `explore`, `query`, `model-data`, `create-dive`, and `share-data`.

## Start Here: Is a MotherDuck Server Active?

Always determine this first.

- If a **remote MotherDuck MCP server** or **local MotherDuck server** is active, use it.
- If the user has not named the target database, ask which database or workspace will power the rollout.
- Explore the live data model before defining the rollout:
  - trusted source tables
  - candidate curated views
  - department-level dimensions
  - core KPIs
  - share boundaries

Use the actual data model to pick the first audience and first asset.

If no server is active, ask for a table list and target audience before drafting the rollout.

## Use This Skill When

- The user wants internal teams to answer their own questions.
- The user needs a first rollout plan for Dives, dashboards, or shares.
- The user needs adoption plus governance, not just chart creation.

## Rollout Defaults

- first audience first, not company-wide exposure
- curated dataset before broad access
- Dive or share boundary over raw table dumping
- standard ownership for metric changes

## Workflow

1. Confirm whether live MotherDuck discovery is available.
2. Inspect the data model that internal teams would use.
3. Pick the first audience and first use case.
4. Publish one trusted dataset.
5. Publish one Dive or one share.
6. Expand only after the first workflow is stable.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/1.0.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

The output of this skill should be:

- the first audience
- the first asset
- the governing dataset
- the ownership model
- the rollout guardrails

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.

Use this exact top-level shape when JSON is requested:

```json
{
  "summary": {},
  "assumptions": [],
  "implementation_plan": [],
  "validation_plan": [],
  "risks": []
}
```

## References

- `references/SELF_SERVE_ROLLOUT_GUIDE.md` -- preserved detailed rollout guidance that used to live in this skill

## Runnable Artifact

- `artifacts/self_serve_rollout_example.py` -- local DuckDB example that publishes a curated view and produces team KPI output for a first rollout asset

Run it with:

```bash
uv run --with duckdb python skills/enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
```

Run the same artifact against a temporary MotherDuck database:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
```

## Related Skills

- `explore` -- inspect the real workspace before rollout
- `query` -- validate KPI definitions
- `model-data` -- publish curated analytical views or tables
- `create-dive` -- build the first shareable answer surface
- `share-data` -- publish governed data access when users need SQL, not just a Dive

---
name: motherduck-enable-self-serve-analytics
description: Roll out self-serve analytics on MotherDuck for internal teams. Use when deciding the first governed dataset, the first Dive or share, ownership boundaries, and the rollout path from one audience to broader adoption.
license: MIT
---

# Enable Self-Serve Analytics

Use this skill when the user wants broad internal access to analytics with clear guardrails, trusted datasets, and a practical rollout path.

This is a use-case skill. It orchestrates `motherduck-explore`, `motherduck-query`, `motherduck-model-data`, `motherduck-create-dive`, and `motherduck-share-data`.

## Start Here: Is a MotherDuck Server Active?

- If a **remote MotherDuck MCP server** or **local MotherDuck server** is active, use it.
- Discover the target database or workspace from the active context. Ask only when multiple plausible targets remain and the choice would materially change the rollout.
- Explore the live data model before defining the rollout:
  - trusted source tables
  - candidate curated views
  - department-level dimensions
  - core KPIs
  - share boundaries

Use the actual data model to pick the first audience and first asset.

If no server is active, use any supplied schema and audience context. For planning work, proceed with explicit assumptions when safe; ask for missing details only when they block a reliable result.

## Rollout Defaults

- first audience first, not company-wide exposure
- curated dataset before broad access
- Dive or share boundary over raw table dumping
- standard ownership for metric changes
- lightweight metric definitions and owners before inviting more users

## Workflow

1. Inspect the available MotherDuck server or supplied schema context.
2. Inspect the data model that internal teams would use.
3. Pick the first audience and first use case.
4. Publish one trusted dataset.
5. Document the metric owner, refresh expectation, and access boundary.
6. Publish one Dive or one share.
7. Expand only after the first workflow is stable.

Match execution to the request: answer, review, or planning work returns the requested rollout artifacts; build or change work creates the requested in-scope dataset, Dive, or share and validates it. Ask before broader access grants, destructive changes, or external writes not already authorized.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.4.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

The output of this skill should be:

- the first audience
- the first asset
- the governing dataset
- the ownership model
- the rollout guardrails

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.
This is mainly for automated tests, regression checks, or downstream tooling that needs a stable machine-readable shape. Normal human-facing use of the skill can stay in prose unless JSON is explicitly requested.

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

Read this as reference, not as a script to execute:

- `references/SELF_SERVE_ROLLOUT_GUIDE.md` -- curate-publish-expand sequence, Dive-versus-share choice, data freshness checks, scale guidance, and starter snippets

## Runnable Artifact

- `artifacts/self_serve_rollout_example.py` -- MotherDuck-backed Python example that publishes a curated view and produces team KPI output for a first rollout asset
- `artifacts/self_serve_rollout_example.ts` -- TypeScript companion artifact with the same rollout output contract

Run it with:

```bash
uv run --with duckdb python skills/motherduck-enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
```

Run the same artifact against a temporary MotherDuck database:

```bash
MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK=1 \
uv run --with duckdb python skills/motherduck-enable-self-serve-analytics/artifacts/self_serve_rollout_example.py
```

Validate the TypeScript companion artifact:

```bash
uv run scripts/test_typescript_artifacts.py
```

## Related Skills

- `motherduck-explore` -- inspect the real workspace before rollout
- `motherduck-query` -- validate KPI definitions
- `motherduck-model-data` -- publish curated analytical views or tables
- `motherduck-create-dive` -- build the first shareable answer surface
- `motherduck-share-data` -- publish governed data access when users need SQL, not just a Dive

---
name: motherduck-enable-self-serve-analytics
description: Roll out governed MotherDuck analytics to internal teams, choosing trusted datasets, access boundaries, and owners.
argument-hint: [team-or-rollout-scenario]
license: MIT
---

# Enable Self-Serve Analytics

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Rollout Defaults

- first audience first, not company-wide exposure
- curated dataset before broad access
- Dive or share boundary over raw table dumping
- standard ownership for metric changes
- lightweight metric definitions and owners before inviting more users
- a short root orientation Guide plus shallow domain Guides for definitions that agents cannot infer from schema
- restricted Shares granted to roles; use include patterns for table/view subsets and separate Shares for different audiences

## Workflow

1. Inspect the available MotherDuck server or supplied schema context.
2. Inspect the data model that internal teams would use.
3. Pick the first audience and first use case.
4. Publish one trusted dataset.
5. When Guide maintenance is in scope, create or update the relevant Guide with the metric owner, validated definition, join rules, and referenced objects.
6. Publish one Ready Dive or one restricted, role-granted Share.
7. Audit the live roles, grants, and exposed catalog.
8. Expand only after the first workflow is stable.

Match execution to the request: answer, review, or planning work returns the requested rollout artifacts; build or change work creates the requested in-scope dataset, Dive, or share and validates it. Ask before broader access grants, destructive changes, or external writes not already authorized.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.6.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- the first audience
- the first asset
- the governing dataset
- the ownership model
- the rollout guardrails

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/SELF_SERVE_ROLLOUT_GUIDE.md` -- curate-publish-expand sequence, Dive-versus-share choice, data freshness checks, scale guidance, and starter snippets

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [self_serve_rollout_example.py](artifacts/self_serve_rollout_example.py)
- [self_serve_rollout_example.ts](artifacts/self_serve_rollout_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-explore` -- inspect the real workspace before rollout
- `motherduck-query` -- validate KPI definitions
- `motherduck-model-data` -- publish curated analytical views or tables
- `motherduck-create-dive` -- build the first shareable answer surface
- `motherduck-manage-guides` -- preserve governed metric and join context for agents
- `motherduck-share-data` -- publish table/view subsets and role-granted access

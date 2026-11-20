---
name: motherduck-build-dashboard
description: Build a MotherDuck dashboard as a Dive, choosing the analytical story, metrics, and section queries.
license: MIT
---

# Build an Analytics Dashboard

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Dashboard Defaults

- One story per dashboard.
- Start with a responsive KPI group, a primary chart, and supporting detail where it helps the decision. Add sections only when the question or data warrants them; these are defaults, not fixed chart quotas.
- Heavy shaping in SQL, not React.
- When the dashboard should trigger an action (approve, refresh, submit), add a write-back button that runs a Flight; see `motherduck-create-dive`.
- Viewers can ask follow-up questions through the Dive's AI Chat, so name sections and metrics in business terms.

## Workflow

1. Inspect the available MotherDuck server or supplied schema context.
2. Read relevant root/domain Guides, then explore the real schema and validate the governed metrics.
3. Pick the dashboard story.
4. Write one query per section.
5. For a new dashboard or layout change, use the design defaults and responsive references in `motherduck-create-dive`; preserve the existing design for a scoped SQL or text edit.
6. Compose the dashboard in a Dive. When MotherDuck MCP is available, call `get_dive_guide` before writing Dive code and before every `save_dive`, `update_dive`, or `edit_dive_content`.
7. When the request includes creating or updating the Dive, save only after responsive, theme, query-state, and data validation. Before `save_dive` or `update_dive`, follow the review step that `get_dive_guide` sets for your client: when it asks you to show the final source or preview and get the user's go-ahead, do that once, unless the user already said to save without review.
8. Read the saved Dive back. Leave work-in-progress as Draft; promote it to Ready only after the requested delivery is validated. Reuse Endorsed Dives before rebuilding an existing trusted answer.

Match execution to the request: answer, review, or planning work returns the requested dashboard artifacts; build or change work creates or updates the requested in-scope Dive and validates it. Ask before destructive replacement, unrelated external writes, or a material expansion of scope.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/3.0.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- the dashboard story
- the section list
- the validated SQL for each section
- the Dive implementation plan
- the save/update path

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/DASHBOARD_IMPLEMENTATION_GUIDE.md` -- section-to-SQL mapping, TSX composition, and validation examples
- `references/DASHBOARD_PATTERNS.md` -- example dashboard compositions and reusable sections

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [dashboard_story_example.py](artifacts/dashboard_story_example.py)
- [dashboard_story_example.ts](artifacts/dashboard_story_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-explore` -- inspect the actual database before deciding the dashboard sections
- `motherduck-query` -- validate each dashboard query
- `motherduck-create-dive` -- useSQLQuery, design defaults, responsive layout, theming, preview/save, and visual QA
- `motherduck-duckdb-sql` -- resolve syntax and function questions

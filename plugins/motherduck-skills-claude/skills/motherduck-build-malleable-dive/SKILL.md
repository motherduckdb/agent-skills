---
name: motherduck-build-malleable-dive
description: Build a generative MotherDuck Dive where a Flight writes a daily briefing and question-to-page specs from a semantic catalog, and viewers ask, investigate, and rearrange it.
argument-hint: [briefing-goal]
license: MIT
---

# Build a Malleable Dive

A malleable Dive is a page that is generated rather than hand-built. A Flight turns a question, an insight, or a fixed daily plan into a JSON spec. The Dive renders that spec with the `motherduck-dive-components` kit, and viewers rearrange it. Use this skill for a daily briefing with insights that drill down, or a Dive that answers new questions with new pages. For one fixed dashboard, use `motherduck-build-dashboard`.

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope databases or shares: grain, date range, categorical columns and their values, and how fresh each source is. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the recipe. If an existing Dive covers the domain, reuse its metric definitions so the numbers match what people already trust.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Interview First

Before writing a recipe, ask the owner who reads the briefing, what they decide, which numbers and targets matter, what explains a change, and which questions they expect to ask. `references/RECIPE_GUIDE.md` has the eight questions. Write the answers into a Guide (topic `briefings/<db>`), into the recipe, and into `questions.json`. When you can't wait for the answers, or the user asked for a plan, list the questions with the assumptions you would use, and continue with the full design. After the first briefing, ask which insight they would act on, which is noise, and what is missing.

## How It Works

The template is in `artifacts/`. A recipe holds everything domain-specific; the rest stays generic:

- `recipes/<name>/domain.py`: the sources to attach, the marts (curated tables), a catalog of datasets, dimensions and measures with descriptions, metrics to watch for change, the fixed daily plan, and context for the model.
- `recipes/<name>/app.json`: brand, theme (a kit theme key or a `makeTheme` brand), example questions, output database, Flight id.
- `python3 artifacts/build.py recipes/<name>` writes `flight/main.py` and `dive/index.tsx`. It inlines the planner rules from the kit's `components.json` and assembles the kit into the Dive. It finds the kit next to this skill, or through `--kit PATH`.

The Flight runs in four modes:

| Mode | What it does |
| --- | --- |
| `briefing` | Plans the page from the recipe's fixed plan. Runs on a schedule. |
| `feedback` | Records viewer events only. |
| `ask` | Plans a page that answers the viewer's question. |
| `investigate` | Plans a drill-down that explains an insight. Its `PARENT` is the page the insight came from. |
| `refresh` | Rebuilds the marts. |

Every mode runs the same steps:

1. **Marts:** build the curated tables. Only briefing and refresh rebuild marts that already exist.
2. **Plan:** `prompt()` returns a plan through a strict JSON schema whose enums are the catalog ids and the kit's component types.
3. **Compile:** Python validates the plan and compiles it to SQL with bound parameters.
4. **Changes:** a deterministic scan for weekly shifts in the watched metrics.
5. **Probe:** `prompt()` proposes up to three follow-up queries that test why something moved. They're catalog ids too, so Python writes the SQL.
6. **Narrate:** `prompt()` writes the headline, insights, captions, a "so what" line per block, and annotations.
   - It reads the follow-up results, the recipe's Guides, the last briefings' insights and viewer ratings.
   - It marks each insight new, ongoing, worsening, improving or resolved.
   - Every number is checked against the data, and if too many don't match, the narrator retries once.
7. **Publish:** one spec row in `<db>.main.dive_specs`. The run, its model calls, its insights and any viewer feedback go to the log tables. After a briefing, the Flight updates a memory Guide.

The Dive learns from use:
- Viewer ratings and chart-type switches reach the Flight with the next run, because a Dive can't write.
- The chart types viewers keep choosing become the defaults.
- A Memory page shows the insight timeline, questions, viewer actions and prompt versions.

`references/LEARNING_LOOP.md` covers the tables, Guides, feedback and `eval.py`.

The Dive reads only that table. It starts the Flight with `useRunFlight` and follows it with `useFlightRun`.

## Workflow

1. Explore the data and write the recipe. Copy `artifacts/recipes/nyc-311` (public `sample_data`), then follow `references/RECIPE_GUIDE.md`.
2. Build, then run the Flight locally with `MODE=briefing`. Check the spec against the guide's checklist. Ask 3 questions, including one off-topic, and investigate one insight. Run `python3 artifacts/eval.py recipes/<name>` and keep the `--out` file as the baseline. Run 3 briefings with consecutive `AS_OF` dates, and check that insights continue rather than repeat.
3. When MotherDuck MCP is available, call `get_flight_guide` before `create_flight`, `update_flight`, or `edit_flight_source`. Push the Flight with `motherduck-cli`: a daily schedule, a 600-second max runtime, and every config key the Dive sends (`MODE`, `PROMPT`, `REQUEST_ID`, `PARENT`, `AS_OF`, `MODEL`, `FEEDBACK`). Run it once in the cloud and read the logs.
4. Put the Flight id in `app.json`, rebuild, and preview with `motherduck dive watch recipes/<name>/dive`. Test the briefing, one question, one Investigate click and Arrange mode.
5. When MotherDuck MCP is available, call `get_dive_guide` before writing Dive code and before every `save_dive`, `update_dive`, or `edit_dive_content`. Before `save_dive` or `update_dive`, follow the review step that `get_dive_guide` sets for your client: when it asks you to show the final source or preview and get the user's go-ahead, do that once, unless the user already said to save without review.

The work is done when:
- the briefing, a question and an investigation each render in the preview with no compile or query errors;
- the eval baseline exists;
- the page's number check passes;
- at least one headline number matches a hand-written query.

To let others use the Dive, they need a share of the output database and `run` on the Flight. The owner grants `run` (`grant_access` over MCP, or `GRANT RUN ON FLIGHT '<flight_id>' TO ROLE <role>`). Recommend the grantees and grant only after the user confirms; a request to share a Dive is not that confirmation.

For answer, review, or planning requests, stop at the requested recipe, plan, or design. For build requests, carry the in-scope work through the local run and preview. Ask before destructive replacement or a broader rollout.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/3.0.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`. The template engine reads them from `MOTHERDUCK_AGENT_HARNESS` and `MOTHERDUCK_AGENT_LLM`.

## Rules That Keep It Safe

- The model names only catalog ids and component types; Python writes all SQL, with filter values as bound parameters. Never let a model write SQL that the Flight or the Dive runs.
- Every run uses the Flight owner's token. The engine validates each config value a caller can pass: the mode, id formats, a 600-character prompt cap, and ISO dates.
- Highlights, annotations, and marker series survive only if they exist in the block's data.
- The Dive never runs SQL from a spec; the Source panel's SQL is display text.
- Viewer feedback reaches the database only through the Flight, which validates every event.
- The viewer's layout lives in `useDiveState('layout')` per page and overrides the generated layout. The open page's question and headline go to `useDiveState('context')`, which the Dive's AI Chat reads.

## Output

For a full engagement, cover the recipe (sources, marts, catalog, daily plan), the validated headline numbers, the Flight and Dive ids and URLs, and the grants the user still has to confirm. For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output).

## References

- `references/RECIPE_GUIDE.md` -- writing `domain.py` and `app.json`, catalog descriptions, the spec checklist, custom components
- `references/SPEC_CONTRACT.md` -- the spec the Flight writes and the Dive renders
- `references/LEARNING_LOOP.md` -- log tables, memory, Guides, viewer feedback, the analyst step, the number check, `eval.py`
- `references/EXECUTION_REFERENCE.md` -- local runs, evals, deploy commands, structured output

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-dive-components` for the component kit, themes, brand themes, and custom components
- `motherduck-create-flight` for Flight scheduling, secrets, run grants, and the Flight Explainer
- `motherduck-create-dive` for the Dive runtime contract, saving, sharing, and embedding
- `motherduck-explore` and `motherduck-query` for the data behind the catalog
- `motherduck-cli` for `flight push`, `dive watch`, and `dive push`

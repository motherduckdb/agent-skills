# September 2026 skill refresh

## Scope and rationale

Reviewed all 22 skill entrypoints and their discovery, reference, and packaging surfaces. The refresh follows the supplied article, the installed skill-creator guidance, [OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills), and [GPT-6 Astra prompting guidance](https://developers.openai.com/api/docs/guides/latest-model), checked September 5, 2026.

The changes reduce discovery cost and unnecessary workflow requirements while preserving MotherDuck-specific contracts. Shared skills remain model-neutral. This is an instruction-quality refresh, not a new certification of every product claim in every reference.

## Changes

All descriptions now identify a narrower capability rather than listing every related keyword. Description text fell from 6,544 to 2,368 characters (64%); the longest is 121 characters. Across the 22 entrypoints, whitespace-delimited words fell from 13,512 to 11,441 (15%). These are text-size measurements, not a claim about model speed or accuracy.

| Skill | Review outcome |
| --- | --- |
| connect | Reuse the project runtime and compatible pins; move installation detail to the runtime reference; remove mandatory runtime ranking. |
| cli | Shorter terminal-specific trigger; retain authentication, output contracts, and remote-state verification. |
| explore | Start from the known object; profile only when statistics matter rather than scanning broadly. |
| query | Narrow analytical trigger; preserve grain and joins; make plan inspection conditional on performance needs. |
| duckdb-sql | Distinguish syntax/support lookup from live query execution; retain dialect and compatibility constraints. |
| rest-api | Short control-plane trigger; retain admin token scope, read-before-write, and deletion boundaries. |
| load-data | Stop after validating a requested load; modeling is a separate scope decision. |
| model-data | Preserve existing framework conventions; a single-table change or explanation does not create a scaffold. |
| manage-guides | Preserve Guide scope and versions; honor already-authorized organization publication. |
| share-data | Replace mandatory sibling-skill prerequisites with actual required context; retain audience and consumer validation. |
| create-dive | Remove catchall visualization trigger; preserve the current design during scoped edits and follow the requested delivery mode. |
| create-flight | Templates are optional starting points; preserve existing schedules during unrelated edits. |
| design-dive | Full design system and evidence handoff apply to new designs or broad redesigns; scoped edits get affected-state checks. |
| ducklake | Narrow storage trigger; retain native-storage default and supported-mode distinctions. |
| security-governance | Narrow control-assessment trigger; retain current-source and documented-guarantee boundaries. |
| pricing-roi | Keep estimates workload-based; a narrow rate lookup does not require a full ROI analysis. |
| build-cfa-app | Shorten discovery; preserve tenant/backend boundaries; move example commands and JSON contract to a conditional reference. |
| build-dashboard | Make chart counts defaults; preserve design for SQL/text edits; move example and JSON details. |
| build-data-pipeline | Shorten discovery; make Guide maintenance conditional; preserve project commands and gotchas in the execution reference. |
| migrate-to-motherduck | Shorten discovery; retain validation and cutover boundaries; move example and JSON details. |
| enable-self-serve-analytics | Shorten discovery; retain staged access rollout; remove duplicate related-skill routing. |
| partner-delivery | Shorten discovery; retain per-client isolation and exceptions; move example and JSON details. |

The six use-case skills each include `references/EXECUTION_REFERENCE.md`. Runnable examples and the explicit JSON shape are preserved. Repository-only test commands are identified as such so installed plugin users are not sent looking for an absent root `scripts/` directory.

README, Claude, Gemini, harness docs, and Gemini routing commands now start with the matching capability instead of requiring connect, explore, and query for every task. The validator no longer enforces that obsolete prose sequence; catalog, dependency, resource, and packaging checks remain in place. Authoring guidance explains conditional references, proportional validation, and preservation of user scope and authorization.

## Verification

- Catalog validator: 22 skills passed, including description equality, graph direction, references, and packaging wiring.
- Claude marketplace and packaged plugin validation passed; Claude and Codex sync checks each verified 96 files.
- Snippets: 1,061 validated, 99 skipped by the existing harness; all validated snippets passed.
- TypeScript: all six companion artifacts passed.
- MotherDuck: all six live artifacts passed; the dlt/dbt reference pipeline completed with 13 successful model/test steps, final data validation, and temporary database cleanup.
- Gemini archive built successfully; its six execution references match source and its manifest is at the archive root.
- Astra use-case contract tests: all six passed using `gpt-6-astra`, each returning raw JSON with the five required keys. Runs took 148–201 seconds each. Inspected completed outputs for live-data grounding, declared assumptions, and a clear distinction between verified reads and proposed mutations; these checks do not prove every future task will behave correctly.
- The first model-test attempt used the older PATH CLI (0.149.1), which rejected `gpt-6-astra`; the successful run used the already-installed app CLI (0.153.4) through a command-local PATH override. No global CLI installation or user configuration was changed.

No version bump or release is part of this refresh. The pre-existing untracked `output/` directory was left untouched.

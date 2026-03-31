# MotherDuck Skills -- Agent Guide

This repo publishes public MotherDuck skills for AI coding agents.

Optimize for:

- clear, opinionated MotherDuck guidance
- low-drift docs and manifests
- runnable examples that reflect real MotherDuck behavior
- small, mechanical changes over broad prose rewrites

## Repo Shape

The catalog is a 3-layer graph:

- `utility`: `connect`, `query`, `explore`, `duckdb-sql`
- `workflow`: `load-data`, `model-data`, `share-data`, `create-dive`, `ducklake`, `security-governance`, `pricing-roi`
- `use-case`: `build-cfa-app`, `build-dashboard`, `build-data-pipeline`, `migrate-to-motherduck`, `enable-self-serve-analytics`, `partner-delivery`

Primary source-of-truth files:

- `skills/*/SKILL.md`: actual skill content and frontmatter
- `skills/catalog.json`: machine-readable skill index and source-doc map
- `README.md`: public catalog and install docs
- `ARCHITECTURE.md`: invariants and dependency rules
- `docs/skill-authoring.md`: repo-specific authoring guidance
- `docs/skills-sync.md`: docs-to-skills drift workflow
- `CLAUDE.md`: Claude-facing catalog/context
- `.claude-plugin/plugin.json`: Claude plugin manifest
- `.codex-plugin/plugin.json`: Codex plugin manifest
- `.agents/plugins/marketplace.json`: repo-local Codex marketplace wiring

Important supporting surfaces:

- `skills/*/references/`: preserved deep guidance and fuller runnable reference projects
- `skills/*/artifacts/`: small runnable examples, now expected to support local-first and MotherDuck-backed validation where appropriate
- `scripts/test_motherduck_artifacts.py`: end-to-end MotherDuck-backed artifact test runner
- `scripts/test_codex_use_cases.py`: strict Codex use-case output and structure runner

## Non-Negotiable Content Rules

- Always write DuckDB SQL, not PostgreSQL SQL.
- Prefer fully qualified table names: `"database"."schema"."table"`.
- Never hardcode tokens; use `MOTHERDUCK_TOKEN` or the documented read-scaling variants.
- Never imply runtime extension installation is generally available.
- Treat DuckLake as opt-in, not the default storage posture.
- Keep related-skill guidance in prose sections like `Related Skills`; do not invent repo-specific frontmatter fields for it.

## Product Defaults to Preserve

- Lead with the Postgres endpoint for thin-client and PostgreSQL-driver interoperability.
- Keep native DuckDB APIs in the guidance when local files, hybrid execution, or direct DuckDB control matter.
- Prefer MCP-assisted exploration when MotherDuck MCP is available.
- For use-case skills, if a remote or local MotherDuck server is active, start from the user's real database/schema instead of inventing one.
- Prefer a native `md:` workspace connection for multi-database exploration, bootstrap flows, and temporary validation environments.
- Call `get_dive_guide` before save/update Dive flows when MCP is available.
- Prefer Parquet over CSV when the format is under our control.
- Prefer structural isolation over query-time tenant filtering for serious customer-facing analytics.

## Editing Rules

- Keep changes targeted. This repo is mostly documentation and manifests; broad rewrites create drift.
- When updating one catalog surface, check the others in the same pass.
- Prefer deduplicating repeated guidance by pointing to the owning skill instead of copying blocks between skills.
- If you shrink a skill, move preserved detail into `references/`; do not silently delete useful content.
- If a change affects real MotherDuck behavior, update the runnable artifact or reference project, not just the prose.
- Do not point shipped skill content at `motherduck-examples`; it is a maintainer-only comparison input, not a plugin/runtime dependency.
- In use-case skills, structured JSON output is only for explicit test/tooling flows. Normal human-facing use can stay in prose unless JSON is explicitly requested.
- `Validation Signals` sections in references are for testing, review, and regression checks; they should not be treated as a required heading in normal user-facing replies.
- Preserve the layer graph:
  - utility skills cannot depend on other skills
  - workflow skills can depend only on utility skills
  - use-case skills can depend only on utility and workflow skills

## Required Checks

Run these when changing skills, catalogs, or manifests:

```bash
uv run scripts/validate_skills.py
```

Run this when editing markdown examples or code fences:

```bash
uv run --with duckdb --with pyyaml python tests/validate_snippets.py
```

Run this when changing artifact behavior, reference projects, or any guidance that claims to be validated against real MotherDuck:

```bash
uv run scripts/test_motherduck_artifacts.py
```

Run this when changing use-case skill output contracts or use-case reference guidance:

```bash
uv run scripts/test_codex_use_cases.py
```

## Common Drift Traps

- `README.md`, `CLAUDE.md`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `.agents/plugins/marketplace.json` falling out of sync with `skills/`
- `skills/catalog.json` no longer matching the actual `references/` and `artifacts/` paths
- `build-dashboard` reintroducing duplicated `create-dive` mechanics
- accidental PostgreSQL-specific claims in SQL examples
- artifacts drifting into local-only behavior when the repo now claims MotherDuck-backed validation
- shipped references accidentally telling plugin users to consult `motherduck-examples`
- use-case skills drifting away from the strict raw-JSON contract used by the Codex test harness
- overcommitting to a single connection path when the guidance should stay scenario-based

## When Unsure

- Check `README.md` for the public story.
- Check `ARCHITECTURE.md` for repo invariants.
- Prefer the simpler, more maintainable wording.
- If two skills overlap, keep the shared mechanics in the lower-level skill and let the higher-level skill focus on orchestration.

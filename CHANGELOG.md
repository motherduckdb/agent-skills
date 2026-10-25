# Changelog

Customer-facing release notes for MotherDuck Skills. Each section becomes the GitHub release notes for its tag, and editing a published section updates that release when the change merges to `main`.

## 3.0.0

### Highlights

- **Access control, end to end.** Agents can now design and review who reads and writes what in MotherDuck: roles, share grants, table-level security, row-level security, column-level security, and masking. Seven ready-made setups cover a first warehouse, separate dev and prod, a curated BI reader, team roles, row and column rules for internal teams, per-customer isolation for customer-facing apps, and agencies serving several clients, each with its Terraform shape.
- **Dives that are complete on the first save.** New Dives start from a template that resizes from phone width to wide panes, supports light and dark themes, keeps filters when a link is shared, shows loading, empty, and error states per section, shows data freshness, exports to CSV, and can include a button that runs a Flight.
- **Watchable Flights by default.** Every new Flight is instrumented for the Flight Explainer, so each run shows its steps, row counts, timing, and the step that failed.
- **Agents pick the right skill more often.** Rewritten skill descriptions and removed contradictions raised correct skill selection in our evals from 70% to 93% of runs, and fully passing tasks from 55% to 85%.

### Added

- Guidance for the September and October 2026 MotherDuck launches:
  - secure views on shares (row-level security, column-level security, masking)
  - Dive write-back through Flights, and `GRANT RUN ON FLIGHT`
  - Flight sizes F4, F16, and F32
  - the Flight Explainer
  - AI SQL functions (`prompt_jev()` for classification and image detection, `prompt()` with reasoning models, `embedding()`)
  - `connection_timeout` for services that should fail fast
  - Guides managed as files with `motherduck guide`
  - the Admin API user listing (`GET /v1/users`)
  - the official Terraform provider
  - Agent Chat in Dives
  - AWS Marketplace purchasing
  - cross-region DuckLake buckets
- MotherDuck MCP server setup for Claude Code, Claude, Cursor, VS Code with GitHub Copilot, Gemini CLI, ChatGPT, Codex, and Copilot Studio.
- A query performance guide: reading `EXPLAIN ANALYZE`, using query history to find waiting, spilling, or data-transfer problems, and when a larger Duckling is the right fix.
- Coverage for MotherDuck MCP tools that were missing:
  - Flight run grants and the Flight Explainer views
  - focused Dive edits and one-step Dive data sharing
  - Guide visibility
  - macros
  - short-lived tokens
- Exports from Dives, and Guides that document the tables your Flights create.

### Changed

- **Breaking:** `motherduck-design-dive` is now part of `motherduck-create-dive`. One skill covers building, designing, theming, and publishing Dives.
- Dive guidance now follows MotherDuck's live Dive runtime guide instead of repeating it. Designs use the MotherDuck palette and runtime-supported styling, and agents follow the runtime's review step before saving a Dive.
- Customer-facing app guidance now defaults to a database, a reader service account, and a restricted share per tenant, with read-scaling tokens kept in the backend.
- Flight run grants and organization-wide Guides are recommended to you, then applied only after you confirm.
- Read scaling uses `session_name` (the older `session_hint` still works but is deprecated).
- The Gemini `/motherduck:route` command now names the skill to start with instead of a fixed sequence.

### Fixed

- Flight creation used outdated MCP parameter names (`md_token_name`, `md_secret_names`); it now uses `access_token_name` and `flight_secret_names`.
- Rules that disagreed between skills are now worded the same everywhere:
  - when to fully qualify table names
  - when to load the Dive guide
  - when to load Guides before a query
- Older text claimed shares could not enforce row or column rules, and that Flight run limits were undocumented. Both are corrected.
- Agents no longer try to call admin MCP tools that the hosted MotherDuck server does not provide.
- Secure views are always written with explicit column lists, so a new source column never leaks to consumers.
- Pipelines no longer fall back to row-by-row inserts.

### Upgrade notes

- Replace any use of `/motherduck-design-dive` with `/motherduck-create-dive`.
- Reinstall or update the plugin or extension in your agent to pick up the new skills.
- If your code passes `session_hint` in a MotherDuck connection string, switch it to `session_name`.

## 2.6.0

### Highlights

- Two new skills: `motherduck-cli` for working with MotherDuck from a terminal and local files, and `motherduck-manage-guides` for the business definitions and conventions agents should follow.
- Faster, more focused skill loading: skill descriptions are about two thirds shorter, and long examples load only when a task needs them.

### Added

- `motherduck-cli` and `motherduck-manage-guides`, bringing the catalog to 22 skills.
- More guidance for shares granted to roles, table-level filtering, the Dive lifecycle and embedding, and Flight configuration and runs.

### Changed

- Agents reuse an existing connection and schema context instead of rediscovering it, keep your existing design during small edits, and scale validation to the size of the change.
- The README has one installation section and one complete skill list.

### Fixed

- Installation now uses `npx -y skills` with no global installer, and states the Node.js 22.20+ requirement for that route.

## 2.5.0

### Highlights

- A dedicated Dive design workflow: mobile-first layouts, light and dark themes, room for filters, reusable layouts across customers, and a restrained business-analytics style.
- A repeatable review loop with screenshots at phone and desktop sizes before a Dive is handed off.

### Added

- `motherduck-design-dive`, with a responsive design system and a visual review playbook (merged into `motherduck-create-dive` in 3.0.0).

### Changed

- Dashboard and Dive creation guidance routes design work through the new workflow, with modernized responsive examples.

### Fixed

- Live MotherDuck examples pin a supported DuckDB version, so validation never picks an unsupported client.

## 2.4.0

### Highlights

- A leaner skill catalog that tells agents what to discover first and where they need your permission before acting.
- Guidance for administering service accounts, tokens, Ducklings, and embedded Dive sessions through the MotherDuck MCP server.

### Added

- MCP-first administration guidance in `motherduck-rest-api`.

### Changed

- Removed repeated instructions and claims likely to go stale (plan names, versions, browser sizes, runtime limits); agents check live sources instead.

### Fixed

- Pipeline validation queries in the dlt and dbt reference project use fully qualified table names.

## 2.3.0

### Changed

- References to the MotherDuck examples repository now point to the MotherDuck Cookbook.

## 2.2.2

### Fixed

- Security update for the dlt and dbt reference project: updated GitPython, urllib3, and idna to resolve all open Dependabot alerts. The project's direct dependencies are unchanged.

## 2.2.1

### Added

- `motherduck-create-flight`: create, schedule, run, and debug MotherDuck Flights (Python jobs on MotherDuck compute), with ready-to-deploy templates for dlt ingestion, a Postgres mirror, and a scheduled S3 partition refresh.

### Changed

- The README leads with installation and shows the latest release.

## 2.2.0

### Highlights

- First tagged release of MotherDuck Skills, packaged for Claude Code, Codex, Cursor, GitHub Copilot, and Gemini CLI.

### Added

- A three-layer catalog: utility skills (connect, explore, query, DuckDB SQL), workflow skills (load, model, share, Dives, DuckLake, security, pricing), and use-case skills (customer-facing apps, dashboards, data pipelines, migrations, self-serve analytics, partner delivery).
- REST API administration for service accounts, tokens, and Duckling configuration.
- Guidance on choosing a DuckDB runtime when connecting, and a file-based project scaffold for data modeling.

---
name: motherduck-create-dive
description: Create, edit, publish, share, or embed MotherDuck Dives using their React and SQL runtime.
argument-hint: [dive-goal]
license: MIT
---

# Create and Manage MotherDuck Dives

## Source Of Truth

- Prefer current MotherDuck Dive docs first.
- **Non-negotiable ordering:** when MotherDuck MCP is available, call `get_dive_guide` before generating Dive code and always before `save_dive` or `update_dive`. The guide defines the current component API and runtime libraries.
- `get_dive_guide` also surfaces relevant conventions from the reserved `dives` Guide topic. Apply those conventions when they do not conflict with the user's explicit requirements.
- Use the blessed Dives example repo as the reference implementation for local preview, Dives-as-code layout, metadata, CI previews, and deploy scripts.
- Use Dives SQL functions when the user wants a scriptable SQL-native create/read/update/delete workflow instead of MCP tools.
- Treat ordinary Dives and embedded Dives separately. Verify current plan entitlements before promising an embed rollout; do not preserve plan names or availability claims from memory.

## Default Posture

- First classify the job: new Dive, existing Dive edit, Dives-as-code workflow, team sharing, or embedding.
- Validate the underlying SQL and schema first with `motherduck-explore` and `motherduck-query`; a good Dive starts with a correct query.
- Keep Dive queries fully qualified and SQL-heavy; let React handle presentation, not data reshaping.
- Treat the component contract as React + `useSQLQuery`, a default export, supported runtime libraries, explicit loading/empty/error states, and no browser-side secrets.
- New Dives start as Draft. Promote a validated Dive to Ready only when the requested delivery includes publication. Only an admin can mark a Dive Endorsed; never self-endorse an agent-created Dive.
- When reusing existing work, prefer Endorsed and then Ready Dives. Archived Dives are retired and excluded from default agent listings unless explicitly requested.
- When local preview uses `REQUIRED_DATABASES`, keep the export on one line and mirror the real share dependencies in metadata or save/update inputs. Avoid aliases that collide with existing database names.
- Preserve an existing Dive’s visual system for scoped edits. For a new Dive, choose a concrete theme direction that fits its audience.
- Prefer one query per visual section or interaction surface rather than one giant cross-purpose query.
- Preview locally before saving when the environment supports it.
- For existing Dives, read the current content and version metadata before overwriting anything. MCP `list_dives` returns `current_version`, and `read_dive` can fetch historical versions.
- Treat embedded Dives as the first-choice path when a product needs a live read-only Dive surface with a backend-created embed session. Move to `motherduck-build-cfa-app` when the app needs custom API contracts, writes, non-Dive routing, tenant policy enforcement, or richer authorization.
- For shared repos or CI/CD, use a service-account token so Dive ownership is not tied to one human user.

## Workflow

1. Choose the requested delivery path: workspace Dive, existing edit, Dives-as-code, sharing, or embedding. Follow only that path; a chart request does not itself authorize sharing or embedding.
2. Explore the live schema and validate the core SQL first.
3. Call `get_dive_guide` if MCP is available, then design the story, sections, interactions, and theme.
4. Build or edit the Dive component, using local preview/hot reload when possible.
5. Call `save_dive`, `update_dive`, or deploy only after queries, loading states, required resources, and visual behavior are correct.
6. Read the resulting URL, version, and status back. If the requested delivery includes publication, promote a validated Draft to Ready through the write-capable path.
7. If teammates or application users need access, configure the underlying shares or embed-session flow explicitly.

For answer, review, or planning requests, stop at the requested design or code artifact. For create, update, or deploy requests, carry the requested in-scope operation through preview and validation; ask before destructive replacement or a broader external rollout that the request did not authorize.

## References

Read only the reference sections needed for the current task.

- Read `references/DIVE_DESIGN_GUIDE.md` for authoring workflows, `useSQLQuery` mechanics, Dives-as-code, editing/version history, sharing, embedding, SQL functions, theming prompts, chart-selection rules, loading/error states, layout patterns, and implementation gotchas

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-explore` for discovering the real tables, views, and dimensions before visualizing them
- `motherduck-query` for validating the SQL each Dive section will run
- `motherduck-design-dive` for mobile-first layout, light/dark themes, filter surfaces, reusable components, and responsive QA
- `motherduck-build-dashboard` when the work is really a multi-section dashboard composition problem
- `motherduck-build-cfa-app` when the requirement is a fuller product surface with per-customer isolation or backend policy control
- `motherduck-cli` when the agent has a shell and should keep Dive source in local files
- `motherduck-manage-guides` for reusable personal or organization Dive conventions

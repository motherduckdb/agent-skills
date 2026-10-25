# Dive Design Guide

Reference for creating, editing, managing, sharing, embedding, and polishing MotherDuck Dives. Use this for the practical mechanics after `motherduck-create-dive` has selected the right workflow.

## Contents

| Section | Covers |
|---|---|
| 1. What a Dive Is | When a Dive fits and when it does not |
| 2. Workflow Selection | Choosing workspace, edit, code, or embed paths |
| 3. Authoring Workflow | End-to-end build steps, `get_dive_guide` ordering |
| 4. Component Contract | Required component shape and runtime libraries |
| 5. Required Resources and Shared Data | `REQUIRED_DATABASES`, metadata, share aliases |
| 6. Editing Existing Dives | MCP and SQL-function edit/version paths |
| 7. Dives as Code | Git repo layout, preview, CI/CD deploy |
| 8. Embedding Dives | Embed sessions, iframe, CSP, server vs dual mode |
| Dive Status Lifecycle | Draft, Ready, Endorsed, Archived trust signals |
| Write-Back with Flights | `useRunFlight`, `useFlightRun`, grants, freshness after a run |
| Exporting Query Results | `exportAs`, `useExport`, formats |
| Agent Chat on Dives | What the in-Dive assistant sees and can change |
| Embedded State and Events | Initial state, state updates, navigation, exports |
| Runtime Guide, Design, and Starter | What `get_dive_guide` owns and the feature-complete defaults this skill adds |
| Common Failure Modes | What breaks Dives in practice |

---

## 1. What a Dive Is

A Dive is a live React component saved in MotherDuck. It queries MotherDuck with `useSQLQuery`, renders interactive UI with normal React, and persists as a workspace artifact with version history.

Use a Dive when the user needs:

- a persistent answer that stays live over MotherDuck data
- an interactive internal data app or dashboard
- a shareable workspace artifact that can be iterated on conversationally
- an embeddable read-only analytics surface inside another app
- a version-controlled React + SQL artifact managed by Git

Do not force a Dive when the user only needs one ad hoc SQL answer, a static export, or a full application with custom backend policy, writes, and non-Dive routes.

## 2. Workflow Selection

Choose the path before writing code:

| User goal | Recommended workflow |
|---|---|
| Quick persistent visualization | MCP-first workspace Dive: explore, generate, preview, save |
| Edit a saved Dive | Read the Dive, inspect current version, edit locally or through MCP, update content |
| Team-maintained Dive | Dives-as-code repo with local preview and PR previews |
| Customer-facing read-only view | Embedded Dive with backend-created embed session |
| Full product analytics app | Escalate to `motherduck-build-cfa-app` |

Always start from live schema exploration when MCP or another MotherDuck connection is available. If the user gives a table or schema excerpt instead, state the assumptions and keep table names easy to replace.

## 3. Authoring Workflow

1. Explore databases, tables, columns, and representative rows.
2. Validate the core SQL outside the Dive first.
3. Call `get_dive_guide` when MCP is available so the current component API and runtime libraries are in scope. Never call `save_dive` or `update_dive` without having called `get_dive_guide` first in the session.
4. Design the data story: primary question, sections, filters, and interaction model.
5. Build a React component with `useSQLQuery`, a default export, safe value conversion, and per-query loading/empty/error states.
6. Preview locally when possible.
7. Call `save_dive` or `update_dive` only after the queries and UI behavior are correct.
8. Read the saved version and status back. New Dives are Draft; promote to Ready only after validation and only when publication is requested.
9. Share data or configure embed sessions only after the saved Dive works.

Prefer incremental edits. A saved Dive can be updated in place, and every content update creates a version.

## 4. Component Contract

`get_dive_guide` defines the contract: a default-exported function component, the allowed imports, `useSQLQuery` and its result shape, value conversion, and loading and error handling. Read it before writing code; it changes with the runtime. For a complete component that applies it, start from `artifacts/feature_complete_dive.tsx` (see "Runtime Guide, Design, and Starter"). Keep aggregation and shaping in SQL and React state for presentation, filters, and interaction.

## 5. Required Resources and Shared Data

Dives can query private databases, shared databases, or org-shared data. If teammates need to view the Dive, the underlying data must be accessible to them.

When a Dive uses a shared database in local preview or code-managed deployment:

- declare the dependency explicitly
- keep local aliases stable
- avoid aliases that collide with the user's existing database names
- prefer aliases with a `_share` suffix when collision risk is unclear
- keep `REQUIRED_DATABASES` on one line in blessed-dives-style repos because the deploy script strips it with a regex
- mirror the actual server-side dependencies in `dive_metadata.json.requiredResources` or the `required_resources` parameter used by SQL functions

Example local-preview export:

```tsx
export const REQUIRED_DATABASES = [{ type: "share", path: "md:_share/eastlake/06fa503c-07d5-4097-b272-58f0cc0f1fdf", alias: "eastlake_share" }];
```

Example metadata:

```json
{
  "id": "",
  "title": "Sales Overview",
  "description": "Sales KPIs and trends",
  "requiredResources": [
    { "url": "md:_share/eastlake/06fa503c-07d5-4097-b272-58f0cc0f1fdf", "alias": "eastlake_share" }
  ]
}
```

A `database` dependency on a personal database works only for its owner; sharing the Dive does not grant access to that database. Before declaring one, check `MD_INFORMATION_SCHEMA.OWNED_SHARES` and prefer an existing, unambiguous share (ask if several exist). Create a share only when the user asks to share the Dive's data, then swap the `database` entry for a `share` entry and keep the alias so SQL does not change. Over MCP, `share_dive_data(diveId)` does this for org-wide access in one call: it creates org-scoped shares for the owned databases the Dive uses and updates the Dive. Use `motherduck-share-data` when the audience should be narrower than the organization.

## 6. Editing Existing Dives

Before editing an existing Dive:

- identify the Dive by ID or exact title
- list Dives to confirm `current_version`
- read the latest content before changing it
- inspect an older version if the user is asking to restore or compare behavior
- preserve the title unless the user explicitly wants a rename
- update metadata separately from content when only title or description changes

MCP path:

1. `list_dives` to find the Dive and current version.
2. `read_dive` for the latest content, or `read_dive(version = N)` for a historical version.
3. Edit and preview the component.
4. Apply focused changes with `edit_dive_content` (a list of exact `old_string`/`new_string` replacements; no prior read needed) or a full rewrite with `update_dive`, following the review step `get_dive_guide` sets for your client.

SQL path:

- `MD_LIST_DIVES()` lists Dives.
- `MD_GET_DIVE(id)` retrieves current source.
- `MD_UPDATE_DIVE_METADATA(...)` changes title/description without creating a content version.
- `MD_UPDATE_DIVE_CONTENT(...)` pushes new component content and creates a new version.
- `MD_LIST_DIVE_VERSIONS(...)` and `MD_GET_DIVE_VERSION(...)` support version inspection.
- `MD_DELETE_DIVE(...)` is destructive; confirm before using it.

## 7. Dives as Code

Use a Git-backed workflow when the Dive is part of a product, shared team surface, or reviewable analytical artifact. The blessed Dives example repo is the reference pattern.

Recommended repo layout:

```text
dives/
  my-dive/
    my-dive.tsx
    dive_metadata.json
.dive-preview/
  src/dive.tsx
scripts/deploy-dive.sh
.github/workflows/deploy_dives.yaml
.github/workflows/cleanup_preview_dives.yaml
```

Workflow:

1. Fork or create the repo.
2. Add a MotherDuck token for local preview in `.dive-preview/.env`; never commit it.
3. Use a service-account read/write token as the GitHub secret `MOTHERDUCK_TOKEN` for shared CI/CD ownership.
4. Put each Dive in `dives/<name>/<name>.tsx` with `dive_metadata.json`.
5. Register each Dive folder in the deploy workflow path filters.
6. Preview locally with the Vite scaffold.
7. On PR, deploy branch-tagged preview Dives and comment the links.
8. On merge, create or update the production Dive matched by title.
9. On branch deletion, clean up matching preview Dives.

The blessed example uses:

```bash
make setup
make new-dive my-dive
make preview my-dive
```

Manual preview is equivalent to:

```bash
cd .dive-preview
npm install
echo 'export { default } from "../../dives/my-dive/my-dive";' > src/dive.tsx
npm run dev
```

Deployment scripts should read source from the Dive folder, strip local-only `REQUIRED_DATABASES`, read metadata, pass `required_resources`, and either create or update based on exact title. Preview deployments should make title collisions impossible by appending the branch name.

## 8. Embedding Dives

Use embedding when an existing application needs a live read-only Dive surface without building a full custom analytics app.

Verify ordinary-Dive and embedded-Dive entitlements against current public docs before promising an embed rollout. Do not carry plan names or availability claims forward from this reference.

Embedding flow:

1. Build and save the Dive.
2. Ensure the service account used for embedding can read the required data.
3. Backend creates an embed session for the Dive.
4. Frontend renders the session in a sandboxed iframe.
5. Refresh the session when it expires.

Use `useDiveState(key, initialValue)` for interactive state that a host may preconfigure. Pass matching JSON-serializable keys through the embed session's `initial_state`; absent keys fall back to the source-declared initial value. State changes are not persisted automatically, so the host must listen for `dive-state-update` messages if it wants to save and restore them.

Keep all admin tokens and service-account tokens on the backend. The browser should receive only the short-lived embed session string.

Treat every iframe `postMessage` as untrusted input. Check `event.origin`, message type, and payload before updating host state, navigating, or starting a download. A `navigation-request` expresses user intent; it is never authorization to mutate application state or grant access. Handle export messages with the current embedding contract and preserve the host application's download and content-security policy.

Backend session creation:

```ts
const response = await fetch(`https://api.motherduck.com/v1/dives/${diveId}/embed-session`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.MOTHERDUCK_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    username: process.env.MOTHERDUCK_SERVICE_ACCOUNT_USERNAME,
    session_hint: customerId,
    initial_state: { customerId, period: "last_30_days" },
  }),
});

const { session } = await response.json();
```

Frontend iframe:

```html
<iframe
  src="https://embed-motherduck.com/sandbox/#session=SESSION_FROM_BACKEND"
  sandbox="allow-scripts allow-same-origin"
  width="100%"
  height="600"
  style="border:0"
></iframe>
```

Add `frame-src https://embed-motherduck.com;` to Content Security Policy when CSP is strict.

Use server mode first. Use dual mode only when the Dive benefits from browser-side DuckDB-Wasm responsiveness. Current MotherDuck Wasm clients no longer require cross-origin isolation headers; verify the current SDK and embedding docs instead of preserving old COI requirements.

Embedded Dives are read-only. Escalate to `motherduck-build-cfa-app` when the product needs custom writes, backend authorization logic, non-Dive routes, or per-customer API contracts.

## Dive Status Lifecycle

Every Dive carries a trust signal that is separate from access control:

| Status | Meaning and agent behavior |
| --- | --- |
| Draft | Work in progress and the default for a new Dive |
| Ready | Reviewed by its owner and suitable for others to use |
| Endorsed | Admin-approved source of truth; prefer it when reusing existing work |
| Archived | Retired; hidden from default agent listings but still readable by ID or URL |

Owners can set Draft, Ready, or Archived on their own Dives. Only admins can set Endorsed. Updating Dive content does not reset the status. Use `list_dives` status ordering when selecting existing work, and never have an agent self-endorse its own output.

Set status with the documented MCP write path or `MD_UPDATE_DIVE_STATUS` through `query_rw`:

```sql
FROM MD_UPDATE_DIVE_STATUS(
  id = '<dive-uuid>'::UUID,
  status = 'ready'
);
```

Read the Dive back after the change. Treat promotion to Ready as a publication step, not an automatic side effect of saving a draft.

## Write-Back with Flights

A Dive never writes through its own SQL. A control in the Dive starts a run of a Flight, the Flight performs the write with its owner's token and secrets, and the Dive follows the run and reloads its data.

1. Build and validate the Flight first (see `motherduck-create-flight`). Declare every key the Dive will send in the Flight's stored `config`; a run can override only existing keys, and the Flight reads them as environment variables.
2. Validate every value inside the Flight as untrusted input and bind it as a SQL parameter.
3. Recommend who should run the Flight, and after the user confirms, grant it: `GRANT RUN ON FLIGHT '<flight_id>' TO ROLE <role>`.
4. Wire the control:

```jsx
import { useRunFlight, useFlightRun } from "@motherduck/react-sql-query";

// Hardcode the ID. MD_LIST_FLIGHTS() only lists the viewer's own Flights.
const APPROVE_ORDER_FLIGHT = "00000000-0000-4000-8000-000000000000";

// `orders` is the useSQLQuery result that reads the table the Flight writes.
function ApproveOrder({ orderId, orders }) {
  const start = useRunFlight(APPROVE_ORDER_FLIGHT);
  const run = useFlightRun(APPROVE_ORDER_FLIGHT, start.data?.runNumber, {
    onFinished: (finished) => {
      if (finished.status === "SUCCEEDED") orders.refetch();
    },
  });
  const busy = start.isPending || run.isChecking;

  return (
    <div>
      <button disabled={busy} onClick={() => start.run({ ORDER_ID: String(orderId), DECISION: "approved" })}>
        {busy ? "Approving..." : "Approve"}
      </button>
      {run.isFinished && run.status !== "SUCCEEDED" && <p role="alert">The approval did not finish.</p>}
      {start.error && <p role="alert">Could not start: {start.error.message}</p>}
      {run.error && <p role="alert">Could not check the run: {run.error.message}</p>}
    </div>
  );
}
```

- Call `run` only from an event handler; every call starts a new run. A resolved `run` means the run started, not that it finished. `runAsync` returns a promise for the same result.
- `useFlightRun` polls for you: `status` moves from `undefined` to `PENDING`, `RUNNING`, then `SUCCEEDED`, `FAILED`, or `CANCELLED`; `isFinished` and `exitCode` are set at the end, and `onFinished` fires once per run. After an hour `isChecking` turns false; call `check()` to look again. Do not write your own polling.
- Viewers without a grant get an error from `run`; show it in plain words and keep the rest of the Dive working. A table of past runs (`MD_LIST_FLIGHT_RUNS`) works only for the owner and Admins.
- Config values must be strings. Convert numbers, dates, and booleans before calling `run`.
- Test from SQL before wiring the UI: `MD_RUN_FLIGHT` returns the `run_number`, and `MD_GET_FLIGHT_RUN` reports its terminal status.
- Freshness: a Dive that reads the database directly sees the write after `refetch()`. When it reads through a Share, the change appears within about a minute. Only when viewers need it immediately: the Flight ends with one `CREATE SNAPSHOT OF "<database>"` (it blocks other writes while it runs), and the Dive, once the run succeeds, runs `REFRESH DATABASE "<alias>"` in a `useSQLQuery` gated with `enabled: run.status === "SUCCEEDED"`, then refetches after that refresh succeeds rather than in `onFinished`.
- Flight side: define every key the Dive sends in the Flight's config (default `''`), validate values against allowed inputs, make a repeated click harmless (set a status rather than append a row), attach only the databases it needs, and set a short `max_runtime_sec`.
- Sharing a Dive that runs Flights: viewers need to see the Dive, read every `REQUIRED_DATABASES` share, and hold a `run` grant on each Flight. Recommend those grants and apply them only after the user confirms; prefer a role over `ORGANIZATION`.
- Runs work in the MotherDuck app, the MCP Dive viewer, and `motherduck dive watch`. Embedded Dives show "This Dive can't run Flights." Viewers with no roles or on a read-scaling token are refused.
- Common failures: no `RUN` grant (not-found or ownership error), an error the Dive does not render (click appears to do nothing), and stale data because the Dive did not rerun its queries.

## Exporting Query Results

Add export controls only when the use case calls for them; the runtime generates the file. Call `exportAs` on a visible query's result to export the same SQL, or use `useExport` for export-only SQL:

```jsx
import { useExport } from "@motherduck/react-sql-query";

const { exportQuery } = useExport();

async function downloadOrders() {
  try {
    await exportQuery({ sql: `SELECT * FROM "analytics"."main"."orders"`, format: "parquet", filename: "orders" });
  } catch (e) {
    setExportError(e.message);
  }
}
```

Formats are `csv`, `json`, `parquet`, and `xlsx`, with format-specific options such as compression and sheet names. Start exports only from a click, never during render, in `useEffect`, or on a timer, and show errors inline. Do not build Blob URLs, hidden anchors, `window.open()` downloads, or `COPY TO` statements.

## Agent Chat on Dives

The **AI Chat** button in a Dive opens MotherDuck's in-app agent. It sees the Dive's queries, their data, and the viewer's current filters and selections, and it acts with the viewer's own permissions. It can create Dives, add charts, change filters or queries, edit the title and description, share the underlying data with the organization (Dive owner only), and delete Dives. Each edit is saved as a new version; deletions are permanent. It cannot change tables or databases.

Design implications for authored Dives:

- Name and describe sections and queries in plain business terms so the agent can explain them.
- Keep filter state in explicit Dive state so the agent sees what the viewer is looking at.
- Treat agent edits like any other edit: read the current version before overwriting, and use version history to recover.
- Organization Admins can turn Agent Chat off on the AI Features settings page.

## Runtime Guide, Design, and Starter

`get_dive_guide` returns the current runtime contract at authoring time. Follow it for these topics instead of restating them in a Dive prompt or in this reference:

- component shape, allowed imports, and unsupported patterns
- `useSQLQuery` result shape, the `N()` conversion helper, DuckDB value handling, and date formatting in SQL
- per-section loading and error placeholders
- `useDiveState` limits, export APIs, and the Flight hooks
- Tailwind support (static utilities only; arbitrary-value and dynamically built classes do not resolve), the MotherDuck palette, chart sizing, and the visual checklist

This skill adds the defaults the runtime guide leaves open, so a new Dive is complete on the first save:

| Default | How |
|---|---|
| Reflows from about 320 px to wide panes | Tailwind breakpoint grids (`grid-cols-2 md:grid-cols-4` for KPIs), `ResponsiveContainer width="100%"`, no fixed widths, no page-level horizontal scroll |
| Light and dark themes | A small token object for each theme applied through inline `style`, starting from `prefers-color-scheme`; light tokens use the MotherDuck palette |
| Filters that survive refresh and sharing | `useDiveState` for period, segment, sort, and selected view; `useState` for drafts and dialogs |
| Every section handles loading, empty, and error | One query per section with its own skeleton, empty message, and `role="alert"` error |
| Freshness | A "data as of" line from `MAX(<timestamp>)` in the header |
| Export | `exportAs` on the detail query, from a click, when people will take the data elsewhere |
| Actions | A write-back control (`useRunFlight` + `useFlightRun`) when the Dive should change data, backed by a Flight instrumented for the Flight Explainer |
| Usable controls | The runtime strips default button styles: give controls a visible border, `h-11` (44 px) targets, and a `focus-visible` ring |
| Ready for AI Chat and sharing | Plain-language titles with units, a Dive description, and share-backed `REQUIRED_DATABASES` before others open it |

Start from `artifacts/feature_complete_dive.tsx`, which implements every row above, and delete the sections the Dive does not need. Read `RESPONSIVE_DIVE_DESIGN_SYSTEM.md` for layout and theme detail and `VISUAL_QA_PLAYBOOK.md` for the review loop.

## Common Failure Modes

- Saving before the SQL has been validated.
- Building one huge query that every UI interaction has to rerun.
- Returning raw rows when the UI needs pre-aggregated values.
- Missing loading, empty, or error states.
- Using an unshared private database when teammates need to view the Dive.
- Letting `REQUIRED_DATABASES` diverge from `dive_metadata.json.requiredResources`.
- Breaking blessed-dives deployment by formatting `REQUIRED_DATABASES` across multiple lines.
- Exposing MotherDuck tokens in browser code.
- Updating content when only metadata should change.
- Deleting or overwriting a Dive without checking version history.
- Writing from Dive SQL instead of starting a Flight, or starting a Flight on render instead of from a click.

---

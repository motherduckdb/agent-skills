# Dive Design Guide

Reference for creating, editing, managing, sharing, embedding, and polishing MotherDuck Dives. Use this for the practical mechanics after `motherduck-create-dive` has selected the right workflow.

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
3. Call `get_dive_guide` when MCP is available so the current component API and runtime libraries are in scope.
4. Design the data story: primary question, sections, filters, and interaction model.
5. Build a React component with `useSQLQuery`, a default export, safe value conversion, and per-query loading/empty/error states.
6. Preview locally when possible.
7. Save or update only after the queries and UI behavior are correct.
8. Share data or configure embed sessions only after the saved Dive works.

Prefer incremental edits. A saved Dive can be updated in place, and every content update creates a version.

## 4. Component Contract

Every Dive component should have:

- a default React component export
- `useSQLQuery` calls for live MotherDuck SQL
- fully qualified table names such as `"database"."schema"."table"`
- SQL that does most aggregation and shaping
- React state only for presentation, filters, and interaction controls
- safe value conversion for unknown query values
- loading, empty, and error states for each independent query

Supported runtime libraries currently include React, `@motherduck/react-sql-query`, Recharts, and `lucide-react`. Verify with `get_dive_guide` before relying on a newly added library.

Use this baseline shape:

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";

const N = (v: unknown): number => (v != null ? Number(v) : 0);

export default function Dive() {
  const { data, isLoading, isError, error } = useSQLQuery(`
    SELECT
      date_trunc('month', order_date) AS month,
      SUM(revenue) AS revenue
    FROM "analytics"."main"."orders"
    GROUP BY 1
    ORDER BY 1
  `);

  const rows = Array.isArray(data) ? data : [];

  if (isError) {
    return <div>Failed to load: {error?.message || "Unknown error"}</div>;
  }

  return <div>{isLoading ? "Loading" : rows.map((row) => N(row.revenue)).join(", ")}</div>;
}
```

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

For workspace-only Dives, MCP can often suggest or create org-scoped shares for private databases referenced by the Dive. Ask explicitly when teammates need access.

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
4. `update_dive` only after the user approves the changed behavior.

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

Current public materials say ordinary Dives are available on all plans, while Embedded Dives require a Business plan. Verify plan access before promising an embed rollout.

Embedding flow:

1. Build and save the Dive.
2. Ensure the service account used for embedding can read the required data.
3. Backend creates an embed session for the Dive.
4. Frontend renders the session in a sandboxed iframe.
5. Refresh the session when it expires.

Keep all admin tokens and service-account tokens on the backend. The browser should receive only the short-lived embed session string.

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

Use server mode first. Use dual mode only when the Dive needs browser-side DuckDB-Wasm responsiveness and the parent app can set cross-origin isolation headers:

```text
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
```

Embedded Dives are read-only. Escalate to `motherduck-build-cfa-app` when the product needs custom writes, backend authorization logic, non-Dive routes, or per-customer API contracts.

## 9. Theme Prompt Template

Use this structure when you want the model to reliably produce a coherent Dive style instead of generic dashboard output.

```text
Theme: Corporate Dashboard
- Feel: crisp, compact business dashboard with restrained motion
- Background: #f5f5f5
- Text: #333333
- Muted: #777777
- Chart colors: ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed"]
- Typography: strong title, quiet KPI labels, sentence-case headings
- Chart rules: thin grid lines, 2px line strokes, 4px bar radius, no heavy card chrome
- Layout: one KPI row, one primary chart, one supporting table
- Interactivity: one time-range toggle, no redundant controls
```

Make the prompt concrete:

- Name a theme or visual reference.
- Specify palette roles, not just one accent color.
- State chart density and layout intent.
- Ask for cross-filtering only when the Dive has a shared drill-down dimension.
- Keep the palette to roughly 5-7 colors.

## 10. Theme Gallery Shortlist

Use these named gallery directions as defaults:

| Theme | Best For | Notes |
|---|---|---|
| `Corporate Dashboard` | KPI, finance, operations | Safe default for compact business dashboards |
| `Tufte Minimal` | Dense analytical views | Strong when the Dive should feel editorial and restrained |
| `FT Salmon` | Executive summaries, narrative analytics | Good for business storytelling with softer contrast |
| `Knowledge Beautiful` | Exploratory visuals | Use when hierarchy and layering matter |

The public Dive gallery is useful for composition cues:

- `KPI Dashboard using Tableau Superstore Data` for standard KPI + trend structure
- `NYC Taxi Operations Dashboard` for operations monitoring layout
- `Spotify Tracks Explorer` for a slightly more exploratory interaction model

Borrow structure and pacing, not pixel-perfect styling.

---

## 11. Recharts Component Reference

All charts must be wrapped in `<ResponsiveContainer width="100%" height={260}>`.

```tsx
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
```

### Common Sub-Components

```tsx
<XAxis dataKey="month" tick={{ fontSize: 12 }} />
<YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
<CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
<Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
<Legend wrapperStyle={{ fontSize: 12 }} />  // only for multiple series
```

**Cell** -- colors individual segments in Bar or Pie:

```tsx
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];
<Bar dataKey="revenue">
  {rows.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
</Bar>
```

### BarChart

```tsx
<ResponsiveContainer width="100%" height={260}>
  <BarChart data={rows}>
    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
    <XAxis dataKey="category" tick={{ fontSize: 12 }} />
    <YAxis tick={{ fontSize: 12 }} />
    <Tooltip />
    <Bar dataKey="revenue" fill="#0777b3" radius={[4, 4, 0, 0]} />
  </BarChart>
</ResponsiveContainer>
```

Bar props: `dataKey`, `fill`, `radius` (corner rounding), `barSize`, `stackId` (same value = stacked).

**Stacked bars:**

```tsx
<Bar dataKey="online" stackId="rev" fill="#0777b3" name="Online" />
<Bar dataKey="store" stackId="rev" fill="#bd4e35" name="In-Store" />
```

### LineChart

```tsx
<ResponsiveContainer width="100%" height={260}>
  <LineChart data={rows}>
    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
    <YAxis tick={{ fontSize: 12 }} />
    <Tooltip />
    <Line type="monotone" dataKey="revenue" stroke="#0777b3" strokeWidth={2} dot={false} />
  </LineChart>
</ResponsiveContainer>
```

Line props: `type` (`"monotone"`, `"linear"`, `"step"`), `dataKey`, `stroke`, `strokeWidth`, `dot`, `strokeDasharray`.

**Multi-line:** add multiple `<Line>` elements with different `dataKey`, `stroke`, and `name` values.

### PieChart

Use only with 2-6 slices. Requires `Cell` for colors.

```tsx
<ResponsiveContainer width="100%" height={260}>
  <PieChart>
    <Pie data={rows} dataKey="revenue" nameKey="category" cx="50%" cy="50%" outerRadius={100}
         label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
      {rows.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
    </Pie>
    <Tooltip />
  </PieChart>
</ResponsiveContainer>
```

Pie props: `dataKey`, `nameKey`, `cx`/`cy`, `innerRadius` (>0 for donut), `outerRadius`, `label`, `paddingAngle`.

### AreaChart

```tsx
<ResponsiveContainer width="100%" height={260}>
  <AreaChart data={rows}>
    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
    <YAxis tick={{ fontSize: 12 }} />
    <Tooltip />
    <Area type="monotone" dataKey="revenue" stroke="#0777b3" fill="#0777b3" fillOpacity={0.15} />
  </AreaChart>
</ResponsiveContainer>
```

Area props: `type`, `dataKey`, `stroke`, `fill`, `fillOpacity` (0.1-0.3), `stackId`.

### ScatterChart

```tsx
<ResponsiveContainer width="100%" height={260}>
  <ScatterChart>
    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
    <XAxis dataKey="spend" name="Ad Spend" tick={{ fontSize: 12 }} />
    <YAxis dataKey="conversions" name="Conversions" tick={{ fontSize: 12 }} />
    <Tooltip cursor={{ strokeDasharray: "3 3" }} />
    <Scatter data={rows} fill="#0777b3" />
  </ScatterChart>
</ResponsiveContainer>
```

---

## 12. Tailwind Utilities Commonly Used

### Layout

`flex`, `flex-col`, `items-center`, `justify-center`, `justify-between`, `grid`, `grid-cols-2`, `grid-cols-3`, `grid-cols-4`, `gap-4`, `gap-6`, `gap-8`, `min-h-screen`, `w-full`

### Spacing

`p-4`/`p-6`/`p-8`, `px-4`/`py-2`, `m-0`, `mb-1`/`mb-4`/`mb-6`/`mb-8`/`mb-10`, `mt-4`/`mt-8`

### Typography

`text-xs` (12px), `text-sm` (14px), `text-base` (16px), `text-lg` (18px), `text-2xl` (24px), `text-5xl` (48px), `font-medium`, `font-semibold`, `font-bold`, `uppercase`, `tracking-wide`

### Colors (Tailwind standard)

`text-gray-400`/`text-gray-500`/`text-gray-600`, `bg-gray-100`/`bg-gray-200`, `bg-white`

For brand colors use inline `style`: `style={{ color: "#231f20" }}`, `style={{ backgroundColor: "#f8f8f8" }}`.

### Animation

`animate-pulse` (skeletons), `animate-spin` (spinners)

### Borders

`rounded`, `rounded-lg`, `border-b`, `border-gray-200`. Use sparingly -- no card borders.

### Overflow

`overflow-x-auto` (horizontal scroll for tables), `truncate`

---

## 13. Loading State Patterns

### KPI Skeleton

```tsx
{isLoading ? (
  <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
) : (
  <p className="text-5xl font-bold" style={{color:"#231f20"}}>
    ${(N(rows[0]?.total) / 1000).toFixed(0)}K
  </p>
)}
```

### Chart Spinner

```tsx
{isLoading ? (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="animate-spin" size={32} style={{color:"#0777b3"}} />
  </div>
) : (
  <ResponsiveContainer width="100%" height={260}>{/* chart */}</ResponsiveContainer>
)}
```

### Table Skeleton

```tsx
{isLoading ? (
  <div className="space-y-3">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />
    ))}
  </div>
) : ( <table>{/* ... */}</table> )}
```

### Error State

```tsx
{isError && (
  <p className="text-sm" style={{color:"#bd4e35"}}>
    Failed to load: {error?.message || "Unknown error"}
  </p>
)}
```

---

## 14. Multi-Query Dive Pattern

Use multiple `useSQLQuery` calls. Name destructured variables uniquely. Each section renders its own loading state.

```tsx
export default function MultiQueryDive() {
  const { data: kpiData, isLoading: kpiLoading } = useSQLQuery(`SELECT ...`);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];

  const { data: trendData, isLoading: trendLoading } = useSQLQuery(`SELECT ...`);
  const trendRows = Array.isArray(trendData) ? trendData : [];

  const { data: catData, isLoading: catLoading } = useSQLQuery(`SELECT ...`);
  const catRows = Array.isArray(catData) ? catData : [];

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      {/* KPI section: uses kpiLoading */}
      {/* Chart section: uses trendLoading */}
      {/* Table section: uses catLoading */}
    </div>
  );
}
```

---

## 15. Table Component Pattern

Use tables for fewer than 8 categories or when exact values matter.

```tsx
<div className="overflow-x-auto">
  <table className="w-full text-sm">
    <thead>
      <tr className="border-b border-gray-200">
        <th className="text-left py-3 font-semibold" style={{color:"#231f20"}}>Category</th>
        <th className="text-right py-3 font-semibold" style={{color:"#231f20"}}>Revenue</th>
        <th className="text-right py-3 font-semibold" style={{color:"#231f20"}}>Orders</th>
      </tr>
    </thead>
    <tbody>
      {rows.map((row, i) => (
        <tr key={i} className="border-b border-gray-200"
            style={{ backgroundColor: i % 2 === 0 ? "transparent" : "#f0f0f0" }}>
          <td className="py-3" style={{color:"#231f20"}}>{row.category}</td>
          <td className="text-right py-3" style={{color:"#231f20"}}>${N(row.revenue).toLocaleString()}</td>
          <td className="text-right py-3" style={{color:"#6a6a6a"}}>{N(row.orders).toLocaleString()}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

Rules: left-align text, right-align numbers, `border-b` separators, alternating row colors, `overflow-x-auto` wrapper, always use `N()`.

---

## 16. Color Usage

### Chart Series (in order)

| Hex | Name | Use |
|---|---|---|
| `#0777b3` | Blue | Primary series, single-series charts |
| `#bd4e35` | Red | Second series, negative values |
| `#2d7a00` | Green | Third series, growth indicators |
| `#e18727` | Orange | Fourth series, warnings |
| `#638CAD` | Blue-gray | Fifth series |
| `#adadad` | Gray | Sixth series, baselines, "other" |

### Text and Background

| Hex | Purpose |
|---|---|
| `#231f20` | Primary text (headings, KPI values, table data) |
| `#6a6a6a` | Secondary text (labels, subtitles) |
| `#f8f8f8` | Page background |
| `#f0f0f0` | Alternating table rows |
| `#e0e0e0` | CartesianGrid stroke |

### KPI Delta Colors

```tsx
const delta = N(rows[0]?.change_pct);
const deltaColor = delta >= 0 ? "#2d7a00" : "#bd4e35";
<span style={{ color: deltaColor }}>{delta >= 0 ? "+" : ""}{delta.toFixed(1)}%</span>
```

---

## 17. Interactive Filters

### Period Selector

```tsx
import { useState } from "react";

const [period, setPeriod] = useState<"7d"|"30d"|"90d">("30d");
const periodDays = { "7d": 7, "30d": 30, "90d": 90 };

const { data, isLoading } = useSQLQuery(`
  SELECT strftime(order_date, '%Y-%m-%d') AS day, SUM(revenue) AS revenue
  FROM "my_db"."main"."sales"
  WHERE order_date >= CURRENT_DATE - INTERVAL ${periodDays[period]} DAY
  GROUP BY 1 ORDER BY 1
`);

<div className="flex gap-2 mb-6">
  {(["7d","30d","90d"] as const).map((p) => (
    <button key={p} onClick={() => setPeriod(p)}
      className="px-4 py-2 rounded text-sm font-medium"
      style={{
        backgroundColor: period === p ? "#0777b3" : "#e0e0e0",
        color: period === p ? "#ffffff" : "#231f20",
      }}>
      {p}
    </button>
  ))}
</div>
```

The query re-executes automatically when state changes. Use inline `style` for active/inactive states.

### Metric Toggle

```tsx
const [metric, setMetric] = useState<"revenue"|"orders">("revenue");

// Query returns both columns
const { data } = useSQLQuery(`SELECT month, SUM(revenue) AS revenue, COUNT(*) AS orders ...`);

// Chart uses selected metric dynamically
<Line dataKey={metric} stroke="#0777b3" strokeWidth={2} dot={false} />
```

---

## 18. Formatting Patterns

```tsx
// Currency
`$${(N(v) / 1000).toFixed(0)}K`       // thousands
`$${(N(v) / 1_000_000).toFixed(1)}M`  // millions
`$${N(v).toLocaleString()}`            // full with commas

// Percentages
`${(N(v) * 100).toFixed(1)}%`         // from decimal
`${N(v).toFixed(1)}%`                  // already percentage

// YAxis formatter
<YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
```

---

## 19. Choosing the Right Chart

| Data Shape | Chart | Notes |
|---|---|---|
| Values over time (single) | LineChart | Prefer `type="linear"` unless smoothing is clearly useful |
| Values over time (multi) | LineChart | Max 3-4 lines |
| Volume over time | AreaChart | Low `fillOpacity` (0.15-0.3) |
| Comparing categories (8+) | BarChart | Horizontal if names are long |
| Comparing categories (<8) | Table | Clearer for small datasets |
| Part of whole (2-6) | PieChart | Never 7+ segments |
| Correlation | ScatterChart | Label axes clearly |
| Stacked breakdown | Stacked AreaChart/BarChart | Use `stackId` |

---

## 20. Common Failure Modes

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

---

## 21. Complete Annotated Example

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";

// REQUIRED: safely converts unknown query values to numbers
const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function ProductAnalytics() {
  // Query 1: KPIs -- independent loading
  const { data: kpiData, isLoading: kpiLoading, isError: kpiError, error: kpiMsg } = useSQLQuery(`
    SELECT SUM(revenue) AS total_revenue, COUNT(DISTINCT order_id) AS total_orders,
           COUNT(DISTINCT product_id) AS total_products,
           ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS avg_order_value
    FROM "analytics_db"."main"."order_items"
  `);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];

  // Query 2: Categories -- independent loading
  const { data: catData, isLoading: catLoading } = useSQLQuery(`
    SELECT category, SUM(revenue) AS revenue
    FROM "analytics_db"."main"."order_items"
    GROUP BY 1 ORDER BY 2 DESC LIMIT 6
  `);
  const catRows = Array.isArray(catData) ? catData : [];

  // Query 3: Recent orders for table
  const { data: tableData, isLoading: tableLoading } = useSQLQuery(`
    SELECT strftime(order_date, '%Y-%m-%d') AS order_date, product_name, category, revenue
    FROM "analytics_db"."main"."order_items"
    ORDER BY order_date DESC LIMIT 8
  `);
  const tableRows = Array.isArray(tableData) ? tableData : [];

  // Reusable KPI card
  const KPI = ({ label, value, prefix = "" }: { label: string; value: string; prefix?: string }) => (
    <div>
      <p className="text-sm mb-1" style={{ color: "#6a6a6a" }}>{label}</p>
      {kpiLoading ? <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
        : <p className="text-5xl font-bold" style={{ color: "#231f20" }}>{prefix}{value}</p>}
    </div>
  );

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      <h1 className="text-2xl font-bold mb-8" style={{ color: "#231f20" }}>Product Analytics</h1>

      {/* KPI Row: grid-cols-4 horizontal layout */}
      <div className="grid grid-cols-4 gap-8 mb-10">
        <KPI label="Total Revenue" prefix="$" value={`${(N(kpiRows[0]?.total_revenue)/1000).toFixed(0)}K`} />
        <KPI label="Total Orders" value={N(kpiRows[0]?.total_orders).toLocaleString()} />
        <KPI label="Products" value={N(kpiRows[0]?.total_products).toLocaleString()} />
        <KPI label="Avg Order Value" prefix="$" value={N(kpiRows[0]?.avg_order_value).toFixed(2)} />
      </div>
      {kpiError && <p className="text-sm mb-4" style={{color:"#bd4e35"}}>Error: {kpiMsg?.message}</p>}

      {/* Bar Chart: top categories */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Revenue by Category</h2>
        {catLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={catRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="revenue" fill={COLORS[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Table: recent orders -- dates formatted in SQL via strftime() */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Recent Orders</h2>
        {tableLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold" style={{color:"#231f20"}}>Date</th>
                  <th className="text-left py-3 font-semibold" style={{color:"#231f20"}}>Product</th>
                  <th className="text-left py-3 font-semibold" style={{color:"#231f20"}}>Category</th>
                  <th className="text-right py-3 font-semibold" style={{color:"#231f20"}}>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row, i) => (
                  <tr key={i} className="border-b border-gray-200"
                      style={{ backgroundColor: i % 2 === 0 ? "transparent" : "#f0f0f0" }}>
                    <td className="py-3" style={{color:"#6a6a6a"}}>{row.order_date}</td>
                    <td className="py-3" style={{color:"#231f20"}}>{row.product_name}</td>
                    <td className="py-3" style={{color:"#231f20"}}>{row.category}</td>
                    <td className="text-right py-3" style={{color:"#231f20"}}>${N(row.revenue).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
```

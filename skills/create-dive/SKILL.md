---
name: create-dive
description: Create interactive MotherDuck Dives — persistent React data apps with live queries and visualizations. Use when building charts, dashboards, KPI displays, or any data visualization that should be saved and shareable.
license: MIT
metadata:
  author: motherduck
  version: "2.0"
  layer: workflow
  language_focus: "typescript|javascript|python"
  depends_on:
    - explore
    - query
---

# Create MotherDuck Dives

Use this skill when building interactive data visualizations, charts, dashboards, KPI displays, or any data app that should be saved to a MotherDuck account and shareable with others.

## Source Of Truth

- Prefer the current MotherDuck Dive guide and public Dives docs first.
- If MotherDuck MCP is available, call `get_dive_guide` before generating or saving a Dive.
- Keep Dive guidance aligned with the documented product posture:
  - Dives are live workspace artifacts
  - queries should stay fully qualified and SQL-heavy
  - preview with small subsets during iteration, then save live `useSQLQuery` hooks
  - for full customer-facing analytics with per-customer isolation, see `build-cfa-app`

## What Is a Dive?

A Dive is a persistent, interactive React data app with live SQL queries. Each Dive is saved to the user's MotherDuck account, is shareable via URL, and always displays current data because queries execute on every render. Dives support charts, tables, KPI cards, and interactive filters -- all powered by real-time MotherDuck queries.

## Prerequisites

- Data must be available in MotherDuck. Use `explore` to discover databases and tables, `query` to verify SQL.
- Know the fully qualified table names (`"database"."schema"."table"`) for every table you will query.

## Language Focus: TypeScript/Javascript and Python

- This skill is **TypeScript/Javascript-first** because Dives are React code.
- Prefer **TypeScript/TSX** examples whenever writing Dive components, hooks, or chart code.
- Use **Python** only around the edges:
  - to prepare data before it lands in MotherDuck
  - to validate the SQL that a Dive will run
  - to automate save/update flows outside the UI code
- If the user asks for a full workflow:
  - use Python for data prep if needed
  - use TypeScript/TSX for the Dive itself

## TypeScript/TSX Starter

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";

export default function RevenueKpi() {
  const { data, isLoading } = useSQLQuery(`
    SELECT SUM(revenue) AS total_revenue
    FROM "analytics"."main"."orders"
  `);
  const rows = Array.isArray(data) ? data : [];
  const N = (v: unknown): number => (v != null ? Number(v) : 0);

  if (isLoading) return <div>Loading...</div>;
  return <div>{N(rows[0]?.total_revenue).toLocaleString()}</div>;
}
```

## Python Validation Starter

```python
import duckdb

conn = duckdb.connect("md:analytics")
preview = conn.sql("""
SELECT SUM(revenue) AS total_revenue
FROM "analytics"."main"."orders"
""").fetchall()
conn.close()
```

---

## 1. The Data Hook -- useSQLQuery

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";

const { data, isLoading, isError, error } = useSQLQuery(`
  SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
         SUM(revenue) AS revenue
  FROM "my_db"."main"."sales"
  GROUP BY 1 ORDER BY 1
`);
const rows = Array.isArray(data) ? data : [];
```

- `data` is already an array of row objects. Do NOT access `data.rows`.
- Always guard with `Array.isArray(data) ? data : []` to handle undefined during loading.
- Each `useSQLQuery` call loads independently with its own `isLoading` / `isError` states.
- Keep one `useSQLQuery` per visual or logical section instead of one giant query that powers the whole page.

## Authoring Workflow

1. Explore and validate the SQL first.
2. When iterating locally, use aggregates or `LIMIT`ed subsets so the preview stays cheap and fast.
3. After the user approves the shape, wire the final component to live `useSQLQuery` calls.
4. Save only once the live queries, loading states, and fully qualified table names are in place.

---

## 2. The N() Helper -- REQUIRED for All Numeric Values

Query results return values as `unknown` types. Passing them directly to Recharts produces `NaN`.

```tsx
const N = (v: unknown): number => (v != null ? Number(v) : 0);
// Usage: N(row.revenue), N(row.count), N(rows[0]?.total)
```

Never skip the `N()` wrapper. Forgetting it is the most common cause of broken charts.

---

## 3. Available Libraries

| Library | Version | Purpose |
|---|---|---|
| React | 18 | Component framework (`useState`, `useMemo`, etc.) |
| Recharts | ~3.7.0 | `BarChart`, `LineChart`, `PieChart`, `AreaChart`, `ScatterChart` |
| Tailwind CSS | CDN | Utility-first styling. **No bracket syntax** (`w-[200px]` is forbidden) |
| Lucide React | latest | Icons: `Loader2`, `TrendingUp`, `TrendingDown`, etc. |
| d3 | latest | Non-chart use only: geo projections, force layouts |

```tsx
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { Loader2 } from "lucide-react";
```

---

## 4. Design Rules

### Layout and Background

- Background: `#f8f8f8` on the outermost container. No card borders or shadows.

<!-- snippet-skip-next -->
```tsx
<div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
```

### KPIs

- Horizontal layout: `grid grid-cols-4 gap-8`. Large values: `text-5xl font-bold`.
- Label text: `text-sm` with `color: "#6a6a6a"`. Value text: `color: "#231f20"`.

### Charts

- Max 1-2 charts per Dive, each 200-280px height.
- Use `<ResponsiveContainer width="100%" height={260}>`.
- Prefer tables over charts for fewer than 8 categories.

### Color Palette

```tsx
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];
```

Text: primary `#231f20`, secondary `#6a6a6a`. Background: `#f8f8f8`.

### Tailwind

- Standard classes only: `p-8`, `gap-4`, `text-sm`, `font-bold`, `grid-cols-4`.
- NEVER bracket syntax (`w-[200px]`, `text-[#333]`). Use inline `style` for custom values.

### Dates

- Format in SQL with `strftime()`. NEVER parse dates in JavaScript.

```sql
SELECT strftime(order_date, '%Y-%m') AS month FROM ...
```

### Loading States

Show inline placeholders per section, not a single full-page spinner.

<!-- snippet-skip-next -->
```tsx
// KPI skeleton
{isLoading ? (
  <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
) : (
  <p className="text-5xl font-bold" style={{color:"#231f20"}}>{N(rows[0]?.total).toLocaleString()}</p>
)}

// Chart spinner
{isLoading ? (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="animate-spin" size={32} style={{color:"#0777b3"}} />
  </div>
) : ( /* chart */ )}
```

### Default Export

Every Dive MUST have a default export: `export default function MyDive() { ... }`.

---

## 5. Creating a Dive

### Via SQL

```sql
SELECT * FROM MD_CREATE_DIVE(
  title = 'My Dashboard',
  content = '... React component code ...'
);
```

Inside SQL strings, escape single quotes by doubling them (`''`).

### Via MCP

1. Call `get_dive_guide` to retrieve the latest authoring reference.
2. Write the React component code.
3. Call `save_dive` with the component code and a title.

### Updating

```sql
SELECT * FROM MD_UPDATE_DIVE_CONTENT(dive_id = 'abc123', content = '...');
```

Or use MCP `update_dive` tool.

### Deleting

Use MCP `delete_dive` tool.

---

## 6. Complete Minimal Example

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";

const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function SalesDashboard() {
  const { data: kpiData, isLoading: kpiLoading } = useSQLQuery(`
    SELECT SUM(revenue) AS total_revenue,
           COUNT(DISTINCT order_id) AS total_orders,
           COUNT(DISTINCT customer_id) AS total_customers,
           ROUND(AVG(revenue), 2) AS avg_order_value
    FROM "my_db"."main"."sales"
  `);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];

  const { data: trendData, isLoading: trendLoading } = useSQLQuery(`
    SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
           SUM(revenue) AS revenue
    FROM "my_db"."main"."sales"
    GROUP BY 1 ORDER BY 1
  `);
  const trendRows = Array.isArray(trendData) ? trendData : [];

  const KPI = ({ label, value, prefix = "" }: {
    label: string; value: string; prefix?: string;
  }) => (
    <div>
      <p className="text-sm mb-1" style={{ color: "#6a6a6a" }}>{label}</p>
      {kpiLoading ? (
        <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
      ) : (
        <p className="text-5xl font-bold" style={{ color: "#231f20" }}>{prefix}{value}</p>
      )}
    </div>
  );

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      <h1 className="text-2xl font-bold mb-8" style={{ color: "#231f20" }}>Sales Dashboard</h1>

      <div className="grid grid-cols-4 gap-8 mb-10">
        <KPI label="Total Revenue" prefix="$" value={`${(N(kpiRows[0]?.total_revenue) / 1000).toFixed(0)}K`} />
        <KPI label="Total Orders" value={N(kpiRows[0]?.total_orders).toLocaleString()} />
        <KPI label="Customers" value={N(kpiRows[0]?.total_customers).toLocaleString()} />
        <KPI label="Avg Order Value" prefix="$" value={N(kpiRows[0]?.avg_order_value).toFixed(2)} />
      </div>

      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Monthly Revenue</h2>
        {trendLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke={COLORS[0]} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
```

---

## 7. Key Rules

- Every Dive MUST have a default export (`export default function ...`).
- ALWAYS define and use the `N()` helper for numeric values from queries.
- ALWAYS format dates in SQL with `strftime()`, never in JavaScript.
- ALWAYS use fully qualified table names: `"database"."schema"."table"`.
- NEVER use Tailwind bracket syntax. Use inline styles for custom values.
- Keep charts to 1-2 per Dive, 200-280px height.
- Use tables instead of charts when there are fewer than 8 categories.
- Show per-section loading placeholders, not a single full-page spinner.
- Use `Array.isArray(data) ? data : []` to guard against undefined data.
- Background `#f8f8f8`, no card borders, no card shadows.

---

## 8. Common Mistakes

- **Forgetting N().** Charts display `NaN` and arithmetic fails silently.
- **Parsing dates in JavaScript.** Use `strftime()` in SQL, not `new Date()` in JS.
- **Using `data.rows`.** The hook returns `data` as a flat array. There is no `.rows` property.
- **Card borders or shadows.** Data floats on the `#f8f8f8` background without containers.
- **Too many charts.** Limit to 1-2 per Dive. Use `build-dashboard` for more.
- **Tailwind bracket syntax.** `w-[200px]` does not work. Use inline `style`.
- **Not guarding `data` with `Array.isArray`.** Calling `.map()` on undefined crashes the Dive.
- **Unqualified table names.** Causes ambiguity errors with multiple databases attached.
- **Single full-page loader.** Each query loads independently; show per-section placeholders.

---

## 9. Workflow Summary

1. Use `explore` to identify tables and columns.
2. Use `query` to verify SQL returns expected data.
3. Write the React component following design rules above.
4. Create via `MD_CREATE_DIVE` (SQL) or `save_dive` (MCP).
5. Verify the Dive renders at the returned URL.
6. Update with `MD_UPDATE_DIVE_CONTENT` or `update_dive` if needed.

---

## Related Skills

- `query` -- Execute and optimize SQL queries against MotherDuck.
- `explore` -- Discover databases, tables, columns, and shares.
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup.
- `build-dashboard` -- Multi-chart orchestration for complex dashboards.

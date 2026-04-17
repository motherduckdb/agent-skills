# Dive Design Guide

Reference for theming, Recharts components, Tailwind utilities, loading patterns, table components, color usage, interactive filters, and annotated examples.

---

## 1. Theme Prompt Template

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

## 2. Theme Gallery Shortlist

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

## 3. Recharts Component Reference

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

## 4. Tailwind Utilities Commonly Used

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

## 5. Loading State Patterns

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

## 6. Multi-Query Dive Pattern

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

## 7. Table Component Pattern

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

## 8. Color Usage

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

## 9. Interactive Filters

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

## 10. Formatting Patterns

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

## 11. Choosing the Right Chart

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

## 12. Manage as Code and Embed

### Manage Dives as Code

Use a Git-backed workflow when the Dive is part of a real product or a shared team artifact:

- store the Dive source in the repo
- iterate locally with hot reload
- review through PR previews
- deploy with a scripted save/update step or CI pipeline

This is the right path when multiple people will maintain the Dive or when preview and production should be reviewable separately.

### Embed Dives

Use embedding when you need a live read-only Dive inside an existing app or site:

- backend creates the embed session
- browser receives only the short-lived session string, not the admin access token
- the embedded Dive is read-only
- the embed session expires after 24 hours
- Embedded Dives require a Business plan unless current docs explicitly say otherwise
- `embed-motherduck.com` may need to be added to `frame-src` if CSP is strict

Use server mode first; it runs queries through the Postgres endpoint and is enough for most embeds. Use dual mode only when the Dive needs browser-side DuckDB-Wasm behavior, and only after configuring cross-origin isolation headers.

Do not put admin tokens in the browser. If the user needs richer application behavior, custom API contracts, writes, non-Dive routing, or backend-side policy enforcement, move to the `motherduck-build-cfa-app` patterns instead.

### Dive Version History

Every saved Dive update creates a version. Before overwriting a Dive:

- inspect `current_version` with `list_dives`
- use `read_dive` without `version` for the latest content
- use `read_dive(version = N)` to inspect a historical version
- treat older versions as read-only unless the user explicitly asks to restore by saving updated content

---

## 13. Complete Annotated Example

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

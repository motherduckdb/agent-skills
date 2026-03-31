<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Build an Analytics Dashboard

Use this skill when creating a multi-chart, multi-KPI interactive dashboard with live MotherDuck data. This is a use-case skill -- it ties together `explore`, `query`, `create-dive`, and `duckdb-sql` into a single end-to-end workflow.

## Source Of Truth

- Prefer the current MotherDuck Dive guide and public Dives docs first.
- If MotherDuck MCP is available, call `get_dive_guide` before saving or updating a dashboard Dive.
- Keep the dashboard guidance aligned with the documented product posture:
  - Dives are for live workspace analytics and the long tail of questions
  - heavy shaping belongs in SQL, not in React
  - small previews are for iteration; saved dashboards should query live data
  - for full customer-facing analytics with per-customer isolation, see `build-cfa-app`

## Verified Delivery Defaults

The repeated repo runs point to a stable dashboard posture:

- keep one dashboard story per Dive instead of mixing several unrelated narratives
- shape metrics and breakdowns in SQL first, then render the result in TSX
- use small previews for iteration, but keep saved dashboards live against MotherDuck data
- escalate to `build-cfa-app` when the request becomes a customer-facing product surface rather than a workspace dashboard

## Validation Signals

Use these signals for testing, review, and regression checks. They are not an instruction to include a separate "Validation Signals" section in normal user-facing replies.

- run `artifacts/dashboard_story_example.py` against a temporary MotherDuck database
- verify the output contains the expected sections: `kpis`, `trend`, `breakdown`, and `detail`
- verify the dashboard still tells one coherent story instead of several unrelated narratives
- treat dashboard plans without explicit section-to-SQL mapping as incomplete

## Language Focus: TypeScript/Javascript and Python

- Prefer **TypeScript/TSX** for dashboard UI examples because Dives are React components.
- Prefer **Python** for:
  - preparing the source dataset
  - validating aggregations before visualization
  - automating dashboard refresh or publication workflows outside the Dive code
- The normal split is:
  - SQL for metrics and aggregation
  - TypeScript/TSX for rendering
  - Python only when data prep or validation is part of the task

## TypeScript/TSX Starter

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const N = (v: unknown): number => (v != null ? Number(v) : 0);

export default function MonthlyRevenueDashboard() {
  const kpis = useSQLQuery(`
    SELECT SUM(revenue) AS total_revenue,
           COUNT(DISTINCT order_id) AS order_count,
           ROUND(AVG(revenue), 2) AS avg_order_value
    FROM "analytics"."main"."orders"
  `);

  const trend = useSQLQuery(`
    SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
           SUM(revenue) AS revenue
    FROM "analytics"."main"."orders"
    GROUP BY 1 ORDER BY 1
  `);

  const kpiRows = Array.isArray(kpis.data) ? kpis.data : [];
  const trendData = (Array.isArray(trend.data) ? trend.data : []).map(r => ({
    month: r.month as string,
    revenue: N(r.revenue),
  }));

  return (
    <div className="p-6" style={{ background: "#f8f8f8" }}>
      <h1 className="text-2xl font-semibold" style={{ color: "#231f20" }}>Revenue</h1>
      <p className="text-sm mb-6" style={{ color: "#6a6a6a" }}>Monthly overview</p>

      <div className="grid grid-cols-3 gap-8 mb-8">
        {[
          { label: "Total Revenue", value: kpiRows[0]?.total_revenue, fmt: (v: number) => `$${(v / 1000).toFixed(0)}K` },
          { label: "Orders", value: kpiRows[0]?.order_count, fmt: (v: number) => v.toLocaleString() },
          { label: "Avg Order", value: kpiRows[0]?.avg_order_value, fmt: (v: number) => `$${v.toFixed(2)}` },
        ].map(({ label, value, fmt }) => (
          <div key={label}>
            {kpis.isLoading ? (
              <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
            ) : (
              <p className="text-5xl font-bold" style={{ color: "#231f20" }}>{fmt(N(value))}</p>
            )}
            <p className="text-sm mt-2" style={{ color: "#6a6a6a" }}>{label}</p>
          </div>
        ))}
      </div>

      {trend.isLoading ? (
        <div className="bg-gray-100 animate-pulse rounded" style={{ height: 250 }} />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="month" fontSize={11} />
            <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} fontSize={11} />
            <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
            <Line type="linear" dataKey="revenue" stroke="#0777b3" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
```

## Python Validation Starter

```python
import duckdb

USE_CASE_USER_AGENT = "agent-skills/1.0.0(harness-codex;llm-gpt-5.4)"

conn = duckdb.connect(f"md:analytics?custom_user_agent={USE_CASE_USER_AGENT}")
rows = conn.sql("""
SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
       SUM(revenue) AS revenue
FROM "analytics"."main"."orders"
GROUP BY 1
ORDER BY 1
""").fetchall()
conn.close()
```

## When to Use

- The user asks for a dashboard, report, or multi-section data app.
- The output requires more than a single chart -- typically KPIs, trend charts, breakdowns, and detail tables combined.
- The data lives in MotherDuck and the result should be a saved, shareable Dive.
- The request is a workspace analytics surface. For full customer-facing apps with per-customer isolation, see `build-cfa-app`.

## Prerequisites

- Data must already exist in MotherDuck. Use `explore` to discover databases and tables before starting.
- Familiarity with `create-dive` skill for Dive mechanics (useSQLQuery, N() helper, Recharts, Tailwind, loading states).

---

## Dashboard Workflow

Follow these six steps in order. Do not skip steps -- each one depends on the output of the previous step.

For implementation:

- prefer **TypeScript/TSX** for the dashboard UI because Dives are React components
- prefer **Python** for validating the source metrics before the UI is written
- do not move grouping, filtering, or date formatting out of SQL just because the UI is in TypeScript

### Step 1: Explore Available Data

Use the `explore` skill to discover what data is available and understand its shape.

1. List databases with `MD_ALL_DATABASES()`.
2. List tables in the target database with `duckdb_tables()`.
3. Inspect columns with `duckdb_columns()` to understand types and nullability.
4. Run `SUMMARIZE` on each key table to understand distributions, ranges, null rates, and cardinality.
5. **Check date ranges** on every time column -- the data may not cover the period you expect, which changes the dashboard story entirely.
6. Sample rows with `LIMIT 10` to see actual values.

A quick date range check prevents building a dashboard on stale or misaligned data:

```sql
SELECT min(order_date) AS earliest,
       max(order_date) AS latest,
       count(*) AS total_rows
FROM "my_db"."main"."orders";
```

Identify the following before proceeding:
- **Key metrics** -- the numeric columns that will become KPIs and chart values (e.g., revenue, order count, session duration).
- **Key dimensions** -- the categorical or temporal columns used for grouping, filtering, and axis labels (e.g., category, region, date).
- **Date/time columns** -- the timestamps used for time-series trends.
- **Relationships** -- how tables join together (shared keys like customer_id, product_id).

Do not proceed to Step 2 until you can name the exact columns you will query.

---

### Step 2: Define the Dashboard Story

Every dashboard tells ONE story. Pick a single narrative focus before writing any code.

**Common dashboard stories:**
- Revenue and sales performance
- Product usage and engagement
- Operational efficiency and reliability
- Customer behavior and retention

**Define the sections:**

1. **KPIs (3-5 numbers).** These are the most important metrics at a glance. Pick the numbers the user would check first every morning. Examples: Total Revenue, Order Count, Average Order Value, Customer Count.

2. **Primary chart (1 required).** This shows the main trend -- usually a time-series. Examples: Monthly Revenue (LineChart), Daily Active Users (AreaChart), Weekly Request Volume (AreaChart).

3. **Secondary chart (0-1 optional).** This shows a breakdown or comparison. Examples: Revenue by Category (BarChart), Error Rate by Endpoint (BarChart), Feature Usage (BarChart).

4. **Detail table (0-1 optional).** Use a table when the user needs exact values or when there are more than 8 categories. Examples: Top 10 Products by Revenue, Slowest Endpoints, Top Pages by Views.

**Constraints:**
- Maximum 5 KPIs.
- Maximum 2 charts.
- Maximum 1 table.
- If you find yourself adding more, split into multiple dashboards instead.

---

### Step 3: Write the SQL Queries

Write one `useSQLQuery` call per dashboard section. Separate queries ensure independent loading states and keep each query simple and debuggable.

**Query design rules:**

1. **One query per section.** KPIs get one query. Each chart gets its own query. The table gets its own query.

2. **Pre-aggregate in SQL, not JavaScript.** Compute sums, averages, counts, and ratios in SQL. The React component should only render values, never compute them.

3. **Format dates in SQL.** Use `strftime(date_trunc('month', ts), '%Y-%m')` or `strftime(date_trunc('day', ts), '%Y-%m-%d')`. Never parse or format dates in JavaScript.

4. **Use fully qualified table names.** Always reference tables as `"database"."schema"."table"`.

5. **Order and limit in SQL.** Sort time-series data with `ORDER BY 1`. Limit detail tables with `LIMIT 10` or `LIMIT 20`.

6. **Use CTEs for complex logic.** Break multi-step calculations into CTEs for readability.

7. **Preview cheaply, save live.** Use small subsets or aggregates while iterating, then keep the final saved Dive wired to live `useSQLQuery` calls.

**Example queries for a sales dashboard:**

```sql
-- KPI query: returns one row with all KPI values
SELECT SUM(revenue) AS total_revenue,
       COUNT(DISTINCT order_id) AS order_count,
       ROUND(AVG(revenue), 2) AS avg_order_value,
       COUNT(DISTINCT customer_id) AS customer_count
FROM "my_db"."main"."orders"

-- Trend query: monthly revenue for a line chart
SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
       SUM(revenue) AS revenue
FROM "my_db"."main"."orders"
GROUP BY 1 ORDER BY 1

-- Breakdown query: revenue by category for a bar chart
SELECT category, SUM(revenue) AS revenue
FROM "my_db"."main"."orders"
GROUP BY 1 ORDER BY 2 DESC LIMIT 8

-- Detail query: top products for a table
SELECT product_name, category,
       SUM(revenue) AS revenue, COUNT(*) AS orders
FROM "my_db"."main"."order_items"
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10
```

Use the `query` skill to test each query against real data before embedding it in the Dive.

---

### Step 4: Design the Layout

Follow these layout conventions for a consistent, professional dashboard.

**Structure (top to bottom):**

1. **Title** -- `text-2xl font-bold mb-8` with `color: "#231f20"`.
2. **KPI row** -- `grid grid-cols-4 gap-8 mb-10` (use `grid-cols-3` or `grid-cols-5` if needed).
3. **Primary chart** -- full width, 200-280px height, `mb-10`.
4. **Secondary chart** -- full width, 200-280px height, `mb-10` (optional).
5. **Detail table** -- full width with `overflow-x-auto` (optional).

**Styling rules:**

- Outermost container: `className="p-8 min-h-screen"` with `style={{ backgroundColor: "#f8f8f8" }}`.
- No card borders, no card shadows. Content floats on the background.
- KPI labels: `text-sm` with `color: "#6a6a6a"`.
- KPI values: `text-5xl font-bold` with `color: "#231f20"`.
- Section headings: `text-lg font-semibold mb-4` with `color: "#231f20"`.
- Use inline `style` for brand colors. Never use Tailwind bracket syntax (`w-[200px]`).

**Color palette for charts:**

```tsx
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];
```

Use colors consistently across all charts. The primary series always uses `#0777b3`.

---

### Step 5: Build the Dive

Assemble the React component using `create-dive` skill patterns.

**Component structure:**

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Loader2 } from "lucide-react";

const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function MyDashboard() {
  // Separate queries for each dashboard section
  const { data: kpiData, isLoading: kpiLoading } = useSQLQuery(`SELECT ... -- KPIs`);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];

  const { data: trendData, isLoading: trendLoading } = useSQLQuery(`SELECT ... -- Time series`);
  const trendRows = Array.isArray(trendData) ? trendData : [];

  const { data: breakdownData, isLoading: breakdownLoading } = useSQLQuery(`SELECT ... -- Breakdown`);
  const breakdownRows = Array.isArray(breakdownData) ? breakdownData : [];

  const { data: detailData, isLoading: detailLoading } = useSQLQuery(`SELECT ... -- Detail table`);
  const detailRows = Array.isArray(detailData) ? detailData : [];

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      {/* Title */}
      {/* KPIs with kpiLoading skeleton */}
      {/* Primary chart with trendLoading spinner */}
      {/* Secondary chart with breakdownLoading spinner */}
      {/* Detail table with detailLoading skeleton */}
    </div>
  );
}
```

**Critical rules:**

- Every Dive MUST have `export default function`.
- ALWAYS define and use the `N()` helper for ALL numeric values from queries.
- ALWAYS guard data with `Array.isArray(data) ? data : []`.
- Each section renders its own loading state independently. Never use a single full-page spinner.
- Wrap every chart in `<ResponsiveContainer width="100%" height={260}>`.

**Loading patterns:**

```tsx
// KPI skeleton
{kpiLoading ? (
  <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
) : (
  <p className="text-5xl font-bold" style={{ color: "#231f20" }}>
    ${N(kpiRows[0]?.total_revenue).toLocaleString()}
  </p>
)}

// Chart spinner
{trendLoading ? (
  <div className="flex items-center justify-center h-64">
    <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
  </div>
) : (
  <ResponsiveContainer width="100%" height={260}>
    {/* chart */}
  </ResponsiveContainer>
)}

// Table skeleton
{detailLoading ? (
  <div className="space-y-3">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />
    ))}
  </div>
) : (
  <table>{/* ... */}</table>
)}
```

Create the Dive via `MD_CREATE_DIVE` (SQL) or `save_dive` (MCP).

---

### Step 6: Iterate

After the initial Dive is created:

1. Open the Dive at the returned URL.
2. Verify that all sections load with real data.
3. Check that KPI values are reasonable and formatted correctly.
4. Confirm charts display the expected trends and categories.
5. Update via `MD_UPDATE_DIVE_CONTENT` (SQL) or `update_dive` (MCP) to fix issues.

Common iteration fixes:
- Adjust date truncation granularity (day vs. week vs. month).
- Change chart type (LineChart to AreaChart, or BarChart to table).
- Tune LIMIT values for breakdown charts and detail tables.
- Add or remove KPIs based on user feedback.

---

## Dashboard Design Principles

1. **Start with KPIs.** The most important numbers appear at the top. A user should understand the current state of the business in the first 2 seconds.

2. **One chart shows the primary trend.** This is almost always a time-series (LineChart or AreaChart). It answers "how is the main metric changing over time?"

3. **Second chart shows a breakdown or comparison.** This is usually a BarChart. It answers "where is the main metric coming from?" or "how do segments compare?"

4. **Tables for detail.** Use a table when there are more than 8 categories or when the user needs exact values. Tables are clearer than bar charts with many bars.

5. **One dashboard, one narrative.** Do not mix unrelated stories (e.g., sales performance and server health) in one dashboard. Build separate dashboards instead.

6. **Consistent colors across all charts.** Use the same `COLORS` array for all charts. The primary series is always `#0777b3`.

7. **Pre-aggregate everything in SQL.** The React component formats and renders. It never computes aggregations, filters data, or transforms values.

---

## Multi-Query Pattern

Each dashboard section gets its own `useSQLQuery` call. This ensures independent loading, independent error handling, and simpler SQL per query.

```tsx
// Separate queries for each dashboard section
const { data: kpiData, isLoading: kpiLoading } = useSQLQuery(`
  SELECT SUM(revenue) AS total_revenue,
         COUNT(DISTINCT order_id) AS order_count,
         ROUND(AVG(revenue), 2) AS avg_order_value,
         COUNT(DISTINCT customer_id) AS customer_count
  FROM "my_db"."main"."orders"
`);
const kpiRows = Array.isArray(kpiData) ? kpiData : [];

const { data: trendData, isLoading: trendLoading } = useSQLQuery(`
  SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
         SUM(revenue) AS revenue
  FROM "my_db"."main"."orders"
  GROUP BY 1 ORDER BY 1
`);
const trendRows = Array.isArray(trendData) ? trendData : [];

const { data: breakdownData, isLoading: breakdownLoading } = useSQLQuery(`
  SELECT category, SUM(revenue) AS revenue
  FROM "my_db"."main"."orders"
  GROUP BY 1 ORDER BY 2 DESC LIMIT 8
`);
const breakdownRows = Array.isArray(breakdownData) ? breakdownData : [];

const { data: detailData, isLoading: detailLoading } = useSQLQuery(`
  SELECT product_name, category,
         SUM(revenue) AS revenue, COUNT(*) AS orders
  FROM "my_db"."main"."order_items"
  GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10
`);
const detailRows = Array.isArray(detailData) ? detailData : [];
```

---

## Key Rules

- **One dashboard = one story.** Do not mix unrelated metrics.
- **Max 5 KPIs, 2 charts, 1 table.** More than this and the dashboard becomes noisy.
- **Every section has independent loading.** Each `useSQLQuery` manages its own `isLoading` state.
- **Pre-aggregate in SQL, not JavaScript.** The component renders values; it does not compute them.
- **Use `N()` for ALL numeric values.** Query results return `unknown` types. Forgetting `N()` produces `NaN`.
- **Format dates in SQL with `strftime()`.** Never use `new Date()` or date parsing in JavaScript.
- **Use fully qualified table names.** Always `"database"."schema"."table"`.
- **No Tailwind bracket syntax.** Use inline `style` for custom values.
- **Background `#f8f8f8`, no card borders, no card shadows.**
- **Default export required.** Every Dive must have `export default function`.

---

## Common Mistakes

1. **Too many charts.** The dashboard becomes noisy and loses focus. Limit to 2 charts maximum. If you need more, build a second dashboard.

2. **One giant query instead of separate queries per section.** Each section should have its own `useSQLQuery` call. One query for everything means one loading state for everything -- the dashboard feels slow and errors cascade.

3. **Formatting and computing in JavaScript instead of SQL.** Compute sums, averages, ratios, and date formatting in SQL. The React component only renders the pre-computed values.

4. **Inconsistent colors across charts.** Define `COLORS` once and use the same array for every chart. Do not pick ad-hoc colors.

5. **Missing loading states.** Every section needs its own loading skeleton or spinner. A blank section while data loads looks broken.

6. **Forgetting the `N()` helper.** Query values are `unknown`. Without `N()`, numeric operations return `NaN` and charts render blank.

7. **Parsing dates in JavaScript.** Use `strftime()` in SQL. JavaScript `new Date()` parsing is unreliable and causes timezone bugs.

8. **Not guarding data with `Array.isArray`.** Calling `.map()` on undefined during the loading phase crashes the entire Dive.

9. **Using Tailwind bracket syntax.** `w-[200px]` and `text-[#333]` do not work in Dives. Use inline `style` instead.

10. **Card borders and shadows.** The design system uses a flat `#f8f8f8` background with no containers. Do not wrap sections in bordered cards.

---

## Related Skills

- `explore` -- Discover databases, tables, columns, and data shares.
- `query` -- Execute and optimize analytical SQL queries against MotherDuck.
- `create-dive` -- Visualization mechanics: useSQLQuery, Recharts, Tailwind, loading states.
- `duckdb-sql` -- DuckDB SQL syntax reference and function lookup.

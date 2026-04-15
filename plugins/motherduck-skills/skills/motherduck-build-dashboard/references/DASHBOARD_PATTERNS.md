# Dashboard Patterns

Copy-pasteable dashboard templates. Each is a complete Dive component with proper imports, independent loading states, `N()` helper, and the standard color palette. Replace placeholder table names with your actual fully qualified names.

---

## 1. Sales Dashboard

KPIs: Total Revenue, Order Count, Avg Order Value, Customer Count. Charts: Monthly Revenue (Line), Revenue by Category (Bar). Table: Top 10 Products.

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Loader2 } from "lucide-react";

const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function SalesDashboard() {
  const { data: kpiData, isLoading: kpiLoading, isError: kpiError, error: kpiMsg } = useSQLQuery(`
    SELECT SUM(revenue) AS total_revenue, COUNT(DISTINCT order_id) AS order_count,
           ROUND(AVG(revenue), 2) AS avg_order_value, COUNT(DISTINCT customer_id) AS customer_count
    FROM "my_db"."main"."orders"
  `);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];
  const { data: trendData, isLoading: trendLoading } = useSQLQuery(`
    SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month, SUM(revenue) AS revenue
    FROM "my_db"."main"."orders" GROUP BY 1 ORDER BY 1
  `);
  const trendRows = Array.isArray(trendData) ? trendData : [];
  const { data: catData, isLoading: catLoading } = useSQLQuery(`
    SELECT category, SUM(revenue) AS revenue
    FROM "my_db"."main"."order_items" GROUP BY 1 ORDER BY 2 DESC LIMIT 8
  `);
  const catRows = Array.isArray(catData) ? catData : [];
  const { data: detailData, isLoading: detailLoading } = useSQLQuery(`
    SELECT product_name, category, SUM(revenue) AS revenue, COUNT(*) AS orders
    FROM "my_db"."main"."order_items" GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10
  `);
  const detailRows = Array.isArray(detailData) ? detailData : [];

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
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-8 mb-10">
        <KPI label="Total Revenue" prefix="$" value={`${(N(kpiRows[0]?.total_revenue) / 1000).toFixed(0)}K`} />
        <KPI label="Order Count" value={N(kpiRows[0]?.order_count).toLocaleString()} />
        <KPI label="Avg Order Value" prefix="$" value={N(kpiRows[0]?.avg_order_value).toFixed(2)} />
        <KPI label="Customers" value={N(kpiRows[0]?.customer_count).toLocaleString()} />
      </div>
      {kpiError && (
        <p className="text-sm mb-4" style={{ color: "#bd4e35" }}>
          Failed to load KPIs: {kpiMsg?.message || "Unknown error"}
        </p>
      )}
      {/* Chart 1: Monthly Revenue Trend */}
      <div className="mb-10">
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
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
              <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
              <Line type="monotone" dataKey="revenue" stroke={COLORS[0]} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Chart 2: Revenue by Category */}
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
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`} />
              <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
              <Bar dataKey="revenue" fill={COLORS[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Table: Top 10 Products by Revenue */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Top Products by Revenue</h2>
        {detailLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold" style={{ color: "#231f20" }}>Product</th>
                  <th className="text-left py-3 font-semibold" style={{ color: "#231f20" }}>Category</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Revenue</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Orders</th>
                </tr>
              </thead>
              <tbody>
                {detailRows.map((row, i) => (
                  <tr key={i} className="border-b border-gray-200"
                      style={{ backgroundColor: i % 2 === 0 ? "transparent" : "#f0f0f0" }}>
                    <td className="py-3" style={{ color: "#231f20" }}>{row.product_name}</td>
                    <td className="py-3" style={{ color: "#6a6a6a" }}>{row.category}</td>
                    <td className="text-right py-3" style={{ color: "#231f20" }}>
                      ${N(row.revenue).toLocaleString()}
                    </td>
                    <td className="text-right py-3" style={{ color: "#6a6a6a" }}>
                      {N(row.orders).toLocaleString()}
                    </td>
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

## 2. Product Analytics Dashboard

KPIs: Active Users, Sessions, Avg Session Duration, Conversion Rate. Charts: Daily Active Users (Area), Feature Usage (Bar). Table: Top Pages.

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Loader2 } from "lucide-react";

const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function ProductAnalyticsDashboard() {
  const { data: kpiData, isLoading: kpiLoading, isError: kpiError, error: kpiMsg } = useSQLQuery(`
    SELECT COUNT(DISTINCT user_id) AS active_users, COUNT(DISTINCT session_id) AS total_sessions,
           ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_session_min,
           ROUND(100.0 * SUM(CASE WHEN converted = true THEN 1 ELSE 0 END) / COUNT(*), 1) AS conversion_rate
    FROM "product_db"."main"."sessions"
    WHERE session_start >= CURRENT_DATE - INTERVAL 30 DAY
  `);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];
  const { data: dauData, isLoading: dauLoading } = useSQLQuery(`
    SELECT strftime(date_trunc('day', session_start), '%Y-%m-%d') AS day,
           COUNT(DISTINCT user_id) AS active_users
    FROM "product_db"."main"."sessions"
    WHERE session_start >= CURRENT_DATE - INTERVAL 30 DAY
    GROUP BY 1 ORDER BY 1
  `);
  const dauRows = Array.isArray(dauData) ? dauData : [];
  const { data: featureData, isLoading: featureLoading } = useSQLQuery(`
    SELECT feature_name, COUNT(*) AS usage_count
    FROM "product_db"."main"."feature_events"
    WHERE event_time >= CURRENT_DATE - INTERVAL 30 DAY
    GROUP BY 1 ORDER BY 2 DESC LIMIT 8
  `);
  const featureRows = Array.isArray(featureData) ? featureData : [];
  const { data: pageData, isLoading: pageLoading } = useSQLQuery(`
    SELECT page_path, COUNT(*) AS views, COUNT(DISTINCT user_id) AS unique_visitors
    FROM "product_db"."main"."page_views"
    WHERE view_time >= CURRENT_DATE - INTERVAL 30 DAY
    GROUP BY 1 ORDER BY 2 DESC LIMIT 10
  `);
  const pageRows = Array.isArray(pageData) ? pageData : [];
  const KPI = ({ label, value, suffix = "" }: {
    label: string; value: string; suffix?: string;
  }) => (
    <div>
      <p className="text-sm mb-1" style={{ color: "#6a6a6a" }}>{label}</p>
      {kpiLoading ? (
        <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
      ) : (
        <p className="text-5xl font-bold" style={{ color: "#231f20" }}>{value}{suffix}</p>
      )}
    </div>
  );

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      <h1 className="text-2xl font-bold mb-8" style={{ color: "#231f20" }}>Product Analytics</h1>
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-8 mb-10">
        <KPI label="Active Users (30d)" value={N(kpiRows[0]?.active_users).toLocaleString()} />
        <KPI label="Sessions" value={N(kpiRows[0]?.total_sessions).toLocaleString()} />
        <KPI label="Avg Session Duration" value={N(kpiRows[0]?.avg_session_min).toFixed(1)} suffix=" min" />
        <KPI label="Conversion Rate" value={N(kpiRows[0]?.conversion_rate).toFixed(1)} suffix="%" />
      </div>
      {kpiError && (
        <p className="text-sm mb-4" style={{ color: "#bd4e35" }}>
          Failed to load KPIs: {kpiMsg?.message || "Unknown error"}
        </p>
      )}
      {/* Chart 1: Daily Active Users Trend */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Daily Active Users</h2>
        {dauLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={dauRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="active_users"
                stroke={COLORS[0]}
                fill={COLORS[0]}
                fillOpacity={0.15}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Chart 2: Feature Usage Breakdown */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Feature Usage</h2>
        {featureLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={featureRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="feature_name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="usage_count" fill={COLORS[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Table: Top Pages by Views */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Top Pages</h2>
        {pageLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold" style={{ color: "#231f20" }}>Page</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Views</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Unique Visitors</th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row, i) => (
                  <tr key={i} className="border-b border-gray-200"
                      style={{ backgroundColor: i % 2 === 0 ? "transparent" : "#f0f0f0" }}>
                    <td className="py-3" style={{ color: "#231f20" }}>{row.page_path}</td>
                    <td className="text-right py-3" style={{ color: "#231f20" }}>
                      {N(row.views).toLocaleString()}
                    </td>
                    <td className="text-right py-3" style={{ color: "#6a6a6a" }}>
                      {N(row.unique_visitors).toLocaleString()}
                    </td>
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

## 3. Operational Metrics Dashboard

KPIs: Total Requests, Error Rate, P95 Latency, Uptime. Charts: Request Volume (Area), Error Rate by Endpoint (Bar). Table: Slowest Endpoints.

```tsx
import { useSQLQuery } from "@motherduck/react-sql-query";
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { Loader2 } from "lucide-react";

const N = (v: unknown): number => (v != null ? Number(v) : 0);
const COLORS = ["#0777b3", "#bd4e35", "#2d7a00", "#e18727", "#638CAD", "#adadad"];

export default function OperationalMetricsDashboard() {
  const { data: kpiData, isLoading: kpiLoading, isError: kpiError, error: kpiMsg } = useSQLQuery(`
    SELECT COUNT(*) AS total_requests,
           ROUND(100.0 * SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) / COUNT(*), 2) AS error_rate,
           ROUND(quantile_cont(latency_ms, 0.95), 0) AS p95_latency_ms,
           ROUND(100.0 * SUM(CASE WHEN status_code < 500 THEN 1 ELSE 0 END) / COUNT(*), 2) AS uptime_pct
    FROM "ops_db"."main"."requests" WHERE request_time >= CURRENT_DATE - INTERVAL 24 HOUR
  `);
  const kpiRows = Array.isArray(kpiData) ? kpiData : [];
  const { data: volumeData, isLoading: volumeLoading } = useSQLQuery(`
    SELECT strftime(date_trunc('hour', request_time), '%Y-%m-%d %H:00') AS hour, COUNT(*) AS requests
    FROM "ops_db"."main"."requests"
    WHERE request_time >= CURRENT_DATE - INTERVAL 24 HOUR
    GROUP BY 1 ORDER BY 1
  `);
  const volumeRows = Array.isArray(volumeData) ? volumeData : [];
  const { data: errorData, isLoading: errorLoading } = useSQLQuery(`
    SELECT endpoint,
           ROUND(100.0 * SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) / COUNT(*), 2) AS error_rate
    FROM "ops_db"."main"."requests"
    WHERE request_time >= CURRENT_DATE - INTERVAL 24 HOUR
    GROUP BY 1 HAVING COUNT(*) >= 10 ORDER BY 2 DESC LIMIT 8
  `);
  const errorRows = Array.isArray(errorData) ? errorData : [];
  const { data: slowData, isLoading: slowLoading } = useSQLQuery(`
    SELECT endpoint, COUNT(*) AS requests, ROUND(AVG(latency_ms), 0) AS avg_latency_ms,
           ROUND(quantile_cont(latency_ms, 0.95), 0) AS p95_latency_ms,
           ROUND(quantile_cont(latency_ms, 0.99), 0) AS p99_latency_ms
    FROM "ops_db"."main"."requests"
    WHERE request_time >= CURRENT_DATE - INTERVAL 24 HOUR
    GROUP BY 1 HAVING COUNT(*) >= 10 ORDER BY 4 DESC LIMIT 10
  `);
  const slowRows = Array.isArray(slowData) ? slowData : [];
  const KPI = ({ label, value, suffix = "" }: {
    label: string; value: string; suffix?: string;
  }) => (
    <div>
      <p className="text-sm mb-1" style={{ color: "#6a6a6a" }}>{label}</p>
      {kpiLoading ? (
        <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
      ) : (
        <p className="text-5xl font-bold" style={{ color: "#231f20" }}>{value}{suffix}</p>
      )}
    </div>
  );

  const errorRateColor = (rate: number): string => {
    if (rate >= 5) return "#bd4e35";
    if (rate >= 1) return "#e18727";
    return "#2d7a00";
  };

  return (
    <div className="p-8 min-h-screen" style={{ backgroundColor: "#f8f8f8" }}>
      <h1 className="text-2xl font-bold mb-8" style={{ color: "#231f20" }}>Operational Metrics</h1>
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-8 mb-10">
        <KPI label="Total Requests (24h)" value={N(kpiRows[0]?.total_requests).toLocaleString()} />
        <div>
          <p className="text-sm mb-1" style={{ color: "#6a6a6a" }}>Error Rate</p>
          {kpiLoading ? (
            <div className="h-12 w-24 bg-gray-200 animate-pulse rounded" />
          ) : (
            <p className="text-5xl font-bold"
               style={{ color: errorRateColor(N(kpiRows[0]?.error_rate)) }}>
              {N(kpiRows[0]?.error_rate).toFixed(2)}%
            </p>
          )}
        </div>
        <KPI label="P95 Latency" value={N(kpiRows[0]?.p95_latency_ms).toLocaleString()} suffix=" ms" />
        <KPI label="Uptime" value={N(kpiRows[0]?.uptime_pct).toFixed(2)} suffix="%" />
      </div>
      {kpiError && (
        <p className="text-sm mb-4" style={{ color: "#bd4e35" }}>
          Failed to load KPIs: {kpiMsg?.message || "Unknown error"}
        </p>
      )}
      {/* Chart 1: Request Volume Over Time */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Request Volume (Hourly)</h2>
        {volumeLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={volumeRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="requests"
                stroke={COLORS[0]}
                fill={COLORS[0]}
                fillOpacity={0.15}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Chart 2: Error Rate by Endpoint */}
      <div className="mb-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Error Rate by Endpoint</h2>
        {errorLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin" size={32} style={{ color: "#0777b3" }} />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={errorRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="endpoint" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(value: number) => `${value}%`} />
              <Bar dataKey="error_rate" fill={COLORS[1]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {/* Table: Slowest Endpoints */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: "#231f20" }}>Slowest Endpoints</h2>
        {slowLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 animate-pulse rounded" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 font-semibold" style={{ color: "#231f20" }}>Endpoint</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Requests</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>Avg Latency</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>P95 Latency</th>
                  <th className="text-right py-3 font-semibold" style={{ color: "#231f20" }}>P99 Latency</th>
                </tr>
              </thead>
              <tbody>
                {slowRows.map((row, i) => (
                  <tr key={i} className="border-b border-gray-200"
                      style={{ backgroundColor: i % 2 === 0 ? "transparent" : "#f0f0f0" }}>
                    <td className="py-3" style={{ color: "#231f20" }}>{row.endpoint}</td>
                    <td className="text-right py-3" style={{ color: "#6a6a6a" }}>
                      {N(row.requests).toLocaleString()}
                    </td>
                    <td className="text-right py-3" style={{ color: "#231f20" }}>
                      {N(row.avg_latency_ms).toLocaleString()} ms
                    </td>
                    <td className="text-right py-3" style={{ color: "#231f20" }}>
                      {N(row.p95_latency_ms).toLocaleString()} ms
                    </td>
                    <td className="text-right py-3"
                        style={{ color: N(row.p99_latency_ms) > 1000 ? "#bd4e35" : "#231f20" }}>
                      {N(row.p99_latency_ms).toLocaleString()} ms
                    </td>
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

---

## Adapting Templates

- **Replace table names** with your actual fully qualified names (`"db"."schema"."table"`).
- **Replace column names** to match your schema. Use `motherduck-explore` to discover columns.
- **Adjust aggregations** to match your data (e.g., `SUM(amount)` vs. `SUM(quantity * unit_price)`).
- **Adjust date granularity**: change `date_trunc('month', ...)` to `'day'`, `'week'`, `'hour'`, or `'quarter'`.
- **Adjust time windows**: change `INTERVAL 30 DAY` to match your reporting period.

All templates share: one `useSQLQuery` per section, `N()` and `COLORS` at file top, `Array.isArray` guards, per-section loading states, `export default function`, `#f8f8f8` background, no card borders.

| Scenario | Template |
|---|---|
| E-commerce, revenue, order analytics | Sales Dashboard |
| SaaS product, user engagement, features | Product Analytics Dashboard |
| API monitoring, infrastructure, SRE | Operational Metrics Dashboard |

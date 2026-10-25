// Feature-complete Dive starter. Read the current `get_dive_guide` first; it owns the
// runtime contract. Replace the database, tables, and columns with the real schema,
// and delete any section the Dive does not need.
//
// What this template turns on by default:
// - layout that reflows from ~320 px to wide panes (2x2 KPIs on narrow, one row on wide)
// - light/dark theme from the viewer's system preference, applied with inline styles
// - filters in useDiveState so they survive refresh and travel with a shared link
// - per-section loading skeleton, empty state, and error message
// - a "data as of" freshness line
// - CSV export of the detail table from a click
// - an optional write-back button that runs a Flight and follows the run
import { useEffect, useMemo, useState } from "react";
import { useDiveState, useFlightRun, useRunFlight, useSQLQuery } from "@motherduck/react-sql-query";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, Moon, RefreshCw, Sun } from "lucide-react";

export const REQUIRED_DATABASES = [
  // Prefer an existing share of the database for a Dive other people will open.
  { type: "database", path: "md:analytics", alias: "analytics" },
];

// Set to a Flight UUID to show the refresh button; null hides it.
const REFRESH_FLIGHT_ID: string | null = null;

const THEMES = {
  light: { canvas: "#f8f8f8", text: "#231f20", muted: "#6a6a6a", grid: "#e6e6e6", line: "#0777b3", skeleton: "#e9e9e9", control: "#ffffff", border: "#d6d6d6", danger: "#bc1200" },
  dark: { canvas: "#15191e", text: "#eef1f4", muted: "#a3adb8", grid: "#2b333c", line: "#5aa9e0", skeleton: "#252c34", control: "#1d232a", border: "#3a434d", danger: "#ff8a7a" },
};
type Theme = typeof THEMES.light;

const PERIODS = { "30d": 30, "90d": 90, "365d": 365 } as const;
type Period = keyof typeof PERIODS;

const N = (value: unknown): number => (value == null ? 0 : Number(value));
const money = (value: number) => value.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const rowsOf = (query: { data?: unknown }) => (Array.isArray(query.data) ? query.data : []);

function prefersDark(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-color-scheme: dark)").matches;
}

function Skeleton({ theme, height }: { theme: Theme; height: number }) {
  return <div className="animate-pulse rounded" style={{ height, background: theme.skeleton }} />;
}

function SectionState({ query, theme, height, empty, children }: {
  query: { isLoading?: boolean; isError?: boolean; error?: unknown; data?: unknown };
  theme: Theme; height: number; empty: string; children: React.ReactNode;
}) {
  if (query.isLoading) return <Skeleton theme={theme} height={height} />;
  if (query.isError) return <p role="alert" className="text-sm" style={{ color: theme.danger }}>Could not load: {String(query.error)}</p>;
  if (rowsOf(query).length === 0) return <p className="text-sm" style={{ color: theme.muted }}>{empty}</p>;
  return <>{children}</>;
}

function Control({ theme, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { theme: Theme }) {
  // The runtime strips default button styles; give every control a visible shape and focus ring.
  return (
    <button
      {...props}
      className="inline-flex h-11 items-center gap-2 rounded border px-3 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50"
      style={{ background: theme.control, color: theme.text, borderColor: theme.border }}
    />
  );
}

export default function RevenueDive() {
  const [dark, setDark] = useState<boolean>(prefersDark());
  const theme = dark ? THEMES.dark : THEMES.light;
  const [period, setPeriod] = useDiveState<Period>("period", "90d");
  const days = PERIODS[period] ?? 90;

  const kpis = useSQLQuery(`
    SELECT SUM(amount) AS revenue, COUNT(*) AS orders, COUNT(DISTINCT customer_id) AS customers,
           SUM(amount) / NULLIF(COUNT(*), 0) AS avg_order
    FROM "analytics"."main"."orders"
    WHERE order_date >= current_date - INTERVAL ${days} DAY
  `);
  const trend = useSQLQuery(`
    SELECT strftime(spine.day, '%Y-%m-%d') AS day, COALESCE(SUM(o.amount), 0) AS revenue
    FROM generate_series(current_date - INTERVAL ${days} DAY, current_date, INTERVAL 1 DAY) AS spine(day)
    LEFT JOIN "analytics"."main"."orders" AS o ON o.order_date = spine.day::DATE
    GROUP BY spine.day ORDER BY spine.day
  `);
  const top = useSQLQuery(`
    SELECT product_name, SUM(amount) AS revenue, COUNT(*) AS orders
    FROM "analytics"."main"."orders"
    WHERE order_date >= current_date - INTERVAL ${days} DAY
    GROUP BY product_name ORDER BY revenue DESC LIMIT 7
  `);
  const freshness = useSQLQuery(`
    SELECT strftime(MAX(order_date), '%Y-%m-%d') AS as_of FROM "analytics"."main"."orders"
  `);

  const k = rowsOf(kpis)[0] ?? {};
  const kpiItems = [
    { label: "Revenue", value: money(N(k.revenue)) },
    { label: "Orders", value: N(k.orders).toLocaleString() },
    { label: "Customers", value: N(k.customers).toLocaleString() },
    { label: "Avg order", value: money(N(k.avg_order)) },
  ];
  const trendData = useMemo(() => rowsOf(trend).map((r) => ({ day: String(r.day), revenue: N(r.revenue) })), [trend.data]);
  const topRows = rowsOf(top).map((r) => ({ product: String(r.product_name), revenue: N(r.revenue), orders: N(r.orders) }));
  const asOf = String(rowsOf(freshness)[0]?.as_of ?? "");

  const [exportError, setExportError] = useState<string | null>(null);
  async function exportTop() {
    try {
      setExportError(null);
      await top.exportAs({ format: "csv", title: "Top products", filename: "top-products" });
    } catch (e) {
      setExportError(String(e));
    }
  }

  return (
    <main className="min-h-screen p-4 md:p-6" style={{ background: theme.canvas, color: theme.text }}>
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Revenue overview</h1>
          <p className="text-sm" style={{ color: theme.muted }}>
            Last {days} days{asOf ? ` · data as of ${asOf}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Period and display">
          {(Object.keys(PERIODS) as Period[]).map((p) => (
            <Control key={p} theme={theme} aria-pressed={p === period} onClick={() => setPeriod(p)}>
              {p}
            </Control>
          ))}
          <Control theme={theme} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"} onClick={() => setDark(!dark)}>
            {dark ? <Sun size={16} /> : <Moon size={16} />}
            <span className="sr-only md:not-sr-only">{dark ? "Light" : "Dark"}</span>
          </Control>
          {REFRESH_FLIGHT_ID && <RefreshButton flightId={REFRESH_FLIGHT_ID} theme={theme} onDone={() => { kpis.refetch(); trend.refetch(); top.refetch(); freshness.refetch(); }} />}
        </div>
      </header>

      <section aria-label="Key metrics" className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        {kpiItems.map((item) => (
          <div key={item.label}>
            {kpis.isLoading ? <Skeleton theme={theme} height={48} /> : <p className="text-3xl font-bold md:text-4xl">{kpis.isError ? "–" : item.value}</p>}
            <p className="text-sm" style={{ color: theme.muted }}>{item.label}</p>
          </div>
        ))}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <section aria-label="Daily revenue" className="lg:col-span-2">
          <h2 className="mb-2 text-sm font-semibold">Daily revenue (USD)</h2>
          <SectionState query={trend} theme={theme} height={240} empty="No orders in this period.">
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trendData} margin={{ left: 4, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} />
                <XAxis dataKey="day" fontSize={11} stroke={theme.muted} minTickGap={24} />
                <YAxis fontSize={11} stroke={theme.muted} tickFormatter={(v) => `${Math.round(N(v) / 1000)}K`} width={40} />
                <Tooltip formatter={(v) => money(N(v))} contentStyle={{ background: theme.control, borderColor: theme.border, color: theme.text }} />
                <Line type="linear" dataKey="revenue" stroke={theme.line} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </SectionState>
        </section>

        <section aria-label="Top products">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Top products</h2>
            <Control theme={theme} onClick={exportTop} disabled={top.isLoading}>
              <Download size={16} /> CSV
            </Control>
          </div>
          {exportError && <p role="alert" className="text-sm" style={{ color: theme.danger }}>{exportError}</p>}
          <SectionState query={top} theme={theme} height={240} empty="No products sold in this period.">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ color: theme.muted }}>
                    <th className="py-1 text-left font-normal">Product</th>
                    <th className="py-1 text-right font-normal">Revenue</th>
                    <th className="py-1 text-right font-normal">Orders</th>
                  </tr>
                </thead>
                <tbody>
                  {topRows.map((r) => (
                    <tr key={r.product} className="border-t" style={{ borderColor: theme.grid }}>
                      <td className="py-1 pr-2">{r.product}</td>
                      <td className="py-1 text-right tabular-nums">{money(r.revenue)}</td>
                      <td className="py-1 text-right tabular-nums">{r.orders.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionState>
        </section>
      </div>
    </main>
  );
}

function RefreshButton({ flightId, theme, onDone }: { flightId: string; theme: Theme; onDone: () => void }) {
  const start = useRunFlight(flightId);
  const run = useFlightRun(flightId, start.data?.runNumber, {
    onFinished: (finished) => {
      if (finished.status === "SUCCEEDED") onDone();
    },
  });
  const busy = start.isPending || run.isChecking;
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    if (run.isFinished) setMessage(run.status === "SUCCEEDED" ? null : "The refresh did not finish.");
  }, [run.isFinished, run.status]);

  return (
    <>
      <Control theme={theme} disabled={busy} onClick={() => start.run({})}>
        <RefreshCw size={16} className={busy ? "animate-spin" : ""} /> {busy ? "Refreshing" : "Refresh"}
      </Control>
      {(message || start.error || run.error) && (
        <p role="alert" className="w-full text-sm" style={{ color: theme.danger }}>
          {message ?? `Could not ${start.error ? "start" : "check"} the refresh: ${(start.error ?? run.error)?.message}`}
        </p>
      )}
    </>
  );
}

export {};
declare const process: { env: Record<string, string | undefined> };

type OrderRow = {
  order_id: number;
  order_date: string;
  category: string;
  customer_id: number;
  revenue: number;
};

function normalizeMetadataValue(value: string | undefined, fallback: string): string {
  const raw = (value ?? "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-._]+|[-._]+$/g, "");
  return normalized || fallback;
}

function buildUseCaseUserAgent(): string {
  const harness = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_HARNESS, "unknown");
  const llm = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_LLM, "unknown");
  return `agent-skills/2.2.0(harness-${harness};llm-${llm})`;
}

const orders: OrderRow[] = [
  { order_id: 1, order_date: "2026-01-03", category: "Database", customer_id: 101, revenue: 1200.0 },
  { order_id: 2, order_date: "2026-01-07", category: "Compute", customer_id: 102, revenue: 800.0 },
  { order_id: 3, order_date: "2026-02-11", category: "Database", customer_id: 101, revenue: 1600.0 },
  { order_id: 4, order_date: "2026-02-21", category: "Sharing", customer_id: 103, revenue: 400.0 },
  { order_id: 5, order_date: "2026-03-03", category: "Compute", customer_id: 104, revenue: 2200.0 },
  { order_id: 6, order_date: "2026-03-18", category: "Database", customer_id: 105, revenue: 900.0 },
];

const totalRevenue = orders.reduce((sum, row) => sum + row.revenue, 0);
const orderCount = new Set(orders.map((row) => row.order_id)).size;
const customerCount = new Set(orders.map((row) => row.customer_id)).size;

const trendMap = new Map<string, number>();
for (const row of orders) {
  const month = row.order_date.slice(0, 7);
  trendMap.set(month, (trendMap.get(month) ?? 0) + row.revenue);
}
const trend = Array.from(trendMap.entries())
  .map(([month, revenue]) => ({ month, revenue }))
  .sort((a, b) => a.month.localeCompare(b.month));

const breakdownMap = new Map<string, number>();
for (const row of orders) {
  breakdownMap.set(row.category, (breakdownMap.get(row.category) ?? 0) + row.revenue);
}
const breakdown = Array.from(breakdownMap.entries())
  .map(([category, revenue]) => ({ category, revenue }))
  .sort((a, b) => b.revenue - a.revenue);

const detail = [...orders]
  .sort((a, b) => b.order_date.localeCompare(a.order_date))
  .slice(0, 5)
  .map(({ order_date, category, revenue }) => ({ order_date, category, revenue }));

const result = {
  backend: {
    mode: "typescript-companion",
    databases: { analytics: "analytics" },
    user_agent: buildUseCaseUserAgent(),
  },
  story: "Revenue and product mix",
  kpis: {
    total_revenue: totalRevenue,
    order_count: orderCount,
    customer_count: customerCount,
  },
  trend,
  breakdown,
  detail,
};

console.log(JSON.stringify(result, null, 2));

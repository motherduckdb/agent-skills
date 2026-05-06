export {};
declare const process: { env: Record<string, string | undefined> };

type RawOrder = {
  order_id: number;
  customer_id: number;
  order_date: string;
  total_amount: number;
  updated_at: string;
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

const rawRows: RawOrder[] = [
  { order_id: 1, customer_id: 101, order_date: "2026-03-01", total_amount: 120.0, updated_at: "2026-03-01T10:00:00" },
  { order_id: 1, customer_id: 101, order_date: "2026-03-01", total_amount: 120.0, updated_at: "2026-03-01T12:00:00" },
  { order_id: 2, customer_id: 102, order_date: "2026-03-02", total_amount: 75.0, updated_at: "2026-03-02T09:00:00" },
  { order_id: 3, customer_id: 103, order_date: "2026-03-03", total_amount: 210.0, updated_at: "2026-03-03T11:00:00" },
];

const latestByOrder = new Map<number, RawOrder>();
for (const row of rawRows) {
  const existing = latestByOrder.get(row.order_id);
  if (!existing || existing.updated_at < row.updated_at) {
    latestByOrder.set(row.order_id, row);
  }
}
const stagingRows = Array.from(latestByOrder.values()).sort((a, b) => a.order_id - b.order_id);

const analyticsMap = new Map<string, { order_count: number; total_revenue: number }>();
for (const row of stagingRows) {
  const current = analyticsMap.get(row.order_date) ?? { order_count: 0, total_revenue: 0 };
  current.order_count += 1;
  current.total_revenue += row.total_amount;
  analyticsMap.set(row.order_date, current);
}
const analyticsRows = Array.from(analyticsMap.entries())
  .map(([order_date, value]) => ({
    order_date,
    order_count: value.order_count,
    total_revenue: value.total_revenue,
    avg_order_value: value.total_revenue / value.order_count,
  }))
  .sort((a, b) => a.order_date.localeCompare(b.order_date));

const result = {
  backend: {
    mode: "typescript-companion",
    databases: { raw: "raw", staging: "staging", analytics: "analytics" },
    user_agent: buildUseCaseUserAgent(),
  },
  ingestion_mode: "bulk_parquet_stage",
  stages: {
    raw: [{ row_count: rawRows.length }],
    staging: [{ row_count: stagingRows.length }],
    analytics: analyticsRows,
  },
};

console.log(JSON.stringify(result, null, 2));

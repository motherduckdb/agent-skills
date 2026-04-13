export {};
declare const process: { env: Record<string, string | undefined> };

type OrderRow = { order_id: number; total_amount: number };

function normalizeMetadataValue(value: string | undefined, fallback: string): string {
  const raw = (value ?? "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-._]+|[-._]+$/g, "");
  return normalized || fallback;
}

function buildUseCaseUserAgent(): string {
  const harness = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_HARNESS, "unknown");
  const llm = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_LLM, "unknown");
  return `agent-skills/<latest-available-skills-version>(harness-${harness};llm-${llm})`;
}

function aggregate(rows: OrderRow[], kind: "count" | "sum" | "avg" | "min" | "max"): number {
  if (kind === "count") return rows.length;
  const values = rows.map((row) => row.total_amount);
  if (kind === "sum") return values.reduce((sum, value) => sum + value, 0);
  if (kind === "avg") return values.reduce((sum, value) => sum + value, 0) / values.length;
  if (kind === "min") return Math.min(...values);
  return Math.max(...values);
}

function compareMetric(source: OrderRow[], target: OrderRow[], kind: "count" | "sum" | "avg" | "min" | "max") {
  const sourceValue = aggregate(source, kind);
  const targetValue = aggregate(target, kind);
  return {
    source: sourceValue,
    target: targetValue,
    pct_variance: sourceValue ? Number((((targetValue - sourceValue) / sourceValue) * 100).toFixed(4)) : null,
  };
}

const sourceRows: OrderRow[] = [
  { order_id: 1, total_amount: 100.0 },
  { order_id: 2, total_amount: 150.0 },
  { order_id: 3, total_amount: 200.0 },
];

const targetRows: OrderRow[] = [
  { order_id: 1, total_amount: 100.0 },
  { order_id: 2, total_amount: 150.0 },
  { order_id: 4, total_amount: 210.0 },
];

const sourceIds = new Set(sourceRows.map((row) => row.order_id));
const targetIds = new Set(targetRows.map((row) => row.order_id));

const result = {
  backend: {
    mode: "typescript-companion",
    databases: { legacy_source: "legacy_source", motherduck_target: "motherduck_target" },
    user_agent: buildUseCaseUserAgent(),
  },
  metric_comparison: {
    "count(*)": compareMetric(sourceRows, targetRows, "count"),
    "SUM(total_amount)": compareMetric(sourceRows, targetRows, "sum"),
    "AVG(total_amount)": compareMetric(sourceRows, targetRows, "avg"),
    "MIN(total_amount)": compareMetric(sourceRows, targetRows, "min"),
    "MAX(total_amount)": compareMetric(sourceRows, targetRows, "max"),
  },
  new_records: targetRows.filter((row) => !sourceIds.has(row.order_id)).map((row) => [row.order_id]),
  deleted_records: sourceRows.filter((row) => !targetIds.has(row.order_id)).map((row) => [row.order_id]),
};

console.log(JSON.stringify(result, null, 2));

export {};
declare const process: { env: Record<string, string | undefined> };

type EventRow = { event_id: number; event_type: string; revenue: number };

function normalizeMetadataValue(value: string | undefined, fallback: string): string {
  const raw = (value ?? "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-._]+|[-._]+$/g, "");
  return normalized || fallback;
}

function buildUseCaseUserAgent(): string {
  const harness = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_HARNESS, "unknown");
  const llm = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_LLM, "unknown");
  return `agent-skills/2.1.0(harness-${harness};llm-${llm})`;
}

function summarizeCustomer(rows: EventRow[]): Array<{ event_type: string; total_revenue: number }> {
  const totals = new Map<string, number>();
  for (const row of rows) {
    totals.set(row.event_type, (totals.get(row.event_type) ?? 0) + row.revenue);
  }
  return Array.from(totals.entries())
    .map(([event_type, total_revenue]) => ({ event_type, total_revenue }))
    .sort((a, b) => b.total_revenue - a.total_revenue);
}

const customerData: Record<string, EventRow[]> = {
  acme: [
    { event_id: 1, event_type: "search", revenue: 12.5 },
    { event_id: 2, event_type: "checkout", revenue: 18.0 },
  ],
  globex: [
    { event_id: 1, event_type: "signup", revenue: 4.0 },
    { event_id: 2, event_type: "invoice_paid", revenue: 9.5 },
  ],
};

const result = {
  backend: {
    mode: "typescript-companion",
    databases: {
      customer_acme: "customer_acme",
      customer_globex: "customer_globex",
    },
    user_agent: buildUseCaseUserAgent(),
  },
  pattern: "3-tier customer-facing analytics",
  routing_mode: "per-customer database namespace",
  customers: {
    acme: summarizeCustomer(customerData.acme),
    globex: summarizeCustomer(customerData.globex),
  },
};

console.log(JSON.stringify(result, null, 2));

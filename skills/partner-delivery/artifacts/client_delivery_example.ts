export {};
declare const process: { env: Record<string, string | undefined> };

function normalizeMetadataValue(value: string | undefined, fallback: string): string {
  const raw = (value ?? "").trim();
  if (!raw) return fallback;
  const normalized = raw.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-._]+|[-._]+$/g, "");
  return normalized || fallback;
}

function buildUseCaseUserAgent(): string {
  const harness = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_HARNESS, "unknown");
  const llm = normalizeMetadataValue(process.env.MOTHERDUCK_AGENT_LLM, "unknown");
  return `agent-skills/1.0.0(harness-${harness};llm-${llm})`;
}

const clients = [
  { slug: "acme", database: "customer_acme", region: "us-east-1" },
  { slug: "globex", database: "customer_globex", region: "eu-central-1" },
];

const result = {
  backend: {
    mode: "typescript-companion",
    databases: {
      customer_acme: "customer_acme",
      customer_globex: "customer_globex",
    },
    user_agent: buildUseCaseUserAgent(),
  },
  delivery_pattern: "one database and service-account boundary per client",
  clients: clients.map((client) => ({
    ...client,
    tables: [{ table_name: "usage_daily" }],
  })),
};

console.log(JSON.stringify(result, null, 2));

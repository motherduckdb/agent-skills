export {};
declare const process: { env: Record<string, string | undefined> };

type AccountRow = { team: string; account_id: number; status: string; arr: number };

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

const accounts: AccountRow[] = [
  { team: "sales", account_id: 1, status: "healthy", arr: 12000.0 },
  { team: "sales", account_id: 2, status: "watch", arr: 7000.0 },
  { team: "success", account_id: 3, status: "healthy", arr: 9000.0 },
  { team: "success", account_id: 4, status: "risk", arr: 5000.0 },
];

const teamMap = new Map<string, { total_accounts: number; total_arr: number }>();
for (const row of accounts) {
  const current = teamMap.get(row.team) ?? { total_accounts: 0, total_arr: 0 };
  current.total_accounts += 1;
  current.total_arr += row.arr;
  teamMap.set(row.team, current);
}

const result = {
  backend: {
    mode: "typescript-companion",
    databases: { analytics: "analytics" },
    user_agent: buildUseCaseUserAgent(),
  },
  first_audience: "customer success",
  first_asset: 'team KPI Dive on top of "analytics"."main"."customer_health"',
  team_kpis: Array.from(teamMap.entries())
    .map(([team, value]) => ({ team, ...value }))
    .sort((a, b) => b.total_arr - a.total_arr),
};

console.log(JSON.stringify(result, null, 2));

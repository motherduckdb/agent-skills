<!-- Preserved detailed implementation guidance moved from SKILL.md so the main skill can stay concise. -->


# Partner Delivery

Use this skill when a consultancy, implementation partner, or multi-client product team is delivering MotherDuck solutions repeatedly across customer accounts. Partners often work across different industries — retail, healthcare, fintech, logistics — so client data models and schemas will differ by industry. What stays consistent is the architecture: isolation, provisioning, connection patterns, and deployment structure. This skill focuses on the repeatable infrastructure layer, not the client-specific data model.

## Source Of Truth

- Prefer current MotherDuck public docs and product pages.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first.
- Verify anything commercial, regional, or security-sensitive against live public materials before giving a definitive answer.

## Verified Delivery Defaults

The repeated repo runs point to a stable partner-delivery posture:

- standardize the isolation and provisioning pattern, not the client schema
- keep one database namespace and one credential boundary per client unless the customer has a stronger requirement
- make region choice explicit in the delivery contract
- treat client-specific ingestion or app code as add-ons around the core multi-client isolation model

## When To Use

- The user needs a repeatable architecture for several customers.
- The user is deciding how much to standardize across clients.
- The user needs region-aware deployment or sharing guidance for a client delivery model.

## Language Focus: TypeScript/Javascript and Python

- Prefer **TypeScript/Javascript** for reusable partner delivery assets in:
  - product backends
  - starter APIs
  - admin or client provisioning tools
- Prefer **Python** for:
  - implementation scripts
  - migration helpers
  - validation tooling
  - operational handoff assets
- When producing a partner-ready solution, it is often best to provide:
  - a TypeScript/Javascript app skeleton
  - Python validation or migration helpers

## TypeScript/Javascript Starter

```ts
type ClientConfig = {
  slug: string;
  database: string;
  region: "us-east-1" | "eu-central-1";
  serviceAccountEnvVar: string;
};

const clients: ClientConfig[] = [
  { slug: "acme", database: "customer_acme", region: "us-east-1", serviceAccountEnvVar: "ACME_MD_TOKEN" },
];
```

## Python Validation Starter

```python
def validate_client_database(conn, database_name: str):
    return conn.sql(f"""
        SELECT table_name
        FROM duckdb_tables()
        WHERE database_name = '{database_name}'
    """).fetchall()
```

## Delivery Principles

- Prefer structural isolation over query-time tenant filtering for serious client work.
- Standardize the architecture, not the client data itself.
- Keep credentials and sharing boundaries explicit per client.
- Use a small set of approved deployment patterns rather than inventing a new one per engagement.

## Public Product Anchors To Use

- Hypertenancy is the public MotherDuck pattern for dedicated compute per user or customer.
- MotherDuck documents service-account-driven provisioning and per-customer or per-workload isolation patterns for Hypertenancy-style applications.
- Read scaling is the public pattern for read-heavy BI and app workloads.
- Dives are shareable live workspace artifacts.
- DuckLake sharing is currently documented as read-only via shares in preview-oriented guidance.
- Shares are zero-copy and database-granularity, so partner delivery should publish curated database boundaries rather than exposing internal staging layouts.

## Recommended Workflow

1. Classify the client pattern:
   - internal analytics enablement
   - customer-facing analytics
   - pipeline and reporting
   - regional or residency-constrained deployment
2. Pick the default architecture.
3. Standardize provisioning and deployment checklists.
4. Design the industry-specific data model, schema, and output assets for their use case.

## Default Multi-Client Pattern

Use this as the default unless the client requirements force a deviation:

- one service account per client
- or one service account per workload boundary when the client has multiple blast-radius tiers
- one database namespace per client or stronger isolation boundary
- shared deployment checklist and provisioning steps
- per-client tokens and access revocation path

For customer-facing analytics with stronger isolation and performance requirements:

- pair this skill with `build-cfa-app`
- use Hypertenancy-style patterns
- add read scaling only when concurrency demands it

## What To Standardize

These are the architecture-level patterns that should be consistent across clients regardless of industry:

- connection pattern
- database provisioning and isolation model
- service account policy
- sharing model

Schemas, table structures, dashboard layouts, and Dive templates will vary by industry. Clients in different industries (e.g., retail vs. healthcare vs. fintech) have different source systems, metrics, and data models. Use `model-data` to design the right schema for each industry rather than forcing a single starter schema across all client engagements.

## When To Use Shares vs Dives vs Full Apps

- Use shares when the client team wants direct access to query data in MotherDuck or downstream tools.
- Use Dives when the client wants a live, shareable visualization inside the MotherDuck workspace.
- Use a full customer-facing app pattern when the client needs embedded analytics, product UX control, or stricter tenant-facing experience guarantees.

## What To Keep Client-Specific

- schema design and table structure (driven by client industry and use case)
- source systems and ingestion sources
- business metrics
- data contracts
- residency constraints
- dashboard and Dive templates (tailored to the client's industry domain)
- end-user UX and rollout cadence

## Region And Compliance Handling

- Verify current region availability before committing to a design.
- Keep client object storage, external buckets, and regional service-account assumptions aligned with the target MotherDuck region whenever the delivery pattern controls those choices.
- Escalate trust/compliance questions to `security-governance` patterns when they become first-order blockers.
- Treat residency, AWS PrivateLink, and formal compliance documents as plan-sensitive and current-state-sensitive topics that require live verification.

The output of this skill should be a repeatable delivery pattern plus the client-specific exceptions that still need attention.

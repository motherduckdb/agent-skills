---
name: motherduck-build-cfa-app
description: Build MotherDuck analytics into customer-facing applications with tenant isolation, backend routing, and serving APIs.
argument-hint: [app-or-tenant-scenario]
license: MIT
---

# Build a Customer-Facing Analytics App

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Default Serving Choices

- **3-tier CFA** is the default:
  - browser -> backend API -> MotherDuck
- Keep customer routing, connection selection, service-account usage, and embed-session creation on the backend.
- **Embedded Dives** are acceptable when:
  - the requirement is read-only
  - the product needs a live Dive surface shipped into an app
  - app-side policy and UX control are limited
  - a backend can create embed sessions and keep admin tokens server-side
- **DuckDB-Wasm** is acceptable only for small, browser-side, read-only workloads.
- **Single shared tenant_id filtering** is the fallback, not the recommendation.
- A filtered Share can expose a curated table/view subset to one audience, but it is not row-level tenant isolation. Different audiences need separate Shares or stronger structural boundaries.
- For embedded Dives, validate `postMessage` origin/type/payload, use `initial_state` only for JSON-serializable UI state, and keep navigation, export, and persistence policy in the host application.

## Workflow

1. Inspect the available MotherDuck server or supplied schema context.
2. Read relevant Guides, explore the actual data model, and validate the governed definitions that will back the app.
3. Choose the serving pattern:
   - 3-tier app
   - embedded Dive
   - browser-only prototype
4. Design the isolation model:
   - per customer database
   - per workload or service-account boundary
5. Define the API contract with allowlisted metrics, dimensions, filters, and customer boundaries.
6. Choose the connection path and read-scaling posture.
7. Produce the implementation plan, API contract, and rollout sequence.

Match execution to the request: answer, review, or planning work returns the requested architecture artifacts; build or change work creates the requested in-scope files or services and validates them. Ask before destructive actions, external writes not already requested, or a material expansion of scope.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.6.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- a recommended serving architecture
- the isolation model
- the connection strategy
- the first implementation slice
- the validation and rollout plan

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/CFA_IMPLEMENTATION_GUIDE.md` -- backend implementation, service accounts, routing, and read-scaling examples
- `references/CFA_ARCHITECTURE.md` -- architecture comparison, isolation model, and connection-path detail

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [customer_routing_example.py](artifacts/customer_routing_example.py)
- [customer_routing_example.ts](artifacts/customer_routing_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` -- choose the correct PG endpoint or native DuckDB path
- `motherduck-explore` -- inspect the live database and schema before choosing an architecture
- `motherduck-model-data` -- design analytics-ready per-customer tables
- `motherduck-query` -- validate serving queries and latency-sensitive aggregations
- `motherduck-load-data` -- build ingestion paths for customer-facing data refresh

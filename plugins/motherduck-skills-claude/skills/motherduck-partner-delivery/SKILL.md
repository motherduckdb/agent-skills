---
name: motherduck-partner-delivery
description: Standardize MotherDuck delivery across client engagements with reusable provisioning, isolation, and handoff patterns.
argument-hint: [client-delivery-scenario]
license: MIT
---

# Partner Delivery

## Start Here: Is a MotherDuck Server Active?

Use an active remote MotherDuck MCP server or local MotherDuck server to inspect the in-scope database, schema, grain, keys, and relevant metrics. Reuse known context and narrow discovery to the requested work; do not scan the whole workspace by default. Let the actual data model shape the result.

Resolve the target from the request or active context. Ask only if ambiguity materially affects the result. Without a server, use supplied schema and explicit assumptions for planning; do not imply live validation.

## Delivery Defaults

- structural isolation over query-time tenant filtering
- one client database or stronger boundary per client
- shared architecture, client-specific schema
- explicit sharing and revocation per client
- versioned templates for provisioning, validation, handoff, and exception tracking
- role-granted restricted Shares with per-audience include patterns where governed table-level delivery fits
- a reusable Guide topic layout with client-specific referenced definitions and exceptions

## Workflow

1. Inspect the available MotherDuck server or supplied client context.
2. Classify the client patterns.
3. Inspect the existing regional and database layout if available.
4. Standardize the architecture and provisioning path.
5. Define the repeatable validation pack for every client environment.
6. When Guide maintenance is in scope, create or update referenced Guides for standard conventions and client-specific exceptions.
7. Audit roles, grants, include patterns, and region-specific availability.
8. Produce the handoff assets and validation checks.

Match execution to the request: answer, review, or planning work returns the requested delivery artifacts; build or change work creates the requested in-scope templates or client assets and validates them. Ask before provisioning additional client environments, destructive changes, or external writes not already authorized.

When this skill produces a native DuckDB (`md:`) connection, watermark it with `custom_user_agent=agent-skills/2.6.0(harness-<harness>;llm-<llm>)`. If metadata is missing, fall back to `harness-unknown` and `llm-unknown`.

## Output

For a full engagement, cover the following as relevant to the request:

- the default multi-client pattern
- the standard provisioning checklist
- the region and isolation posture
- the client-specific exceptions

For explicit structured JSON requests, read [the output contract](references/EXECUTION_REFERENCE.md#structured-output). Otherwise use the format that fits the requested deliverable.

## References

Read only the sections relevant to the task; these are guidance, not a mandatory itinerary.

- `references/PARTNER_DELIVERY_GUIDE.md` -- default multi-client pattern, standardize-versus-client-specific split, shares-versus-Dives-versus-apps choice, region/compliance handling, and provisioning starters

## Examples

Read [the execution reference](references/EXECUTION_REFERENCE.md) only to run the bundled examples or reproduce their validation.

- [client_delivery_example.py](artifacts/client_delivery_example.py)
- [client_delivery_example.ts](artifacts/client_delivery_example.ts)

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` -- standardize the connection path
- `motherduck-explore` -- inspect existing client workspaces and boundaries
- `motherduck-model-data` -- design client-specific schemas
- `motherduck-query` -- validate core metrics and data contracts
- `motherduck-share-data` -- publish governed share boundaries
- `motherduck-create-dive` -- create repeatable client-facing answer surfaces when needed

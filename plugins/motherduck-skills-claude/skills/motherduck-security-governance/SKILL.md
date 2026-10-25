---
name: motherduck-security-governance
description: Assess or configure MotherDuck security: roles and grants, isolation, residency, compliance, and governance as code.
argument-hint: [security-question]
license: MIT
---

# Security and Governance

## Source Of Truth

- Prefer current MotherDuck public trust, security, pricing, and product documentation.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first.
- Use current SSO and data-recovery docs when the requirement involves identity-provider login, restore windows, named snapshots, or `UNDROP DATABASE`.
- Verify claims against live public materials before making compliance or commercial assertions.

## Default Posture

- Prefer service accounts for production systems, not personal tokens.
- Keep credentials in backend-controlled secrets, not browsers or hardcoded notebooks.
- Prefer structural isolation over query-time tenant filtering for serious B2B or CFA workloads.
- Treat region and residency as first-class architectural constraints that require current public confirmation.
- Be explicit about whether the boundary is a share, a Dive, a database, or a full application.
- Separate platform permissions (roles), data grants (who can attach a share), include patterns (which tables/views that share exposes), and secure views (which rows, columns, and values each consumer of that share sees).
- Secure views on shares provide row-level security, column-level security, and masking keyed on the consumer's identity or roles (plan-gated; verify current availability). For multi-tenant customer-facing products, structural isolation remains the stronger default; secure views fit internal audiences and partner or per-service-account shares.
- Flight `RUN` grants let others trigger a Flight that always executes with the owner's credentials. Review them like any privileged entry point: who holds the grant, which config the caller controls, and what the owner's token can write.
- Map AI data flows explicitly: `prompt_jev()` sends text and images to TypeSafe in the US from every region (off by default in EU regions); `prompt()` from Asia Pacific regions is served by a US endpoint; Agent Chat inference stays in the organization's geography. Admins control these on the AI Features settings page.
- Flights can process PHI only under a signed HIPAA BAA; verify the current terms before relying on it.
- Separate documented product guarantees from architectural recommendations and assumptions in the final answer.

## Workflow

1. Identify where credentials live and who administers them.
2. Define the actual isolation boundary: account, database, schema, share secure view, or query filter.
3. Determine which preset/custom roles users hold, who can read, write, share, or administer the data, and which grants actually provide access.
4. Check whether residency, compliance, or contractual guarantees are part of the requirement.
5. Use only publicly documented security anchors unless the user has current commercial documentation in hand.

## References

Read only the reference sections needed for the current task.

- Read `references/SECURITY_GOVERNANCE_PLAYBOOK.md` for public security anchors, service-account posture, residency and AI data flows, sharing boundaries, Flight run grants, governance as code, and what not to overstate

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for secure token handling and endpoint selection
- `motherduck-explore` when governance depends on what data is actually present and how it is partitioned
- `motherduck-share-data` when the design includes governed data distribution

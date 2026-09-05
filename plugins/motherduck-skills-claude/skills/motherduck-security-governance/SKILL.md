---
name: motherduck-security-governance
description: Assess MotherDuck security, permissions, isolation, residency, and compliance requirements against documented controls.
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
- Separate platform permissions (roles), data grants (who can attach a share), and include patterns (which tables/views that share exposes).
- Separate documented product guarantees from architectural recommendations and assumptions in the final answer.

## Workflow

1. Identify where credentials live and who administers them.
2. Define the actual isolation boundary: account, database, schema, or query filter.
3. Determine which preset/custom roles users hold, who can read, write, share, or administer the data, and which grants actually provide access.
4. Check whether residency, compliance, or contractual guarantees are part of the requirement.
5. Use only publicly documented security anchors unless the user has current commercial documentation in hand.

## References

Read only the reference sections needed for the current task.

- Read `references/SECURITY_GOVERNANCE_PLAYBOOK.md` for public security anchors, service-account posture, residency framing, sharing boundaries, and what not to overstate

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` for secure token handling and endpoint selection
- `motherduck-explore` when governance depends on what data is actually present and how it is partitioned
- `motherduck-share-data` when the design includes governed data distribution

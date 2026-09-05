---
name: motherduck-pricing-roi
description: Assess MotherDuck costs, plan fit, and ROI using current pricing and the workload’s compute and storage needs.
argument-hint: [workload-or-pricing-question]
license: MIT
---

# Pricing and ROI

## Source Of Truth

- Always verify current numbers, plan limits, and feature entitlements against the live public pricing page before answering.
- If the MotherDuck MCP `ask_docs_question` feature is available, use it first for pricing-related documentation lookups.
- Use the live pricing, Hypertenancy, and Trust & Security pages for exact commercial framing.

## Default Posture

- Do not hardcode pricing numbers unless you have verified them in the current turn.
- When quoting numbers, include the verification date and the public source you checked.
- For estimates and comparisons, separate storage, compute, and operational overhead. A narrow price lookup needs only the relevant verified rate and conditions.
- Map workload shape to cost shape before comparing vendors or plans.
- Treat many pricing questions as risk, predictability, or procurement questions rather than purely technical ones.
- Verify plan-sensitive entitlements such as Flight scheduling/runtime limits, custom roles, table-level security, regions, and embedded features in the current turn; do not infer them from an older release note.

## Workflow

1. Identify the workload shape, team size, and comparison baseline.
2. Determine whether the real concern is raw spend, predictability, procurement, or operational overhead.
3. Map the workload to MotherDuck cost buckets and plan posture.
4. Frame ROI in terms of systems replaced, complexity removed, and faster delivery.
5. Call out what still needs live pricing-page or sales confirmation.

## References

Read only the reference sections needed for the current task.

- Read `references/PRICING_ROI_PLAYBOOK.md` for workload-to-cost mapping, publicly safe talking points, ROI framing, and what not to promise

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-connect` when the pricing discussion depends on connection-path choices
- `motherduck-security-governance` when compliance, residency, or commercial controls affect ROI
- `motherduck-build-cfa-app` and `motherduck-build-dashboard` when the economics depend on the application architecture

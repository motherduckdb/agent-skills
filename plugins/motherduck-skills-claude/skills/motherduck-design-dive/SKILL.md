---
name: motherduck-design-dive
description: Design or improve a MotherDuck Dive’s layout, responsive behavior, themes, filters, and visual accessibility.
argument-hint: [dive-or-design-goal]
license: MIT
---

# Design a MotherDuck Dive

Use this skill for the visual system and interaction design of a Dive. Pair it with `motherduck-create-dive` for current React and `useSQLQuery` mechanics, and with `motherduck-build-dashboard` when the task also includes defining the analytical story and SQL.

## Design Defaults

For a new Dive or a full redesign, use these defaults unless the user's design requirements differ. For a scoped edit, preserve the existing visual system and check affected states.

- start at a 320 px viewport and enhance upward
- use fluid containers and responsive grids instead of fixed desktop widths
- expose a light/dark theme control with token-based chart and UI colors, using the system preference as the initial default when practical
- reserve a predictable filter surface: visible on wide screens and a drawer or sheet on narrow screens
- keep charts inside bounded, responsive containers with readable labels at every breakpoint
- use a restrained business-analytics visual language: neutral surfaces, compact hierarchy, visible axes, quiet borders, and limited decoration
- make each KPI component useful on its own with value, label, comparison context, and a small trend or progress visual when the data supports it
- keep customer variation in data, labels, logo, and theme tokens rather than changing the information architecture
- support keyboard use, visible focus, 44 px touch targets, sufficient contrast, and non-color status cues

Avoid ornamental gradients, glass effects, glowing accents, oversized hero metrics, decorative bento layouts, excessive pills, floating shapes, and prose that sounds like a marketing landing page.

## Workflow

1. Inspect the existing Dive, supplied design paper, screenshots, and live schema before proposing a layout.
2. If MotherDuck MCP is available, call `get_dive_guide` before writing Dive code and again before any save or update if the guide may have changed. Apply relevant conventions surfaced from the reserved `dives` Guide topic unless the user asks for a different direction. Use this skill for the responsive shell when generic styling examples conflict with the user's explicit design requirements.
3. Define the audience, primary decision, metric hierarchy, filter dimensions, and reuse boundary.
4. Sketch the 320 px composition first: header, filter trigger, compact one- or two-column KPI group, primary chart, supporting sections, and detail view.
5. Expand that composition into tablet and desktop grids without changing reading order.
6. Implement semantic design tokens, theme switching, reusable cards, responsive chart wrappers, and filter state.
7. Validate query correctness separately, then preview the complete Dive with loading, empty, error, long-label, and dense-data states.
8. Inspect the rendered result at affected viewports and themes. Use the full visual QA reference for a new design, broad redesign, or requested evidence handoff; a label or SQL edit does not require a new design report.

For answer, review, or planning requests, return the requested design artifact without changing a Dive. For build or redesign requests, implement and preview the in-scope Dive; save or update it only when the request includes that operation.

## Deliverable

Return the implemented change or requested design, the checks performed, and any concrete limitation. For a full design handoff, include the hierarchy, filter behavior, responsive rules, theme tokens, component boundaries, and evidence described in the visual QA reference.

Do not call a design mobile-friendly based only on responsive CSS. Report the viewports and states actually checked.

## References

Read only the reference sections needed for the current task.

- Read `references/RESPONSIVE_DIVE_DESIGN_SYSTEM.md` for the layout grid, component anatomy, theme tokens, filter model, anti-patterns, and QA checklist.
- Read `references/VISUAL_QA_PLAYBOOK.md` for the repeatable screenshot, visual inspection, iteration, and reviewer handoff loop.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-create-dive` for the current component contract, preview, save/update, and required resources
- `motherduck-build-dashboard` for the analytical story, section queries, and end-to-end dashboard workflow
- `motherduck-explore` for discovering real dimensions and filter candidates
- `motherduck-query` for validating the SQL behind each visual state

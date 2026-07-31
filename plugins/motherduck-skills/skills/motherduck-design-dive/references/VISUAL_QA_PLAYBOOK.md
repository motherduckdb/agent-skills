# Dive Visual QA Playbook

Use this loop after the SQL is correct and before saving or updating a Dive. The output is an evidence bundle that another agent or designer can inspect without recreating the run.

## 1. Prepare the Preview

1. Call `get_dive_guide` before writing Dive code.
2. Validate every visual query independently against the intended database.
3. Preview the complete Dive with live data. Keep tokens out of source, logs, screenshots, and reports.
4. Make loading, empty, and error states visible before checking the populated state.

## 2. Capture the First Pass

Use consistent viewports so comparisons remain meaningful:

| State | Viewport | Required capture |
| --- | --- | --- |
| Desktop | 1440 × 900 | light and dark |
| Narrow mobile | 320 × 720 | populated light theme and filter trigger |
| Mobile | 375 × 812 | light and dark |
| Mobile filters | 375 × 812 | drawer or sheet open |

Capture full-page PNGs with stable names such as `desktop-v1.png`, `mobile-320-v1.png`, `mobile-v1.png`, and `mobile-filter-drawer-v1.png`.

Record for every viewport:

- `document.documentElement.scrollWidth` and `clientWidth`
- full-page `scrollHeight`
- console errors and actionable warnings
- theme control behavior
- one filter interaction and the affected metrics or charts
- keyboard focus and drawer close behavior

## 3. Inspect the Images

Open the screenshots with a vision-capable inspection tool. Judge what is visible, not what the code intended.

Score each category from 1 to 5:

- information hierarchy and reading order
- density and use of space
- KPI usefulness, including embedded context visuals
- chart legibility and label density
- filter discoverability and active-filter visibility
- mobile reflow, touch targets, and horizontal overflow
- light/dark contrast and non-color cues
- consistency across components and customer-neutral reuse
- absence of ornamental or generic AI-generated styling

Write findings in severity order. Name the viewport, component, evidence, and proposed correction. Do not approve a mobile layout by shrinking the desktop canvas.

## 4. Iterate and Recapture

Fix the highest-impact structural problem first. Common examples are excessive mobile height, unreadable axes, hidden filters, rigid card widths, low-contrast chart lines, or customer-specific labels in the shared component layer.

After each meaningful change:

1. repeat the same viewport and interaction checks
2. capture `*-v2.png` or `*-final.png`
3. compare the new image with the previous one
4. confirm that the fix did not regress the other theme or viewport

Stop when there are no critical or high-severity findings and any remaining tradeoffs are documented.

## 5. Preserve the Evidence

Store one review folder per Dive, for example:

```text
output/playwright/<dive-slug>/
├── dive.tsx
├── QA_REPORT.md
├── desktop-final.png
├── desktop-dark-final.png
├── mobile-final.png
├── mobile-dark-final.png
└── mobile-filter-drawer-final.png
```

The report should include the Dive title and URL, data source, viewport measurements, interaction result, console status, first-pass findings, changes made, remaining tradeoffs, and exact evidence paths. Give the folder to reviewers so they can comment on concrete artifacts and propose the next iteration.

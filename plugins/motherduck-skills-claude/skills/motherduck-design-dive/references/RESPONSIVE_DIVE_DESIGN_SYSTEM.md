# Responsive Dive Design System

Use this reference after `motherduck-design-dive` has established the audience, decision, metrics, and filter dimensions.

## Contents

| Section | Covers |
|---|---|
| 1. Visual Direction | Restrained business-analytics style |
| 2. Responsive Layout | Mobile-first grid and reflow rules |
| 3. Filters | Persistent filter capacity across viewport sizes |
| 4. Component Anatomy | KPI, chart, and table composition |
| 5. Theme System | Light/dark tokens and chart colors |
| 6. Reuse Across Customers | Stable shell and configurable inputs |
| 7. Accessibility | Touch, keyboard, contrast, and status |
| 8. Responsive QA | Required viewports, states, and evidence |

---

## 1. Visual Direction

Aim for the useful qualities of a modern business-intelligence tool:

- compact and information-dense without feeling cramped
- neutral page background with clearly separated analytical regions
- one restrained accent plus semantic success, warning, and danger colors
- sentence-case labels and short, literal headings
- tabular numerals for metrics
- subtle borders or low-elevation shadows, not both everywhere
- visible chart scaffolding when it aids comparison
- motion only for state changes and feedback

Do not imitate a specific vendor's chrome or branding. "Power BI-style" means a practical filterable canvas and disciplined information hierarchy, not a pixel copy.

Reject these common generated-UI tells:

- gradient-filled pages or cards
- glassmorphism, glow, neon, or excessive blur
- oversized radius on every surface
- giant KPI typography that crowds out context
- decorative cards with no analytical role
- one icon per heading by default
- repeated pills for ordinary metadata
- inspirational subtitles or vague editorial copy
- layouts that look balanced only with demo-length labels

Use a 4 px spacing base. A practical scale is 4, 8, 12, 16, 24, 32, and 48 px. Default card padding should be 16 px on phones and 20–24 px on wider screens.

## 2. Responsive Layout

Preserve one reading order in the DOM. Change grid placement, not the logical sequence.

| Viewport | Canvas | Grid | Filter surface | Typical card span |
|---|---|---|---|---|
| 320–479 px | full width, 16 px gutters | 1 content column; KPI group may use 2 compact columns when values fit | toolbar button opens sheet/drawer | KPI 1–2; content full width |
| 480–767 px | full width, 20 px gutters | 2 KPI columns; content remains 1 column | toolbar button opens sheet/drawer | KPI 1–2; content full width |
| 768–1199 px | fluid, 24 px gutters | 12 columns | compact filter bar or collapsible rail | KPI 3–6; chart 6–12 |
| 1200 px and up | centered, max 1440 px, 24–32 px gutters | 12 columns | persistent 240–280 px rail or full filter bar | KPI 3; chart 6–8 |

Use these implementation rules:

- set `min-width: 0` on grid and flex children that contain charts or long text
- use `minmax(0, 1fr)` for fluid grid tracks
- give every `ResponsiveContainer` a parent with an explicit or aspect-ratio-derived height
- prefer `clamp()` for title and KPI type; do not scale body text below 14 px
- stack comparison charts before shrinking labels into illegibility
- turn wide tables into an intentional horizontal scroll region with a visible cue, or replace secondary columns with a mobile detail disclosure
- keep the primary insight above the first long scroll on a common phone
- avoid fixed widths, fixed page heights, and viewport-width units inside embedded Dives

Recommended section order:

1. compact title, freshness, and theme control
2. active-filter summary and mobile filter trigger
3. KPI components
4. primary trend or comparison
5. supporting breakdown
6. detail table or expandable records

## 3. Filters

Design the filter capacity before arranging charts.

Use one filter model across breakpoints:

- desktop: persistent rail or compact top bar
- tablet: collapsible rail or wrapping top bar
- mobile: one clearly labeled `Filters` button opening a sheet or drawer
- all sizes: active-filter count, removable summary chips, `Reset`, and explicit applied state

Keep high-frequency filters visible first: date range, primary entity, segment, and status. Put rare controls behind `More filters`.

Filter controls must:

- use the same labels and value semantics across customers
- preserve selections when the surface collapses
- expose an obvious reset path
- announce changes to assistive technology when results refresh
- distinguish "no matching rows" from query failure
- avoid a query per keystroke; debounce free-text inputs or apply them explicitly

When values are interpolated into SQL, allowlist known options or use the current safe pattern from `get_dive_guide`. Never concatenate arbitrary user input into a query.

## 4. Component Anatomy

### KPI component

Include:

- short label
- primary value
- time or population context
- comparable delta with baseline named
- 40–72 px sparkline, progress bar, or bullet chart when trend data exists
- tooltip or disclosure for non-obvious definitions

Do not show a green arrow without saying what it compares with. Do not assume "up" is good.

### Chart component

Include:

- finding-oriented or literal title
- optional one-line subtitle that adds context
- chart body in a bounded responsive wrapper
- units on axis or in the title
- legend only when series cannot be labeled directly
- accessible fallback or nearby summary for the key result
- local loading, empty, and error treatment

Reduce x-axis tick count on phones. Prefer horizontal bars for long category labels. Avoid pie charts for precise comparison or more than five categories.

### Table component

Include:

- descriptive title and row count when useful
- sortable headers only when sorting is implemented
- sticky header for long tables
- numeric alignment and consistent formatting
- truncation with an accessible full-value path
- mobile column priority or row disclosure

### Card shell

Use the card only when it communicates grouping. A page full of identical containers weakens hierarchy. Let adjacent KPI components share a group; use stronger separation for the primary chart and filter surface.

## 5. Theme System

Drive UI and chart styling from semantic CSS variables on the Dive root. Do not scatter light-theme hex values through JSX.

```tsx
const themeTokens = {
  light: {
    canvas: "#f4f6f8",
    surface: "#ffffff",
    surfaceMuted: "#eef1f4",
    text: "#18212b",
    textMuted: "#5f6b78",
    border: "#d8dee5",
    accent: "#2563eb",
    success: "#16834a",
    warning: "#a45f00",
    danger: "#c43d3d",
  },
  dark: {
    canvas: "#11161c",
    surface: "#19212a",
    surfaceMuted: "#222c37",
    text: "#f2f5f7",
    textMuted: "#aeb8c3",
    border: "#34404c",
    accent: "#79a7ff",
    success: "#58c98b",
    warning: "#efb35a",
    danger: "#ff8585",
  },
};
```

Use a three-state preference when practical: system, light, dark. Persist an explicit choice locally, but render a stable default before browser-only APIs are available. The toggle needs an accessible label and must not rely on icon shape alone.

Chart palettes need separate light and dark values with comparable perceptual separation. Keep grid lines quieter than data marks, keep tooltips on a solid surface, and verify semantic colors against both backgrounds. Never encode a category only by red versus green.

## 6. Reuse Across Customers

Keep the shell stable. Parameterize:

- title, description, and data freshness
- metric definitions and formatters
- permitted filters and default selections
- series labels and semantic colors
- optional logo and accent token
- table columns and drill-down targets

Do not parameterize the basic reading order, breakpoint model, spacing scale, loading states, or accessibility behavior per customer.

Prefer a small component vocabulary:

- `DiveShell`
- `DiveHeader`
- `FilterSurface`
- `ActiveFilters`
- `MetricGroup` and `MetricCard`
- `ChartPanel`
- `DetailTable`
- `QueryState`

Keep customer IDs and branding out of shared component names and CSS classes. Treat customer-specific SQL and labels as inputs to the stable design system.

## 7. Accessibility

- Keep interactive targets at least 44 by 44 px on touch layouts.
- Preserve a visible `:focus-visible` treatment in both themes.
- Use native buttons, labels, selects, and tables before custom substitutes.
- Keep body text at 14–16 px and avoid low-contrast muted text.
- Add text or icon-shape cues to semantic colors.
- Do not make hover the only way to reveal exact values.
- Respect reduced-motion preferences.
- Ensure drawers trap focus, close with Escape, and restore focus to their trigger.
- Give chart regions an accessible name and provide the key takeaway in text.

## 8. Responsive QA

Preview the actual implementation, not only the design intent.

Required viewport matrix:

| Width | What to verify |
|---|---|
| 320 px | no clipped controls; filter drawer; readable KPI and chart labels |
| 375 px | common phone composition and first-screen priority |
| 768 px | tablet reflow; KPI pairing; filter transition |
| 1024 px | compact desktop/tablet landscape grid |
| 1440 px | max-width, persistent filters, and balanced chart spans |

At each relevant width, check:

- light and dark themes
- loading, empty, error, and populated states
- longest realistic title, filter value, category label, and formatted number
- keyboard traversal and visible focus
- tooltip and drawer behavior
- horizontal overflow
- chart resize after filter and theme changes

Also check 200% browser zoom and the narrowest expected embedded container. A passing result has no page-level horizontal scroll, no obscured filter controls, no zero-height charts, and no theme token left with light-only contrast.

Capture the tested viewport sizes and any remaining constraint in the handoff. A generic statement such as "responsive" is not QA evidence.

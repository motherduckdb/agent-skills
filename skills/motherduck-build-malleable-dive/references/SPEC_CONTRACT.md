# Spec Contract (version 1)

The Flight writes specs; the Dive renders them. Read this when you change the engine, add a block type, or debug a page that renders wrong.

The Flight writes one row per generation to `<DB>.main.dive_specs`:

| Column | Meaning |
| --- | --- |
| `id` | spec id (UUID); the Dive selects by it |
| `request_id` | the id the Dive sent as config, so it can open its own answer |
| `kind` | `briefing` (the overview), `question` (asked in the ask bar) or `investigation` (opened from an insight) |
| `prompt`, `title` | shown in the history list |
| `created_at` | UTC |
| `status`, `error` | `ready` or `failed` and why |
| `spec` | the JSON document below |

## Document

```jsonc
{
  "version": 1,
  "id": "…", "kind": "question", "prompt": "…",
  "as_of": "2023-01-09", "generated_at": "…", "model": "…",
  "title": "Heat complaints by borough",
  "subtitle": "…",
  "headline": "One sentence with the key number",
  "summary": "2-3 sentences",
  "follow_ups": ["…", "…", "…"],     // rendered as "Ask next" buttons
  "problems": [],                      // components the compiler dropped
  "prompt_version": "04751d1f87",      // hash of every instruction and schema
  "checks": { "checked": 40, "grounded": 40, "ungrounded": [] },   // the number check
  "context": { "briefings_remembered": 3, "earlier_insights": 12, "feedback_used": 4,
               "guides": ["…"], "probes_run": 3, "probes_shown": 2 },
  // investigation pages only:
  "parent": "…",                       // id of the page the insight came from
  "parent_title": "311 briefing",
  "insight": { "title": "…", "body": "…", "question": "…" },
  "blocks": [ /* see below, in reading order */ ]
}
```

## Blocks

Common fields: `id`, `type`, `title`, `span` (4, 6, 8 or 12 of a 12-column
grid), `caption` and an optional `insight` (from the narrator), `why` (from the
planner), `about` (`definitions` from the catalog, and `why`) and `source`
(dataset, measures, dimension, window, filters, display-only SQL). A follow-up
query the analyst step ran and the narrator promoted has `probe: true`, an id
`p1` to `p3`, and its `hypothesis`.

| `type` | Data fields | Narrator fields | Viewer can switch to |
| --- | --- | --- | --- |
| `kpi` | `items[]`: `key`, `label` (with the segment when filtered), `value`, `prior`, `format`, `good`, `spark[]`, `spark_x[]`, `spark_grain`; `compare` | `caption` | metric cards, compact stats, gauges (rates only) |
| `line` | `x` (`kind: time`, `grain`), `series[]`, `data[]` | `highlight[]` (x values), `annotations[]` (`x`, `label`, `series`), `points[]` (`x`, `series`: where each marker dot sits) | area, bar, heatmap, table |
| `bar` | `x` (`kind: category`), `series[]`, `data[]` | `highlight[]` | treemap, table |
| `table` | same as bar; a series `format` of `row` reads `_format` per row | `highlight[]` | bar, when all series share a unit |
| `table` with `drivers: true` | compiled from a plan block of type `drivers`: one row per `dimension: value` with `before`, `now`, `change` and, for counts, `share` of the total change; `total` (`label`, `before`, `now`, `format`) | `highlight[]` | — |
| `heatmap` | calendar: `mode: 'calendar'` with the line shape at day grain; matrix: the line shape with one series per row | `highlight[]` | line, area, table |
| `sankey` | `nodes[]` (`name`, `side`), `links[]` (`source`, `target`, `value`), `format`, `source_label`, `target_label`, plus the flows in the bar shape | `highlight[]` | bar, table |
| `treemap` | `tree` (`name`, `children[]`) and `format`, or the bar shape; plus the groups in the bar shape | `highlight[]` | bar, table |
| `callouts` | `items[]`: `tone` (critical, warning, positive, info), `title`, `body`, `block_id`, `question` (the investigation behind the Investigate button), `continuity` (new, ongoing, worsening, improving, resolved), `refers_to`, `first_seen`, `times_seen` | — | — |
| `text` | `body` | — | — |

`series[]` entries are `{key, label, format, good?, muted?}`. A key ending in
`_prior` is the comparison value of the key before it; charts draw it in the
muted colour and tables show it as a delta badge.

The full component catalog, with every renderer a block can switch to, is
`artifacts/components.json` in `motherduck-dive-components`. The changes table also carries
`timeline: { date: 'since', title: 'x' }`, so it can render as a timeline.

Formats: `currency` (USD), `pct` (a fraction, 0.071 → 7.1%), `count`,
`number`, `delta_pct`, `text`, `row`.

## Validation

- The planner's schema only allows catalog measures and dimensions. The compiler
  drops measures from other datasets, mixed units on line and bar charts, and
  exact duplicates of an earlier component.
- The narrator's `highlight` and `annotations` are kept only when the x value
  exists in that block's data. A marker's `series` is kept only when it names a
  series of that block; otherwise the dot goes on the series that moves most at
  that period.
- The Dive renders unknown block types as "Unsupported component type", so an
  older Dive survives a newer spec.

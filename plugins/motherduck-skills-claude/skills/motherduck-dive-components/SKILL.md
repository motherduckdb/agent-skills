---
name: motherduck-dive-components
description: Build Dive UIs from a reusable React component kit (stat cards, gauges, area, heatmap, Sankey, treemap, timeline, date picker), brand themes, and custom components.
argument-hint: [component-or-theme-goal]
license: MIT
---

# MotherDuck Dive Components

A component kit for Dives, copied into the Dive as source the way shadcn/ui works: a Dive is one `.tsx` file that may import only the runtime libraries `get_dive_guide` lists, so nothing is installed. Use it when a Dive needs more than the basic charts, a consistent look across several Dives, a brand theme, or a component the kit lacks. `motherduck-create-dive` owns the Dive mechanics (runtime contract, saving, sharing, embedding, write-back); this skill owns the visual building blocks.

When MotherDuck MCP is available, call `get_dive_guide` before writing Dive code and before every `save_dive`, `update_dive`, or `edit_dive_content`.

## Start Here

1. Open `artifacts/gallery/index.html` in a browser to see every component on sample data, with each block's data behind its `</>` button. It needs no MotherDuck account.
2. Read `artifacts/components.json`: for each component, the data shape it renders, when to use it, and the other renderers it can switch to.
3. Pick components for the question, write the Dive's queries, and build blocks from the rows.

## Kit

| Path | What it holds |
| --- | --- |
| `artifacts/kit/core.tsx` | Themes, `makeTheme`, `ThemeCtx`, formatting (`N`, `fmt`, `niceTicks`), primitives (`Card`, `Badge`, `Button`, `Segmented`, `Skeleton`, `Delta`, `Sparkline`), `registerComponent`, `BlockView` |
| `artifacts/kit/blocks.tsx` | KPI row, line, bar, table, callouts, text |
| `artifacts/kit/stats.tsx` | Metric cards, compact stats, radial gauges |
| `artifacts/kit/area.tsx` | Area chart with headline value, legend toggles, crosshair |
| `artifacts/kit/heatmap.tsx` | Calendar (daily activity) and matrix heatmaps |
| `artifacts/kit/sankey.tsx` | Flows from one set of categories to another |
| `artifacts/kit/treemap.tsx` | Part-to-whole, grouped, click to zoom |
| `artifacts/kit/timeline.tsx` | Events in order |
| `artifacts/kit/datepicker.tsx` | Single date and range picker with presets (an input, not a block) |
| `artifacts/examples/funnel.tsx` | A custom component to copy |
| `artifacts/assemble.py` | Concatenates the kit, custom files, and your Dive into one `index.tsx` |

## Blocks

Every component renders a block: a plain object with `id`, `type`, `title`, and data in the shape `components.json` gives. Components never run SQL. Query with `useSQLQuery`, convert values with `N()`, build the block, and render it with `BlockView`:

```tsx
// @imports
import { useSQLQuery } from '@motherduck/react-sql-query';
// @imports-end

export const REQUIRED_DATABASES = [{ type: 'database', path: 'md:analytics', alias: 'analytics' }];

export default function DailyVisits() {
	const q = useSQLQuery(`SELECT strftime(day, '%Y-%m-%d') AS x, count(*) AS visits
	                       FROM "analytics"."main"."events" GROUP BY 1 ORDER BY 1`);
	const rows = Array.isArray(q.data) ? q.data : [];
	const block = {
		id: 'daily', type: 'heatmap', mode: 'calendar', title: 'Daily visits',
		x: { kind: 'time', grain: 'day' },
		series: [{ key: 'visits', label: 'Visits', format: 'count' }],
		data: rows.map((r: any) => ({ x: String(r.x), visits: N(r.visits) })),
	};
	return (
		<ThemeCtx.Provider value={makeTheme('motherduck')}>
			<Card title={block.title} icon={componentIcon(block.type)}>
				{q.isLoading ? <Skeleton h={140} /> : <BlockView block={block} />}
			</Card>
		</ThemeCtx.Provider>
	);
}
```

Any block can also carry narrative and context:
- `insight`: a "so what" line, rendered by `<BlockInsight>`.
- `about`: `{ definitions: [{ term, text }], why }`, which `<SourceFooter>` shows with the source.
- `probe` and `hypothesis`: mark a follow-up query.

Callout items can carry `continuity` (`new`, `ongoing`, `worsening`, `improving`, `resolved`) with `first_seen` and `times_seen`. Pass a `nav` with `rate` and `rating` to add thumbs up and down.

A `questions` block asks viewers about a date or a segment the data can't explain. Each answer is a note: `{ kind: 'date' | 'topic', x, grain?, dimension?, value?, category, note }`. Pass a `nav` with `annotate` and `noteFor` to take answers. `withNotes(block, notes)` pins notes to every block that shows that date or value, as markers on line and area charts. `<NotesLine>` lists them under a block, and `<NoteForm>` adds one from any chart.

Formats are `count`, `currency`, `pct` (a fraction), `number`, `delta_pct`, `text`, and `row` (read `_format` per row). Set `good: 'down'` on measures where lower is better, so deltas colour by meaning rather than direction.

Assemble and preview with the MotherDuck CLI:

```bash
python3 artifacts/assemble.py app.tsx -o my-dive/index.tsx --components kpi,line,heatmap
motherduck dive watch my-dive
```

Omit `--components` to include the whole kit. Before `save_dive` or `update_dive`, follow the review step that `get_dive_guide` sets for your client: when it asks you to show the final source or preview and get the user's go-ahead, do that once, unless the user already said to save without review.

## Variants

A block can render with any registered component whose `accepts(block)` takes its data: a KPI row as stats, metric cards, compact stats, or gauges; a line as area, bar, heatmap, or table; a bar as treemap or table. `variantsFor(block)` lists them. Offer the switch with `Segmented`, and keep the viewer's choice in `useDiveState`.

## Themes and Brands

`motherduck` is the default theme and follows the visual rules in `get_dive_guide`: flat, no card chrome, the MotherDuck palette. Use it unless the user asks for another look or the Dive already has one. The kit also ships `swiss` (greyscale, one red accent), `paper` (cards), `duck` (brutalist brand), and `night` (dark).

For a brand, ask for the accent colour, flat or card look, and a font, then derive a theme:

```tsx
const theme = makeTheme({ base: 'paper', name: 'Acme', accent: '#0f766e', font: 'Georgia, serif', radius: 6 });
```

Dives cannot load web fonts, so offer system font stacks. Read `references/THEMING.md` for the token list and the contrast and colour checks.

## Custom Components

When no kit component shows the data well, copy `artifacts/examples/funnel.tsx`, render only from the block with `useTheme()` tokens, and register it with `registerComponent(type, { label, icon, render, variants, accepts })`. Pass the file to `assemble.py --extra`. Read `references/CUSTOM_COMPONENTS.md` for the contract, the catalog entry, and how a Flight can plan the new component.

## Rules

- Keep SQL out of components; a block is data only.
- Run every value through `N()` before maths or charts; format dates in SQL.
- Use inline styles for colours and sizes; arbitrary Tailwind values do not resolve.
- Each kit file declares its imports between `// @imports` and `// @imports-end`; `assemble.py` merges them. Do not name a component after an icon or chart it imports (`Gauge`, `Treemap`, `Sankey`).
- After adding or changing a component, add a sample block to `artifacts/gallery/app.tsx`, rebuild the page with `python3 artifacts/gallery/build_page.py` (needs Node.js), and check it in the default theme and one other at desktop and phone width.

## References

- `references/THEMING.md` -- built-in themes, `makeTheme` tokens, asking for a brand, contrast checks
- `references/CUSTOM_COMPONENTS.md` -- writing, registering, and cataloguing a new component

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-create-dive` for the Dive runtime contract, saving, sharing, embedding, and write-back
- `motherduck-cli` for `dive watch`, `dive push`, and keeping Dive source in files
- `motherduck-query` for validating the SQL each block renders

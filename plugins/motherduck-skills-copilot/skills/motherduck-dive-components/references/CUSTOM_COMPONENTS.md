# Custom components

Add a component when the catalog has nothing that shows the data well (a funnel, a
cohort grid, a map, a bullet chart). Built-in and custom components use the same
mechanism, so a custom one gets variants, theming and the Arrange mode for free.

## 1. Write the renderer

Start from `artifacts/examples/funnel.tsx`:

```tsx
// @imports
import { Filter } from 'lucide-react';
// @imports-end

function FunnelBlock({ block }: any) {
	const t = useTheme();                       // tokens: t.text, t.muted, t.accent, t.series, t.flat, t.radius
	const s = block.series[0];
	const steps = block.data.map((d: any) => ({ label: String(d.x), v: N(d[s.key]) ?? 0 }));
	return <div style={{ color: t.text }}>{steps.length} steps</div>; // see the full file for the bars
}
```

- Props: `{ block, onJump?, nav? }`. `onJump(blockId)` scrolls to another block;
  `nav` carries page actions in a malleable Dive (Investigate). Ignore what you don't use.
- Read everything from `block`. Never run SQL in a component.
- Use theme tokens for every colour, and `t.flat` to switch between the Swiss look
  (no fills, rules, square corners) and the card look.
- `N()` every number, `fmt(value, format)` every label, `humanize()` category names.
- Empty data: render a short muted sentence, not an empty frame.
- Give charts a tooltip and an `aria-label`.

## 2. Register it

```tsx
registerComponent('funnel', {
	label: 'Funnel',            // the variant switcher's label
	icon: Filter,               // the card title's icon
	render: FunnelBlock,
	variants: ['bar', 'table'], // renderers a viewer can switch to
	accepts: (b) => b.series?.length === 1 && b.series[0].format === 'count',
	chrome: true,               // wrap in a Card (title, caption, source); false for callouts-like blocks
});
```

`accepts` decides when this renderer is offered as a variant of another block. Reuse an
existing data shape where you can (the funnel takes the bar shape), so a block can move
between your component and the built-ins.

## 3. Assemble and look at it

```sh
python3 artifacts/assemble.py artifacts/gallery/app.tsx -o gallery-dive/index.tsx --extra artifacts/examples/funnel.tsx
motherduck dive watch gallery-dive
python3 artifacts/gallery/build_page.py   # the same gallery as artifacts/gallery/index.html
```

Add a sample block to `artifacts/gallery/app.tsx`, and check it in Swiss and Paper, narrow
and wide.

## 4. Tell agents and the Flight about it

- Kit components: add an entry to `artifacts/components.json` (`type`, `file`, `kind`, `data`,
  `when`, `variants`, and `plan_rule` if the malleable Flight should plan it).
- A Flight that plans pages from these components (see `motherduck-build-malleable-dive`) reads the
  `plan_rule` entries, so give a component a `plan_rule` only when a planner can choose it from data
  alone.

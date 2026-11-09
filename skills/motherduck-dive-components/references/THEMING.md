# Theming

## Built-in themes

| Key | Look | Series | Accent |
| --- | --- | --- | --- |
| `motherduck` (default) | The `get_dive_guide` look: `#f8f8f8` page, flat, no card chrome | MotherDuck palette (`#0777b3`, `#bd4e35`, `#2d7a00`, …) | Blue `#0777b3`; green and red only for values with a good direction |
| `swiss` | White, black type, rules instead of cards, flat | Greyscale, told apart by dash patterns | Red `#e4002b`, only for emphasis: highlights, critical tone, active controls |
| `paper` | Warm grey page, white rounded cards | MotherDuck palette (`#0777b3`, `#bd4e35`, `#2d7a00`, …) | Blue `#0777b3` |
| `duck` | MotherDuck brutalist: sand page, 2 px borders, offset shadows, mono headings | Sky, coral, teal, yellow | Ink `#383838` |
| `night` | Dark | Bright palette | Blue `#58a6ff` |

## Brand themes

`makeTheme(spec)` returns a theme from a key or from a base plus tokens:

```tsx
makeTheme('motherduck');
makeTheme({ base: 'swiss', name: 'Acme', accent: '#0f766e' });
makeTheme({ base: 'paper', name: 'Acme', accent: '#0f766e', series: ['#0f766e', '#f59e0b', '#6366f1'], font: 'Georgia, serif', heading: 'Georgia, serif', radius: 6 });
```

Tokens you can set: `accent`, `highlight`, `accentSoft`, `series` (up to 6), `bg`,
`panel`, `text`, `muted`, `line`, `grid`, `font`, `heading`, `radius`, `border`,
`shadow`, `name`.

- A **flat** base keeps rules instead of cards. `swiss` also keeps series greyscale, so the
  accent marks only emphasis; use it when the brand has one strong colour. Passing `series`
  turns the greyscale off.
- A **card** base (`paper`, `night`) puts the accent first in the series palette,
  unless you pass `series`.


## Asking for a brand

Ask for:
1. The primary colour as a hex value (and a second and third if charts need several series).
2. Flat and editorial (Swiss) or cards (Paper)?
3. A font. Dives can't load web fonts or external stylesheets: use a system stack
   (`ui-sans-serif, system-ui`, `Helvetica Neue, Helvetica, Arial`, `Georgia, serif`,
   `ui-monospace, Menlo`). If the brand font is installed locally it will show for that
   viewer only.

Check before you ship:
- Text on the accent (buttons, selected dates) needs a contrast ratio of 4.5:1. White
  on very light accents fails: darken the accent or set `accent` to a darker shade and
  `highlight` to the lighter one.
- Series colours must be distinguishable in a line chart; keep 3 to 6, and avoid
  red/green pairs as the only difference.
- Positive and negative tones (`tones.positive`, `tones.critical`) mean good and bad,
  not up and down; a measure with `good: 'down'` turns green when it falls.
- Look at the gallery with the brand on: `Try a brand` in `artifacts/gallery/index.html`
  shows `makeTheme(...)` live.

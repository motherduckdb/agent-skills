# Recipe Guide

## Contents

- Write `domain.py`
- Write `app.json`
- Check the spec
- Custom components
- Gotchas

A recipe is two files in `recipes/<name>/`. Copy `artifacts/recipes/nyc-311` and replace its contents; you do not edit the template for a new domain. If a domain needs something the template lacks, change `artifacts/template/` so every recipe gets it.

## Write `domain.py`

| Name | What to put there |
| --- | --- |
| `DB` | A new database for the output, named for the data, such as `<domain>_briefing`. The Flight creates it. |
| `ATTACH` | `(alias, path)` for every source: a share URL or `md:<database>`. |
| `MARTS` | Curated tables the generator may use, as `name: SELECT …`. The Flight runs `CREATE OR REPLACE TABLE "<DB>".main.<name> AS …`. Pre-aggregate to the grain the measures need; keep event-level rows only when a measure needs `count(DISTINCT …)`. Later marts can read earlier ones. |
| `MARTS_REFRESH` | `"missing"` for static data, `"always"` for data that changes daily. Only briefing and refresh runs rebuild existing marts. |
| `ANCHOR` | `(mart, day column)` whose maximum is the default analysis date. |
| `AS_OF_DEFAULT` | `"max"` (the anchor's last day) or `"yesterday"`. |
| `COMPARES`, `DEFAULT_COMPARE` | From `none`, `previous_period`, `previous_year`. Leave out `previous_year` with less than about 14 months of data. |
| `CATALOG` | Datasets the planner may use (see below). |
| `WATCH` | 5 to 10 `("dataset.measure", "Label")` pairs for the weekly change scan. |
| `BASELINE_WEEKS` | How many first weeks of the history count as normal for the change table. |
| `BRIEFING_PLAN` | The fixed daily page: a KPI row of 3 or 4 measures, charts paired into rows of 12, a ranking table last. Block fields are those of the planner schema: `type`, `title`, `measures`, `dimension`, `series_dimension`, `window`, `compare`, `filters`, `limit`, `span`, `why`. |
| `DOMAIN_DESCRIPTION`, `AUDIENCE`, `BRIEFING_QUESTION` | One line each; they frame every prompt. |
| `DOMAIN_CONTEXT` | Facts the narrator may use only when the data supports them: definitions, seasonality, known data gaps. |
| `PLANNER_HINTS` | How to answer typical questions, and which dimension explains a moved metric. |
| `LABELS`, `ACRONYMS` | Optional display names. A qualified key such as `"assistant.sessions"` wins over a short one. |

### The catalog

```python
CATALOG = {
    "requests": {
        "label": "311",                     # prefixes ambiguous measure names
        "table": "mart_requests",
        "time": "day",                      # or "month"
        "lag_days": 0,                      # for a source that lands late
        "about": "One sentence the planner reads.",
        "dims": {"borough": ("borough", "Brooklyn, Queens, Bronx, Manhattan, Staten Island")},
        "measures": {
            "requests": ("sum(requests)", "count", "Service requests"),
            "avg_days_to_close": ("sum(resolution_hours) / nullif(sum(closed), 0) / 24", "number", "Average days to close", "down"),
        },
    },
}
```

- The planner sees only these descriptions. Write them for a model that has never seen the data, and list real values for each dimension.
- Measure formats are `count`, `currency`, `pct` (a fraction) and `number`. Add `"down"` when lower is better.
- Give each dataset the dimensions that explain why a number moves, not only those that show it: the referrer behind a channel, the descriptor behind a complaint type. Investigations and the drivers table can break a change down only by catalog dimensions.
- A placeholder bucket such as `(anonymized)` or `unknown` gets its own value, so filters can exclude it.

## Write `app.json`

```json
{
  "brand": "NYC 311",
  "tagline": "Service requests briefing",
  "placeholder": "Ask about 311 requests…",
  "theme": "motherduck",
  "db": "nyc_311_briefing",
  "flightId": "",
  "flight": { "name": "nyc-311-generative-dive" },
  "examples": ["Which agencies take longest to close requests?"]
}
```

`theme` is a kit theme key or a brand spec such as `{ "base": "paper", "name": "Acme", "accent": "#0f766e" }`. Leave `flightId` empty until the Flight is pushed. `requiredDatabases` replaces the default `md:<db>` entry when the Dive should read a share of the output database.

## Check the spec

Read a spec back with `SELECT spec FROM "<db>".main.dive_specs WHERE request_id = '<id>'` and check:

- Every KPI label is unique. When two datasets share a measure name, add a qualified `LABELS` entry.
- At least one headline number matches a hand-written query or the Dive people already use.
- The narrative quotes the right measure. A wrong label produces a confidently wrong sentence.
- No component is dominated by a placeholder bucket.
- Recent values are not cut short. Closing times, conversions and other measures that complete after the event look better or worse for the last weeks. End the marts early for static data, or say so in `DOMAIN_CONTEXT`.
- An investigation filters every block to the segment, and its drivers table names a cause.

## Custom components

Write the renderer as the `motherduck-dive-components` skill describes and put it in `recipes/<name>/components/`; `build.py` assembles every `.tsx` file there. For the planner to choose it, add a compiler in `domain.py`:

```python
def compile_funnel(c, b):
    """c is the Flight's compiler (c.q(sql, params), c.as_of); b is the validated plan block."""
    rows = c.q('SELECT step, count(*) FROM "my_db".main.mart_steps GROUP BY 1 ORDER BY min(step_order)', [])
    return {
        "x": {"key": "x", "kind": "category"},
        "series": [{"key": "v", "label": "People", "format": "count"}],
        "data": [{"x": s, "v": v} for s, v in rows],
        "source": {"dataset": "steps", "measures": b["measures"], "sql": ["…"]},
    }

CUSTOM_COMPONENTS = {
    "funnel": {"plan_rule": "funnel: people at each step of the activation journey, in order.", "compile": compile_funnel},
}
```

## Gotchas

- `prompt()` needs `json_schema := '{"name": …, "strict": true, "schema": …}'`; a bare schema returns NULL.
- `<form onSubmit>` never fires inside a Dive. Use a button's `onClick` and Enter in `onKeyDown`.
- Write timestamps as explicit UTC values; `now()::TIMESTAMP` converts in the session time zone.
- A source that lands late needs `lag_days`, or every comparison shows a false drop.
- When a rate is split by a dimension, the template picks the groups by volume. Ranking by the rate itself picks tiny groups.

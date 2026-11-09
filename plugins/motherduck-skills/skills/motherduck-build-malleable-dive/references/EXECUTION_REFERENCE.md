# Execution Reference

Read this to run the bundled example, deploy a recipe, or answer an explicit structured-output request. The NYC 311 recipe illustrates the pattern; it is not the user's dataset.

## Structured Output

If the caller explicitly asks for structured JSON, return raw JSON only with no Markdown fences or prose before/after it.
This is mainly for automated tests, regression checks, or downstream tooling that needs a stable machine-readable shape. Normal human-facing use of the skill can stay in prose unless JSON is explicitly requested.

Use this exact top-level shape when JSON is requested:

```json
{
  "summary": {},
  "assumptions": [],
  "implementation_plan": [],
  "validation_plan": [],
  "risks": []
}
```

## Run the Example Locally

The NYC 311 recipe reads `nyc.service_requests` from MotherDuck's public `sample_data` share and writes to a new `nyc_311_briefing` database. It needs `MOTHERDUCK_TOKEN` and Python with `duckdb`.

From `artifacts/`:

```bash
python3 build.py recipes/nyc-311
cd recipes/nyc-311/flight
MODE=briefing REQUEST_ID=t1 uv run --with duckdb==1.5.6 python main.py
```

The first run builds the mart from about 6.4 million source rows; it and later runs take 15 to 40 seconds. The last line prints the spec id and status. Then try a question and an investigation:

```bash
MODE=ask PROMPT="Which agencies take longest to close requests?" REQUEST_ID=t2 uv run --with duckdb==1.5.6 python main.py
MODE=investigate PARENT=<briefing spec id> PROMPT="<a question from the briefing's insights>" REQUEST_ID=t3 uv run --with duckdb==1.5.6 python main.py
```

Score the planner on the recipe's questions, then the full generation on a few of them:

```bash
python3 eval.py recipes/nyc-311 --out baseline.json
python3 eval.py recipes/nyc-311 --narrate --only 1,3,9 --baseline baseline.json
```

Record viewer feedback the way the Dive does, to test the feedback path:

```bash
MODE=feedback FEEDBACK='[{"e":"rate_insight","s":"<spec id>","t":"<insight title>","v":"up"}]' uv run --with duckdb==1.5.6 python main.py
```

Pin the `duckdb` version to the one `get_flight_guide` lists for the Flight runtime when you need local runs to match the cloud exactly.

## Deploy

```bash
motherduck flight push recipes/<name>/flight --schedule-cron "0 6 * * *" \
  --config '{"MODE":"briefing","PROMPT":"","REQUEST_ID":"","AS_OF":"","MODEL":"<model>","PARENT":"","FEEDBACK":"","BOARD":""}' \
  --max-runtime-sec 600
```

`build.py` writes `flight.metadata.json` and `dive.metadata.json` from `app.json` when they are missing; each push adds the object's id. Put the Flight id in `app.json` as `flightId`, rebuild, preview with `motherduck dive watch recipes/<name>/dive`, then `motherduck dive push recipes/<name>/dive`. Check the current `prompt()` model names in the MotherDuck AI function docs before you set `MODEL`.

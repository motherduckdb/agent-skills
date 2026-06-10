# MotherDuck Flights Reference

Condensed from the MotherDuck Flights docs (concepts, key tasks, MCP tool pages, SQL function pages) and the live `get_flight_guide` output. When MCP is available, `get_flight_guide` is the runtime source of truth; this file is the offline summary.

## Contents

| Section | Covers |
| --- | --- |
| What a Flight Is | Concept, execution model, when to use one |
| Anatomy of a Flight | Fields: name, source, requirements, token, config, secrets, schedule |
| Runtime Environment | CPU/RAM/disk, run sequence, shared-infra Preview caveat |
| Authentication | MOTHERDUCK_TOKEN injection, access token labels, service accounts |
| Config vs Secrets | Env-var injection rules, the `<secret_name>_<PARAM>` gotcha |
| Scheduling | UTC cron syntax, clearing schedules, schedule status |
| Versioning and Update Semantics | What bumps a version, PATCH carry-forward |
| Runs, Logs, and Cancellation | Run lifecycle, polling, log retrieval |
| MCP Tool Reference | Every flight MCP tool with parameters |
| MCP vs SQL Naming | Parameter name differences between the two surfaces |
| Loading Data from a Flight | Strategy by data volume, anti-patterns |
| Ingestion and Transformation Patterns | dlt, Postgres, community extensions, dbt |
| Production Checklist | Pre-schedule hardening steps |
| Troubleshooting | Symptom-to-cause table |

## What a Flight Is

A Flight is a Python program MotherDuck schedules and runs server-side, on demand or on a recurring schedule, with direct access to your databases. Each run gets its own isolated runtime that executes `main()` to completion and exits — there is no managed worker pool, queue, or distributed state. The flight reaches data like any DuckDB client: it opens an `md:` connection that routes through a Duckling.

Use a flight when a job should run unattended on MotherDuck, retry on a schedule, and keep a run history: ingest from external sources, refresh aggregates, run dbt, export Parquet/CSV to object storage, post scheduled alerts, reverse ETL, AI enrichment. Do not use one for interactive exploration (use the SQL editor or `motherduck-query`) or for orchestration spanning many external systems with complex dependencies — a dedicated orchestrator like Airflow or Prefect is still the better tool there. Fan-out is your job: a flight can trigger other flights (`MD_RUN_FLIGHT`) or thread-pool within a run.

## Anatomy of a Flight

| Field | Meaning |
| --- | --- |
| `name` | Human-readable, non-empty; used in UI, logs, listings. |
| `source_code` | One single-file Python script. Convention: top-level `def main() -> None:` plus `if __name__ == "__main__": main()`. Executed as `python main.py`. No CLI args. |
| `requirements_txt` | Plain `requirements.txt` text, one pinned package per line. Anything on PyPI. Not PEP 723 inline metadata. |
| `access_token_name` / `md_token_name` | Label of a MotherDuck access token to inject as `MOTHERDUCK_TOKEN`. Omit to use the default `MotherDuck Flights` token. List labels with `SELECT * FROM md_access_tokens();`. |
| `config` | `{string: string}` map of **non-secret** values surfaced as env vars under their original key. Full-replace on update. |
| `flight_secret_names` / `md_secret_names` | Names of `TYPE flights` secrets whose params are injected as env vars (encrypted at rest). Full-replace on update. |
| `schedule_cron` | Optional standard 5-field cron expression, **UTC**. Omit for on-demand only. |

## Runtime Environment

Each run executes this sequence: allocate a Python runtime → inject `MOTHERDUCK_TOKEN`, config keys, and secret params as env vars → `pip install` the requirements → execute `main()` capturing stdout+stderr → record status and logs.

The container is constrained:

- **2 CPU cores** — a large thread pool will not speed things up.
- **16GB RAM ceiling** — exceeding it kills the run. Prefer disk-buffered loading over holding datasets in memory.
- **~150GB scratch disk at `/tmp/`** — use it for staging files and on-disk DuckDB databases; clean up between batches.
- It is a Linux process: `subprocess` works, `apt-get install` of Debian packages works (git, ffmpeg, Playwright). dlt and similar tools that write under `HOME` should set `os.environ.setdefault("HOME", "/tmp")`.
- DuckDB extensions can be installed inside the flight's *local* DuckDB process (`INSTALL postgres`, `INSTALL bigquery FROM community`) — the no-runtime-extension rule applies to MotherDuck's server-side engine, not to the flight container.
- Python version, run timeout, and concurrency quotas are not publicly documented; treat long runs and parallel runs conservatively.

**Preview caveat:** flights run on shared compute infrastructure across tenants. During Preview, do not process, store, or log ePHI, payment card data, or other regulated or sensitive personal data in flights.

## Authentication

The runtime provides a MotherDuck access token as the `MOTHERDUCK_TOKEN` env var, so `duckdb.connect("md:")` works with no credentials in code. By default it is the `MotherDuck Flights` token for your user; pin a specific token (for example a service-account token) by passing its label as `access_token_name` (`md_token_name` on MCP). Pick a label whose scope covers exactly the databases the flight needs — and no more.

## Config vs Secrets

Both arrive as env vars; the difference is encryption and naming.

- **Config**: non-sensitive knobs (region, table names, batch sizes). Key `REGION` arrives as env var `REGION`. Not encrypted — never put API keys, passwords, or tokens here.
- **Secrets**: create once, reuse across flights:

```sql
CREATE SECRET api_secret IN motherduck (
  TYPE flights,
  PARAMS MAP { 'API_KEY': 'sk-...', 'API_HOST': 'api.example.com' }
);
```

  Reference it with `flight_secret_names = ["api_secret"]`. Each param is injected as **`<secret_name>_<PARAM>`** — here `api_secret_API_KEY` and `api_secret_API_HOST`, *not* bare `API_KEY`. DuckDB lowercases unquoted secret names; keep param keys UPPERCASE. On naming conflicts, the last secret in the list wins. This prefixing is the most common flight-authoring bug; a robust pattern is to check the bare name first (local runs) and then scan `os.environ` for any key ending in `_<PARAM>` (deployed runs).
- `CREATE SECRET` must run on a read-write connection (`query_rw`, the UI, or a direct connection); the read-only MCP `query` tool rejects it. S3 access for private buckets is separate: an account-level `TYPE S3` secret read by the engine, not env-injected.

## Scheduling

`schedule_cron` is a standard 5-field cron expression in UTC:

```text
*/15 * * * *      every 15 minutes
0 * * * *         hourly at :00
0 6 * * *         daily at 06:00 UTC
0 6 * * 1         every Monday at 06:00 UTC
```

Step syntax requires a base: `*/N` or `M-N/S`; a bare `/N` is invalid. Omit `schedule_cron` to create an on-demand-only flight; on `update_flight`, pass `""` to clear the schedule, omit to leave it unchanged. A schedule can be `active` or `disabled`; disabling does not delete it. Schedule changes are metadata-only (no new version).

## Versioning and Update Semantics

- Content fields — `source_code`, `requirements_txt`, `config`, `flight_secret_names`, `access_token_name` — are immutable per version. Any change to them creates a new 1-indexed FlightVersion.
- `name` and `schedule_cron` changes do not create a version.
- `update_flight` is a PATCH: omitted fields are unchanged, and when you touch any content field the others are carried forward — send only what changes. But `config` and `flight_secret_names` are full replacements when sent, never merges.
- A run locks to the version current when it started; a mid-run update only affects the next run.
- Inspect history with `list_flight_versions` or `get_flight(id, version)` — use the run record's `flight_version` to read the exact source a failing run executed.

## Runs, Logs, and Cancellation

Run lifecycle: `PENDING` → `RUNNING` → terminal `SUCCEEDED` | `FAILED` | `CANCELLED` (SQL surface prefixes these with `RUN_STATUS_`). `run_flight` returns immediately with the new run (sequential per-flight `run_number`); poll `list_flight_runs` (newest first) for completion. `exit_code` is 0 on success, NULL while in progress. Multiple concurrent runs of one flight are allowed.

- `run_flight(id, config?)` — the optional `config` is a per-run override merged over the stored config (provided keys win, only keys already defined on the flight can be set); the flight itself is unchanged. Use it for backfill dates or one-off parameter changes. Non-secret values only.
- `get_flight_logs(id, run_number, max_bytes?)` — combined stdout/stderr plus the full run record (status, exit_code, timing) in one call; truncation keeps the tail (`max_bytes` minimum 1024). Logs are available while `RUNNING` and after any terminal status.
- `cancel_flight_run(id, run_number)` — returns `canceled: true` on a successful transition; calling it on a terminal or nonexistent run is a tool error.

## MCP Tool Reference

Call `get_flight_guide` (no arguments) first — it returns the current authoring guide.

| Tool | Required | Optional | Notes |
| --- | --- | --- | --- |
| `create_flight` | `name`, `source_code` | `requirements_txt`, `config`, `md_secret_names`, `md_token_name`, `schedule_cron` | Returns flight `id` + `current_version` (1). |
| `update_flight` | `id` | any field above, plus `name` | PATCH; content fields bump the version; `schedule_cron: ""` clears. |
| `edit_flight_source` | `id`, `edits[]` | — | Each edit: `{old_string, new_string, replace_all?}`; `old_string` must match exactly once unless `replace_all`. Applied sequentially; creates a new version. No prior `get_flight` needed. MCP-only. |
| `get_flight` | `id` | `version` | Metadata + full version snapshot (source, requirements, config, secrets) in one call. |
| `list_flights` | — | `keywords`, `limit` (default 100, max 500) | Case-insensitive name filter; all words must match. Summary only. |
| `list_flight_versions` | `id` | `limit` | Newest first, full content per version. |
| `run_flight` | `id` | `config` | Async; returns run with `run_number`, status `PENDING`/`RUNNING`. |
| `list_flight_runs` | `id` | `limit` | Newest first; each run reports the effective config it ran with. |
| `get_flight_logs` | `id`, `run_number` | `max_bytes` | Logs + run record; tail on truncation. (Docs page: `get-flight-run-logs`.) |
| `cancel_flight_run` | `id`, `run_number` | — | Error on terminal/nonexistent runs. |
| `delete_flight` | `id` | — | Permanently deletes flight, versions, schedule, run history, logs; cancels active runs. Irreversible — confirm with the user first. |

## MCP vs SQL Naming

The same operations exist as server-side SQL functions (`FROM MD_CREATE_FLIGHT(...)`, `MD_UPDATE_FLIGHT`, `MD_RUN_FLIGHT`, `MD_FLIGHTS()`, `MD_GET_FLIGHT`, `MD_GET_FLIGHT_VERSION`, `MD_GET_FLIGHT_LOGS`, `MD_DELETE_FLIGHT`, ...). They are not available on local-only DuckDB connections. Name differences:

| MCP | SQL |
| --- | --- |
| `md_token_name` | `access_token_name` |
| `md_secret_names` | `flight_secret_names` |
| `id` | `flight_id` (cast as `?::UUID`) |
| `limit` | quoted `"LIMIT"` / `"OFFSET"` |
| status `SUCCEEDED` | status `RUN_STATUS_SUCCEEDED` |
| `edit_flight_source` | no equivalent — `MD_GET_FLIGHT` → edit client-side → `MD_UPDATE_FLIGHT` |

Resolve a flight by name in SQL with `SELECT flight_id FROM MD_FLIGHTS() WHERE flight_name = ?`.

## Loading Data from a Flight

Match the strategy to volume:

| Volume | Strategy |
| --- | --- |
| < ~1K rows | Direct `INSERT` is fine. |
| ~1K rows – ~50MB | Write CSV/JSON to `/tmp/`, bulk-load with `read_csv_auto` / `read_json_auto`; or accumulate a DataFrame and let DuckDB query it. O(1) memory. |
| 50MB+ | Stage into a local on-disk DuckDB file (compressed, ~150GB scratch), flush in 10–100MB batches, then copy into MotherDuck. |
| Very large / max throughput | Write Parquet to S3 and load from there (parallel reads); needs cloud credentials. |

Avoid: `executemany()` (row-by-row under the hood), many small `INSERT` round-trips (~50–100ms each), and uncompressed temp tables that blow the 16GB ceiling (if you must, `CHECKPOINT` periodically). Prefer one bulk multi-row `INSERT` with bound parameters when inserting from Python lists.

## Ingestion and Transformation Patterns

- **dlt (recommended for API/source ingestion):** declarative pipelines with schema evolution, incremental loading, and a native MotherDuck destination. Set `loader_file_format="parquet"` and `write_disposition="merge"` + `primary_key` for idempotent loads. See the dlt template in `FLIGHT_EXAMPLES.md`.
- **Postgres:** `INSTALL postgres; LOAD postgres; ATTACH '' AS pg (TYPE postgres, READ_ONLY)` with credentials passed through libpq env vars, then one streaming `CREATE OR REPLACE TABLE ... AS SELECT * FROM pg."schema"."table"` per table — atomic, idempotent, bounded memory. See the Postgres template in `FLIGHT_EXAMPLES.md`.
- **Other warehouses via community extensions:** open a *local* DuckDB (`duckdb.connect(":memory:", config={"allow_community_extensions": True})`), `INSTALL bigquery FROM community; LOAD bigquery; LOAD motherduck; ATTACH 'md:'` — extensions unsupported server-side still work inside the flight container. Keep heavy compute in the source warehouse or MotherDuck; the flight just moves data.
- **Transformation/refresh:** recompute heavy aggregates on a cron and write to a target table dashboards read; for DAG-shaped transformation, run dbt with the `dbt-duckdb` adapter inside the flight.
- **Audit ledger:** append one row per run (`run_at TIMESTAMPTZ` first) to a small tracker table so every run leaves a queryable trail.

## Production Checklist

1. One successful on-demand run with logs reviewed before any schedule is attached.
2. Service-account token via `access_token_name`, scoped to only the target databases.
3. All sensitive values in `TYPE flights` secrets; nothing sensitive in `config` or source.
4. `requirements_txt` fully pinned (supply-chain note from the docs: flights do not scan your code or dependencies — avoid untrusted packages).
5. Idempotent writes and `IF NOT EXISTS` bootstrap so reruns and first runs both succeed.
6. Non-zero exit on failure (raise, or `sys.exit(1)`) so the run reports `FAILED` instead of silently succeeding.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Run `FAILED`, non-zero `exit_code` | Python exception in `main()` — read `get_flight_logs` for the traceback. |
| `ImportError` / `ModuleNotFoundError` | Package missing from `requirements_txt` or version mismatch; fix and `update_flight`. |
| Fails at `duckdb.connect("md:")` with a version error | Unpinned or too-new `duckdb`; pin the latest MotherDuck-supported release (`duckdb==1.5.2`). |
| `KeyError` on a secret env var | Reading the bare param name instead of `<secret_name>_<PARAM>`, or the secret name was not passed in `flight_secret_names`. |
| `MOTHERDUCK_TOKEN` missing | Wrong `access_token_name` label. |
| Schedule didn't fire | Schedule `disabled`, or the cron is UTC and you expected local time. |
| New version not picked up | The run started before the update; runs lock to the version current at start. |
| Run killed without a traceback | Likely the 16GB RAM ceiling; switch to disk-buffered loading. |
| Older flight reports empty `config` on runs | Flight predates per-run config overrides; one `update_flight` redeploys it. |

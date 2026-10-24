# MotherDuck Flights Reference

Condensed from the MotherDuck Flights docs (concepts, key tasks, MCP tool pages, SQL function pages) and the live `get_flight_guide` output. When MCP is available, `get_flight_guide` is the runtime source of truth; this file is the offline summary.

## Contents

| Section | Covers |
| --- | --- |
| What a Flight Is | Concept, execution model, when to use one |
| Anatomy of a Flight | Fields: name, source, requirements, token, config, secrets, schedule |
| Runtime Environment | Run sequence, Flight sizes, regions, admin visibility, compliance |
| Authentication | MOTHERDUCK_TOKEN injection, access token labels, service accounts |
| Config vs Secrets | Bare and namespaced env-var injection rules |
| Scheduling | UTC cron syntax, clearing schedules, schedule status |
| Versioning and Update Semantics | What bumps a version, PATCH carry-forward |
| Runs, Logs, and Cancellation | Run lifecycle, polling, log retrieval, admin cancellation |
| Run Grants | `GRANT RUN ON FLIGHT`, who can see what, owner-credential model |
| Flight Explainer | Step chart and `@flight-run` progress lines |
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
| `access_token_name` | Label of a MotherDuck access token to inject as `MOTHERDUCK_TOKEN`. Omit to use the default `MotherDuck Flights` token. List labels with `SELECT * FROM md_access_tokens();`. |
| `config` | `{string: string}` map of **non-secret** values surfaced as env vars under their original key. Full-replace on update. |
| `flight_secret_names` | Names of `TYPE flights` secrets whose params are injected as env vars (encrypted at rest). Full-replace on update. |
| `schedule_cron` | Optional standard 5-field cron expression, **UTC**. Omit for on-demand only. |
| `max_runtime_sec` | Optional run cap; `0` means no timeout, omission uses the plan default, and values above the plan cap are rejected. |
| `instance_type` | Optional runner size: `F4`, `F16`, or `F32`. Omission uses the plan default. |

## Runtime Environment

Each run executes this sequence: allocate a Python runtime → inject `MOTHERDUCK_TOKEN`, config keys, and secret params as env vars → `pip install` the requirements → execute `main()` capturing stdout+stderr → record status and logs.

The container is constrained. Call `get_flight_guide` for the current scratch-disk, timeout, and concurrency limits before sizing a workload. Prefer bounded concurrency, disk-buffered loading, and cleanup of `/tmp/` between batches.

Flight sizes (the name is the memory in GB):

| Size | vCPU | Memory | Scratch | Use for |
| --- | --- | --- | --- | --- |
| `F4` | 0.5 | 4 GB | 20 GB | API calls, alerts, jobs that mostly send SQL |
| `F16` | 2 | 16 GB | 150 GB | dbt with `dbt-duckdb`, dlt ingest, multi-step Python (default on paid plans) |
| `F32` | 4 | 32 GB | 300 GB | In-process ML, large dbt projects, after reducing peak memory did not help (Business and Enterprise) |

Set the size with `instance_type` on `MD_CREATE_FLIGHT` or `MD_UPDATE_FLIGHT` (for example `CALL MD_UPDATE_FLIGHT(flight_id := '<id>', instance_type := 'F4')`). Omitting it on create uses the plan default; omitting it on update keeps the current size. A size change creates a new version and applies from the next run. Lite orgs without a payment method run F4 only. Billing is per run-hour at a per-size, per-region rate; read current rates from the pricing page instead of storing them. SQL sent over `md:` executes on a Duckling and is billed as Duckling compute, so a Flight that only orchestrates SQL rarely needs more than F4.

Flights run in every MotherDuck region, including the AWS Asia Pacific regions; scheduling, concurrency, and per-run maximums still vary by plan, so confirm them in `get_flight_guide`. Organization Admins can view every Flight in the org and cancel any pending or running run; editing and deleting stay with the owner.

- It is a Linux process: `subprocess` works, `apt-get install` of Debian packages works (git, ffmpeg, Playwright). dlt and similar tools that write under `HOME` should set `os.environ.setdefault("HOME", "/tmp")`.
- DuckDB extensions can be installed inside the flight's *local* DuckDB process (`INSTALL postgres`, `INSTALL bigquery FROM community`) — the no-runtime-extension rule applies to MotherDuck's server-side engine, not to the flight container.
- Source is limited to 200 KB and `requirements_txt` to 20 KB; load datasets and fixtures from object storage at runtime. The run timeout is `max_runtime_sec` (plan default and cap). Read the Python version and concurrency limits from `get_flight_guide` rather than assuming them.

Flights are generally available. They can process protected health information only when the organization has a signed HIPAA BAA with MotherDuck (an existing BAA covers Flights). For other regulated workloads, verify the isolation model and workload restrictions in current docs; do not infer guarantees from this reference.

## Authentication

The runtime provides a MotherDuck access token as the `MOTHERDUCK_TOKEN` env var, so `duckdb.connect("md:")` works with no credentials in code. By default it is the `MotherDuck Flights` token for your user; pin a specific token (for example a service-account token) by passing its label as `access_token_name` (the same name on MCP and SQL). Pick a label whose scope covers exactly the databases the flight needs — and no more.

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

  Reference it with `flight_secret_names = ["api_secret"]`. Each param is injected under a namespaced key (`api_secret_API_KEY`, `api_secret_API_HOST`) and, when safe, a bare convenience alias (`API_KEY`, `API_HOST`). Prefer the namespaced form in deployed code because it is stable and unambiguous. Names preserve case exactly. When bare keys collide, later secrets win the raw alias; config overrides a colliding secret variable. Reserved `MOTHERDUCK_TOKEN` and `MOTHERDUCK_FLIGHTS_RUN` parameters receive only their namespaced form.
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

`max_runtime_sec` stops a run that exceeds its configured cap. Read the allowed cap from `get_flight_guide` or current plan documentation. Validate it before any source/config deployment so a rejected cap cannot leave content state ambiguous.

## Versioning and Update Semantics

- Content fields — `source_code`, `requirements_txt`, `config`, `flight_secret_names`, `access_token_name`, `max_runtime_sec` — are immutable per version. Any change to them creates a new 1-indexed FlightVersion.
- `name` and `schedule_cron` changes do not create a version.
- `update_flight` is a PATCH: omitted fields are unchanged, and when you touch any content field the others are carried forward — send only what changes. But `config` and `flight_secret_names` are full replacements when sent, never merges.
- A run locks to the version current when it started; a mid-run update only affects the next run.
- Inspect history with `list_flight_versions` or `get_flight(id, version)` — use the run record's `flight_version` to read the exact source a failing run executed.

## Runs, Logs, and Cancellation

Run lifecycle: `PENDING` → `RUNNING` → terminal `SUCCEEDED` | `FAILED` | `CANCELLED` (SQL surface prefixes these with `RUN_STATUS_`). `run_flight` returns immediately with the new run (sequential per-flight `run_number`); poll `get_flight_run` for that exact run when available, otherwise use `list_flight_runs` (newest first). `exit_code` is 0 on success and NULL while in progress. Multiple concurrent runs of one flight are allowed.

- `run_flight(id, config?)` — the optional `config` is a per-run override merged over the stored config (provided keys win, only keys already defined on the flight can be set); the flight itself is unchanged. Use it for backfill dates or one-off parameter changes. Non-secret values only.
- `get_flight_logs(id, run_number, max_bytes?)` — combined stdout/stderr plus the full run record (status, exit_code, timing) in one call; truncation keeps the tail (`max_bytes` minimum 1024). Logs are available while `RUNNING` and after any terminal status.
- `cancel_flight_run(id, run_number)` — returns `canceled: true` on a successful transition; calling it on a terminal or nonexistent run is a tool error. The owner and organization Admins can cancel; the same operation exists as `MD_CANCEL_FLIGHT_RUN` in SQL and `motherduck flight cancel` in the CLI.

## Run Grants

The owner can let others start a Flight without sharing its source, logs, or credentials:

```sql
SELECT flight_id, flight_name FROM MD_LIST_FLIGHTS();
GRANT RUN ON FLIGHT '<flight_id>' TO ROLE order_approvers, USER "ops-bot";
SHOW GRANTS ON FLIGHT '<flight_id>';
REVOKE RUN ON FLIGHT '<flight_id>' FROM USER "ops-bot";
```

- Grantees are typed: `USER <username>` (a MotherDuck username, not an email), `ROLE <role>` (preset roles nest, so `explorer` reaches Builders and Admins), or `ORGANIZATION` (includes service accounts). Use the Flight ID, not its name. A statement is all-or-nothing. Over MCP, use `grant_access` / `revoke_access` with `resource_type = 'flight'`.
- Recommend grants and apply them only after the user confirms who should run the Flight. Prefer a role that matches the intended audience over `ORGANIZATION`.
- Find roles with `SELECT role_name, role_type FROM md_list_roles()` and a username from an email with `SELECT member_name FROM md_list_role_members('<role>') WHERE email = '<email>'` (non-admins only see roles they belong to). Never guess a username; ask, or grant to a role.
- Removing someone's access to a Dive does not remove their `run` grant; revoke it separately.
- Every run uses the owner's token, secrets, and database permissions, whoever starts it. Treat per-run config from grantees as untrusted: validate it in `main()` and bind values as parameters. Config values appear in run history, so keep sensitive values in secrets.
- Grantees can start runs (including from a Dive) and read the status of runs they started with `MD_GET_FLIGHT_RUN` / `get_flight_run`. They cannot list all runs, read source or logs, use `view_flight_run`, cancel, edit, or delete. Restricted members cannot run Flights even with a grant.
- Only the owner can add `RUN` grants. Admins can list and revoke them. Users with no roles, and read-scaling tokens, cannot run Flights even with a grant.
- `MD_LIST_FLIGHT_RUNS` records who started each run (`started_by_name`), visible to the owner and Admins. `MD_LIST_FLIGHT_GRANTEES` returns grants as a joinable table.

## Flight Explainer

Over MCP, load `get_flight_viz_guide` before authoring instrumentation (it covers fan-out, branches, child Flights, and JSON logging) and open runs with `view_flight_run`.

The Explainer tab on a run shows a live step graph with status, row counts, timing, touched tables, and the failing step. It needs two pieces in `main.py`, matched by step ID:

```python
# @flight
#   flowchart TD
#     pull[Fetch orders]:::extract --> load[Write orders]:::load
#     load --> verify{Counts match?}:::check
# @end-flight
from datetime import datetime, timezone

def ts():
    return datetime.now(timezone.utc).isoformat()

def mark(step, status, **fields):
    parts = [f"@flight-run {step} {status}", *(f"{k}={v}" for k, v in fields.items()), f"ts={ts()}"]
    print(" ".join(parts), flush=True)

# mark("pull", "running"); rows = fetch(); mark("pull", "ok", rows=len(rows))
```

- Line format: `@flight-run <step_id> <running|ok|failed|skipped> [rows=N] [error="..."] [effect=table:db.schema.table] [key=<fan-out instance>] [branch=<edge label>] [ts=<ISO-8601>]`. Print with `flush=True`.
- Every chart node needs an explicit ID. Kind classes include `:::extract`, `:::transform`, `:::load`, `:::check`, `:::query`, `:::wait`, `:::switch`, and `:::flight`. Styling is ignored.
- Report `branch=` on decision steps and `key=` per fan-out instance. Only the first 5,000 log lines are read, so keep free-text logging small.
- Instrumentation applies to runs that start after the version that adds it. In the UI, **Add Flight Explainer support with AI** produces a prompt for an MCP-connected agent to add it.

## MCP Tool Reference

Call `get_flight_guide` (no arguments) first — it returns the current authoring guide plus relevant conventions from the reserved `flights` Guide topic. When a shell and filesystem are available, `motherduck flight guide` plus pull/edit/push is more context-efficient for file-shaped work.

| Tool | Required | Optional | Notes |
| --- | --- | --- | --- |
| `create_flight` | `name`, `source_code` | `requirements_txt`, `config`, `flight_secret_names`, `access_token_name`, `schedule_cron`, `max_runtime_sec`, `instance_type` | Returns flight `id` + `current_version` (1). |
| `update_flight` | `id` | any field above, plus `name` | PATCH; content fields bump the version; `schedule_cron: ""` clears; validate runtime cap first. |
| `edit_flight_source` | `id`, `edits[]` | — | Each edit: `{old_string, new_string, replace_all?}`; `old_string` must match exactly once unless `replace_all`. Applied sequentially; creates a new version. No prior `get_flight` needed. MCP-only. |
| `get_flight` | `id` | `version` | Metadata + full version snapshot (source, requirements, config, secrets) in one call. |
| `list_flights` | — | `keywords`, `limit` (default 100, max 500), `owner_only` | Case-insensitive name filter; all words must match. Admins see org Flights; `owner_only = true` restricts to their own. Returns `owner_name`. |
| `list_flight_versions` | `id` | `limit` | Newest first, full content per version. |
| `run_flight` | `id` | `config` | Async; returns run with `run_number`, status `PENDING`/`RUNNING`. |
| `get_flight_run` | `id`, `run_number` | — | Reads one exact run without re-listing the run history. |
| `list_flight_runs` | `id` | `limit` | Newest first; each run reports the effective config it ran with. |
| `get_flight_logs` | `id`, `run_number` | `limit`, `offset`, `order`, `max_bytes` | Logs + run record. Returns the last 200 lines by default (`order` `'desc'`); page with `limit`/`offset`. |
| `view_flight_run` | `id` | `run_number` | Opens a run as a live step diagram when the Flight is instrumented (`has_chart=false` otherwise). Prefer it over raw logs when the user wants to see how a run went. Owner or Admin only. |
| `get_flight_viz_guide` | — | `section` | Full Flight Explainer convention; load it before adding or debugging instrumentation. |
| `grant_access` / `revoke_access` | `resource_type = 'flight'`, `id`, `grantees` | `permission` (`run`) | Grantees are `{type: 'user'|'role'|'organization', name}`; an unknown name fails the whole call. "Could not find Flight" can mean no permission. |
| `cancel_flight_run` | `id`, `run_number` | — | Error on terminal/nonexistent runs. |
| `delete_flight` | `id` | — | Permanently deletes flight, versions, schedule, run history, logs; cancels active runs. Irreversible — confirm with the user first. |

Flight and run listings are server-paged and ordered newest first. Use bounded `limit`/`offset` values instead of assuming an unparameterized list reads the entire organization. Fetch one exact run with `get_flight_run` when that tool is available.

## MCP vs SQL Naming

The same operations exist as server-side SQL functions (`FROM MD_CREATE_FLIGHT(...)`, `MD_UPDATE_FLIGHT`, `MD_RUN_FLIGHT`, `MD_LIST_FLIGHTS()`, `MD_GET_FLIGHT`, `MD_GET_FLIGHT_VERSION`, `MD_GET_FLIGHT_LOGS`, `MD_DELETE_FLIGHT`, ...). They are not available on local-only DuckDB connections. Name differences:

| MCP | SQL |
| --- | --- |
| `id` | `flight_id` (cast as `?::UUID`) |
| `limit` | quoted `"LIMIT"` / `"OFFSET"` |
| status `SUCCEEDED` | status `RUN_STATUS_SUCCEEDED` |
| `edit_flight_source` | no equivalent — `MD_GET_FLIGHT` → edit client-side → `MD_UPDATE_FLIGHT` |

Token and secret parameters use the same names on both surfaces (`access_token_name`, `flight_secret_names`).

Resolve a flight by name in SQL with `SELECT flight_id FROM MD_LIST_FLIGHTS() WHERE flight_name = ?`.

Every query a run issues is tagged in `query_history` and `recent_queries` with a `user_agent` starting `md-flights(<flight_id>,run_id=<run uuid>)`, followed by the Flight's own `custom_user_agent` when set. Filter on that prefix to see what a Flight or one run queried and what it cost.

`MD_GET_FLIGHT_LOGS` is tabular: it returns one row per log line rather than one `logs` blob column. Inspect the current function schema and preserve its ordering columns; do not select a nonexistent `logs` field. The MCP and CLI log commands adapt that table into their user-facing output.

## Loading Data from a Flight

Match the strategy to volume:

| Volume | Strategy |
| --- | --- |
| < ~1K rows | Direct `INSERT` is fine. |
| ~1K rows – ~50MB | Write CSV/JSON to `/tmp/`, bulk-load with `read_csv_auto` / `read_json_auto`; or accumulate a DataFrame and let DuckDB query it. O(1) memory. |
| 50MB+ | Stage into a local on-disk DuckDB file, flush in bounded batches, then copy into MotherDuck; verify scratch capacity first. |
| Very large / max throughput | Write Parquet to S3 and load from there (parallel reads); needs cloud credentials. |

Avoid: `executemany()` (row-by-row under the hood), many small `INSERT` round-trips, and uncompressed temp tables that exceed the runtime memory limit. Prefer one bulk multi-row `INSERT` with bound parameters when inserting from Python lists.

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
4. Bare and namespaced secret aliases used deliberately; collisions are absent or intentional.
5. `requirements_txt` fully pinned (supply-chain note from the docs: flights do not scan your code or dependencies — avoid untrusted packages).
6. Idempotent writes and `IF NOT EXISTS` bootstrap so reruns and first runs both succeed.
7. `max_runtime_sec` fits the current plan and workload.
8. Non-zero exit on failure (raise, or `sys.exit(1)`) so the run reports `FAILED` instead of silently succeeding.
9. Smallest Flight size that fits the Python work.
10. Explainer step chart and `@flight-run` lines for multi-step jobs; `RUN` grants only for the users or roles that need them.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Run `FAILED`, non-zero `exit_code` | Python exception in `main()` — read `get_flight_logs` for the traceback. |
| `ImportError` / `ModuleNotFoundError` | Package missing from `requirements_txt` or version mismatch; fix and `update_flight`. |
| Fails at `duckdb.connect("md:")` with a version error | Unpinned or unsupported `duckdb`; resolve and pin a version from `https://motherduck.com/docs/duckdb-versions.json`. The included examples retain their tested pin for reproducibility. |
| `KeyError` on a secret env var | The secret was not included in `flight_secret_names`, the parameter name differs from the expected uppercase key, or the code chose the wrong namespaced alias. |
| `MOTHERDUCK_TOKEN` missing | Wrong `access_token_name` label. |
| Schedule didn't fire | Schedule `disabled`, or the cron is UTC and you expected local time. |
| New version not picked up | The run started before the update; runs lock to the version current at start. |
| Run killed without a traceback | Reduce peak memory (push work into SQL, bounded batches, lower dbt `--threads`); if it still fails, raise `instance_type` within the plan cap. |
| `ModuleNotFoundError: No module named 'motherduck'` | There is no `motherduck` package; use `import duckdb` and `duckdb.connect("md:")`. |
| Slow startup on every run | Connect with `md:<db>?attach_mode=single` instead of attaching the whole workspace. |
| `You can only run or modify Flights that you own` | Ask the owner (`owner_name`) to act or grant `run`, or copy the source into a new Flight you own. |
| Older flight reports empty `config` on runs | Flight predates per-run config overrides; one `update_flight` redeploys it. |

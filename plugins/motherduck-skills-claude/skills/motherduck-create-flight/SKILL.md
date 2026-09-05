---
name: motherduck-create-flight
description: Create, run, schedule, or debug MotherDuck Flights, Python jobs executed on MotherDuck compute.
argument-hint: [flight-goal]
license: MIT
---

# Create and Manage MotherDuck Flights

## Source Of Truth

- **Non-negotiable ordering:** when MotherDuck MCP is available, call `get_flight_guide` before `create_flight`, `update_flight`, or `edit_flight_source`. The guide defines the current authoring contract, runtime limits, and tool semantics.
- `get_flight_guide` also surfaces conventions from the reserved `flights` Guide topic. Apply those conventions when they fit the requested workload.
- Prefer current MotherDuck Flights docs over memory. Verify lifecycle status, runtime limits, and tool semantics instead of preserving them as durable prompt claims.
- Without MCP, the same operations exist as SQL functions (`MD_CREATE_FLIGHT`, `MD_RUN_FLIGHT`, `MD_LIST_FLIGHTS()`, ...) that execute server-side on a MotherDuck connection. Parameter names differ slightly between the two surfaces; see the naming table in `references/FLIGHTS_GUIDE.md`.

## Default Posture

- One Flight = one single-file Python script with `def main(): ...` and `if __name__ == "__main__": main()`. No CLI args — every knob comes from env vars via `config` (non-secret) or `TYPE flights` secrets (sensitive).
- Connect with `duckdb.connect("md:")`; the runtime injects `MOTHERDUCK_TOKEN` automatically. Never hardcode a token in source, config, or requirements.
- Always pin dependencies in `requirements_txt`. Resolve the highest MotherDuck-supported DuckDB version from `https://motherduck.com/docs/duckdb-versions.json` before authoring a new Flight; use the tested pin in the included templates only when reproducing those examples. An unpinned or unsupported `duckdb` can fail at connect.
- Each secret param is injected under a stable namespaced `<secret_name>_<PARAM>` key and, when safe, a bare `<PARAM>` convenience alias. Prefer namespaced keys in deployed Flight code; bare aliases can collide, be overridden by config, and are withheld for reserved runtime keys.
- Bulk-load, never row-by-row: stage to `/tmp/` and `read_csv_auto`/`read_json_auto`/`read_parquet`, or one CTAS / `INSERT ... SELECT`. No `executemany()` against MotherDuck.
- Make every run idempotent: `CREATE OR REPLACE TABLE` full refresh, partition `DELETE` + `INSERT`, or dlt `write_disposition="merge"` with a primary key. Bootstrap with `CREATE DATABASE IF NOT EXISTS` / `CREATE SCHEMA IF NOT EXISTS` so the first run succeeds on a fresh account.
- Validate any config-supplied identifier (database, schema, table names) against `[A-Za-z_][A-Za-z0-9_]*` before interpolating it into DDL; bind all data values as `?` parameters.
- Create the flight **without** a schedule first, trigger one on-demand run, read the logs, and only then attach `schedule_cron` (5-field cron, UTC).
- Set and validate `max_runtime_sec` when the workload needs an explicit cap; read the current plan limit from `get_flight_guide` instead of hardcoding it.
- For production, use a service-account token via `access_token_name` and keep its database permissions as narrow as the workload allows.
- Treat a Flight as orchestration and light processing, not a place to crunch large tables in Python memory. Push heavy compute into SQL and verify runtime capacity with `get_flight_guide` before sizing disk- or memory-intensive work.

## Workflow

1. Classify the job: ingestion, transformation/refresh, export or alerting, or admin automation. If the job is interactive analysis or a one-off query, use `motherduck-query` instead — no Flight needed.
2. Call `get_flight_guide` (MCP) and confirm which database the flight writes to with `motherduck-explore`.
3. Reuse a matching template in `references/FLIGHT_EXAMPLES.md` when it fits; otherwise write a focused script that preserves the runtime, secrets, and idempotency contracts.
4. Create any required `TYPE flights` secret first, then `create_flight` with `name`, `source_code`, pinned `requirements_txt`, `config`, and secret names — no `schedule_cron` yet.
5. `run_flight`, poll `get_flight_run` when available (or `list_flight_runs` as a fallback) until terminal, and read `get_flight_logs`. Iterate with `edit_flight_source` (surgical) or `update_flight` (full field replacement); each content change creates a new version.
6. If scheduling was requested, set it only after a successful run with `update_flight(schedule_cron = ...)` and state that cron is UTC. Clear it with `schedule_cron = ""` only when requested; preserve an existing schedule during unrelated edits.

For answer, review, or planning requests, do not create or schedule a Flight. For create or update requests, complete the requested in-scope deployment and on-demand validation; attaching a recurring schedule is authorized only when the request includes scheduling.

## References

Read only the reference sections needed for the current task.

- Read `references/FLIGHTS_GUIDE.md` for the full concept and operations reference: anatomy, runtime environment, config vs secrets, scheduling, versioning, run lifecycle, the complete MCP tool reference, MCP-vs-SQL naming, loading strategies by data volume, and troubleshooting.
- Read `references/FLIGHT_EXAMPLES.md` for three complete, best-practice flight templates (dlt ingestion, Postgres ingestion, scheduled S3 partition refresh) with their `requirements.txt`, secret setup, and deploy calls.

## Related Skills

Load related skills only for missing capabilities; reuse established context.

- `motherduck-load-data` for choosing the ingestion SQL the flight will run (CTAS, `INSERT ... SELECT`, cloud-storage secrets)
- `motherduck-query` for validating the DuckDB SQL inside the flight before deploying it
- `motherduck-explore` for confirming target databases, schemas, and tables exist
- `motherduck-build-data-pipeline` when the work is a full raw/staging/analytics pipeline design and the flight is just its scheduler
- `motherduck-cli` when the agent has a shell and should keep Flight source in local files
- `motherduck-manage-guides` for reusable personal or organization Flight conventions

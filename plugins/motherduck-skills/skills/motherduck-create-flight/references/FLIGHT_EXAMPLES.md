# Flight Examples

Three complete, best-practice flight templates adapted from MotherDuck's flight-plans templates: a dlt API ingestion flight, a Postgres mirroring flight, and a scheduled S3 partition refresh. Start from the closest one and adapt it through config knobs rather than rewriting it.

## Contents

| Section | Covers |
| --- | --- |
| Shared Conventions | Patterns every template follows |
| Example: dlt Ingestion Flight | Any dlt source → MotherDuck with merge semantics |
| Example: Postgres Ingestion Flight | Mirror Postgres tables via the postgres extension |
| Example: Scheduled S3 Partition Refresh | Refresh one Hive partition from Parquet in S3 |
| Deploying a Template | Secret setup, create, test run, schedule |
| Choosing a Template | Which starting point for which job |

## Shared Conventions

Every template follows the same contract; preserve these when adapting:

- `def main() -> None:` entrypoint with `if __name__ == "__main__": main()`; single file; no CLI args.
- All knobs from env vars through an `env(name, default)` helper, so users adapt by setting `config` values, not editing code.
- `duckdb.connect("md:")` with the injected `MOTHERDUCK_TOKEN`; no credentials in source.
- `IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")` validation for every config-supplied name interpolated into DDL; `?` parameters for all data values.
- `CREATE DATABASE IF NOT EXISTS` / `CREATE SCHEMA IF NOT EXISTS` bootstrap so the first run works on a fresh account.
- Idempotent writes (merge, atomic `CREATE OR REPLACE`, or partition `DELETE` + `INSERT`) plus an append-only run ledger with `run_at TIMESTAMPTZ` first.
- `print()`/`logging` to stdout (captured as run logs); exit non-zero on failure.
- Pinned `requirements_txt` with `duckdb==1.5.2` (latest MotherDuck-supported release).

## Example: dlt Ingestion Flight

Runs a dlt pipeline into MotherDuck on a schedule: Parquet loader files, schema evolution, merge semantics keyed on `PRIMARY_KEY`, and a run ledger. The demo source is public GitHub repo metadata (no credentials) so a fresh deploy produces a successful run; replace `repo_rows` with any dlt source — an API, a database, a filesystem, or a dlt verified source.

```python
import os
import re
from collections.abc import Iterator

import dlt
import duckdb
import httpx


IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
WRITE_DISPOSITIONS = {"append", "merge", "replace"}


def repo_rows(repos: list[str]) -> Iterator[dict]:
    # Demo source: public GitHub repository metadata, no credentials needed.
    # Replace this generator with your own dlt source (an API, a database, a
    # filesystem, or a dlt verified source) to ingest real data. Yield plain
    # dicts and dlt infers the schema and evolves it as fields change.
    for repo in repos:
        response = httpx.get(
            f"https://api.github.com/repos/{repo}",
            timeout=30,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        payload = response.json()
        yield {
            "repo": repo,
            "stars": payload.get("stargazers_count"),
            "forks": payload.get("forks_count"),
            "open_issues": payload.get("open_issues_count"),
            "default_branch": payload.get("default_branch"),
            "pushed_at": payload.get("pushed_at"),
        }


def main() -> None:
    # Every knob is read from Flight config/env, so you adapt this template by
    # setting config values rather than editing code. Defaults load public GitHub
    # repo stats into flights_demo so a fresh deploy produces a successful run.
    database = validate_identifier("DESTINATION_DATABASE", env("DESTINATION_DATABASE", "flights_demo"))
    dataset_name = env("DATASET_NAME", "flights_demo_dlt")
    table_name = env("TABLE_NAME", "github_repo_stats")
    pipeline_name = env("PIPELINE_NAME", "flights_dlt_ingest")
    primary_key = env("PRIMARY_KEY", "repo")
    write_disposition = env("WRITE_DISPOSITION", "merge")
    if write_disposition not in WRITE_DISPOSITIONS:
        raise ValueError(
            f"WRITE_DISPOSITION must be one of {sorted(WRITE_DISPOSITIONS)}, got {write_disposition!r}"
        )
    ledger_table = validate_identifier("RUN_LEDGER_TABLE", env("RUN_LEDGER_TABLE", "dlt_ingest_runs"))
    repos = [
        repo.strip()
        for repo in env("GITHUB_REPOS", "duckdb/duckdb,motherduckdb/motherduck-docs,dlt-hub/dlt").split(",")
        if repo.strip()
    ]

    # dlt writes working files under HOME; a Flight has a writable /tmp.
    os.environ.setdefault("HOME", "/tmp")
    # Point the dlt MotherDuck destination at our database. The injected
    # MOTHERDUCK_TOKEN supplies the credential, so no token appears here.
    os.environ["DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE"] = database

    # Create the destination database so dlt has a catalog to build the dataset in;
    # dlt creates the dataset (schema) and tables, but not the database itself.
    con = duckdb.connect("md:")
    con.execute(f"CREATE DATABASE IF NOT EXISTS {database}")

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination="motherduck",
        dataset_name=dataset_name,
    )
    load_info = pipeline.run(
        repo_rows(repos),
        table_name=table_name,
        write_disposition=write_disposition,
        primary_key=primary_key,
        # Prefer Parquet loader files over row-wise insert_values so larger
        # sources stay on a bulk-loading path. Keep this unless you have measured
        # a reason to change it.
        loader_file_format="parquet",
    )

    # Record the dlt load package summary so each run leaves an audit trail. The
    # ledger lives in the database's main schema, separate from the dlt dataset.
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.main")
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {database}.main.{ledger_table} (
            run_at TIMESTAMPTZ,
            pipeline_name VARCHAR,
            destination_dataset VARCHAR,
            destination_table VARCHAR,
            load_summary VARCHAR
        )
        """
    )
    con.execute(
        f"INSERT INTO {database}.main.{ledger_table} VALUES (current_timestamp, ?, ?, ?, ?)",
        [pipeline_name, dataset_name, table_name, str(load_info)],
    )
    con.close()
    print(load_info)


def env(name: str, default: str) -> str:
    value = os.environ.get(name, default).strip()
    return value or default


def validate_identifier(name: str, value: str) -> str:
    # The database and ledger table names flow into CREATE/INSERT statements that
    # cannot be parameterized, so reject anything that is not a plain SQL
    # identifier before any SQL runs.
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a simple SQL identifier, got {value!r}")
    return value


if __name__ == "__main__":
    main()
```

`requirements_txt`:

```text
duckdb==1.5.2
dlt[motherduck]==1.27.0
httpx==0.28.1
```

Config knobs (all optional): `DESTINATION_DATABASE`, `DATASET_NAME`, `TABLE_NAME`, `PIPELINE_NAME`, `PRIMARY_KEY`, `WRITE_DISPOSITION` (`append`/`merge`/`replace`), `RUN_LEDGER_TABLE`, `GITHUB_REPOS`. When you swap in a credentialed source, put the credentials in a `TYPE flights` secret and read them as `<secret_name>_<PARAM>` env vars.

## Example: Postgres Ingestion Flight

Mirrors PostgreSQL base tables into a MotherDuck database using the DuckDB `postgres` core extension. Each table moves in one streaming statement — `CREATE OR REPLACE TABLE <target> AS SELECT * FROM pg."schema"."table"` — which is atomic (one-step swap), idempotent (rerun fully replaces), and memory-bounded (DuckDB pipelines the scan into the write). Includes/excludes are config-driven, each table gets jittered exponential-backoff retries with per-table failure isolation, and results land in an audit table.

Create the connection secret first (params must be UPPERCASE; they arrive as `pg_HOST`, `pg_PASSWORD`, ... because the unquoted secret name is lowercased):

```sql
CREATE SECRET pg IN motherduck (
    TYPE flights,
    PARAMS MAP {
        'HOST':     '<your-postgres-host>',
        'PORT':     '5432',
        'DATABASE': '<your_database>',
        'USER':     '<YOUR_USER>',
        'PASSWORD': '<YOUR_PASSWORD>',
        'SSLMODE':  'require'
    }
);
```

```python
"""
Postgres -> MotherDuck batch ELT flight

Mirrors PostgreSQL base tables into a MotherDuck database using the DuckDB postgres
extension. Each table is moved by a single streaming SQL statement that is atomic,
idempotent, and memory-bounded. Per-table logging lands in
<target>.main.flight_tracker.

Inputs (case sensitive, use uppercase):
    Secret `pg` (TYPE flights) -> Postgres connection params:
        Required: HOST, DATABASE, USER, PASSWORD
        Optional: PORT, SSLMODE
    Config (non-secret env vars):
        MOTHERDUCK_HOST  - optional host override; exported before connect.
        TARGET_DATABASE  - MotherDuck database to write into (default: postgres_ingest).
        INCLUDED_SCHEMAS / EXCLUDED_SCHEMAS  - comma-separated schema names.
        INCLUDED_TABLES  / EXCLUDED_TABLES   - comma-separated, fully qualified schema.table.
        MAX_RETRIES (5)
        RETRY_BASE_SECONDS (2)
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime, timezone

import duckdb
from tenacity import (
    Retrying,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("pg2md")

# PostgreSQL system schemas that are never mirrored.
SYSTEM_SCHEMAS = {"information_schema", "pg_catalog", "pg_toast"}

# Postgres connection params from the flight secret.
# The secret injects each as `<secret_name>_<KEY>`
PG_PARAMS = (
    ("HOST", "PGHOST", None, True),
    ("PORT", "PGPORT", "5432", False),
    ("DATABASE", "PGDATABASE", None, True),
    ("USER", "PGUSER", None, True),
    ("PASSWORD", "PGPASSWORD", None, True),
    ("SSLMODE", "PGSSLMODE", "prefer", False),
)

# Local DuckDB catalog name the source Postgres database is ATTACHed as. Referenced by
# attach_postgres(), discover_base_tables(), and load_table() -- one source of truth.
PG_ALIAS = "pg"


# --------------------------------------------------------------------------- #
# Small SQL / env helpers
# --------------------------------------------------------------------------- #
def quote_ident(ident: str) -> str:
    """Quote an identifier the way DuckDB/Postgres expect, so names with special
    characters or reserved words are handled correctly."""
    return '"' + ident.replace('"', '""') + '"'


def csv_set(name: str) -> frozenset[str]:
    """Turn a comma-separated env var into a clean set for membership filtering."""
    raw = os.environ.get(name, "") or ""
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


# --------------------------------------------------------------------------- #
# Table selection
# --------------------------------------------------------------------------- #
def is_selected(
    schema: str,
    table: str,
    included_schemas: frozenset[str],
    excluded_schemas: frozenset[str],
    included_tables: frozenset[str],
    excluded_tables: frozenset[str],
) -> bool:
    """Decide whether a discovered base table is mirrored, applying the two
    include/exclude gates where exclude always wins and system schemas are excluded."""
    fqtn = f"{schema}.{table}"
    if schema in SYSTEM_SCHEMAS or schema.startswith("pg_temp") or schema.startswith("pg_toast"):
        return False
    if included_schemas and schema not in included_schemas:
        return False
    if schema in excluded_schemas:
        return False
    if included_tables and fqtn not in included_tables:
        return False
    if fqtn in excluded_tables:
        return False
    return True


# --------------------------------------------------------------------------- #
# Connection + setup
# --------------------------------------------------------------------------- #
def connect_motherduck() -> duckdb.DuckDBPyConnection:
    """Open the MotherDuck connection that backs the whole flight, targeting the
    configured host when one is set."""
    host = os.environ.get("MOTHERDUCK_HOST")
    if host:
        os.environ["motherduck_host"] = host
        log.info("Targeting MotherDuck host: %s", host)
    else:
        log.info("MOTHERDUCK_HOST not set; using runtime default MotherDuck host")
    return duckdb.connect("md:")


def attach_postgres(con: duckdb.DuckDBPyConnection, secret_name: str) -> None:
    """Wire up the read-only Postgres source so tables can be streamed out, keeping the
    password out of SQL by passing credentials through libpq env vars.
    ATTACHes READ_ONLY as `pg`."""
    for key, libpq_var, default, required in PG_PARAMS:
        env_var = f"{secret_name}_{key}"
        value = os.environ.get(env_var, default)
        if value is None:
            if required:
                raise RuntimeError(f"Required Postgres secret env var {env_var!r} is not set")
            continue
        os.environ[libpq_var] = str(value)

    con.execute("INSTALL postgres")
    con.execute("LOAD postgres")
    con.execute(f"ATTACH '' AS {PG_ALIAS} (TYPE postgres, READ_ONLY)")
    log.info(
        "Attached Postgres %s:%s/%s (read-only, sslmode=%s)",
        os.environ["PGHOST"], os.environ["PGPORT"],
        os.environ["PGDATABASE"], os.environ["PGSSLMODE"],
    )


def ensure_target(con: duckdb.DuckDBPyConnection, target_db: str) -> None:
    """Create the target database and the audit logging table up front."""
    target = quote_ident(target_db)
    con.execute(f"CREATE DATABASE IF NOT EXISTS {target}")
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {target}.main.flight_tracker ("
        "  run_id               VARCHAR,"
        "  flight_secret_name   VARCHAR,"
        "  source_schema        VARCHAR,"
        "  source_table         VARCHAR,"
        "  destination_database VARCHAR,"
        "  destination_schema   VARCHAR,"
        "  destination_table    VARCHAR,"
        "  rows_loaded          BIGINT,"
        "  attempts             INTEGER,"
        "  started_at           TIMESTAMP,"
        "  finished_at          TIMESTAMP,"
        "  update_ts            TIMESTAMP"
        ")"
    )


# --------------------------------------------------------------------------- #
# Discovery + per-table load
# --------------------------------------------------------------------------- #
def discover_base_tables(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str]]:
    """List the candidate source tables to iterate on"""
    rows = con.execute(
        f"SELECT table_schema, table_name FROM postgres_query('{PG_ALIAS}', "
        "'SELECT table_schema, table_name FROM information_schema.tables "
        "WHERE table_type = ''BASE TABLE''') "
        "ORDER BY table_schema, table_name"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def load_table(con: duckdb.DuckDBPyConnection, target_db: str, schema: str, table: str) -> int:
    """Perform the entire data movement for one table as a single atomic, idempotent,
    streaming CTAS. Returns the row count the CTAS reports as inserted."""
    tgt_table = f"{quote_ident(target_db)}.{quote_ident(schema)}.{quote_ident(table)}"
    src_table = f"{PG_ALIAS}.{quote_ident(schema)}.{quote_ident(table)}"
    return con.execute(f"CREATE OR REPLACE TABLE {tgt_table} AS SELECT * FROM {src_table}").fetchone()[0]


def record_success(
    con: duckdb.DuckDBPyConnection, target_db: str, run_id: str, secret_name: str,
    schema: str, table: str, rows_loaded: int, attempts: int,
    started_at: datetime, finished_at: datetime, update_ts: datetime,
) -> None:
    """After success, append a row to the audit table"""
    con.execute(
        f"INSERT INTO {quote_ident(target_db)}.main.flight_tracker "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [run_id, secret_name, schema, table, target_db, schema, table,
         rows_loaded, attempts, started_at, finished_at, update_ts],
    )


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Orchestrate the full-refresh ELT: connect, attach, discover, then load each
    table sequentially with per-table retries/isolation and record results."""
    # Run config, read once from the environment and referenced as needed below.
    RUN_ID = str(uuid.uuid4())
    TARGET_DB = os.environ.get("TARGET_DATABASE", "postgres_ingest")
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))
    RETRY_BASE_SECONDS = float(os.environ.get("RETRY_BASE_SECONDS", "2"))
    INCLUDED_SCHEMAS = csv_set("INCLUDED_SCHEMAS")
    EXCLUDED_SCHEMAS = csv_set("EXCLUDED_SCHEMAS")
    INCLUDED_TABLES = csv_set("INCLUDED_TABLES")
    EXCLUDED_TABLES = csv_set("EXCLUDED_TABLES")
    # MotherDuck Flights secret holding the Postgres connection; its params arrive as
    # <SECRET_NAME>_HOST, <SECRET_NAME>_PORT, ... Change it to point at another secret.
    SECRET_NAME = "pg"

    log.info("Run %s -> target %r", RUN_ID, TARGET_DB)

    con = connect_motherduck()
    attach_postgres(con, SECRET_NAME)
    ensure_target(con, TARGET_DB)

    all_tables = discover_base_tables(con)
    selected = [
        (s, t) for (s, t) in all_tables
        if is_selected(s, t, INCLUDED_SCHEMAS, EXCLUDED_SCHEMAS, INCLUDED_TABLES, EXCLUDED_TABLES)
    ]
    log.info("Discovered %d base table(s); %d selected after filters", len(all_tables), len(selected))

    if not selected:
        log.warning("No tables selected - nothing to do.")
        return

    # Pre-create the target schemas (mirroring source schema names) once.
    for sch in sorted({s for (s, _) in selected}):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_ident(TARGET_DB)}.{quote_ident(sch)}")

    started_all = datetime.now(timezone.utc)
    failed: list[str] = []
    succeeded = 0
    rows_total = 0

    for schema, table in selected:
        fqtn = f"{schema}.{table}"
        started = datetime.now(timezone.utc)
        retryer = Retrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=RETRY_BASE_SECONDS, max=60) + wait_random(0, 1),
            reraise=True,
        )
        try:
            rows = retryer(load_table, con, TARGET_DB, schema, table)
            attempts = retryer.statistics.get("attempt_number", 1)
            finished = datetime.now(timezone.utc)
            record_success(con, TARGET_DB, RUN_ID, SECRET_NAME, schema, table, rows,
                           attempts, started, finished, datetime.now(timezone.utc))
            succeeded += 1
            rows_total += rows
            log.info("OK   %-50s %12d rows (attempts=%d)", fqtn, rows, attempts)
        except Exception as exc:  # noqa: BLE001 - per-table isolation is intentional
            attempts = retryer.statistics.get("attempt_number", 1)
            failed.append(fqtn)
            log.error("FAIL %-50s (attempts=%d) %s: %s", fqtn, attempts, type(exc).__name__, exc)

    total_seconds = (datetime.now(timezone.utc) - started_all).total_seconds()
    log.info("Summary: %d succeeded, %d failed, %d rows in %.1fs (run %s)",
             succeeded, len(failed), rows_total, total_seconds, RUN_ID)

    if failed:
        log.error("Failed tables: %s", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

`requirements_txt` — the `postgres` extension is a DuckDB core extension loaded at runtime (`INSTALL postgres; LOAD postgres`), not a pip package, so there is no pip Postgres client dependency:

```text
duckdb==1.5.2
tenacity==9.0.0
```

## Example: Scheduled S3 Partition Refresh

Refreshes exactly one Hive partition of a MotherDuck table from partitioned Parquet in S3 on each run: schema inferred once via a zero-row CTAS, then `DELETE` + `INSERT` scoped to the partition so DuckDB prunes every other partition folder. Defaults read the public DuckDB PyPI download stats, partitioned by `year`. Override `LOAD_PARTITION` per run (via `run_flight` config overrides) to backfill specific partitions.

```python
import os
import re
from datetime import datetime, timezone

import duckdb


IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def main() -> None:
    # Every knob is read from Flight config/env, so you adapt this template by
    # setting config values rather than editing code. Defaults point at the
    # public DuckDB PyPI download stats, partitioned in S3 by year.
    source_glob = env(
        "SOURCE_GLOB",
        "s3://us-prd-motherduck-open-datasets/pypi/duckdb/pypi_daily_stats/**/*.parquet",
    )
    partition_column = validate_identifier("PARTITION_COLUMN", env("PARTITION_COLUMN", "year"))
    database = validate_identifier("DESTINATION_DATABASE", env("DESTINATION_DATABASE", "flights_demo"))
    schema = validate_identifier("DESTINATION_SCHEMA", env("DESTINATION_SCHEMA", "main"))
    table = validate_identifier("DESTINATION_TABLE", env("DESTINATION_TABLE", "duckdb_pypi_downloads"))
    ledger_table = validate_identifier("RUN_LEDGER_TABLE", env("RUN_LEDGER_TABLE", "ingest_runs"))
    hive_partitioning = "true" if env_bool("HIVE_PARTITIONING", True) else "false"
    load_partition = resolve_partition(env("LOAD_PARTITION", ""))

    destination = f"{database}.{schema}.{table}"
    ledger = f"{database}.{schema}.{ledger_table}"

    con = duckdb.connect("md:")

    # The Flight creates its own destination, so it runs on the first deploy
    # without depending on a database or schema that already exists.
    con.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}")

    # Create the destination once by inferring its columns from the source.
    # LIMIT 0 reads no rows, so this is cheap and keeps the destination's types
    # aligned with the source Parquet (including the partition column).
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {destination} AS
        SELECT *
        FROM read_parquet(?, hive_partitioning = {hive_partitioning})
        WHERE {partition_column} = ?
        LIMIT 0
        """,
        [source_glob, load_partition],
    )

    # Replace exactly one partition. Filtering on the partition column lets DuckDB
    # prune every other partition folder, so the scan cost stays flat as more
    # partitions land. To transform instead of copying through, replace this
    # SELECT * with your own projection or aggregation (keep the partition column).
    con.execute(f"DELETE FROM {destination} WHERE {partition_column} = ?", [load_partition])
    con.execute(
        f"""
        INSERT INTO {destination}
        SELECT *
        FROM read_parquet(?, hive_partitioning = {hive_partitioning})
        WHERE {partition_column} = ?
        """,
        [source_glob, load_partition],
    )

    row_count = con.execute(
        f"SELECT count(*) FROM {destination} WHERE {partition_column} = ?",
        [load_partition],
    ).fetchone()[0]

    # A lightweight audit trail of which partition each run refreshed.
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {ledger} (
            run_at TIMESTAMPTZ,
            source_glob VARCHAR,
            destination_table VARCHAR,
            partition_column VARCHAR,
            load_partition VARCHAR,
            row_count BIGINT
        )
        """
    )
    con.execute(
        f"INSERT INTO {ledger} VALUES (current_timestamp, ?, ?, ?, ?, ?)",
        [source_glob, destination, partition_column, str(load_partition), row_count],
    )
    print(f"refreshed {destination} partition {partition_column}={load_partition}: {row_count} rows")


def env(name: str, default: str) -> str:
    value = os.environ.get(name, default).strip()
    return value or default


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def validate_identifier(name: str, value: str) -> str:
    # Database, schema, table, and column names flow into CREATE/DELETE/INSERT
    # statements that cannot be parameterized, so reject anything that is not a
    # plain SQL identifier before any SQL runs.
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a simple SQL identifier, got {value!r}")
    return value


def resolve_partition(raw: str) -> int | str:
    # Default to the current UTC year's partition. Set LOAD_PARTITION in config to
    # target another partition: a different year, a date string, a region code, and
    # so on. Digit-only values are treated as integers so they match a numeric
    # partition column (such as a Hive year) and still prune cleanly.
    if not raw:
        return datetime.now(timezone.utc).year
    return int(raw) if raw.lstrip("-").isdigit() else raw


if __name__ == "__main__":
    main()
```

`requirements_txt`:

```text
duckdb==1.5.2
```

Private buckets need an account-level `TYPE S3` secret (read by the engine, not env-injected); the default public bucket needs none.

## Deploying a Template

1. Create any required `TYPE flights` secret on a read-write connection (`query_rw`, the UI, or a direct connection — the read-only `query` tool rejects `CREATE SECRET`).
2. Create the flight without a schedule. With MCP:

```text
create_flight(
  name = "postgres-nightly-mirror",
  source_code = <flight source above>,
  requirements_txt = "duckdb==1.5.2\ntenacity==9.0.0\n",
  md_secret_names = ["pg"],
  config = { "TARGET_DATABASE": "postgres_ingest", "EXCLUDED_SCHEMAS": "audit,scratch" },
)
```

   With SQL, the same call is `FROM MD_CREATE_FLIGHT(name := ..., source_code := ..., requirements_txt := ..., flight_secret_names := ['pg'], config := MAP {...})`.
3. Trigger one on-demand run (`run_flight`), poll `list_flight_runs` until terminal, and read `get_flight_logs`. Fix issues with `edit_flight_source`.
4. Attach the schedule only after a clean run: `update_flight(id, schedule_cron = "0 6 * * *")` — cron is UTC, and schedule changes do not create a new version.

## Choosing a Template

| Job | Start from | Why |
| --- | --- | --- |
| API or SaaS source, evolving schema, incremental loads | dlt template | Schema evolution + merge semantics for free |
| Mirror an operational Postgres database | Postgres template | Streaming atomic CTAS per table, no pip driver needed |
| Files landing in object storage on a cadence | S3 partition template | Partition-pruned refresh keeps cost flat |
| Another warehouse (BigQuery, Snowflake) | Postgres template shape | Swap the ATTACH for the community extension or vendor client; keep the per-table CTAS + ledger pattern |
| Pure SQL transformation/refresh | S3 template shape minus the read | Keep the bootstrap, idempotent write, and ledger; replace the load with your `INSERT ... SELECT` |

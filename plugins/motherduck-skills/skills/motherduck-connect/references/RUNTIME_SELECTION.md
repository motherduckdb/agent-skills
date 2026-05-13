# Runtime Selection

Reference for choosing **which runtime executes the connection** to MotherDuck: MCP server, Python (with `uv` or `pip`), Node.js, or the DuckDB CLI. This is a separate decision from `CONNECTION_GUIDE.md`, which picks the *connection method* (PG endpoint vs native DuckDB API vs pg_duckdb vs WASM).

## Decision Tree

```text
Is a MotherDuck MCP server available AND the work ad-hoc/exploration?
├── Yes ─────────────────> Use MCP tools (query, list_databases, ...). STOP.
└── No  ─────────────────> Detect a runtime in this order:
                            uv installed?         ──> uv run --with "duckdb==<v>" script.py
                            python3 + pip?        ──> pip install "duckdb==<v>"
                            node + npm?           ──> npm install @duckdb/node-api@<v>
                            none of the above?    ──> install CLI via install.motherduck.com
```

Always stop at the first match. If the host project already declares a language (a `pyproject.toml`, `package.json`, or similar lockfile is present), follow that language even when the priority order would suggest otherwise — do not add a second runtime alongside an existing one.

## Ad-hoc vs Pipeline

- **Ad-hoc / exploration.** One-shot, interactive, may be discarded after the answer is found. No artifact gets checked in. The MCP server is the right runtime here when it is available, because there is nothing to ship and the agent can iterate directly.
- **Recurring / pipeline.** Scheduled, version-controlled, runs unattended. The code lives in a repo and survives the conversation. Pipelines need a real runtime (Python, Node, or CLI) so the script is reproducible without an MCP session.

The MCP path is useful only for ad-hoc work. Even if MCP is available, a pipeline must use Python, Node, or the CLI so the source can be committed and executed in CI or production.

## Detection Commands

Run these in order. The first one that exits 0 picks the runtime.

```bash
command -v uv         # preferred Python runner
command -v python3    # fallback Python
command -v node       # fallback runtime
command -v duckdb     # CLI already present
```

Also check whether the host project already commits to a language:

```bash
test -f pyproject.toml || test -f requirements.txt   # Python project
test -f package.json                                 # Node project
```

## Version Pinning

MotherDuck supports a curated set of DuckDB versions; the latest upstream DuckDB release is not automatically available on MotherDuck. Always pin to a MotherDuck-supported version.

```bash
curl -s https://motherduck.com/docs/duckdb-versions.json
```

Parse the response and pick the highest supported version. Use that exact version string in every install command below. Re-fetch the JSON before each install — do not cache.

## Install Snippets

Pin `<version>` to the highest version returned by the JSON above.

### `uv` (preferred)

```bash
uv run --with "duckdb==<version>" script.py
```

`uv` resolves the dependency in an isolated environment per run, so the script is reproducible without a separate venv. This is the preferred path for both ad-hoc scripts and pipelines.

### `pip` (fallback Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "duckdb==<version>"
```

Use only when `uv` is not available and the project does not already use `uv`.

### `npm` (Node.js)

```bash
npm install "@duckdb/node-api@<version>"
```

Use when the host project is already a Node/TypeScript project, or when no Python runtime is available.

### DuckDB CLI (last resort)

```bash
curl -s https://install.motherduck.com | env -u motherduck_token HOME="$install_home" sh
```

Pick `$install_home` as a writable project-local directory (for example `./.duckdb`) so the install does not pollute the user's home. The CLI is appropriate for shell-driven ad-hoc exploration and for pipelines that are themselves shell scripts; for any program that already runs Python or Node, prefer the matching client library.

## When to Override the Order

- The host project already commits to a language (a `pyproject.toml`, `package.json`, or comparable lockfile is present). Follow the project's language.
- The pipeline is a shell script and the workload is a single SQL file. The CLI is appropriate even though it is last in the priority order.
- The user explicitly asks for a specific runtime. Honor the request and skip detection.

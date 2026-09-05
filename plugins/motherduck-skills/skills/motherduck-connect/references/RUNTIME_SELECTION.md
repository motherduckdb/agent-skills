# Runtime Selection

Reference for choosing **which runtime executes the connection** to MotherDuck: MCP server, MotherDuck CLI, Python (with `uv` or `pip`), Node.js, or the DuckDB CLI. This is separate from `CONNECTION_GUIDE.md`, which picks the connection method.

## Runtime Choice

Honor the user's runtime choice and reuse the project's language, lockfile, and working connection. Otherwise choose by task:

| Task | Preferred runtime |
| --- | --- |
| Chat-only exploration or inline answers | Available MotherDuck MCP tools |
| Dive/Flight source files, shell automation, large outputs | MotherDuck CLI |
| Application or pipeline code | Its existing Python, Node, or other client runtime |
| New standalone Python example | `uv` with a supported DuckDB pin |
| Shell-based SQL | Existing DuckDB CLI, or a platform-appropriate install |

Do not install another runtime merely because it appears earlier in a detection list. MCP can support discovery and validation alongside committed application code.

## Ad-hoc vs Pipeline

- **Ad-hoc / exploration.** One-shot, interactive, may be discarded after the answer is found. No artifact gets checked in. The MCP server is the right runtime here when it is available, because there is nothing to ship and the agent can iterate directly.
- **Recurring / pipeline.** Scheduled, version-controlled, runs unattended. The code lives in a repo and survives the conversation. Pipelines need a real runtime (Python, Node, or CLI) so the script is reproducible without an MCP session.

A recurring pipeline needs committed source and an unattended runtime, which can include a MotherDuck Flight. MCP can create and operate that Flight; an interactive MCP session alone is not a scheduler.

## Detection Commands

Check only candidates relevant to the task and project:

```bash
command -v uv         # preferred Python runner
command -v python3    # fallback Python
command -v node       # Node project runtime
command -v motherduck # MotherDuck file workflows
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

Keep an existing compatible pin. For a new installation, select a supported version from the live response and use it in the matching client package. Reuse the response during the task; refresh it if compatibility fails or the version choice is stale.

## Install Snippets

Use a supported `<version>` compatible with the project and selected client package.

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

Use when the project or requested implementation uses Node/TypeScript.

### DuckDB CLI

```bash
curl -s https://install.motherduck.com | env -u motherduck_token HOME="$install_home" sh
```

Pick `$install_home` as a writable project-local directory (for example `./.duckdb`) so the install does not pollute the user's home. The CLI is appropriate for shell-driven ad-hoc exploration and for pipelines that are themselves shell scripts; for any program that already runs Python or Node, prefer the matching client library.

## Selection Examples

- The host project already commits to a language (a `pyproject.toml`, `package.json`, or comparable lockfile is present). Follow the project's language.
- The pipeline is a shell script and the workload is a single SQL file. The DuckDB CLI can fit without a Python or Node wrapper.
- The user explicitly asks for a specific runtime. Honor the request and skip detection.

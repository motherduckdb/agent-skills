# MotherDuck CLI Playbook

Reference for terminal-based MotherDuck work. Command flags can evolve; use current docs and `--help` as the runtime source of truth.

## Contents

| Section | Covers |
| --- | --- |
| CLI or MCP | Interface choice by task shape |
| Install and Upgrade | Platform-aware setup and current-version checks |
| Authentication and Isolation | Browser login, token automation, `MOTHERDUCK_HOME` |
| Output Contracts | JSON, CSV, exit codes, and filtering |
| Query Workflow | Read-only and write-query posture |
| Dive Workflow | Guide, init/pull, watch, push |
| Flight Workflow | Guide, init/pull, test, push, run, logs |
| Automation Safety | Mutations, secrets, signup, and cleanup |
| Troubleshooting | Common symptoms and next checks |

## CLI or MCP

Choose the interface independently from the SQL or product workflow.

| Task shape | Default |
| --- | --- |
| Coding agent with shell and filesystem | CLI |
| Dive or Flight source edited across iterations | CLI |
| CI job or shell automation | CLI |
| Large query result written to a file | CLI |
| Chat client without shell access | MCP |
| Inline catalog exploration or rendered Dive | MCP |
| Explore interactively, then implement in a repo | MCP for discovery, CLI for files and publication |

The CLI keeps source and large results out of model context. MCP exposes structured tools and inline resources. Do not force one interface across every phase.

## Install and Upgrade

Follow the current CLI install page. On macOS or Linux, the documented installer can install only the MotherDuck CLI:

```bash
curl -s https://install.motherduck.com | SKIP_DUCKDB_CLI=1 sh
```

Use the documented PowerShell installer on Windows. Do not translate the POSIX command mechanically.

```powershell
powershell -c "$env:SKIP_DUCKDB_CLI=1; irm https://install.motherduck.com | iex"
```

After installation:

```bash
motherduck status
motherduck upgrade
```

Run `upgrade` only when the user asks to upgrade or a current command reports an incompatible version. Never pipe an installer into a privileged shell without inspecting the environment and current docs.

## Authentication and Isolation

Interactive login opens a browser:

```bash
motherduck login
motherduck status
```

For CI or an agent runtime, inject a scoped token and isolate state:

```bash
: "${MOTHERDUCK_TOKEN:?inject a scoped MotherDuck token before running automation}"
export MOTHERDUCK_HOME="/absolute/task-specific/path/.motherduck"
motherduck status --output json
```

`MOTHERDUCK_HOME` must be absolute. Use one directory per concurrent job. Never echo the token, write it into CLI project files, or commit the state directory.

`motherduck new` creates an account and organization. Run it only for an explicit signup request; missing credentials alone do not authorize account creation.

## Output Contracts

Resource commands support structured output:

```bash
motherduck dive list --output json
motherduck flight list --output json
```

Successful resource operations return an object containing `success: true` plus a resource-shaped field. Failures return `success: false`, an error, and a non-zero process exit.

`motherduck query --output json` is different: it returns a bare JSON array. Use CSV for large tabular output:

```bash
motherduck query "SELECT * FROM sample_data.nyc.taxi LIMIT 1000" --output csv > result.csv
```

Filter JSON before reading it into context:

```bash
motherduck dive list --output json | jq -r '.dives[] | [.id, .title, .status] | @tsv'
```

## Query Workflow

Use DuckDB SQL even though the command is a thin terminal interface.

```bash
motherduck query "DESCRIBE sample_data.nyc.taxi" --output json
motherduck query "SELECT count(*) AS rows FROM sample_data.nyc.taxi" --output json
```

Prefer read-only inspection for exploratory work. A user request to query or inspect does not authorize DDL/DML. When a write is requested, make the target explicit and verify it afterward with a separate read.

## Dive Workflow

Read the current guide before writing code:

```bash
motherduck dive guide
```

Create or pull a local Dive:

```bash
motherduck dive init taxi_trips --title "Taxi trips"
DIVE_ID_OR_NAME="taxi_trips"
motherduck dive pull "$DIVE_ID_OR_NAME"
```

Edit the generated source with the normal repository workflow, then preview without stealing focus and capture machine-readable events:

```bash
motherduck dive watch taxi_trips --no-open --log-file preview.ndjson
```

Inspect compile and query events in the log. Publish only when requested:

```bash
motherduck dive push taxi_trips --output json
```

Read back the returned ID, URL, version, and status. A new Dive is Draft; promote it to Ready only after content, query, and viewport validation. Do not self-endorse it.

## Flight Workflow

Read the current guide first:

```bash
motherduck flight guide
```

Initialize or pull source, then keep Python and requirements in local files:

```bash
motherduck flight init --name nightly_load nightly_load
FLIGHT_ID_OR_NAME="nightly_load"
motherduck flight pull "$FLIGHT_ID_OR_NAME" --dir nightly_load
```

Use `motherduck flight --help` for the current local validation command and push flags. Create the remote Flight without a schedule, trigger one run, and capture its number:

```bash
motherduck flight push nightly_load --output json
motherduck flight run nightly_load --output json
```

Poll only the relevant run through the current exact-run command when available; otherwise list one newest run. On failure, read the bounded log tail:

```bash
motherduck flight list-runs nightly_load --limit 1 --output json
RUN_NUMBER="1"
motherduck flight logs nightly_load --run "$RUN_NUMBER" | tail -100
```

Attach a schedule only after a successful on-demand run and only when scheduling was requested. Use the CLI secret commands for secret metadata, but never place secret values in shell history or logs.

## Automation Safety

- Check the process exit code before parsing output.
- Use `set -euo pipefail` in repeatable shell automation.
- Bound polling and log output; stop on a terminal run state.
- Keep signup, publication, schedules, secrets, and deletes inside the explicit task scope.
- Use task-specific state and output paths; do not repurpose `HOME`.
- Read back remote resources after every mutation.
- Confirm destructive Dive/Flight deletion and explain whether recovery is possible.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Command or flag rejected | Run the command's `--help`; do not rely on remembered syntax |
| `motherduck --version` reports an unexpected command surface | Check `command -v motherduck` and `motherduck --help` for a PATH collision; do not overwrite another installation implicitly |
| Browser login unavailable | Use an approved scoped `MOTHERDUCK_TOKEN`, not a pasted credential |
| Parallel agents affect each other | Give each an absolute, unique `MOTHERDUCK_HOME` |
| JSON parsing fails | Check exit code and whether `query` returned its documented bare array |
| Dive code fails at runtime | Re-read `motherduck dive guide`, then inspect the preview NDJSON |
| Flight run fails | Read the exact run and bounded logs; verify requirements, config, secrets, and runtime limit |
| CLI source differs from remote | Pull or list the remote version before pushing over it |

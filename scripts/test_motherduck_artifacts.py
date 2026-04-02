#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///

from __future__ import annotations

import argparse
import os
import sys

from _lib.motherduck_artifacts import (
    REFERENCE_PROJECT,
    artifact_env,
    expected_user_agent,
    pipeline_env,
    require_motherduck_token,
    run_command,
    selected_artifacts,
    verify_artifact_output,
)
from _lib.repo import ROOT


def run_checked(command: list[str], *, env: dict[str, str], cwd=ROOT) -> str:
    print(f"$ {' '.join(command)}")
    result = run_command(command, cwd=cwd, env=env)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.exit_code != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.exit_code}: {' '.join(command)}"
        )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MotherDuck-backed artifact smoke tests.")
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="Optional subset of artifact slugs to run.",
    )
    parser.add_argument(
        "--skip-reference-project",
        action="store_true",
        help="Skip the dlt+dbt reference project smoke test.",
    )
    args = parser.parse_args()

    require_motherduck_token()

    env = os.environ.copy()
    expected_agent = expected_user_agent(env)

    for artifact in selected_artifacts(args.artifacts):
        stdout = run_checked(
            ["uv", "run", "--with", "duckdb", "python", str(artifact.path)],
            env=artifact_env(artifact.slug, env),
        )
        verify_artifact_output(
            artifact.path,
            stdout,
            expected_agent=expected_agent,
        )

    if not args.skip_reference_project:
        reference_env = pipeline_env(env)
        try:
            run_checked(["uv", "sync", "--python", "3.12"], env=reference_env, cwd=REFERENCE_PROJECT)
            run_checked(["uv", "run", "python", "pipeline/run_all.py"], env=reference_env, cwd=REFERENCE_PROJECT)
        finally:
            run_checked(["uv", "run", "python", "pipeline/cleanup.py"], env=reference_env, cwd=REFERENCE_PROJECT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

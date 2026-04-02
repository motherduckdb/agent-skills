#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///

from __future__ import annotations

import argparse
import json
from _lib.motherduck_artifacts import (
    REFERENCE_PROJECT,
    artifact_env,
    pipeline_env,
    require_motherduck_token,
    run_command,
    selected_artifacts,
    summary_with_output,
)
from _lib.repo import ROOT


def benchmark_artifact(slug: str, path, runs: int) -> dict[str, object]:
    run_results: list[dict[str, object]] = []
    for _ in range(runs):
        result = run_command(
            ["uv", "run", "--with", "duckdb", "python", str(path)],
            cwd=ROOT,
            env=artifact_env(slug),
        )
        entry = result.to_summary()
        if result.exit_code == 0:
            payload = json.loads(result.stdout)
            entry["backend"] = payload.get("backend", {})
            entry["top_level_keys"] = sorted(payload.keys())
        else:
            entry.update(summary_with_output(result))
        run_results.append(entry)

    return {
        "name": slug,
        "type": "artifact",
        "runs": run_results,
    }


def benchmark_reference_pipeline(runs: int) -> dict[str, object]:
    run_results: list[dict[str, object]] = []
    for _ in range(runs):
        env = pipeline_env()

        sync_result = run_command(["uv", "sync", "--python", "3.12"], cwd=REFERENCE_PROJECT, env=env)
        run_entry: dict[str, object] = {"uv_sync": sync_result.to_summary()}

        if sync_result.exit_code == 0:
            pipeline_result = run_command(
                ["uv", "run", "python", "pipeline/run_all.py"],
                cwd=REFERENCE_PROJECT,
                env=env,
            )
            run_entry["run_all"] = summary_with_output(pipeline_result)
        else:
            run_entry["uv_sync"] = summary_with_output(sync_result)

        cleanup_result = run_command(
            ["uv", "run", "python", "pipeline/cleanup.py"],
            cwd=REFERENCE_PROJECT,
            env=env,
        )
        run_entry["cleanup"] = summary_with_output(cleanup_result)
        run_results.append(run_entry)

    return {
        "name": "build-data-pipeline-reference",
        "type": "reference-project",
        "runs": run_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark MotherDuck-backed use-case artifacts.")
    parser.add_argument("--runs", type=int, default=1, help="Number of times to run each artifact and the pipeline reference project.")
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="Optional subset of artifact slugs to benchmark.",
    )
    parser.add_argument(
        "--skip-reference-project",
        action="store_true",
        help="Skip the dlt+dbt reference project benchmark.",
    )
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    require_motherduck_token()

    report = {
        "artifact_runs": [
            benchmark_artifact(artifact.slug, artifact.path, args.runs)
            for artifact in selected_artifacts(args.artifacts)
        ],
    }
    if not args.skip_reference_project:
        report["reference_project"] = benchmark_reference_pipeline(args.runs)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = [
    ("build-cfa-app", ROOT / "skills" / "build-cfa-app" / "artifacts" / "customer_routing_example.py"),
    ("build-dashboard", ROOT / "skills" / "build-dashboard" / "artifacts" / "dashboard_story_example.py"),
    ("build-data-pipeline", ROOT / "skills" / "build-data-pipeline" / "artifacts" / "pipeline_stage_example.py"),
    ("migrate-to-motherduck", ROOT / "skills" / "migrate-to-motherduck" / "artifacts" / "migration_validation_example.py"),
    ("enable-self-serve-analytics", ROOT / "skills" / "enable-self-serve-analytics" / "artifacts" / "self_serve_rollout_example.py"),
    ("partner-delivery", ROOT / "skills" / "partner-delivery" / "artifacts" / "client_delivery_example.py"),
]
REFERENCE_PROJECT = ROOT / "skills" / "build-data-pipeline" / "references" / "dlt-dbt-motherduck-project"


def run_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], float]:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env)
    elapsed = time.perf_counter() - start
    return result, elapsed


def benchmark_artifact(slug: str, path: Path, runs: int) -> dict[str, object]:
    run_results: list[dict[str, object]] = []
    for _ in range(runs):
        env = os.environ.copy()
        env["MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK"] = "1"
        env["MOTHERDUCK_ARTIFACT_PREFIX"] = f"bench_{slug}_{uuid.uuid4().hex[:8]}"
        result, elapsed = run_command(["uv", "run", "--with", "duckdb", "python", str(path)], cwd=ROOT, env=env)
        entry: dict[str, object] = {
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 3),
        }
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            entry["backend"] = payload.get("backend", {})
            entry["top_level_keys"] = sorted(payload.keys())
        else:
            entry["stdout_tail"] = result.stdout[-2000:]
            entry["stderr_tail"] = result.stderr[-2000:]
        run_results.append(entry)

    return {
        "name": slug,
        "type": "artifact",
        "runs": run_results,
    }


def benchmark_reference_pipeline(runs: int) -> dict[str, object]:
    run_results: list[dict[str, object]] = []
    for _ in range(runs):
        env = os.environ.copy()
        env["MOTHERDUCK_PIPELINE_DB"] = f"bench_pipeline_{uuid.uuid4().hex[:8]}"
        env.pop("VIRTUAL_ENV", None)

        sync_result, sync_elapsed = run_command(["uv", "sync", "--python", "3.12"], cwd=REFERENCE_PROJECT, env=env)
        run_entry: dict[str, object] = {
            "uv_sync": {
                "exit_code": sync_result.returncode,
                "elapsed_seconds": round(sync_elapsed, 3),
            }
        }

        if sync_result.returncode == 0:
            pipeline_result, pipeline_elapsed = run_command(
                ["uv", "run", "python", "pipeline/run_all.py"],
                cwd=REFERENCE_PROJECT,
                env=env,
            )
            run_entry["run_all"] = {
                "exit_code": pipeline_result.returncode,
                "elapsed_seconds": round(pipeline_elapsed, 3),
                "stdout_tail": pipeline_result.stdout[-2000:],
                "stderr_tail": pipeline_result.stderr[-2000:],
            }
        else:
            run_entry["uv_sync"]["stdout_tail"] = sync_result.stdout[-2000:]
            run_entry["uv_sync"]["stderr_tail"] = sync_result.stderr[-2000:]

        cleanup_result, cleanup_elapsed = run_command(
            ["uv", "run", "python", "pipeline/cleanup.py"],
            cwd=REFERENCE_PROJECT,
            env=env,
        )
        run_entry["cleanup"] = {
            "exit_code": cleanup_result.returncode,
            "elapsed_seconds": round(cleanup_elapsed, 3),
            "stdout_tail": cleanup_result.stdout[-2000:],
            "stderr_tail": cleanup_result.stderr[-2000:],
        }
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
        "--skip-reference-project",
        action="store_true",
        help="Skip the dlt+dbt reference project benchmark.",
    )
    args = parser.parse_args()

    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if not os.environ.get("MOTHERDUCK_TOKEN"):
        raise RuntimeError("Missing MOTHERDUCK_TOKEN")

    report = {
        "artifact_runs": [benchmark_artifact(slug, path, args.runs) for slug, path in ARTIFACTS],
    }
    if not args.skip_reference_project:
        report["reference_project"] = benchmark_reference_pipeline(args.runs)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.motherduck_user_agent import build_use_case_user_agent

ARTIFACTS = [
    ROOT / "skills" / "build-cfa-app" / "artifacts" / "customer_routing_example.py",
    ROOT / "skills" / "build-dashboard" / "artifacts" / "dashboard_story_example.py",
    ROOT / "skills" / "build-data-pipeline" / "artifacts" / "pipeline_stage_example.py",
    ROOT / "skills" / "migrate-to-motherduck" / "artifacts" / "migration_validation_example.py",
    ROOT / "skills" / "enable-self-serve-analytics" / "artifacts" / "self_serve_rollout_example.py",
    ROOT / "skills" / "partner-delivery" / "artifacts" / "client_delivery_example.py",
]
REFERENCE_PROJECT = ROOT / "skills" / "build-data-pipeline" / "references" / "dlt-dbt-motherduck-project"


def run(command: list[str], *, env: dict[str, str], cwd: Path | None = None) -> str:
    print(f"$ {' '.join(command)}")
    result = subprocess.run(
        command,
        check=True,
        cwd=cwd or ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.stdout


def verify_artifact_output(artifact: Path, stdout: str, *, expected_user_agent: str) -> None:
    payload = json.loads(stdout)
    actual = payload.get("backend", {}).get("user_agent")
    if actual != expected_user_agent:
        raise RuntimeError(
            f"{artifact.name} returned user_agent={actual!r}, expected {expected_user_agent!r}"
        )


def main() -> int:
    if not os.environ.get("MOTHERDUCK_TOKEN"):
        raise RuntimeError("Missing MOTHERDUCK_TOKEN")

    env = os.environ.copy()
    env["MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK"] = "1"
    expected_user_agent = build_use_case_user_agent(
        harness=env.get("MOTHERDUCK_AGENT_HARNESS"),
        llm=env.get("MOTHERDUCK_AGENT_LLM"),
    )

    for artifact in ARTIFACTS:
        stdout = run(["uv", "run", "--with", "duckdb", "python", str(artifact)], env=env)
        verify_artifact_output(
            artifact,
            stdout,
            expected_user_agent=expected_user_agent,
        )

    pipeline_env = env.copy()
    pipeline_env["MOTHERDUCK_PIPELINE_DB"] = f"tmp_agent_skills_pipeline_{uuid.uuid4().hex[:8]}"
    pipeline_env.pop("VIRTUAL_ENV", None)
    try:
        run(["uv", "sync", "--python", "3.12"], env=pipeline_env, cwd=REFERENCE_PROJECT)
        run(["uv", "run", "python", "pipeline/run_all.py"], env=pipeline_env, cwd=REFERENCE_PROJECT)
    finally:
        run(["uv", "run", "python", "pipeline/cleanup.py"], env=pipeline_env, cwd=REFERENCE_PROJECT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

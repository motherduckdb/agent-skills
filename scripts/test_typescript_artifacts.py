#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from motherduck_artifact_support import expected_user_agent
from repo_support import ROOT


TS_ARTIFACTS = [
    ROOT / "skills" / "build-cfa-app" / "artifacts" / "customer_routing_example.ts",
    ROOT / "skills" / "build-dashboard" / "artifacts" / "dashboard_story_example.ts",
    ROOT / "skills" / "build-data-pipeline" / "artifacts" / "pipeline_stage_example.ts",
    ROOT / "skills" / "migrate-to-motherduck" / "artifacts" / "migration_validation_example.ts",
    ROOT / "skills" / "enable-self-serve-analytics" / "artifacts" / "self_serve_rollout_example.ts",
    ROOT / "skills" / "partner-delivery" / "artifacts" / "client_delivery_example.ts",
]


def run_checked(command: list[str], *, cwd: Path = ROOT, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def main() -> int:
    env = os.environ.copy()
    expected_agent = expected_user_agent(env)

    with tempfile.TemporaryDirectory(prefix="md_ts_artifacts_") as tmpdir:
        out_dir = Path(tmpdir)
        for artifact in TS_ARTIFACTS:
            artifact_out_dir = out_dir / artifact.stem
            compile_command = [
                "npx",
                "--yes",
                "--package",
                "typescript",
                "tsc",
                "--outDir",
                str(artifact_out_dir),
                "--target",
                "ES2022",
                "--module",
                "commonjs",
                "--strict",
                "--skipLibCheck",
                "--pretty",
                "false",
                str(artifact),
            ]
            run_checked(compile_command, env=env)

            js_path = artifact_out_dir / f"{artifact.stem}.js"
            result = run_checked(["node", str(js_path)], env=env)
            payload = json.loads(result.stdout)
            actual = payload.get("backend", {}).get("user_agent")
            if actual != expected_agent:
                raise RuntimeError(
                    f"{artifact.name} returned user_agent={actual!r}, expected {expected_agent!r}"
                )

    print(f"Validated {len(TS_ARTIFACTS)} TypeScript artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

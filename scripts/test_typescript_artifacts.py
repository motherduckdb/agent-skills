#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from _lib.motherduck_artifacts import expected_user_agent, selected_artifacts
from _lib.repo import ROOT


def typescript_artifact_paths(selected_slugs: list[str] | None = None) -> list[Path]:
    return [
        artifact.path.with_suffix(".ts")
        for artifact in selected_artifacts(selected_slugs)
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
    parser = argparse.ArgumentParser(description="Compile and run TypeScript companion artifacts.")
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="Optional subset of artifact slugs to run.",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    expected_agent = expected_user_agent(env)
    artifact_paths = typescript_artifact_paths(args.artifacts)

    with tempfile.TemporaryDirectory(prefix="md_ts_artifacts_") as tmpdir:
        out_dir = Path(tmpdir)
        for artifact in artifact_paths:
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

    print(f"Validated {len(artifact_paths)} TypeScript artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

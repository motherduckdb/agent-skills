#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from _lib.codex import (
    CodexAppServer,
    CodexSupportError,
    IsolatedCodexHome,
    MARKETPLACE,
    plugin_name,
    require_codex_cli,
    use_case_skill_names,
)
from _lib.repo import ROOT
REQUIRED_KEYS = [
    "summary",
    "assumptions",
    "implementation_plan",
    "validation_plan",
    "risks",
]


class UseCaseTestError(Exception):
    pass


def parse_json_output(raw: str, *, skill_name: str) -> dict:
    candidate = raw.strip()
    if candidate.startswith("```"):
        raise UseCaseTestError(
            f"{skill_name} returned fenced JSON; use-case skills must emit raw JSON only when structured JSON is requested"
        )
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise UseCaseTestError(f"{skill_name} returned invalid JSON: {exc}") from exc


def run_use_case(env: dict[str, str], plugin_name: str, skill_name: str) -> dict[str, object]:
    prompt = (
        f"Use ${plugin_name}:{skill_name} to create a concise but concrete full use case. "
        "Ground it in real MotherDuck execution, preserve the skill's defaults and best practices, "
        "and return structured JSON with keys summary, assumptions, implementation_plan, validation_plan, and risks."
    )
    with tempfile.NamedTemporaryFile(prefix=f"{skill_name}-", suffix=".json", delete=False) as handle:
        output_path = Path(handle.name)

    start = time.perf_counter()
    result = subprocess.run(
        ["codex", "exec", "-C", str(ROOT), "-o", str(output_path), prompt],
        text=True,
        capture_output=True,
        env=env,
    )
    elapsed = round(time.perf_counter() - start, 3)

    entry: dict[str, object] = {
        "skill": skill_name,
        "elapsed_seconds": elapsed,
        "exit_code": result.returncode,
    }
    if result.returncode != 0:
        entry["stdout_tail"] = result.stdout[-1000:]
        entry["stderr_tail"] = result.stderr[-1000:]
        return entry

    try:
        raw = output_path.read_text()
        payload = parse_json_output(raw, skill_name=skill_name)
        missing = [key for key in REQUIRED_KEYS if key not in payload]
        if missing:
            raise UseCaseTestError(f"{skill_name} output missing keys: {missing}")

        entry["top_level_keys"] = sorted(payload.keys())
        entry["summary_preview"] = str(payload["summary"])[:160]
        return entry
    finally:
        output_path.unlink(missing_ok=True)


def main() -> int:
    require_codex_cli()

    parser = argparse.ArgumentParser(description="Exercise all MotherDuck use-case skills through the installed Codex plugin.")
    parser.add_argument(
        "--skills",
        nargs="*",
        help="Optional subset of use-case skill names to run. Defaults to all top-level use-case skills.",
    )
    args = parser.parse_args()

    current_plugin_name = plugin_name()
    default_skills = use_case_skill_names()
    selected_skills = args.skills or default_skills

    with IsolatedCodexHome(prefix="codex-usecase-home-") as (_, env):
        with CodexAppServer(env=env) as server:
            server.call("plugin/install", {"marketplacePath": str(MARKETPLACE), "pluginName": current_plugin_name})
            results = [run_use_case(env, current_plugin_name, skill_name) for skill_name in selected_skills]

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CodexSupportError as exc:
        print(f"Codex use-case test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except UseCaseTestError as exc:
        print(f"Codex use-case test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

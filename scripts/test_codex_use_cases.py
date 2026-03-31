#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
REQUIRED_KEYS = [
    "summary",
    "assumptions",
    "implementation_plan",
    "validation_plan",
    "risks",
]


class UseCaseTestError(Exception):
    pass


def rpc_call(proc: subprocess.Popen[str], request_id: int, method: str, params: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params

    assert proc.stdin is not None
    assert proc.stdout is not None

    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()

    while True:
        line = proc.stdout.readline()
        if not line:
            raise UseCaseTestError(f"app-server closed while waiting for {method}")
        message = json.loads(line)
        if message.get("id") == request_id:
            if "error" in message:
                raise UseCaseTestError(f"{method} failed: {message['error']}")
            return message["result"]


def normalize_json_output(raw: str) -> dict:
    candidate = raw.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    return json.loads(candidate)


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

    raw = output_path.read_text()
    payload = normalize_json_output(raw)
    missing = [key for key in REQUIRED_KEYS if key not in payload]
    if missing:
        raise UseCaseTestError(f"{skill_name} output missing keys: {missing}")

    entry["top_level_keys"] = sorted(payload.keys())
    entry["summary_preview"] = str(payload["summary"])[:160]
    return entry


def main() -> int:
    if shutil.which("codex") is None:
        raise UseCaseTestError("codex CLI is not installed or not on PATH")

    parser = argparse.ArgumentParser(description="Exercise all MotherDuck use-case skills through the installed Codex plugin.")
    parser.add_argument(
        "--skills",
        nargs="*",
        help="Optional subset of use-case skill names to run. Defaults to all top-level use-case skills.",
    )
    args = parser.parse_args()

    plugin_name = json.loads(PLUGIN_MANIFEST.read_text())["name"]
    default_skills = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md") if path.parent.name in {
        "build-cfa-app",
        "build-dashboard",
        "build-data-pipeline",
        "migrate-to-motherduck",
        "enable-self-serve-analytics",
        "partner-delivery",
    })
    selected_skills = args.skills or default_skills

    tmp_home = Path(tempfile.mkdtemp(prefix="codex-usecase-home-"))
    env = os.environ.copy()
    env["HOME"] = str(tmp_home)

    source_codex_home = Path.home() / ".codex"
    tmp_codex_home = tmp_home / ".codex"
    tmp_codex_home.mkdir(parents=True, exist_ok=True)
    for filename in ("auth.json", "config.toml"):
        source_path = source_codex_home / filename
        if source_path.exists():
            shutil.copy2(source_path, tmp_codex_home / filename)

    proc = subprocess.Popen(
        ["codex", "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        rpc_call(proc, 1, "initialize", {"protocolVersion": "0.1.0", "clientInfo": {"name": "codex-usecase-test", "version": "1.0.0"}})
        rpc_call(proc, 2, "plugin/install", {"marketplacePath": str(MARKETPLACE), "pluginName": plugin_name})
        results = [run_use_case(env, plugin_name, skill_name) for skill_name in selected_skills]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        shutil.rmtree(tmp_home, ignore_errors=True)

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UseCaseTestError as exc:
        print(f"Codex use-case test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

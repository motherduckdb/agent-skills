#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"


class SmokeTestError(Exception):
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
            raise SmokeTestError(f"app-server closed while waiting for {method}")
        message = json.loads(line)
        if message.get("id") == request_id:
            if "error" in message:
                raise SmokeTestError(f"{method} failed: {message['error']}")
            return message["result"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeTestError(message)


def main() -> int:
    if shutil.which("codex") is None:
        raise SmokeTestError("codex CLI is not installed or not on PATH")

    plugin_name = json.loads(PLUGIN_MANIFEST.read_text())["name"]
    source_skill_names = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))
    namespaced_skill_names = sorted(f"{plugin_name}:{skill_name}" for skill_name in source_skill_names)

    tmp_home = Path(tempfile.mkdtemp(prefix="codex-plugin-home-"))
    tmp_project = tmp_home / "scratch"
    tmp_project.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(tmp_home)

    proc = subprocess.Popen(
        ["codex", "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        rpc_call(proc, 1, "initialize", {"protocolVersion": "0.1.0", "clientInfo": {"name": "codex-plugin-smoke", "version": "1.0.0"}})

        listed = rpc_call(proc, 2, "plugin/list", {"cwds": [str(ROOT)], "forceRemoteSync": False})
        marketplaces = listed.get("marketplaces", [])
        require(marketplaces, "plugin/list returned no marketplaces")
        require(
            any(
                item.get("name") == plugin_name
                for marketplace in marketplaces
                for item in marketplace.get("plugins", [])
            ),
            "plugin/list did not expose the MotherDuck plugin",
        )

        plugin = rpc_call(
            proc,
            3,
            "plugin/read",
            {"marketplacePath": str(MARKETPLACE), "pluginName": plugin_name},
        ).get("plugin", {})
        plugin_skills = sorted(skill.get("name") for skill in plugin.get("skills", []))
        require(
            plugin_skills == namespaced_skill_names,
            f"plugin/read skill mismatch: expected {namespaced_skill_names}, found {plugin_skills}",
        )

        rpc_call(
            proc,
            4,
            "plugin/install",
            {"marketplacePath": str(MARKETPLACE), "pluginName": plugin_name},
        )

        installed = rpc_call(proc, 5, "plugin/list", {"cwds": [str(ROOT)], "forceRemoteSync": False})
        installed_plugin = next(
            item
            for marketplace in installed.get("marketplaces", [])
            for item in marketplace.get("plugins", [])
            if item.get("name") == plugin_name
        )
        require(installed_plugin.get("installed") is True, "plugin was not marked installed after plugin/install")
        require(installed_plugin.get("enabled") is True, "plugin was not marked enabled after plugin/install")

        skills_result = rpc_call(proc, 6, "skills/list", {"cwds": [str(tmp_project)], "forceReload": True})
        cwd_skill_sets = skills_result.get("data", [])
        require(cwd_skill_sets, "skills/list returned no cwd entries")
        resolved_skill_names = sorted(
            skill.get("name")
            for entry in cwd_skill_sets
            for skill in entry.get("skills", [])
            if skill.get("name") in set(namespaced_skill_names)
        )
        require(
            resolved_skill_names == namespaced_skill_names,
            f"skills/list did not surface installed plugin skills: expected {namespaced_skill_names}, found {resolved_skill_names}",
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    print(f"Codex plugin smoke test passed for {plugin_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeTestError as exc:
        print(f"Codex plugin smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

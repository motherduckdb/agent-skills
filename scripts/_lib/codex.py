from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from itertools import count
from pathlib import Path

from _lib.repo import ROOT, read_json_file


MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SKILLS_DIR = ROOT / "skills"
USE_CASE_SKILLS = {
    "build-cfa-app",
    "build-dashboard",
    "build-data-pipeline",
    "migrate-to-motherduck",
    "enable-self-serve-analytics",
    "partner-delivery",
}


class CodexSupportError(Exception):
    pass


def require_codex_cli() -> None:
    if shutil.which("codex") is None:
        raise CodexSupportError("codex CLI is not installed or not on PATH")


def plugin_name() -> str:
    return str(read_json_file(PLUGIN_MANIFEST)["name"])


def source_skill_names() -> list[str]:
    return sorted(path.parent.name for path in SKILLS_DIR.glob("*/SKILL.md"))


def use_case_skill_names() -> list[str]:
    return sorted(skill_name for skill_name in source_skill_names() if skill_name in USE_CASE_SKILLS)


class IsolatedCodexHome:
    def __init__(self, *, prefix: str) -> None:
        self.prefix = prefix
        self.home: Path | None = None

    def __enter__(self) -> tuple[Path, dict[str, str]]:
        self.home = Path(tempfile.mkdtemp(prefix=self.prefix))
        env = os.environ.copy()
        env["HOME"] = str(self.home)

        source_codex_home = Path.home() / ".codex"
        target_codex_home = self.home / ".codex"
        target_codex_home.mkdir(parents=True, exist_ok=True)
        for filename in ("auth.json", "config.toml"):
            source_path = source_codex_home / filename
            if source_path.exists():
                shutil.copy2(source_path, target_codex_home / filename)

        return self.home, env

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.home is not None:
            shutil.rmtree(self.home, ignore_errors=True)


class CodexAppServer:
    def __init__(self, *, env: dict[str, str]) -> None:
        self.env = env
        self.proc: subprocess.Popen[str] | None = None
        self._request_ids = count(1)

    def __enter__(self) -> "CodexAppServer":
        self.proc = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env,
        )
        self.call(
            "initialize",
            {
                "protocolVersion": "0.1.0",
                "clientInfo": {"name": "motherduck-codex-test", "version": "1.0.0"},
            },
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)

    def call(self, method: str, params: dict | None = None) -> dict:
        if self.proc is None or self.proc.stdin is None or self.proc.stdout is None:
            raise CodexSupportError("codex app-server is not running")

        request_id = next(self._request_ids)
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params

        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise CodexSupportError(f"codex app-server closed while waiting for {method}")
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise CodexSupportError(f"{method} failed: {message['error']}")
            return message["result"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CodexSupportError(message)

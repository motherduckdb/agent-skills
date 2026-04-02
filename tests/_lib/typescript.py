from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


TS_CHECK_SCRIPT = Path(__file__).resolve().parents[1] / "ts_syntax_check.js"
TS_LANGUAGES = {"ts", "tsx", "typescript", "javascript", "js"}
LANGUAGE_KINDS = {"ts": "TS", "tsx": "TSX", "javascript": "JS", "js": "JS"}


def validate_typescript_batch(
    snippets: list[tuple[int, object]],
) -> dict[int, list[str]]:
    if not snippets:
        return {}

    batch = []
    index_map: dict[int, int] = {}
    original_indexes = [original_index for original_index, _ in snippets]
    for batch_index, (original_index, snippet) in enumerate(snippets):
        batch.append(
            {
                "code": snippet.code,
                "kind": LANGUAGE_KINDS.get(snippet.language, "TS"),
            }
        )
        index_map[batch_index] = original_index

    try:
        result = _run_typescript_check(batch)
    except FileNotFoundError:
        return {
            original_index: ["  TypeScript/Node.js not available for syntax checking"]
            for original_index in original_indexes
        }
    except subprocess.TimeoutExpired:
        return {
            original_index: ["  TypeScript syntax check timed out"]
            for original_index in original_indexes
        }

    try:
        results = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        error_message = result.stderr.strip() or result.stdout.strip() or "Unknown parse error"
        return {
            original_index: [f"  {error_message}"]
            for original_index in original_indexes
        }

    return {
        index_map[entry["index"]]: [
            f"  Line {error['line']}: {error['message']}"
            for error in entry["errors"]
        ]
        for entry in results
        if entry["errors"]
    }


def _run_typescript_check(batch: list[dict[str, str]]) -> subprocess.CompletedProcess[str]:
    result = _invoke_ts_checker(batch)
    missing_typescript = "Cannot find module 'typescript'" in (result.stderr or "") or (
        "Cannot find module 'typescript'" in (result.stdout or "")
    )
    if not missing_typescript:
        return result

    with tempfile.TemporaryDirectory(prefix="md-skills-ts-") as temp_dir:
        temp_path = Path(temp_dir)
        subprocess.run(
            ["npm", "install", "--silent", "--prefix", str(temp_path), "typescript"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        env = os.environ.copy()
        node_path = str(temp_path / "node_modules")
        existing_node_path = env.get("NODE_PATH")
        env["NODE_PATH"] = node_path if not existing_node_path else f"{node_path}{os.pathsep}{existing_node_path}"
        return _invoke_ts_checker(batch, env=env)


def _invoke_ts_checker(
    batch: list[dict[str, str]],
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(TS_CHECK_SCRIPT)],
        input=json.dumps(batch),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

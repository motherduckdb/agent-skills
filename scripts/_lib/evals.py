from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from _lib.repo import ROOT

EVALS_DIR = ROOT / "evals"
GOLDEN_TASKS = EVALS_DIR / "golden_tasks.json"
SKILLS_DIR = ROOT / "skills"
CLAUDE_PLUGIN_DIR = ROOT / "plugins" / "motherduck-skills-claude"

SKILL_PATH_RE = re.compile(r"skills/(motherduck-[a-z0-9-]+)/SKILL\.md")
SKILL_NAME_RE = re.compile(r"\b(motherduck-[a-z0-9-]+)\b")
TASK_KEYS = {"id", "prompt", "expect_skills", "must", "must_not"}
HARNESSES = ("claude", "codex", "gemini")


class EvalError(Exception):
    pass


def source_skill_names() -> set[str]:
    return {path.parent.name for path in SKILLS_DIR.glob("*/SKILL.md")}


def load_tasks(path: Path = GOLDEN_TASKS) -> dict:
    payload = json.loads(path.read_text())
    validate_tasks(payload)
    return payload


def validate_tasks(payload: dict) -> None:
    """Static checks, run by validate_skills.py so the suite cannot drift from the catalog."""
    skills = source_skill_names()
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise EvalError(f"{GOLDEN_TASKS}: 'tasks' must be a non-empty list")
    seen: set[str] = set()
    for task in tasks:
        missing = TASK_KEYS - set(task)
        if missing:
            raise EvalError(f"{GOLDEN_TASKS}: task {task.get('id')!r} missing keys {sorted(missing)}")
        task_id = task["id"]
        if task_id in seen:
            raise EvalError(f"{GOLDEN_TASKS}: duplicate task id {task_id!r}")
        seen.add(task_id)
        if not task["expect_skills"]:
            raise EvalError(f"{GOLDEN_TASKS}: task {task_id!r} needs at least one expected skill")
        unknown = [name for name in task["expect_skills"] if name not in skills]
        if unknown:
            raise EvalError(f"{GOLDEN_TASKS}: task {task_id!r} expects unknown skills {unknown}")
        if not task["must"]:
            raise EvalError(f"{GOLDEN_TASKS}: task {task_id!r} needs at least one 'must' check")
        for check in [*task["must"], *task["must_not"]]:
            if not check.get("pattern") or not check.get("why"):
                raise EvalError(f"{GOLDEN_TASKS}: task {task_id!r} has a check without 'pattern' and 'why'")
            try:
                re.compile(check["pattern"])
            except re.error as exc:
                raise EvalError(f"{GOLDEN_TASKS}: task {task_id!r} has invalid regex {check['pattern']!r}: {exc}")


@dataclass
class RunOutput:
    answer: str
    loaded_skills: list[str]
    elapsed_seconds: float
    exit_code: int | None
    cost_usd: float | None = None
    error: str | None = None


@dataclass
class Grade:
    task_id: str
    run: int
    passed: bool
    routed: bool
    loaded_skills: list[str]
    failed_checks: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    cost_usd: float | None = None
    error: str | None = None


def _skills_in_text(text: str, known: set[str]) -> list[str]:
    found = {match for match in SKILL_PATH_RE.findall(text) if match in known}
    return sorted(found)


def _ordered_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def run_claude(prompt: str, *, model: str | None, timeout: int, known: set[str]) -> RunOutput:
    if shutil.which("claude") is None:
        raise EvalError("claude CLI is not installed or not on PATH")
    command = [
        "claude", "-p", prompt,
        "--plugin-dir", str(CLAUDE_PLUGIN_DIR),
        "--setting-sources", "project",
        "--strict-mcp-config",
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "bypassPermissions",
        "--disallowed-tools", "Bash,Write,Edit,NotebookEdit,WebFetch,WebSearch",
    ]
    if model:
        command += ["--model", model]
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="md-skill-eval-") as cwd:
        try:
            result = subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                                    timeout=timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return RunOutput("", [], time.perf_counter() - start, None, error="timeout")
    elapsed = time.perf_counter() - start
    loaded: list[str] = []
    answer = ""
    cost = None
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                payload = block.get("input", {})
                if block.get("name") == "Skill":
                    name = str(payload.get("skill", "")).split(":")[-1]
                    if name in known:
                        loaded.append(name)
                else:
                    loaded += _skills_in_text(json.dumps(payload), known)
        elif event.get("type") == "result":
            answer = event.get("result") or ""
            cost = event.get("total_cost_usd")
    error = None if result.returncode == 0 else result.stderr[-500:]
    return RunOutput(answer, _ordered_unique(loaded), elapsed, result.returncode, cost, error)


def run_codex(prompt: str, *, model: str | None, timeout: int, known: set[str]) -> RunOutput:
    """Runs through the installed Codex plugin in an isolated CODEX home.

    Skill loading is inferred from SKILL.md paths that appear in tool events, because
    Codex loads skills by reading their files.
    """
    from _lib.codex import MARKETPLACE, CodexAppServer, IsolatedCodexHome, plugin_name, require_codex_cli

    require_codex_cli()
    start = time.perf_counter()
    with IsolatedCodexHome(prefix="md-skill-eval-codex-") as (_, env):
        with CodexAppServer(env=env) as server:
            server.call("plugin/install", {"marketplacePath": str(MARKETPLACE), "pluginName": plugin_name()})
        with tempfile.TemporaryDirectory(prefix="md-skill-eval-") as cwd:
            output = Path(cwd) / "answer.txt"
            command = ["codex", "exec", "--json", "--ignore-user-config", "-C", cwd, "-o", str(output)]
            if model:
                command += ["--model", model]
            command.append(prompt)
            try:
                result = subprocess.run(command, text=True, capture_output=True, env=env,
                                        timeout=timeout, stdin=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                return RunOutput("", [], time.perf_counter() - start, None, error="timeout")
            answer = output.read_text() if output.exists() else ""
    loaded = _skills_in_text(result.stdout, known)
    error = None if result.returncode == 0 else result.stderr[-500:]
    return RunOutput(answer, loaded, time.perf_counter() - start, result.returncode, None, error)


def run_gemini(prompt: str, *, model: str | None, timeout: int, known: set[str]) -> RunOutput:
    """Runs headless Gemini CLI with the MotherDuck extension already installed
    (`gemini extensions install https://github.com/motherduckdb/agent-skills`).

    Skill loading is inferred from SKILL.md paths or skill names in tool-call events.
    """
    if shutil.which("gemini") is None:
        raise EvalError("gemini CLI is not installed or not on PATH")
    command = ["gemini", "-p", prompt, "--output-format", "stream-json"]
    if model:
        command += ["--model", model]
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="md-skill-eval-") as cwd:
        try:
            result = subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                                    timeout=timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return RunOutput("", [], time.perf_counter() - start, None, error="timeout")
    answer_parts: list[str] = []
    tool_text: list[str] = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = str(event.get("type", ""))
        if kind in {"tool_use", "tool_call"}:
            tool_text.append(json.dumps(event))
        elif kind == "message" and event.get("role") == "assistant":
            answer_parts.append(str(event.get("content", "")))
    tool_blob = "\n".join(tool_text)
    loaded = _skills_in_text(tool_blob, known) + [
        name for name in SKILL_NAME_RE.findall(tool_blob) if name in known
    ]
    error = None if result.returncode == 0 else result.stderr[-500:]
    return RunOutput("".join(answer_parts), _ordered_unique(loaded), time.perf_counter() - start,
                     result.returncode, None, error)


RUNNERS = {"claude": run_claude, "codex": run_codex, "gemini": run_gemini}


def grade(task: dict, run_index: int, output: RunOutput) -> Grade:
    routed = any(name in output.loaded_skills for name in task["expect_skills"])
    failed: list[str] = []
    if not routed:
        failed.append(f"routing: expected one of {task['expect_skills']}, loaded {output.loaded_skills or 'none'}")
    for check in task["must"]:
        if not re.search(check["pattern"], output.answer, re.IGNORECASE):
            failed.append(f"must: {check['why']} ({check['pattern']})")
    for check in task["must_not"]:
        if re.search(check["pattern"], output.answer, re.IGNORECASE):
            failed.append(f"must_not: {check['why']} ({check['pattern']})")
    if output.error:
        failed.append(f"error: {output.error[:200]}")
    return Grade(
        task_id=task["id"], run=run_index, passed=not failed, routed=routed,
        loaded_skills=output.loaded_skills, failed_checks=failed,
        elapsed_seconds=round(output.elapsed_seconds, 1), cost_usd=output.cost_usd, error=output.error,
    )


def summarize(grades: list[Grade], runs: int) -> dict:
    by_task: dict[str, list[Grade]] = {}
    for item in grades:
        by_task.setdefault(item.task_id, []).append(item)
    tasks = {}
    for task_id, items in by_task.items():
        passes = sum(item.passed for item in items)
        tasks[task_id] = {
            "passes": passes,
            "runs": len(items),
            "routing_hits": sum(item.routed for item in items),
            "intermittent": 0 < passes < len(items),
            "failures": sorted({check for item in items for check in item.failed_checks}),
        }
    total_runs = len(grades)
    return {
        "runs_per_task": runs,
        "task_pass_rate": round(sum(t["passes"] == t["runs"] for t in tasks.values()) / max(len(tasks), 1), 3),
        "run_pass_rate": round(sum(item.passed for item in grades) / max(total_runs, 1), 3),
        "routing_accuracy": round(sum(item.routed for item in grades) / max(total_runs, 1), 3),
        "cost_usd": round(sum(item.cost_usd or 0 for item in grades), 4),
        "tasks": tasks,
    }


def compare(current: dict, baseline: dict) -> dict:
    """Per-task flips. Aggregate scores hide regressions, so report every task that changed."""
    flips = {"regressed": [], "improved": []}
    for task_id, now in current["tasks"].items():
        before = baseline.get("tasks", {}).get(task_id)
        if before is None:
            continue
        now_ok = now["passes"] == now["runs"]
        before_ok = before["passes"] == before["runs"]
        if before_ok and not now_ok:
            flips["regressed"].append(task_id)
        elif now_ok and not before_ok:
            flips["improved"].append(task_id)
    return flips


def environment_label(harness: str, model: str | None) -> str:
    return f"{harness}:{model or os.environ.get('MOTHERDUCK_AGENT_LLM', 'default')}"

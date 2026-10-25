#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

"""Run the golden skill evals through an agent harness and report per-task results.

Each task checks two things: that the agent loaded an expected skill (routing), and
that its answer passes the task's rubric. Every task runs more than once because
regressions are often intermittent, and a baseline comparison reports which tasks
flipped rather than only the aggregate score.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from _lib.evals import (
    HARNESSES,
    RUNNERS,
    EvalError,
    compare,
    environment_label,
    grade,
    load_tasks,
    source_skill_names,
    summarize,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--harness", choices=HARNESSES, default="claude")
    parser.add_argument("--model", help="Model override passed to the harness CLI.")
    parser.add_argument("--runs", type=int, default=2, help="Runs per task (default 2).")
    parser.add_argument("--tasks", nargs="*", help="Subset of task ids.")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--plugin-dir", type=Path,
                        help="Claude only: plugin directory to test (default: this checkout's packaged plugin).")
    parser.add_argument("--out", type=Path, help="Write the full JSON report here.")
    parser.add_argument("--baseline", type=Path, help="Earlier report to compare per-task results against.")
    parser.add_argument("--fail-under", type=float, default=None,
                        help="Exit 1 when the run pass rate is below this value (0-1).")
    args = parser.parse_args()

    payload = load_tasks()
    tasks = payload["tasks"]
    if args.tasks:
        wanted = set(args.tasks)
        unknown = wanted - {task["id"] for task in tasks}
        if unknown:
            raise EvalError(f"unknown task ids: {sorted(unknown)}")
        tasks = [task for task in tasks if task["id"] in wanted]

    known = source_skill_names()
    runner = RUNNERS[args.harness]
    suffix = payload.get("instructions_suffix", "")
    jobs = [(task, run) for task in tasks for run in range(1, args.runs + 1)]

    def execute(job):
        task, run = job
        output = runner(f"{task['prompt']}\n\n{suffix}".strip(), model=args.model,
                        timeout=args.timeout_seconds, known=known, plugin_dir=args.plugin_dir)
        result = grade(task, run, output)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {task['id']} run {run} skills={result.loaded_skills}", file=sys.stderr)
        return result

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        grades = list(pool.map(execute, jobs))

    summary = summarize(grades, args.runs)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": environment_label(args.harness, args.model),
        "summary": summary,
        "runs": [vars(item) for item in grades],
    }
    if args.baseline:
        report["flips"] = compare(summary, json.loads(args.baseline.read_text())["summary"])

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps({key: summary[key] for key in ("task_pass_rate", "run_pass_rate", "routing_accuracy", "cost_usd")}))
    for task_id, entry in summary["tasks"].items():
        if entry["passes"] < entry["runs"]:
            flag = " (intermittent)" if entry["intermittent"] else ""
            print(f"- {task_id}: {entry['passes']}/{entry['runs']}{flag}")
            for failure in entry["failures"]:
                print(f"    {failure}")
    if "flips" in report:
        print(f"flips vs baseline: {json.dumps(report['flips'])}")

    if args.fail_under is not None and summary["run_pass_rate"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvalError as exc:
        print(f"skill evals failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

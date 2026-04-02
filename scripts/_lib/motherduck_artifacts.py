from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from _lib.motherduck_user_agent import build_use_case_user_agent
from _lib.repo import ROOT


@dataclass(frozen=True)
class ArtifactTarget:
    slug: str
    path: Path


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float

    def to_summary(self) -> dict[str, object]:
        return {
            "exit_code": self.exit_code,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }


ARTIFACT_TARGETS = [
    ArtifactTarget("build-cfa-app", ROOT / "skills" / "build-cfa-app" / "artifacts" / "customer_routing_example.py"),
    ArtifactTarget("build-dashboard", ROOT / "skills" / "build-dashboard" / "artifacts" / "dashboard_story_example.py"),
    ArtifactTarget("build-data-pipeline", ROOT / "skills" / "build-data-pipeline" / "artifacts" / "pipeline_stage_example.py"),
    ArtifactTarget("migrate-to-motherduck", ROOT / "skills" / "migrate-to-motherduck" / "artifacts" / "migration_validation_example.py"),
    ArtifactTarget("enable-self-serve-analytics", ROOT / "skills" / "enable-self-serve-analytics" / "artifacts" / "self_serve_rollout_example.py"),
    ArtifactTarget("partner-delivery", ROOT / "skills" / "partner-delivery" / "artifacts" / "client_delivery_example.py"),
]
REFERENCE_PROJECT = ROOT / "skills" / "build-data-pipeline" / "references" / "dlt-dbt-motherduck-project"


def selected_artifacts(selected_slugs: list[str] | None = None) -> list[ArtifactTarget]:
    if not selected_slugs:
        return ARTIFACT_TARGETS
    selected = set(selected_slugs)
    return [artifact for artifact in ARTIFACT_TARGETS if artifact.slug in selected]


def require_motherduck_token(env: dict[str, str] | None = None) -> None:
    if not (env or os.environ).get("MOTHERDUCK_TOKEN"):
        raise RuntimeError("Missing MOTHERDUCK_TOKEN")


def run_command(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str],
) -> CommandResult:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env)
    elapsed = time.perf_counter() - start
    return CommandResult(
        command=tuple(command),
        cwd=cwd,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        elapsed_seconds=elapsed,
    )


def artifact_env(
    slug: str,
    base_env: dict[str, str] | None = None,
    *,
    prefix: str | None = None,
) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK"] = "1"
    env["MOTHERDUCK_ARTIFACT_PREFIX"] = prefix or f"tmp_{slug}_{uuid.uuid4().hex[:8]}"
    return env


def pipeline_env(
    base_env: dict[str, str] | None = None,
    *,
    database_name: str | None = None,
) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["MOTHERDUCK_PIPELINE_DB"] = database_name or f"tmp_pipeline_{uuid.uuid4().hex[:8]}"
    env.pop("VIRTUAL_ENV", None)
    return env


def expected_user_agent(base_env: dict[str, str] | None = None) -> str:
    env = base_env or os.environ
    return build_use_case_user_agent(
        harness=env.get("MOTHERDUCK_AGENT_HARNESS"),
        llm=env.get("MOTHERDUCK_AGENT_LLM"),
    )


def verify_artifact_output(artifact: Path, stdout: str, *, expected_agent: str) -> None:
    payload = json.loads(stdout)
    actual = payload.get("backend", {}).get("user_agent")
    if actual != expected_agent:
        raise RuntimeError(
            f"{artifact.name} returned user_agent={actual!r}, expected {expected_agent!r}"
        )


def summary_with_output(result: CommandResult) -> dict[str, object]:
    summary = result.to_summary()
    summary["stdout_tail"] = result.stdout[-2000:]
    summary["stderr_tail"] = result.stderr[-2000:]
    return summary

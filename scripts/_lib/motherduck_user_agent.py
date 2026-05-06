from __future__ import annotations

import os
import re


INTEGRATION_NAME = "agent-skills"
INTEGRATION_VERSION = "2.2.0"
HARNESS_ENV_VAR = "MOTHERDUCK_AGENT_HARNESS"
LLM_ENV_VAR = "MOTHERDUCK_AGENT_LLM"
DEFAULT_HARNESS = "unknown"
DEFAULT_LLM = "unknown"

INVALID_METADATA_RE = re.compile(r"[^A-Za-z0-9._-]+")


def normalize_metadata_value(value: str | None, *, fallback: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return fallback

    normalized = INVALID_METADATA_RE.sub("-", raw)
    normalized = normalized.strip("-._")
    return normalized or fallback


def build_use_case_user_agent(
    *,
    harness: str | None = None,
    llm: str | None = None,
) -> str:
    harness_value = normalize_metadata_value(
        harness if harness is not None else os.environ.get(HARNESS_ENV_VAR),
        fallback=DEFAULT_HARNESS,
    )
    llm_value = normalize_metadata_value(
        llm if llm is not None else os.environ.get(LLM_ENV_VAR),
        fallback=DEFAULT_LLM,
    )

    return (
        f"{INTEGRATION_NAME}/{INTEGRATION_VERSION}"
        f"(harness-{harness_value};llm-{llm_value})"
    )

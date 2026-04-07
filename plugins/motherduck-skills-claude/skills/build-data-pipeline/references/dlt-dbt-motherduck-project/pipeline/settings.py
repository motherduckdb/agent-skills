from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from scripts._lib.motherduck_user_agent import build_use_case_user_agent

DEFAULT_DATABASE = "md_skills_pipeline_demo"
DATABASE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
USER_AGENT = build_use_case_user_agent()


@dataclass(frozen=True)
class Settings:
    token: str
    database: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    return project_root() / "data"


def load_settings() -> Settings:
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise RuntimeError("Missing env var: MOTHERDUCK_TOKEN")

    database = os.environ.get("MOTHERDUCK_PIPELINE_DB", DEFAULT_DATABASE)
    if not DATABASE_RE.match(database):
        raise RuntimeError(
            "MOTHERDUCK_PIPELINE_DB must match ^[A-Za-z_][A-Za-z0-9_]*$"
        )

    return Settings(token=token, database=database)

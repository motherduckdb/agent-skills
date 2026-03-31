from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.bootstrap import bootstrap_database
from pipeline.load_raw import load_raw_data
from pipeline.settings import project_root


def resolve_dbt_binary() -> str:
    dbt_binary = shutil.which("dbt")
    if dbt_binary:
        return dbt_binary

    candidate = Path(sys.executable).resolve().with_name("dbt")
    if candidate.exists():
        return str(candidate)

    raise RuntimeError("dbt executable not found. Run `uv sync --python 3.12` first.")


def run_dbt_build() -> None:
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(project_root())
    subprocess.run(
        [resolve_dbt_binary(), "build"],
        check=True,
        cwd=project_root(),
        env=env,
    )


def run_validation() -> None:
    subprocess.run(
        [sys.executable, "pipeline/validate.py"],
        check=True,
        cwd=project_root(),
        env=os.environ.copy(),
    )


def main() -> None:
    bootstrap_database()
    load_raw_data()
    run_dbt_build()
    run_validation()


if __name__ == "__main__":
    main()

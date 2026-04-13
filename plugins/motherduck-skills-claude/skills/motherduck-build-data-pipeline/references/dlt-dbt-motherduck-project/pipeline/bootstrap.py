from __future__ import annotations

import duckdb

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.settings import USER_AGENT, load_settings

SCHEMAS = ("raw", "staging", "analytics")


def bootstrap_database() -> None:
    settings = load_settings()

    workspace = duckdb.connect(
        "md:",
        config={
            "motherduck_token": settings.token,
            "custom_user_agent": USER_AGENT,
        },
    )
    try:
        workspace.execute(f'CREATE DATABASE IF NOT EXISTS "{settings.database}"')
    finally:
        workspace.close()

    target = duckdb.connect(
        f"md:{settings.database}",
        config={
            "motherduck_token": settings.token,
            "custom_user_agent": USER_AGENT,
        },
    )
    try:
        for schema in SCHEMAS:
            target.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    finally:
        target.close()

    print(
        f"Bootstrapped MotherDuck database '{settings.database}' with schemas: "
        + ", ".join(SCHEMAS)
    )


if __name__ == "__main__":
    bootstrap_database()

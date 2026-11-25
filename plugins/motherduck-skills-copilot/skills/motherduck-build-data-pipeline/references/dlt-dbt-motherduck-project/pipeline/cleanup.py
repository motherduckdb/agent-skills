from __future__ import annotations

import duckdb

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.settings import USER_AGENT, load_settings


def cleanup_database() -> None:
    settings = load_settings()

    workspace = duckdb.connect(
        "md:",
        config={
            "motherduck_token": settings.token,
            "custom_user_agent": USER_AGENT,
        },
    )
    try:
        workspace.execute(f'DROP DATABASE IF EXISTS "{settings.database}"')
    finally:
        workspace.close()

    print(f"Dropped MotherDuck database '{settings.database}'.")


if __name__ == "__main__":
    cleanup_database()

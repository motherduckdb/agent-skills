from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import duckdb


DEFAULT_USER_AGENT = "agent-skills/1.0.0(artifact-tests)"
TRUTHY = {"1", "true", "yes", "on"}


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in TRUTHY


def sanitize_identifier(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_]+", "_", value.lower())
    cleaned = cleaned.strip("_")
    return cleaned or "artifact"


@dataclass
class ArtifactSession:
    conn: duckdb.DuckDBPyConnection
    mode: str
    databases: dict[str, str]
    created_databases: list[str]

    def database_name(self, key: str) -> str:
        return self.databases[key]

    def table(self, database_key: str, schema: str, table: str) -> str:
        return ".".join(
            [
                quote_ident(self.databases[database_key]),
                quote_ident(schema),
                quote_ident(table),
            ]
        )

    def describe(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "databases": self.databases,
        }


@contextmanager
def artifact_session(
    *,
    slug: str,
    database_keys: list[str],
    user_agent: str = DEFAULT_USER_AGENT,
) -> Iterator[ArtifactSession]:
    use_motherduck = env_flag("MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK")
    if not use_motherduck:
        conn = duckdb.connect()
        attached: dict[str, str] = {}
        try:
            for key in database_keys:
                name = sanitize_identifier(key)
                attached[key] = name
                conn.execute(f"ATTACH ':memory:' AS {quote_ident(name)}")
            yield ArtifactSession(
                conn=conn,
                mode="local",
                databases=attached,
                created_databases=[],
            )
        finally:
            conn.close()
        return

    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise RuntimeError(
            "MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK is set but MOTHERDUCK_TOKEN is missing"
        )

    prefix = os.environ.get("MOTHERDUCK_ARTIFACT_PREFIX")
    if prefix:
        prefix = sanitize_identifier(prefix)
    else:
        prefix = f"tmp_agent_skills_{sanitize_identifier(slug)}_{uuid.uuid4().hex[:8]}"

    conn = duckdb.connect(
        "md:",
        config={
            "motherduck_token": token,
            "custom_user_agent": user_agent,
        },
    )
    created_databases: list[str] = []
    databases: dict[str, str] = {}
    try:
        for key in database_keys:
            name = f"{prefix}_{sanitize_identifier(key)}"
            databases[key] = name
            conn.execute(f"CREATE DATABASE {quote_ident(name)}")
            created_databases.append(name)
        yield ArtifactSession(
            conn=conn,
            mode="motherduck",
            databases=databases,
            created_databases=created_databases,
        )
    finally:
        for database_name in reversed(created_databases):
            conn.execute(f"DROP DATABASE IF EXISTS {quote_ident(database_name)}")
        conn.close()

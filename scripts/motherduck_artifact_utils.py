from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import duckdb

from scripts.motherduck_user_agent import build_use_case_user_agent

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
    user_agent: str

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
            "user_agent": self.user_agent,
        }


def _local_session(database_keys: list[str], *, user_agent: str) -> Iterator[ArtifactSession]:
    conn = duckdb.connect()
    attached = {
        key: sanitize_identifier(key)
        for key in database_keys
    }
    try:
        for database_name in attached.values():
            conn.execute(f"ATTACH ':memory:' AS {quote_ident(database_name)}")
        yield ArtifactSession(
            conn=conn,
            mode="local",
            databases=attached,
            created_databases=[],
            user_agent=user_agent,
        )
    finally:
        conn.close()


def _resolve_motherduck_prefix(slug: str) -> str:
    prefix = os.environ.get("MOTHERDUCK_ARTIFACT_PREFIX")
    if prefix:
        return sanitize_identifier(prefix)
    return f"tmp_agent_skills_{sanitize_identifier(slug)}_{uuid.uuid4().hex[:8]}"


def _require_motherduck_token() -> str:
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if token:
        return token
    raise RuntimeError(
        "MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK is set but MOTHERDUCK_TOKEN is missing"
    )


def _motherduck_session(
    slug: str,
    database_keys: list[str],
    *,
    user_agent: str,
) -> Iterator[ArtifactSession]:
    conn = duckdb.connect(
        "md:",
        config={
            "motherduck_token": _require_motherduck_token(),
            "custom_user_agent": user_agent,
        },
    )
    created_databases: list[str] = []
    databases: dict[str, str] = {}
    prefix = _resolve_motherduck_prefix(slug)
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
            user_agent=user_agent,
        )
    finally:
        for database_name in reversed(created_databases):
            conn.execute(f"DROP DATABASE IF EXISTS {quote_ident(database_name)}")
        conn.close()


@contextmanager
def artifact_session(
    *,
    slug: str,
    database_keys: list[str],
    user_agent: str | None = None,
) -> Iterator[ArtifactSession]:
    effective_user_agent = user_agent or build_use_case_user_agent()
    if not env_flag("MOTHERDUCK_ARTIFACT_USE_MOTHERDUCK"):
        yield from _local_session(database_keys, user_agent=effective_user_agent)
        return

    yield from _motherduck_session(
        slug,
        database_keys,
        user_agent=effective_user_agent,
    )

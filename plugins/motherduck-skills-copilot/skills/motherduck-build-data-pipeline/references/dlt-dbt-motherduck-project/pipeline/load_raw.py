from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import dlt
from dlt.destinations import motherduck

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.settings import USER_AGENT, data_dir, load_settings


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


@dlt.resource(name="customers_raw")
def customers_raw() -> Iterator[dict[str, Any]]:
    yield from read_jsonl(data_dir() / "customers.jsonl")


@dlt.resource(name="orders_raw")
def orders_raw() -> Iterator[dict[str, Any]]:
    yield from read_jsonl(data_dir() / "orders.jsonl")


def load_raw_data() -> None:
    settings = load_settings()

    pipeline = dlt.pipeline(
        pipeline_name="md_skills_dlt_dbt_reference",
        destination=motherduck(
            {
                "database": settings.database,
                "password": settings.token,
                "custom_user_agent": USER_AGENT,
            }
        ),
        dataset_name="raw",
    )

    info = pipeline.run(
        [customers_raw(), orders_raw()],
        write_disposition="replace",
    )
    print(info)


if __name__ == "__main__":
    load_raw_data()

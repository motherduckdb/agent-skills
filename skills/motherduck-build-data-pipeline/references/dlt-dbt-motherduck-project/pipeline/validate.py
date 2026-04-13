from __future__ import annotations

from datetime import date
from decimal import Decimal

import duckdb

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.settings import USER_AGENT, load_settings

EXPECTED_SUMMARY = [
    ("c1", "Acme Rockets", "enterprise", "north_america", 2, Decimal("155.00"), date(2026, 1, 12)),
    ("c2", "Birch Analytics", "mid_market", "emea", 1, Decimal("75.00"), date(2026, 1, 14)),
    ("c3", "Cedar Logistics", "enterprise", "apac", 1, Decimal("200.00"), date(2026, 1, 20)),
]


def validate_pipeline() -> None:
    settings = load_settings()

    conn = duckdb.connect(
        f"md:{settings.database}",
        config={
            "motherduck_token": settings.token,
            "custom_user_agent": USER_AGENT,
        },
    )
    try:
        counts = conn.sql(
            """
            SELECT
                (SELECT count(*) FROM "raw"."customers_raw") AS raw_customers,
                (SELECT count(*) FROM "raw"."orders_raw") AS raw_orders,
                (SELECT count(*) FROM "staging"."stg_orders") AS staged_orders,
                (SELECT count(*) FROM "analytics"."fct_customer_revenue") AS mart_rows
            """
        ).fetchone()
        assert counts == (3, 6, 4, 3), counts

        summary = conn.sql(
            """
            SELECT
                customer_id,
                customer_name,
                segment,
                region,
                order_count,
                total_amount,
                last_order_date
            FROM "analytics"."fct_customer_revenue"
            ORDER BY customer_id
            """
        ).fetchall()
        assert summary == EXPECTED_SUMMARY, summary
    finally:
        conn.close()

    print("Validation passed.")
    for row in EXPECTED_SUMMARY:
        print(row)


if __name__ == "__main__":
    validate_pipeline()

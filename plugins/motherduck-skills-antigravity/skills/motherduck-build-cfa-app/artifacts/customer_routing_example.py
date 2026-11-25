import json
import sys
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts._lib.motherduck_artifact_utils import artifact_session


def fetch_rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    with artifact_session(
        slug="motherduck-build-cfa-app",
        database_keys=["customer_acme", "customer_globex"],
    ) as session:
        conn = session.conn
        for db_key, values in {
            "customer_acme": [(1, "search", 12.5), (2, "checkout", 18.0)],
            "customer_globex": [(1, "signup", 4.0), (2, "invoice_paid", 9.5)],
        }.items():
            conn.execute(
                f"""
                CREATE TABLE {session.table(db_key, "main", "analytics_events")} (
                    event_id INTEGER,
                    event_type VARCHAR,
                    revenue DOUBLE
                )
                """
            )
            conn.executemany(
                f"INSERT INTO {session.table(db_key, 'main', 'analytics_events')} VALUES (?, ?, ?)",
                values,
            )

        def query_customer(database_key: str) -> list[dict]:
            return fetch_rows(
                conn,
                f"""
                SELECT event_type, SUM(revenue) AS total_revenue
                FROM {session.table(database_key, "main", "analytics_events")}
                GROUP BY 1
                ORDER BY total_revenue DESC
                """,
            )

        result = {
            "backend": session.describe(),
            "pattern": "3-tier customer-facing analytics",
            "routing_mode": "per-customer database namespace",
            "customers": {
                "acme": query_customer("customer_acme"),
                "globex": query_customer("customer_globex"),
            },
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

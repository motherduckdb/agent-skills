import json
import sys
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts.motherduck_artifact_utils import artifact_session


def one(conn: duckdb.DuckDBPyConnection, sql: str) -> dict:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row))


def many(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    with artifact_session(slug="build-dashboard", database_keys=["analytics"]) as session:
        conn = session.conn
        orders_table = session.table("analytics", "main", "orders")
        conn.execute(
            f"""
            CREATE TABLE {orders_table} (
                order_id INTEGER,
                order_date DATE,
                category VARCHAR,
                customer_id INTEGER,
                revenue DOUBLE
            )
            """
        )
        conn.executemany(
            f"INSERT INTO {orders_table} VALUES (?, ?, ?, ?, ?)",
            [
                (1, "2026-01-03", "Database", 101, 1200.0),
                (2, "2026-01-07", "Compute", 102, 800.0),
                (3, "2026-02-11", "Database", 101, 1600.0),
                (4, "2026-02-21", "Sharing", 103, 400.0),
                (5, "2026-03-03", "Compute", 104, 2200.0),
                (6, "2026-03-18", "Database", 105, 900.0),
            ],
        )

        result = {
            "backend": session.describe(),
            "story": "Revenue and product mix",
            "kpis": one(
                conn,
                f"""
                SELECT
                  SUM(revenue) AS total_revenue,
                  COUNT(DISTINCT order_id) AS order_count,
                  COUNT(DISTINCT customer_id) AS customer_count
                FROM {orders_table}
                """,
            ),
            "trend": many(
                conn,
                f"""
                SELECT strftime(date_trunc('month', order_date), '%Y-%m') AS month,
                       SUM(revenue) AS revenue
                FROM {orders_table}
                GROUP BY 1
                ORDER BY 1
                """,
            ),
            "breakdown": many(
                conn,
                f"""
                SELECT category, SUM(revenue) AS revenue
                FROM {orders_table}
                GROUP BY 1
                ORDER BY revenue DESC
                """,
            ),
            "detail": many(
                conn,
                f"""
                SELECT strftime(order_date, '%Y-%m-%d') AS order_date,
                       category,
                       revenue
                FROM {orders_table}
                ORDER BY order_date DESC
                LIMIT 5
                """,
            ),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

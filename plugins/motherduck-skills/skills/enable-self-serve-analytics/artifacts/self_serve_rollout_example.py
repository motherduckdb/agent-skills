import json
import sys
from pathlib import Path

import duckdb

sys.path.append(str(Path(__file__).resolve().parents[3]))

from scripts.motherduck_artifact_utils import artifact_session


def fetch_rows(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    cursor = conn.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    with artifact_session(
        slug="enable-self-serve-analytics",
        database_keys=["analytics"],
    ) as session:
        conn = session.conn
        accounts_table = session.table("analytics", "main", "accounts")
        customer_health_view = session.table("analytics", "main", "customer_health")
        conn.execute(
            f"""
            CREATE TABLE {accounts_table} (
                team VARCHAR,
                account_id INTEGER,
                status VARCHAR,
                arr DOUBLE
            )
            """
        )
        conn.executemany(
            f"INSERT INTO {accounts_table} VALUES (?, ?, ?, ?)",
            [
                ("sales", 1, "healthy", 12000.0),
                ("sales", 2, "watch", 7000.0),
                ("success", 3, "healthy", 9000.0),
                ("success", 4, "risk", 5000.0),
            ],
        )
        conn.execute(
            f"""
            CREATE OR REPLACE VIEW {customer_health_view} AS
            SELECT team, account_id, status, arr
            FROM {accounts_table}
            WHERE status IS NOT NULL
            """
        )

        result = {
            "backend": session.describe(),
            "first_audience": "customer success",
            "first_asset": f"team KPI Dive on top of {customer_health_view}",
            "team_kpis": fetch_rows(
                conn,
                f"""
                SELECT team, COUNT(*) AS total_accounts, SUM(arr) AS total_arr
                FROM {customer_health_view}
                GROUP BY 1
                ORDER BY total_arr DESC
                """,
            ),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
